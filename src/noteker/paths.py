"""Runtime path resolution for config and logs.

In development (no PyInstaller bundle): config/ is found next to pyproject.toml.
When installed as Noteker.app: user data lives in ~/.noteker/ so it survives app updates.
Override with NOTEKER_CONFIG_DIR environment variable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def is_bundled() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def data_dir() -> Path:
    """Root directory for user data (config, logs)."""
    if env := os.environ.get("NOTEKER_CONFIG_DIR"):
        d = Path(env)
    elif is_bundled():
        d = Path.home() / ".noteker"
    else:
        # Walk up from this file to find the project root (contains pyproject.toml).
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "pyproject.toml").exists():
                return parent
        d = Path.home() / ".noteker"
    d.mkdir(parents=True, exist_ok=True)
    return d


DATA_DIR = data_dir()
CONFIG_FILE = DATA_DIR / "config" / "settings.yaml"
LOG_FILE = DATA_DIR / "logs" / "noteker.log"
