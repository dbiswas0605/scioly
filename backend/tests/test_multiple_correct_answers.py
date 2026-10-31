from __future__ import annotations

import uuid

from app.crud.exam_attempts import _is_exact_option_selection
from app.schemas.exam_attempt import AnswerInput
from app.services.llm.schema import clean_parsed_questions


def test_multiple_correct_labels_are_cleaned() -> None:
    [question] = clean_parsed_questions(
        [
            {
                "question_number": 1,
                "question_type": "mcq",
                "prompt_text": "Select all that apply",
                "suggested_correct_option_labels": ["a", "C"],
                "options": [
                    {"option_label": "A", "option_text": "first"},
                    {"option_label": "B", "option_text": "second"},
                    {"option_label": "C", "option_text": "third"},
                ],
            }
        ]
    )

    assert [option["is_correct"] for option in question["options"]] == [
        True,
        False,
        True,
    ]
    assert question["llm_suggested_answer"] == "A, C"


def test_parser_accepts_legacy_single_correct_label() -> None:
    [question] = clean_parsed_questions(
        [
            {
                "question_type": "mcq",
                "suggested_correct_option_label": "B",
                "options": [
                    {"option_label": "A", "option_text": "first"},
                    {"option_label": "B", "option_text": "second"},
                ],
            }
        ]
    )

    assert [option["is_correct"] for option in question["options"]] == [False, True]
    assert question["llm_suggested_answer"] == "B"


def test_answer_input_accepts_multiple_and_legacy_selection() -> None:
    question_id = uuid.uuid4()
    first_option_id = uuid.uuid4()
    second_option_id = uuid.uuid4()

    multiple = AnswerInput(
        question_id=question_id,
        selected_option_ids=[first_option_id, second_option_id],
    )
    legacy = AnswerInput(question_id=question_id, selected_option_id=first_option_id)

    assert multiple.selected_option_ids == [first_option_id, second_option_id]
    assert legacy.selected_option_ids == []
    assert legacy.selected_option_id == first_option_id


def test_multi_select_scoring_requires_an_exact_match() -> None:
    correct = {uuid.uuid4(), uuid.uuid4()}
    extra = uuid.uuid4()

    assert _is_exact_option_selection(correct, correct)
    assert not _is_exact_option_selection({next(iter(correct))}, correct)
    assert not _is_exact_option_selection(correct | {extra}, correct)
    assert not _is_exact_option_selection(set(), correct)
    assert not _is_exact_option_selection({extra}, set())
