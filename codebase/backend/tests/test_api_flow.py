from __future__ import annotations

import os
import re
import tempfile
from uuid import uuid4

import pytest

os.environ["GEMINI_ENABLED"] = "false"
os.environ["ALLOW_FALLBACK"] = "true"
os.environ["DATABASE_PATH"] = os.path.join(
    tempfile.gettempdir(),
    f"vlearn-focus-test-{uuid4()}.sqlite3",
)

from fastapi.testclient import TestClient

from app.data_service import (
    get_document_outline,
    get_page_source,
    is_instructional_page,
    select_quiz_context,
)
from app.main import app
from app.store import store
from app.validation import validate_quiz


client = TestClient(app)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def test_health_and_two_document_options() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    response = client.get("/api/documents")
    assert response.status_code == 200
    documents = response.json()
    assert [item["document_id"] for item in documents] == ["day01", "day02"]
    assert all(item["page_count"] == 29 for item in documents)

    outline = client.get("/api/documents/day02/outline")
    assert outline.status_code == 200
    assert len(outline.json()["pages"]) == 29


@pytest.mark.parametrize(
    ("document_id", "non_instructional_page"),
    [("day01", 2), ("day02", 2)],
)
def test_curated_knowledge_base_is_complete_and_stratified(
    document_id: str,
    non_instructional_page: int,
) -> None:
    outline = get_document_outline(document_id)
    assert len(outline["pages"]) == 29
    assert not is_instructional_page(
        get_page_source(document_id, non_instructional_page)
    )

    instructional = [
        page for page in outline["pages"] if page["is_instructional"]
    ]
    assert len(instructional) >= 20
    for page in instructional:
        source = get_page_source(document_id, page["page_number"])
        assert source["topics"]
        assert source["summary"]
        assert source["knowledge_points"]
        assert source["evidence"]
        assert all(
            normalize(evidence) in normalize(source["content"])
            for evidence in source["evidence"]
        )

    context = select_quiz_context(document_id, 20)
    context_pages = [page["page_number"] for page in context]
    assert len(context_pages) == 20
    assert len(set(context_pages)) == 20
    assert max(context_pages) - min(context_pages) >= 20
    assert non_instructional_page not in context_pages


@pytest.mark.parametrize(
    ("question_count", "minimum_unique_pages"),
    [(5, 4), (10, 8), (20, 15)],
)
def test_public_quiz_supports_selected_count_and_does_not_leak(
    question_count: int,
    minimum_unique_pages: int,
) -> None:
    response = client.post(
        "/api/quizzes/generate",
        json={"document_id": "day02", "question_count": question_count},
    )
    assert response.status_code == 200
    quiz = response.json()
    assert quiz["document"]["page_count"] == 29
    assert len(quiz["questions"]) == question_count
    assert (
        len({question["source_page"] for question in quiz["questions"]})
        >= minimum_unique_pages
    )
    for question in quiz["questions"]:
        assert "nội dung nào được nêu trực tiếp" not in normalize(
            question["question"]
        )
        assert is_instructional_page(
            get_page_source("day02", question["source_page"])
        )
        assert "correct_answer" not in question
        assert "explanation" not in question
        assert "evidence_quote" not in question
        assert all("misconception" not in choice for choice in question["choices"])


def test_complete_document_learning_loop() -> None:
    public = client.post(
        "/api/quizzes/generate",
        json={"document_id": "day02", "question_count": 10},
    ).json()
    quiz = store.get_quiz(public["quiz_id"])
    assert quiz is not None

    attempt_response = client.post(
        "/api/attempts/grade",
        json={
            "quiz_id": quiz.quiz_id,
            "learner_id": "pytest-learner",
            "answers": [
                {
                    "question_id": question.question_id,
                    "selected_answer": question.choices[-1].id,
                }
                for question in quiz.questions
            ],
        },
    )
    assert attempt_response.status_code == 200
    attempt = attempt_response.json()
    assert attempt["document_id"] == "day02"
    assert attempt["total"] == 10
    for answer in attempt["answers"]:
        page = get_page_source("day02", answer["source_page"])
        assert normalize(answer["evidence_quote"]) in normalize(page["content"])

    review = client.post(
        "/api/reviews/generate",
        json={"attempt_id": attempt["attempt_id"]},
    )
    assert review.status_code == 200
    assert review.json()["key_points"]

    reinforcement_public = client.post(
        "/api/reinforcement/generate",
        json={"attempt_id": attempt["attempt_id"]},
    ).json()
    assert len(reinforcement_public["questions"]) == 4
    reinforcement = store.get_quiz(reinforcement_public["quiz_id"])
    assert reinforcement is not None

    reinforced = client.post(
        "/api/attempts/grade",
        json={
            "quiz_id": reinforcement.quiz_id,
            "learner_id": "pytest-learner",
            "parent_attempt_id": attempt["attempt_id"],
            "answers": [
                {
                    "question_id": question.question_id,
                    "selected_answer": question.correct_answer,
                }
                for question in reinforcement.questions
            ],
        },
    ).json()
    assert reinforced["score"] == 4
    progress = client.get(f"/api/progress/{reinforced['attempt_id']}")
    assert progress.status_code == 200
    assert progress.json()["after_percentage"] == 100


def test_validator_rejects_fabricated_evidence_and_low_coverage() -> None:
    generated = client.post(
        "/api/quizzes/generate",
        json={"document_id": "day01", "question_count": 10},
    ).json()
    quiz = store.get_quiz(generated["quiz_id"])
    assert quiz is not None
    questions = [question.model_dump() for question in quiz.questions]
    questions[0]["evidence_quote"] = "Nội dung hoàn toàn không có trong tài liệu."

    result = validate_quiz("day01", questions, 10, 8)
    assert result["valid"] is False
    assert any(
        error["code"] == "EVIDENCE_NOT_FOUND_IN_PAGE"
        for error in result["errors"]
    )

    same_page = [questions[1] for _ in range(10)]
    for index, question in enumerate(same_page):
        question = question.copy()
        question["question_id"] = f"LOW-{index}"
        question["question"] = f"Câu hỏi coverage {index}"
        same_page[index] = question
    coverage = validate_quiz("day01", same_page, 10, 8)
    assert any(
        error["code"] == "INSUFFICIENT_DOCUMENT_COVERAGE"
        for error in coverage["errors"]
    )

    invalid_choice_ids = [question.copy() for question in questions]
    invalid_choice_ids[0] = invalid_choice_ids[0].copy()
    invalid_choice_ids[0]["choices"] = [
        choice.copy() for choice in invalid_choice_ids[0]["choices"]
    ]
    invalid_choice_ids[0]["choices"][3]["id"] = "D splinter"
    choice_validation = validate_quiz("day01", invalid_choice_ids, 10, 8)
    assert any(
        error["code"] == "INVALID_CHOICE_IDS"
        for error in choice_validation["errors"]
    )


def test_document_endpoint_serves_pdf() -> None:
    response = client.get("/api/documents/day02")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
