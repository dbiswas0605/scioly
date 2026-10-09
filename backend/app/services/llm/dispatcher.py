"""Entry point routers call to parse a paper. Tries every *enabled*
LLM provider in priority order (lowest `priority` number first — so local
providers like Ollama, LM Studio, and MLX can be given priority over cloud
ones) and falls back to the next provider if one fails, rather than requiring a single
"active" provider to work."""
from __future__ import annotations

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


def parse_paper_with_llm(db: Session, paper: QuestionPaper) -> list[dict]:
    providers = admin_crud.list_enabled_llm_providers(db)
    if not providers:
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
            return parser(provider, paper)
        except (LlmNotConfiguredError, LlmUnsupportedError, LlmRequestError) as exc:
            failures.append(f"{provider.display_name}: {exc}")
            continue

    raise LlmRequestError(
        "Every enabled LLM provider failed:\n" + "\n".join(failures)
    )
