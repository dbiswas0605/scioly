"""Shared extraction prompt/schema and result cleanup, used by every
provider-specific parser (Anthropic, and the OpenAI-compatible path used for
OpenAI/Ollama/MLX) so they agree on the exact same output shape."""
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = (
    "You are an expert at digitizing Science Olympiad practice exams. You "
    "will be given the raw content of an uploaded question paper. Extract "
    "every question in the document, preserving the original question "
    "numbering and wording exactly. For each question, determine whether it "
    "is multiple-choice (mcq) or short-answer. For mcq questions, extract "
    "every answer option with its label (A, B, C, D, ...) and text.\n\n"
    "For every mcq question you MUST set suggested_correct_option_label: "
    "first check whether the source document itself indicates the correct "
    "option (an answer key, a marked/bolded answer, an asterisk, etc.) and "
    "use that if present. Otherwise, work out the correct answer yourself "
    "using your own subject-matter knowledge of the topic — these are "
    "ordinary Science Olympiad questions with a single objectively correct "
    "option, so you should almost always be able to determine one. Only "
    "leave suggested_correct_option_label null in the rare case where the "
    "question is genuinely ambiguous, malformed, or unanswerable from the "
    "given options even after reasoning about it — do not leave it null "
    "merely because the source lacks an explicit answer key.\n\n"
    "For explanation_text: if the source includes a written explanation, "
    "copy it in. Otherwise, write a brief (1-3 sentence) explanation "
    "yourself justifying why the correct option is right. Only leave it "
    "null if you couldn't determine a correct answer at all.\n\n"
    "A parent/teacher will review and can correct every suggestion before "
    "anything is shown to students, so it's fine to commit to a best-effort "
    "answer rather than abstaining — but never fabricate options or "
    "question text that isn't in the source. Call the "
    "record_parsed_questions tool exactly once with every question found."
)

QUESTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_number": {"type": "integer"},
                    "question_type": {
                        "type": "string",
                        "enum": ["mcq", "short_answer"],
                    },
                    "prompt_text": {"type": "string"},
                    "explanation_text": {"type": ["string", "null"]},
                    "short_answer_expected": {"type": ["string", "null"]},
                    "suggested_correct_option_label": {"type": ["string", "null"]},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "option_label": {"type": "string"},
                                "option_text": {"type": "string"},
                            },
                            "required": ["option_label", "option_text"],
                        },
                    },
                },
                "required": [
                    "question_number",
                    "question_type",
                    "prompt_text",
                    "options",
                ],
            },
        },
    },
    "required": ["questions"],
}

TOOL_NAME = "record_parsed_questions"
TOOL_DESCRIPTION = "Record every question extracted from the exam document."


def _clean_question(raw: dict[str, Any], fallback_number: int) -> dict[str, Any]:
    question_type = raw.get("question_type")
    if question_type not in ("mcq", "short_answer"):
        question_type = "mcq" if raw.get("options") else "short_answer"

    options: list[dict[str, Any]] = []
    suggested_label = raw.get("suggested_correct_option_label")
    if question_type == "mcq":
        for index, option in enumerate(raw.get("options") or []):
            label = str(option.get("option_label") or chr(ord("A") + index)).strip()
            options.append(
                {
                    "option_label": label,
                    "option_text": (option.get("option_text") or "").strip(),
                    "is_correct": bool(
                        suggested_label
                        and label.upper() == str(suggested_label).strip().upper()
                    ),
                    "display_order": index,
                }
            )

    return {
        "question_number": raw.get("question_number") or fallback_number,
        "question_type": question_type,
        "prompt_text": (raw.get("prompt_text") or "").strip(),
        "explanation_text": raw.get("explanation_text") or None,
        "short_answer_expected": raw.get("short_answer_expected") or None,
        "llm_suggested_answer": suggested_label or None,
        "options": options,
    }


def clean_parsed_questions(raw_questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize whatever the model returned into the shape
    `app.crud.questions.replace_questions_for_paper` expects, and always
    renumber sequentially by return order — trusting the model's own
    question_number values risks duplicates, which would violate the
    paper_id+question_number unique constraint."""
    cleaned = [
        _clean_question(raw, fallback_number=index + 1)
        for index, raw in enumerate(raw_questions)
    ]
    for index, question in enumerate(cleaned):
        question["question_number"] = index + 1
    return cleaned
