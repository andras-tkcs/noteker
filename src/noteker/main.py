"""Noteker MCP server — handwritten PDF notes → clean Markdown via Claude Vision."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from fastmcp import FastMCP

from .paths import CONFIG_FILE, LOG_FILE
from .pdf_renderer import render_pdf_pages
from .transcriber import transcribe_pages

VERSION = "0.1.0"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------- #
# Logging
# ---------------------------------------------------------------------------- #

def _setup_logging(level: str = "INFO") -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-8s [%(name)s] %(message)s")

    file_h = logging.FileHandler(LOG_FILE)
    file_h.setFormatter(fmt)

    # stderr only — stdout is the MCP wire protocol
    stderr_h = logging.StreamHandler(sys.stderr)
    stderr_h.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(file_h)
    root.addHandler(stderr_h)


# ---------------------------------------------------------------------------- #
# Config
# ---------------------------------------------------------------------------- #

def _load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_api_key(config: dict[str, Any]) -> str:
    key = (config.get("anthropic") or {}).get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError(
            "Anthropic API key not configured. "
            f"Set 'anthropic.api_key' in {CONFIG_FILE} "
            "or export the ANTHROPIC_API_KEY environment variable."
        )
    return key


# ---------------------------------------------------------------------------- #
# MCP server
# ---------------------------------------------------------------------------- #

mcp = FastMCP(name="noteker", version=VERSION)


@mcp.tool()
async def noteker_process_pdf(file_path: str, note_context: str = "") -> str:
    """Convert a local PDF of handwritten notes into clean Markdown using Claude Vision.

    file_path: absolute path to a PDF file on the local filesystem.
    note_context: optional hint about the content (e.g. 'team meeting 2025-06-20').
                  Helps Claude resolve ambiguous words.
    """
    config = _load_config()
    api_key = _get_api_key(config)
    model = (config.get("anthropic") or {}).get("model", "claude-sonnet-4-6")
    noteker_cfg = config.get("noteker") or {}
    max_pages = int(noteker_cfg.get("max_pages", 50))
    dpi = int(noteker_cfg.get("dpi", 150))

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {file_path}")

    logger.info(
        "Processing '%s' (model=%s, max_pages=%d, dpi=%d)", path.name, model, max_pages, dpi
    )
    pages = render_pdf_pages(str(path), max_pages=max_pages, dpi=dpi)

    if not pages:
        return "*(empty PDF — no pages rendered)*"

    return await transcribe_pages(
        pages,
        note_context=note_context,
        api_key=api_key,
        model=model,
    )


@mcp.tool()
async def noteker_status() -> dict[str, Any]:
    """Return Noteker version and configuration status."""
    config = _load_config()
    api_key_set = bool(
        (config.get("anthropic") or {}).get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    )
    noteker_cfg = config.get("noteker") or {}
    return {
        "version": VERSION,
        "config_file": str(CONFIG_FILE),
        "config_exists": CONFIG_FILE.exists(),
        "anthropic_api_key_set": api_key_set,
        "model": (config.get("anthropic") or {}).get("model", "claude-sonnet-4-6"),
        "max_pages": int(noteker_cfg.get("max_pages", 50)),
        "dpi": int(noteker_cfg.get("dpi", 150)),
    }


# ---------------------------------------------------------------------------- #
# Entry point
# ---------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    config = _load_config()
    log_level = (config.get("logging") or {}).get("level", "INFO")
    _setup_logging(log_level)
    logger.info("Noteker %s starting", VERSION)

    try:
        asyncio.run(mcp.run_async(transport="stdio"))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
