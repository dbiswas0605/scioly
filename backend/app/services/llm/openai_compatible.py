"""Parses an uploaded question paper via any OpenAI-compatible chat
completions endpoint. Used for the real OpenAI API, and for local models
served through an OpenAI-compatible server: Ollama exposes one natively at
`/v1`, and MLX models can be served the same way via a bridge like
`mlx_lm.server`. We don't load Ollama/MLX models in-process — "local LLM
support" here means talking to whatever local server you already have
running, pointed at by the provider's `base_url`.
"""
from __future__ import annotations

import base64
import json

import openai

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

# Only used when the provider row doesn't set its own base_url.
DEFAULT_BASE_URLS = {
    "ollama": "http://localhost:11434/v1",
    "mlx": "http://localhost:8080/v1",
}

PARSE_FUNCTION = {
    "type": "function",
    "function": {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "parameters": QUESTIONS_SCHEMA,
    },
}


def _resolve_base_url(provider: LlmProvider) -> str | None:
    return provider.base_url or DEFAULT_BASE_URLS.get(provider.provider_key)


def _client_for(provider: LlmProvider) -> openai.OpenAI:
    # Local servers usually don't check the key, but the SDK requires a
    # non-empty string.
    return openai.OpenAI(
        api_key=provider.api_key or "not-needed",
        base_url=_resolve_base_url(provider),
    )


def _build_user_content(paper: QuestionPaper) -> list[dict]:
    content_type = paper.source_content_type
    instruction = {
        "type": "text",
        "text": (
            f"This document is titled '{paper.title}'. Extract every "
            "question from it."
        ),
    }

    if content_type == "application/pdf":
        # No native PDF support over this API shape — text-only fallback,
        # so embedded images/diagrams are lost.
        return [{"type": "text", "text": extract_pdf_text(paper.source_file)}, instruction]

    if content_type.startswith("image/"):
        data_url = (
            f"data:{content_type};base64,"
            f"{base64.b64encode(paper.source_file).decode('ascii')}"
        )
        return [{"type": "image_url", "image_url": {"url": data_url}}, instruction]

    if content_type == "text/plain":
        return [
            {"type": "text", "text": paper.source_file.decode("utf-8", errors="replace")},
            instruction,
        ]

    if content_type == DOCX_CONTENT_TYPE:
        return [{"type": "text", "text": extract_docx_text(paper.source_file)}, instruction]

    if content_type == "application/msword":
        raise LlmUnsupportedError(
            "Legacy .doc files aren't supported yet — please re-save the "
            "file as a PDF or .docx and upload again."
        )

    raise LlmUnsupportedError(
        f"Don't know how to parse files of type '{content_type}' yet."
    )


def test_connection(provider: LlmProvider) -> dict:
    """Cheap connectivity/auth check: list models from the configured
    endpoint. Never raises — always returns a result dict."""
    if provider.provider_key == "openai" and not provider.api_key:
        return {
            "ok": False,
            "message": "No API key is set for OpenAI yet.",
            "model_checked": provider.model_name,
            "model_available": None,
        }

    base_url = _resolve_base_url(provider)
    client = _client_for(provider)
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
    except openai.AuthenticationError:
        return {
            "ok": False,
            "message": "The API key was rejected.",
            "model_checked": provider.model_name,
            "model_available": None,
        }
    except openai.APIConnectionError as exc:
        return {
            "ok": False,
            "message": f"Couldn't connect to {base_url or 'the API'} — is it running? ({exc})",
            "model_checked": provider.model_name,
            "model_available": None,
        }
    except openai.APIError as exc:
        return {
            "ok": False,
            "message": f"Request failed: {exc}",
            "model_checked": provider.model_name,
            "model_available": None,
        }

    model_available = provider.model_name in model_ids
    message = "Connection succeeded."
    if model_available:
        message += f" Model '{provider.model_name}' is available."
    else:
        message += (
            f" Note: '{provider.model_name}' wasn't in the list this endpoint "
            "reported — some local servers only list models that are "
            "already pulled/loaded, so double check the model name."
        )
    return {
        "ok": True,
        "message": message,
        "model_checked": provider.model_name,
        "model_available": model_available,
    }


def parse_paper(provider: LlmProvider, paper: QuestionPaper) -> list[dict]:
    if provider.provider_key == "openai" and not provider.api_key:
        raise LlmNotConfiguredError(
            f"{provider.display_name} has no API key set — add one in "
            "Admin → LLM Settings."
        )

    content = _build_user_content(paper)
    client = _client_for(provider)

    try:
        response = client.chat.completions.create(
            model=provider.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            tools=[PARSE_FUNCTION],
            tool_choice={"type": "function", "function": {"name": TOOL_NAME}},
        )
    except openai.AuthenticationError as exc:
        raise LlmNotConfiguredError(
            f"{provider.display_name}'s API key was rejected — check it in "
            "Admin → LLM Settings."
        ) from exc
    except openai.APIConnectionError as exc:
        base_url = _resolve_base_url(provider) or "the configured endpoint"
        raise LlmRequestError(
            f"Couldn't connect to {provider.display_name} at {base_url} — "
            f"is it running? ({exc})"
        ) from exc
    except openai.APIError as exc:
        raise LlmRequestError(f"{provider.display_name} request failed: {exc}") from exc

    message = response.choices[0].message
    tool_calls = message.tool_calls or []
    call = next((c for c in tool_calls if c.function.name == TOOL_NAME), None)
    if call is None:
        raise LlmRequestError(
            f"{provider.display_name} didn't call the extraction tool — its "
            "model may not support tool/function calling."
        )

    try:
        arguments = json.loads(call.function.arguments)
    except (TypeError, ValueError) as exc:
        raise LlmRequestError(
            f"{provider.display_name} returned malformed structured output: {exc}"
        ) from exc

    raw_questions = arguments.get("questions") or []
    if not raw_questions:
        raise LlmRequestError(
            f"{provider.display_name} didn't find any questions in this document."
        )

    return clean_parsed_questions(raw_questions)
