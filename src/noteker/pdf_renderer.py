"""PDF page rasterization via PyMuPDF."""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

_DEFAULT_DPI = 150  # good balance of image quality vs. API payload size for handwritten notes


@dataclass
class RenderedPage:
    page_num: int      # 1-based
    image_base64: str  # base64-encoded PNG
    media_type: str = "image/png"


def render_pdf_pages(
    file_path: str,
    *,
    max_pages: int = 50,
    dpi: int = _DEFAULT_DPI,
    page_start: int | None = None,
    page_end: int | None = None,
) -> list[RenderedPage]:
    """Render each page of a PDF to a base64-encoded PNG.

    page_start / page_end are 1-based and inclusive. When provided, only pages
    in that range are rendered, overriding max_pages.
    Skips completely blank pages (pixmap is all-white) to avoid wasting API calls.
    """
    doc = fitz.open(file_path)
    total = doc.page_count

    if page_start is not None or page_end is not None:
        first = max(1, page_start or 1)
        last = min(total, page_end or total)
        if first > last:
            doc.close()
            raise ValueError(
                f"page_start ({first}) must be ≤ page_end ({last}); PDF has {total} pages."
            )
        indices = range(first - 1, last)
        logger.info("Page range requested: %d–%d of %d total", first, last, total)
    else:
        if total > max_pages:
            logger.warning(
                "PDF has %d pages; processing first %d (max_pages=%d)", total, max_pages, max_pages
            )
        indices = range(min(total, max_pages))

    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pages: list[RenderedPage] = []

    for i in indices:
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

        if _is_blank(pix):
            logger.debug("Page %d: blank, skipping", i + 1)
            continue

        png_bytes = pix.tobytes("png")
        encoded = base64.standard_b64encode(png_bytes).decode("ascii")
        pages.append(RenderedPage(page_num=i + 1, image_base64=encoded))
        logger.debug("Page %d rendered (%d KB)", i + 1, len(png_bytes) // 1024)

    doc.close()
    logger.info("Rendered %d page(s) from %s", len(pages), file_path)
    return pages


def _is_blank(pix: fitz.Pixmap, threshold: int = 250) -> bool:
    """Return True if a pixmap is effectively all white (no ink)."""
    samples = pix.samples
    # All RGB channels above threshold → blank
    return all(b >= threshold for b in samples)
