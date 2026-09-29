"""Parses an uploaded question paper into structured questions using
Anthropic Claude. Claude gets native PDF/image document blocks (no lossy
text extraction needed) for PDFs up to 100 pages — Claude's hard limit —
beyond that we fall back to text-only extraction. This is otherwise more
capable than the OpenAI-compatible path used for OpenAI/Ollama/MLX — see
`openai_compatible.py`.
"""
from __future__ import annotations

import base64
import io

import anthropic
from pypdf import PdfReader

from app.models.llm_provider import LlmProvider
from app.models.question_paper import QuestionPaper
from app.services.llm.errors import (
    LlmNotConfiguredError,
    LlmRequestError,
    LlmUnsupportedError,
)
from app.services.llm.schema import (
    QUESTIONS_SCHEMA,
    SYSTEM_PROMPT,
    TOOL_DESCRIPTION,
    TOOL_NAME,
    clean_parsed_questions,
)
from app.services.llm.text_extraction import (
    DOCX_CONTENT_TYPE,
    extract_docx_text,
    extract_pdf_text,
)

# Claude's native PDF document support hard-caps at 100 pages per request
# (each page is processed like an image internally). Beyond that we fall
# back to text-only extraction so large scanned exams still work, at the
# cost of losing embedded images/diagrams for this specific paper.
MAX_NATIVE_PDF_PAGES = 100

# Claude's context window is 200k input tokens. Page *count* alone doesn't
# predict token cost — a handful of high-resolution scanned pages can blow
# past this just as easily as hundreds of simple ones — so we also measure
# the actual token cost via the (free, no-completion) count_tokens endpoint
# and fall back to text extraction if the native PDF block would be too
# big, leaving headroom under the 200k limit for the system prompt/tools.
MAX_INPUT_TOKENS = 190_000

PARSE_TOOL = {
    "name": TOOL_NAME,
    "description": TOOL_DESCRIPTION,
    "input_schema": QUESTIONS_SCHEMA,
}


def _count_input_tokens(
    client: anthropic.Anthropic, provider: LlmProvider, content_block: dict
) -> int | None:
    """Returns None if counting itself fails — callers should treat that as
    "assume it's fine" and let the real request surface any error, rather
    than blocking a possibly-valid parse."""
    try:
        result = client.messages.count_tokens(
            model=provider.model_name,
            system=SYSTEM_PROMPT,
            tools=[PARSE_TOOL],
            tool_choice={"type": "tool", "name": TOOL_NAME},
            messages=[
                {
                    "role": "user",
                    "content": [content_block, {"type": "text", "text": "placeholder"}],
                }
            ],
        )
        return result.input_tokens
    except anthropic.APIError:
        return None


def _build_content_block(
    client: anthropic.Anthropic, provider: LlmProvider, paper: QuestionPaper
) -> dict:
    content_type = paper.source_content_type

    if content_type == "application/pdf":
        page_count = len(PdfReader(io.BytesIO(paper.source_file)).pages)
        if page_count <= MAX_NATIVE_PDF_PAGES:
            native_block = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.b64encode(paper.source_file).decode("ascii"),
                },
            }
            token_count = _count_input_tokens(client, provider, native_block)
            if token_count is None or token_count <= MAX_INPUT_TOKENS:
                return native_block

        text_block = {"type": "text", "text": extract_pdf_text(paper.source_file)}
        token_count = _count_input_tokens(client, provider, text_block)
        if token_count is not None and token_count > MAX_INPUT_TOKENS:
            raise LlmRequestError(
                f"{provider.display_name}: this document is too large to parse "
                f"in one request (~{token_count:,} tokens, over the "
                f"{MAX_INPUT_TOKENS:,} budget) even as plain text — try "
                "splitting it into smaller files."
            )
        return text_block

    if content_type.startswith("image/"):
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": content_type,
                "data": base64.b64encode(paper.source_file).decode("ascii"),
            },
        }

    if content_type == "text/plain":
        return {
            "type": "text",
            "text": paper.source_file.decode("utf-8", errors="replace"),
        }

    if content_type == DOCX_CONTENT_TYPE:
        return {"type": "text", "text": extract_docx_text(paper.source_file)}

    if content_type == "application/msword":
        raise LlmUnsupportedError(
            "Legacy .doc files aren't supported yet — please re-save the file "
            "as a PDF or .docx and upload again."
        )

    raise LlmUnsupportedError(
        f"Don't know how to parse files of type '{content_type}' yet."
    )


def test_anthropic_connection(provider: LlmProvider) -> dict:
    """Make a cheap, no-completion call (list models) to verify the
    provider's API key actually works, and whether its configured model is
    one the account can access. Never raises — always returns a result dict
    with `ok` describing what happened, so callers can surface it as a
    normal (200) response rather than an error."""
    client = anthropic.Anthropic(api_key=provider.api_key, base_url=provider.base_url or None)
    try:
        models = client.models.list(limit=100)
        model_ids = [m.id for m in models.data]
    except anthropic.AuthenticationError:
        return {
            "ok": False,
            "message": "The API key was rejected by Anthropic — it may be invalid, expired, or revoked.",
            "model_checked": provider.model_name,
            "model_available": None,
        }
    except anthropic.PermissionDeniedError:
        return {
            "ok": False,
            "message": "This API key doesn't have permission to access the Anthropic API.",
            "model_checked": provider.model_name,
            "model_available": None,
        }
    except anthropic.APIError as exc:
        return {
            "ok": False,
            "message": f"Couldn't reach Anthropic: {exc}",
            "model_checked": provider.model_name,
            "model_available": None,
        }

    model_available = provider.model_name in model_ids
    message = "API key is valid."
    if model_available:
        message += f" Model '{provider.model_name}' is available on this account."
    else:
        message += (
            f" Note: '{provider.model_name}' wasn't found in this account's "
            "available models — double check the model name."
        )

    return {
        "ok": True,
        "message": message,
        "model_checked": provider.model_name,
        "model_available": model_available,
    }


def parse_paper(provider: LlmProvider, paper: QuestionPaper) -> list[dict]:
    """Call Anthropic Claude to extract structured questions from a paper's
    uploaded source file. Returns cleaned question dicts ready for
    `app.crud.questions.replace_questions_for_paper`."""
    if not provider.api_key:
        raise LlmNotConfiguredError(
            f"{provider.display_name} has no API key set — add one in "
            "Admin → LLM Settings."
        )

    client = anthropic.Anthropic(api_key=provider.api_key, base_url=provider.base_url or None)
    content_block = _build_content_block(client, provider, paper)

    try:
        response = client.messages.create(
            model=provider.model_name,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=[PARSE_TOOL],
            tool_choice={"type": "tool", "name": TOOL_NAME},
            messages=[
                {
                    "role": "user",
                    "content": [
                        content_block,
                        {
                            "type": "text",
                            "text": (
                                f"This document is titled '{paper.title}'. "
                                "Extract every question from it."
                            ),
                        },
                    ],
                }
            ],
        )
    except anthropic.AuthenticationError as exc:
        raise LlmNotConfiguredError(
            f"{provider.display_name}'s API key was rejected — check it in "
            "Admin → LLM Settings."
        ) from exc
    except anthropic.APIError as exc:
        raise LlmRequestError(f"{provider.display_name} request failed: {exc}") from exc

    tool_use = next(
        (block for block in response.content if block.type == "tool_use"), None
    )
    if tool_use is None:
        raise LlmRequestError(f"{provider.display_name} didn't return any structured questions.")

    raw_questions = tool_use.input.get("questions") or []
    if not raw_questions:
        raise LlmRequestError(f"{provider.display_name} didn't find any questions in this document.")

    return clean_parsed_questions(raw_questions)
