# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Noteker.app
#
# Produces:
#   dist/Noteker.app/
#     Contents/MacOS/noteker   ← stdio MCP server (Claude's entry point)
#
# Build:
#   pip install pyinstaller
#   pyinstaller Noteker.spec
#
# Notes:
#   - Run on the target architecture. For Apple Silicon: arch -arm64 pyinstaller ...
#   - Code-signing and notarization are handled by build_dmg.sh.

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

SRC = str(Path("src").resolve())
sys.path.insert(0, SRC)

# Icon is optional — CI builds without one use the default macOS app icon.
_icon_candidate = os.environ.get("NOTEKER_ICNS", "src/noteker/resources/icon_512.png")
ICON = _icon_candidate if os.path.exists(_icon_candidate) else None

# fastmcp-slim is an optional alias; skip gracefully if not installed.
try:
    _fastmcp_slim_meta = copy_metadata("fastmcp-slim")
except Exception:
    _fastmcp_slim_meta = []

from PyInstaller.utils.hooks import collect_dynamic_libs

datas = [
    *collect_data_files("fastmcp"),
    *copy_metadata("fastmcp"),
    *_fastmcp_slim_meta,
    *collect_data_files("anthropic"),
    *collect_data_files("pymupdf"),
]

# PyMuPDF ships its own compiled libmupdf — must be bundled as a dynamic lib.
binaries = [
    *collect_dynamic_libs("pymupdf"),
]

hidden_imports = [
    "fastmcp",
    "mcp",
    "anthropic",
    "pymupdf",
    "fitz",
    "yaml",
]

a = Analysis(
    ["src/_entry.py"],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="noteker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,       # speaks MCP over stdio — must be a console app
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Noteker",
)

app = BUNDLE(
    coll,
    name="Noteker.app",
    icon=ICON,
    bundle_identifier="com.noteker.app",
    version="0.1.0",
    info_plist={
        "CFBundleDisplayName": "Noteker",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "1",
        "LSUIElement": True,           # no Dock icon — background helper
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "13.0",
        "com.apple.security.network.client": True,
    },
)
