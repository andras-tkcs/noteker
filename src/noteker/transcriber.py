"""Handwriting transcription via Claude Vision API.

Each page image is sent to Claude in a separate API call so that:
- Context limits are never hit regardless of PDF length.
- Per-page errors are isolated and don't abort the whole document.
"""
from __future__ import annotations

import logging

import anthropic

from .pdf_renderer import RenderedPage

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are transcribing handwritten notes exported from Noteshelf3 on an iPad.
The handwriting may be irregular, messy, or use personal shorthand.

For each page image:
1. Read and transcribe all handwritten text. Use surrounding context to resolve ambiguous letters or words.
2. Preserve the original structure: headings, bullet points, numbered lists, underlines as **bold**.
3. If a sketch or diagram is present, describe it briefly in [square brackets].
4. Fix clear mis-reads caused by letterform ambiguity (e.g. "rn" vs "m", "cl" vs "d") using context.
5. Output clean, well-structured Markdown. No preamble, no commentary — only the transcribed notes.

If the page is blank or has no readable content, output exactly: *(blank)*\
"""


async def transcribe_pages(
    pages: list[RenderedPage],
    *,
    note_context: str = "",
    api_key: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 4096,
) -> str:
    """Transcribe a list of rendered PDF pages and return combined Markdown."""
    client = anthropic.AsyncAnthropic(api_key=api_key)
    results: list[str] = []

    try:
        for page in pages:
            logger.info("Transcribing page %d/%d", page.page_num, len(pages))

            content: list[dict] = []
            if note_context:
                content.append({"type": "text", "text": f"Context: {note_context}\n\n"})
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": page.media_type,
                    "data": page.image_base64,
                },
            })
            content.append({
                "type": "text",
                "text": "Transcribe and format these handwritten notes as clean Markdown.",
            })

            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content}],
            )
            page_text = response.content[0].text.strip()
            logger.debug("Page %d: %d chars", page.page_num, len(page_text))

            if page_text and page_text != "*(blank)*":
                results.append(f"## Page {page.page_num}\n\n{page_text}")
    finally:
        await client.close()

    return "\n\n---\n\n".join(results) if results else "*(no readable content found)*"
