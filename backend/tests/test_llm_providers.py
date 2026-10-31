"""Tests for local OpenAI-compatible LLM provider wiring."""

from __future__ import annotations

import json
from contextlib import contextmanager
from types import SimpleNamespace

from app.services.llm import anthropic_parser, dispatcher, openai_compatible
from app.services.llm.dispatcher import (
    _PARSERS,
)
from app.services.llm.dispatcher import (
    test_provider_connection as check_provider_connection,
)
from app.services.llm.errors import LlmRequestError


def _mock_message_stream(response, call_arguments):
    @contextmanager
    def stream(**kwargs):
        call_arguments.update(kwargs)
        yield SimpleNamespace(get_final_message=lambda: response)

    return stream


def test_lm_studio_uses_default_base_url() -> None:
    provider = SimpleNamespace(provider_key="lm_studio", base_url=None)

    assert openai_compatible._resolve_base_url(provider) == "http://lm-studio:1234/v1"


def test_local_loopback_base_url_uses_host_gateway_in_container(monkeypatch) -> None:
    monkeypatch.setattr(openai_compatible, "_is_containerized", lambda: True)
    provider = SimpleNamespace(
        provider_key="lm_studio",
        base_url="http://127.0.0.1:1234",
    )

    assert (
        openai_compatible._resolve_base_url(provider)
        == "http://host.docker.internal:1234/v1"
    )


def test_lm_studio_base_url_without_path_adds_v1(monkeypatch) -> None:
    monkeypatch.setattr(openai_compatible, "_is_containerized", lambda: False)
    provider = SimpleNamespace(
        provider_key="lm_studio",
        base_url="http://localhost:1234/",
    )

    assert openai_compatible._resolve_base_url(provider) == "http://localhost:1234/v1"


def test_local_loopback_base_url_stays_unchanged_outside_container(monkeypatch) -> None:
    monkeypatch.setattr(openai_compatible, "_is_containerized", lambda: False)
    provider = SimpleNamespace(
        provider_key="lm_studio",
        base_url="http://127.0.0.1:1234/v1",
    )

    assert openai_compatible._resolve_base_url(provider) == provider.base_url


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
        source_filename="sample.txt",
        source_content_type="text/plain",
        source_file=b"What is 2 + 2?",
    )
    progress_messages = []

    questions = openai_compatible.parse_paper(
        provider, paper, progress=progress_messages.append
    )

    assert call_arguments["tool_choice"] == "required"
    assert questions[0]["prompt_text"] == "What is 2 + 2?"
    assert any("Sending the document" in message for message in progress_messages)
    assert any(
        "Validated 1 extracted question" in message for message in progress_messages
    )


def test_markdown_is_read_as_text_by_all_provider_paths() -> None:
    paper = SimpleNamespace(
        title="Markdown questions",
        source_filename="questions.md",
        source_content_type="text/markdown",
        source_file=b"# Questions\n\n1. What is 2 + 2?",
    )

    compatible_content = openai_compatible._build_user_content(paper)
    anthropic_content = anthropic_parser._build_content_block(None, None, paper)

    assert compatible_content[0]["text"] == paper.source_file.decode()
    assert anthropic_content["text"] == paper.source_file.decode()


def test_markdown_extension_is_supported_with_generic_content_type() -> None:
    paper = SimpleNamespace(
        title="Markdown questions",
        source_filename="QUESTIONS.MARKDOWN",
        source_content_type="application/octet-stream",
        source_file=b"# Questions\n\n1. What is 2 + 2?",
    )

    assert openai_compatible._build_user_content(paper)[0]["text"] == (
        paper.source_file.decode()
    )
    assert anthropic_parser._build_content_block(None, None, paper)["text"] == (
        paper.source_file.decode()
    )


def test_anthropic_parser_uses_json_schema_output_without_tool_choice(
    monkeypatch,
) -> None:
    call_arguments = {}
    response = SimpleNamespace(
        content=[
            SimpleNamespace(
                type="text",
                text=json.dumps(
                    {
                        "questions": [
                            {
                                "question_number": 1,
                                "question_type": "short_answer",
                                "prompt_text": "What is 2 + 2?",
                                "explanation_text": None,
                                "short_answer_expected": "4",
                                "suggested_correct_option_label": None,
                                "options": [],
                            }
                        ]
                    }
                ),
            )
        ],
        stop_reason="end_turn",
        usage=SimpleNamespace(output_tokens=150),
    )

    client = SimpleNamespace(
        messages=SimpleNamespace(stream=_mock_message_stream(response, call_arguments)),
    )
    monkeypatch.setattr(
        anthropic_parser.anthropic, "Anthropic", lambda **_kwargs: client
    )
    monkeypatch.setattr(
        anthropic_parser,
        "_build_content_block",
        lambda *_args, **_kwargs: {"type": "text", "text": "Question source"},
    )
    provider = SimpleNamespace(
        api_key="test-key",
        base_url=None,
        display_name="Anthropic",
        model_name="claude-opus-5-5",
    )
    paper = SimpleNamespace(
        title="Sample",
        source_filename="sample.md",
    )

    questions = anthropic_parser.parse_paper(provider, paper)

    assert questions[0]["prompt_text"] == "What is 2 + 2?"
    assert call_arguments["max_tokens"] == anthropic_parser.MAX_OUTPUT_TOKENS
    assert "tool_choice" not in call_arguments
    assert "tools" not in call_arguments
    output_schema = call_arguments["extra_body"]["output_config"]["format"]["schema"]
    assert output_schema["required"] == ["questions"]
    assert output_schema["additionalProperties"] is False
    question_schema = output_schema["properties"]["questions"]["items"]
    assert question_schema["required"] == list(question_schema["properties"])
    assert question_schema["additionalProperties"] is False


def test_anthropic_parser_reports_truncated_output(monkeypatch) -> None:
    call_arguments = {}
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='{"questions":[{"prompt":"')],
        stop_reason="max_tokens",
        usage=SimpleNamespace(output_tokens=32_768),
    )

    client = SimpleNamespace(
        messages=SimpleNamespace(stream=_mock_message_stream(response, call_arguments)),
    )
    monkeypatch.setattr(
        anthropic_parser.anthropic, "Anthropic", lambda **_kwargs: client
    )
    monkeypatch.setattr(
        anthropic_parser,
        "_build_content_block",
        lambda *_args, **_kwargs: {"type": "text", "text": "Question source"},
    )
    provider = SimpleNamespace(
        api_key="test-key",
        base_url=None,
        display_name="Anthropic",
        model_name="claude-opus-5-5",
    )
    paper = SimpleNamespace(title="Sample", source_filename="sample.md")

    try:
        anthropic_parser.parse_paper(provider, paper)
    except LlmRequestError as exc:
        assert "response was truncated" in str(exc)
        assert "32,768-token output limit" in str(exc)
    else:
        raise AssertionError("Expected truncated Anthropic output to be rejected.")

    assert call_arguments["max_tokens"] == 32_768


def test_anthropic_token_count_uses_json_schema_without_tool_choice() -> None:
    call_arguments = {}

    def count_tokens(**kwargs):
        call_arguments.update(kwargs)
        return SimpleNamespace(input_tokens=42)

    client = SimpleNamespace(
        messages=SimpleNamespace(count_tokens=count_tokens),
    )
    provider = SimpleNamespace(model_name="claude-opus-5-5")

    assert (
        anthropic_parser._count_input_tokens(
            client, provider, {"type": "text", "text": "Question source"}
        )
        == 42
    )
    assert "tool_choice" not in call_arguments
    assert "tools" not in call_arguments
    assert "output_config" in call_arguments["extra_body"]


def test_dispatcher_logs_provider_failure_reason(monkeypatch) -> None:
    provider = SimpleNamespace(
        provider_key="openai",
        display_name="OpenAI",
        model_name="test-model",
    )

    def fail_parse(_provider, _paper, progress=None):
        raise LlmRequestError("Connection timed out after 30 seconds.")

    monkeypatch.setattr(
        dispatcher.admin_crud, "list_enabled_llm_providers", lambda _db: [provider]
    )
    monkeypatch.setitem(dispatcher._PARSERS, "openai", fail_parse)
    messages = []

    try:
        dispatcher.parse_paper_with_llm(None, None, progress=messages.append)
    except LlmRequestError as exc:
        assert "Connection timed out after 30 seconds." in str(exc)
    else:
        raise AssertionError("Expected parsing to fail when the provider times out.")

    assert any(
        "OpenAI failed: Connection timed out after 30 seconds." in message
        for message in messages
    )
