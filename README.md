# Noteker

**Noteker** is a macOS MCP server that converts handwritten PDF notes into clean Markdown using Claude Vision. Give it a PDF, get back structured text — no OCR engine, no separate models, no setup beyond an Anthropic API key.

Designed for notes exported from **Noteshelf3** on iPad, but works with any handwritten PDF.

---

## How it works

```
Claude ──MCP stdio──▶ noteker
                          │
               ┌──────────▼──────────┐
               │  PyMuPDF             │
               │  PDF → PNG per page  │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │  Claude Vision API   │
               │  transcribe + format │
               └──────────┬──────────┘
                          │
               clean Markdown ──▶ Claude
```

Each page is rendered to an image and sent to Claude Vision, which transcribes the handwriting and formats it as Markdown in a single pass. Blank pages are skipped automatically.

---

## Tools

| Tool | Description |
|------|-------------|
| `noteker_process_pdf(file_path, note_context="")` | Transcribe a local PDF of handwritten notes. Returns clean Markdown. `note_context` is an optional hint (e.g. `"team meeting 2025-06-20"`) that helps Claude resolve ambiguous words. |
| `noteker_status()` | Return version, config path, and whether the API key is set. |

---

## Installation

### From the DMG (recommended)

1. Download the latest `Noteker-x.y.z.dmg` from the [Releases](../../releases) page.
2. Open the DMG and drag **Noteker.app** to `/Applications`.
3. Copy the example config to your home directory:

```bash
mkdir -p ~/.noteker/config
cp /Applications/Noteker.app/Contents/Resources/config/settings.yaml.example \
   ~/.noteker/config/settings.yaml
```

4. Edit `~/.noteker/config/settings.yaml` and add your Anthropic API key (see [Configuration](#configuration)).
5. Register Noteker with Claude (see [MCP registration](#mcp-registration)).

### From source

**Requirements:** Python 3.11+, macOS

```bash
git clone https://github.com/andras-tkcs/noteker
cd noteker
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Copy and edit the config:

```bash
cp config/settings.yaml.example config/settings.yaml
# Edit config/settings.yaml — add your Anthropic API key
```

Register Noteker with Claude (see [MCP registration](#mcp-registration)) using the path `.venv/bin/noteker`.

---

## Configuration

Config file location:

| Context | Path |
|---------|------|
| DMG install | `~/.noteker/config/settings.yaml` |
| From source | `config/settings.yaml` (next to `pyproject.toml`) |
| Override | Set `NOTEKER_CONFIG_DIR` environment variable |

```yaml
anthropic:
  # API key from console.anthropic.com → API Keys
  # Can also be set via the ANTHROPIC_API_KEY environment variable.
  api_key: sk-ant-api03-...
  # Model used for transcription.
  # claude-sonnet-4-6 is recommended. Use claude-opus-4-8 for very difficult handwriting.
  model: claude-sonnet-4-6

noteker:
  # Maximum pages to process per PDF (safety cap).
  max_pages: 50
  # Rendering resolution. 150 DPI works well for most handwriting.
  # Increase to 200 if the handwriting is very small.
  dpi: 150

logging:
  level: INFO
```

### Anthropic API key

Create a key at [console.anthropic.com](https://console.anthropic.com) → **API Keys**. It looks like `sk-ant-api03-...`.

You can set it in `settings.yaml` as shown above, or export it as an environment variable — Noteker checks both:

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

Adding the export to `~/.zshrc` means you never need it in the config file.

---

## MCP registration

Add Noteker to Claude's MCP configuration. The config file is `~/.claude/claude_desktop_config.json` (Claude desktop app) or the project-level `.claude/settings.json`.

### DMG install

```json
{
  "mcpServers": {
    "noteker": {
      "command": "/Applications/Noteker.app/Contents/MacOS/noteker"
    }
  }
}
```

### From source

```json
{
  "mcpServers": {
    "noteker": {
      "command": "/absolute/path/to/noteker/.venv/bin/noteker"
    }
  }
}
```

### With ANTHROPIC_API_KEY in the MCP config (alternative to settings.yaml)

```json
{
  "mcpServers": {
    "noteker": {
      "command": "/Applications/Noteker.app/Contents/MacOS/noteker",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-api03-..."
      }
    }
  }
}
```

After saving the config, restart Claude Code (or reload MCP servers) and run `noteker_status()` to confirm the setup.

---

## Usage

A typical session with both Noteker and [Loopline](https://github.com/andras-tkcs/loopline):

```
# 1. Find the PDF on Google Drive (via loopline)
drive_list_files(query="name contains 'Meeting Notes' and mimeType='application/pdf'")
→ file_id: "1aBcD..."

# 2. Download it locally (via loopline — drive_save_to_path)
drive_save_to_path(file_id="1aBcD...")
→ /Users/you/Downloads/Meeting Notes 2025-06-20.pdf

# 3. Transcribe the handwriting (via noteker)
noteker_process_pdf(
  file_path="/Users/you/Downloads/Meeting Notes 2025-06-20.pdf",
  note_context="product team standup"
)
→ ## Page 1
  ### Action items
  - Follow up with design on the onboarding flow
  ...
```

Noteker is source-agnostic — any local PDF works, regardless of how it got there.

---

## Building a DMG

```bash
pip install pyinstaller
brew install create-dmg
bash scripts/build_dmg.sh
```

Output: `dist/Noteker-<version>.dmg`

Optional code signing:

```bash
bash scripts/build_dmg.sh --sign "Developer ID Application: Your Name (TEAMID)"
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
