"""Tests for local OpenAI-compatible LLM provider wiring."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.llm import openai_compatible
from app.services.llm.dispatcher import (
    _PARSERS,
)
from app.services.llm.dispatcher import (
    test_provider_connection as check_provider_connection,
)


def test_lm_studio_uses_default_base_url() -> None:
    provider = SimpleNamespace(provider_key="lm_studio", base_url=None)

    assert openai_compatible._resolve_base_url(provider) == "http://lm-studio:1234/v1"


def test_lm_studio_uses_openai_compatible_parser() -> None:
    assert _PARSERS["lm_studio"] is openai_compatible.parse_paper


def test_lm_studio_connection_test_uses_openai_compatible_path(
    monkeypatch,
) -> None:
    provider = SimpleNamespace(provider_key="lm_studio")
    expected = {
        "ok": True,
        "message": "Connection succeeded.",
        "model_checked": "loaded-model",
        "model_available": True,
    }
    monkeypatch.setattr(
        openai_compatible, "test_connection", lambda configured: expected
    )

    assert check_provider_connection(provider) == expected


def test_parse_paper_uses_supported_tool_choice(monkeypatch) -> None:
    call_arguments = {}

    def create_completion(**kwargs):
        call_arguments.update(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        tool_calls=[
                            SimpleNamespace(
                                function=SimpleNamespace(
                                    name="record_parsed_questions",
                                    arguments=(
                                        '{"questions":[{"question_number":1,'
                                        '"question_type":"short_answer",'
                                        '"prompt_text":"What is 2 + 2?",'
                                        '"options":[]}]}'
                                    ),
                                )
                            )
                        ]
                    )
                )
            ]
        )

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_completion),
        )
    )
    monkeypatch.setattr(openai_compatible, "_client_for", lambda provider: client)

    provider = SimpleNamespace(
        provider_key="lm_studio",
        api_key=None,
        model_name="qwen2.5-3b-instruct-mlx",
        display_name="LM Studio (local)",
    )
    paper = SimpleNamespace(
        title="Sample",
        source_content_type="text/plain",
        source_file=b"What is 2 + 2?",
    )

    questions = openai_compatible.parse_paper(provider, paper)

    assert call_arguments["tool_choice"] == "required"
    assert questions[0]["prompt_text"] == "What is 2 + 2?"
