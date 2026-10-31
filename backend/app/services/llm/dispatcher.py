"""Entry point routers call to parse a paper. Tries every *enabled*
LLM provider in priority order (lowest `priority` number first — so local
providers like Ollama, LM Studio, and MLX can be given priority over cloud
ones) and falls back to the next provider if one fails, rather than requiring a single
"active" provider to work."""
from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.crud import admin_settings as admin_crud
from app.models.llm_provider import LlmProvider
from app.models.question_paper import QuestionPaper
from app.services.llm import anthropic_parser, openai_compatible
from app.services.llm.errors import (
    LlmNotConfiguredError,
    LlmRequestError,
    LlmUnsupportedError,
)

_PARSERS = {
    "anthropic": anthropic_parser.parse_paper,
    "openai": openai_compatible.parse_paper,
    "ollama": openai_compatible.parse_paper,
    "lm_studio": openai_compatible.parse_paper,
    "mlx": openai_compatible.parse_paper,
}


def test_provider_connection(provider: LlmProvider) -> dict:
    if provider.provider_key == "anthropic":
        return anthropic_parser.test_anthropic_connection(provider)
    if provider.provider_key in ("openai", "ollama", "lm_studio", "mlx"):
        return openai_compatible.test_connection(provider)
    return {
        "ok": False,
        "message": f"Testing isn't implemented for '{provider.provider_key}' yet.",
        "model_checked": provider.model_name,
        "model_available": None,
    }


def parse_paper_with_llm(
    db: Session,
    paper: QuestionPaper,
    progress: Callable[[str], None] | None = None,
) -> list[dict]:
    if progress:
        progress("Checking enabled LLM providers in configured priority order.")
    providers = admin_crud.list_enabled_llm_providers(db)
    if not providers:
        if progress:
            progress("No enabled LLM providers are available.")
        raise LlmNotConfiguredError(
            "No LLM provider is enabled. Turn one on in Admin → LLM "
            "Settings first."
        )

    failures: list[str] = []
    for provider in providers:
        parser = _PARSERS.get(provider.provider_key)
        if parser is None:
            failures.append(f"{provider.display_name}: unsupported provider.")
            continue

        try:
            if progress:
                progress(
                    f"Starting {provider.display_name} with model "
                    f"'{provider.model_name}'."
                )
            questions = parser(provider, paper, progress=progress)
            if progress:
                progress(
                    f"{provider.display_name} returned {len(questions)} "
                    "structured question(s)."
                )
            return questions
        except (LlmNotConfiguredError, LlmUnsupportedError, LlmRequestError) as exc:
            failures.append(f"{provider.display_name}: {exc}")
            if progress:
                progress(
                    f"{provider.display_name} failed: {exc} "
                    "Checking the next enabled provider."
                )
            continue

    raise LlmRequestError(
        "Every enabled LLM provider failed:\n" + "\n".join(failures)
    )
