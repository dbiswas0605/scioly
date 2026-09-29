"""Plain-text extraction for providers that don't have native PDF/image
document support (i.e. everything going through the OpenAI-compatible
path). Anthropic gets true PDF/image blocks instead — see
`anthropic_parser.py` — so this module is only used there for .docx."""
from __future__ import annotations

import io

from docx import Document
from pypdf import PdfReader

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def extract_docx_text(file_bytes: bytes) -> str:
    document = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def extract_pdf_text(file_bytes: bytes) -> str:
    """Text-only PDF extraction — loses images/diagrams/layout. Used as a
    fallback for providers without native PDF support."""
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
