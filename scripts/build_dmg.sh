#!/usr/bin/env bash
# Build Noteker.dmg — a drag-to-install macOS disk image.
#
# Prerequisites (build machine only):
#   pip install pyinstaller
#   brew install create-dmg
#
# Usage:
#   ./scripts/build_dmg.sh [--sign "Developer ID Application: Your Name (TEAMID)"]
#
# Output: dist/Noteker-<version>.dmg
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ -x ".venv/bin/pyinstaller" ]; then
  PYTHON=".venv/bin/python"
  PYINSTALLER=".venv/bin/pyinstaller"
elif command -v pyinstaller &>/dev/null; then
  PYTHON="$(command -v python3)"
  PYINSTALLER="$(command -v pyinstaller)"
else
  echo "PyInstaller not found — installing into .venv…"
  .venv/bin/pip install --quiet pyinstaller
  PYTHON=".venv/bin/python"
  PYINSTALLER=".venv/bin/pyinstaller"
fi

VERSION=$("$PYTHON" -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['version'])")
APP_NAME="Noteker"
BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
DMG_PATH="dist/${DMG_NAME}"

SIGN_IDENTITY="${SIGN_IDENTITY:-}"
for arg in "$@"; do
  case "$arg" in
    --sign) SIGN_IDENTITY="${2:-}"; shift 2 ;;
  esac
done

echo "=== Building ${APP_NAME} ${VERSION} ==="

# ── 1. Convert PNG icon to ICNS ──────────────────────────────────────────────
ICON_SRC="src/noteker/resources/icon_512.png"
ICON_DIR="build/noteker_icons.iconset"
ICNS_PATH="build/noteker.icns"

if [ ! -f "$ICON_SRC" ]; then
  echo "⚠  Icon not found at ${ICON_SRC} — building without a custom icon"
fi
if [ -f "$ICON_SRC" ]; then
  echo "→ Converting icon to .icns…"
  mkdir -p "$ICON_DIR"
  sips -z 16 16     "$ICON_SRC" --out "${ICON_DIR}/icon_16x16.png"      >/dev/null
  sips -z 32 32     "$ICON_SRC" --out "${ICON_DIR}/icon_16x16@2x.png"   >/dev/null
  sips -z 32 32     "$ICON_SRC" --out "${ICON_DIR}/icon_32x32.png"      >/dev/null
  sips -z 64 64     "$ICON_SRC" --out "${ICON_DIR}/icon_32x32@2x.png"   >/dev/null
  sips -z 128 128   "$ICON_SRC" --out "${ICON_DIR}/icon_128x128.png"    >/dev/null
  sips -z 256 256   "$ICON_SRC" --out "${ICON_DIR}/icon_128x128@2x.png" >/dev/null
  sips -z 256 256   "$ICON_SRC" --out "${ICON_DIR}/icon_256x256.png"    >/dev/null
  sips -z 512 512   "$ICON_SRC" --out "${ICON_DIR}/icon_256x256@2x.png" >/dev/null
  cp "$ICON_SRC"                      "${ICON_DIR}/icon_512x512.png"
  iconutil -c icns "$ICON_DIR" -o "$ICNS_PATH"
  export NOTEKER_ICNS="$ICNS_PATH"
fi

# ── 2. Build .app bundle ──────────────────────────────────────────────────────
echo "→ Running PyInstaller…"
NOTEKER_ICNS="${NOTEKER_ICNS:-}" $PYINSTALLER --noconfirm Noteker.spec

# ── 3. Optional code signing ──────────────────────────────────────────────────
if [ -n "$SIGN_IDENTITY" ]; then
  echo "→ Code-signing with: ${SIGN_IDENTITY}"
  codesign --deep --force --options runtime \
    --sign "$SIGN_IDENTITY" \
    --entitlements scripts/entitlements.plist \
    "$BUNDLE"
fi

# ── 4. Package into DMG ───────────────────────────────────────────────────────
echo "→ Building DMG…"
rm -f "$DMG_PATH"

create-dmg \
  --volname "${APP_NAME}" \
  --window-pos 200 120 \
  --window-size 520 340 \
  --icon-size 128 \
  --icon "${APP_NAME}.app" 130 160 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 390 160 \
  --no-internet-enable \
  "$DMG_PATH" \
  "dist/${APP_NAME}.app"

echo ""
echo "✓ Done: ${DMG_PATH}"
echo "  Size: $(du -sh "${DMG_PATH}" | cut -f1)"
echo ""
echo "After install, add to Claude Code MCP config:"
echo "  noteker: /Applications/Noteker.app/Contents/MacOS/noteker"
