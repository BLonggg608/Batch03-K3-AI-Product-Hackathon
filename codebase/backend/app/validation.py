from __future__ import annotations

import re

from .data_service import (
    get_document_outline,
    get_page_source,
    is_instructional_page,
)
from .models import QuizQuestion, QuizValidationResult


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def validate_quiz(
    document_id: str,
    questions: list[dict],
    expected_count: int,
    minimum_unique_pages: int,
) -> dict:
    outline = get_document_outline(document_id)
    valid_pages = {page["page_number"] for page in outline["pages"]}
    errors: list[dict] = []
    warnings: list[dict] = []

    if len(questions) != expected_count:
        errors.append(
            {
                "code": "WRONG_QUESTION_COUNT",
                "expected": expected_count,
                "actual": len(questions),
            }
        )

    seen_questions: set[str] = set()
    seen_evidence: set[str] = set()
    used_pages: set[int] = set()
    answer_distribution: list[str] = []

    for index, raw in enumerate(questions):
        try:
            question = QuizQuestion.model_validate(raw)
        except Exception as exc:
            errors.append(
                {
                    "code": "INVALID_QUESTION_SCHEMA",
                    "question_index": index,
                    "detail": str(exc),
                }
            )
            continue

        if question.source_page not in valid_pages:
            errors.append(
                {
                    "code": "INVALID_SOURCE_PAGE",
                    "question_id": question.question_id,
                }
            )
        else:
            used_pages.add(question.source_page)
            source = get_page_source(document_id, question.source_page)
            if not is_instructional_page(source):
                errors.append(
                    {
                        "code": "NON_INSTRUCTIONAL_SOURCE",
                        "question_id": question.question_id,
                        "source_page": question.source_page,
                        "source_title": source["title"],
                    }
                )
            evidence = normalize(question.evidence_quote)
            if len(evidence) < 12 or evidence not in normalize(source["content"]):
                errors.append(
                    {
                        "code": "EVIDENCE_NOT_FOUND_IN_PAGE",
                        "question_id": question.question_id,
                        "source_page": question.source_page,
                    }
                )
            if evidence in seen_evidence:
                warnings.append(
                    {
                        "code": "REUSED_EVIDENCE",
                        "question_id": question.question_id,
                    }
                )
            seen_evidence.add(evidence)

        if len(question.choices) != 4:
            errors.append(
                {
                    "code": "WRONG_CHOICE_COUNT",
                    "question_id": question.question_id,
                }
            )
        choice_ids = [choice.id for choice in question.choices]
        if len(set(choice_ids)) != len(choice_ids):
            errors.append(
                {
                    "code": "DUPLICATE_CHOICE_IDS",
                    "question_id": question.question_id,
                }
            )
        if question.correct_answer not in choice_ids:
            errors.append(
                {
                    "code": "INVALID_CORRECT_ANSWER",
                    "question_id": question.question_id,
                }
            )
        else:
            answer_distribution.append(question.correct_answer)

        normalized_question = normalize(question.question)
        if any(
            phrase in normalized_question
            for phrase in (
                "nội dung nào được nêu trực tiếp",
                "nội dung nào được đề cập",
                "theo slide",
                "ở đầu slide",
                "trên trang",
            )
        ):
            errors.append(
                {
                    "code": "GENERIC_OR_META_QUESTION",
                    "question_id": question.question_id,
                }
            )
        if normalized_question in seen_questions:
            errors.append(
                {
                    "code": "DUPLICATE_QUESTION",
                    "question_id": question.question_id,
                }
            )
        seen_questions.add(normalized_question)

    if len(used_pages) < minimum_unique_pages:
        errors.append(
            {
                "code": "INSUFFICIENT_DOCUMENT_COVERAGE",
                "minimum_unique_pages": minimum_unique_pages,
                "actual_unique_pages": len(used_pages),
                "used_pages": sorted(used_pages),
            }
        )
    if len(set(answer_distribution)) == 1 and len(answer_distribution) > 1:
        warnings.append({"code": "SAME_CORRECT_ANSWER_FOR_ALL_QUESTIONS"})

    return QuizValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
    ).model_dump()
