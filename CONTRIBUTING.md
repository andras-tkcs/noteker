# Contributing

Contributions are welcome. The `main` branch is protected; all changes go through pull requests.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Build the DMG

```bash
./scripts/build_dmg.sh
```

## Code style

- Follow existing patterns in the codebase.
- No comments unless the *why* is non-obvious.
- Keep dependencies minimal.
