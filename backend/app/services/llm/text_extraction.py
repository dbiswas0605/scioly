"""Plain-text extraction for providers that don't have native PDF/image
document support (i.e. everything going through the OpenAI-compatible
path). Anthropic gets true PDF/image blocks instead — see
`anthropic_parser.py` — so this module is only used there for .docx."""
from __future__ import annotations

import io
from collections.abc import Callable

from docx import Document
from pypdf import PdfReader

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
MARKDOWN_CONTENT_TYPES = {"text/markdown", "text/x-markdown"}


def is_markdown_file(content_type: str, filename: str) -> bool:
    normalized_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    return normalized_type in MARKDOWN_CONTENT_TYPES or filename.lower().endswith(
        (".md", ".markdown")
    )


def extract_docx_text(
    file_bytes: bytes, progress: Callable[[str], None] | None = None
) -> str:
    if progress:
        progress("Reading text paragraphs from the Word document.")
    document = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def extract_pdf_text(
    file_bytes: bytes, progress: Callable[[str], None] | None = None
) -> str:
    """Text-only PDF extraction — loses images/diagrams/layout. Used as a
    fallback for providers without native PDF support."""
    reader = PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)
    if progress:
        progress(f"Reading selectable text from {page_count} PDF page(s).")

    text: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text.append(page.extract_text() or "")
        if progress and (index == 1 or index % 5 == 0 or index == page_count):
            progress(f"Read PDF page {index} of {page_count}.")
    return "\n".join(text)
