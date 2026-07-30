from __future__ import annotations

import math
from uuid import uuid4

from fastapi import HTTPException

from .config import ALLOW_FALLBACK
from .data_service import (
    get_document_summary,
    get_page_source,
    select_quiz_context,
)
from .gemini_service import gemini
from .models import (
    Choice,
    ChoicePublic,
    Quiz,
    QuizPublic,
    QuizQuestion,
    QuizQuestionPublic,
)
from .store import store
from .validation import validate_quiz


def _spread_pages(document_id: str, count: int) -> list[int]:
    return [
        page["page_number"]
        for page in select_quiz_context(document_id, count)
    ]


def _fallback_questions(
    document_id: str,
    question_count: int,
    mode: str,
    preferred_pages: list[int] | None = None,
) -> list[dict]:
    pages = list(dict.fromkeys(preferred_pages or []))
    for page in _spread_pages(document_id, question_count):
        if page not in pages:
            pages.append(page)
        if len(pages) == question_count:
            break
    pages = pages[:question_count]

    evidence_by_page: dict[int, str] = {}
    titles: dict[int, str] = {}
    for page_number in pages:
        page = get_page_source(document_id, page_number)
        if not page["evidence"]:
            continue
        evidence_by_page[page_number] = page["evidence"][0]
        titles[page_number] = page["title"]

    if len(evidence_by_page) < question_count:
        raise HTTPException(status_code=422, detail="Không đủ evidence trong tài liệu.")

    evidence_items = list(evidence_by_page.items())
    questions: list[dict] = []
    choice_ids = ["A", "B", "C", "D"]
    question_templates = [
        "Theo bài học, nhận định nào đúng về “{title}”?",
        "Phát biểu nào mô tả đúng kiến thức về “{title}”?",
        "Ý nào phản ánh đúng đặc điểm của “{title}”?",
        "Đâu là cách hiểu phù hợp về “{title}”?",
    ]
    prefix = "R" if mode == "reinforcement" else "Q"
    for index, (page_number, evidence) in enumerate(evidence_items):
        other_evidence = [
            text for page, text in evidence_items if page != page_number
        ]
        distractors = [
            other_evidence[(index + offset) % len(other_evidence)]
            for offset in range(3)
        ]
        correct_position = index % 4
        option_texts = distractors.copy()
        option_texts.insert(correct_position, evidence)
        questions.append(
            {
                "question_id": f"{document_id.upper()}-{prefix}{index + 1:02}",
                "question": question_templates[index % len(question_templates)].format(
                    title=titles[page_number]
                ),
                "choices": [
                    Choice(
                        id=choice_id,
                        text=text,
                        misconception=(
                            None
                            if position == correct_position
                            else "Nội dung này thuộc một phần khác trong tài liệu."
                        ),
                    ).model_dump()
                    for position, (choice_id, text) in enumerate(
                        zip(choice_ids, option_texts)
                    )
                ],
                "correct_answer": choice_ids[correct_position],
                "explanation": (
                    f"Evidence xuất hiện trực tiếp tại trang {page_number} của tài liệu."
                ),
                "evidence_quote": evidence,
                "source_page": page_number,
            }
        )
    return questions


def create_quiz(
    document_id: str,
    mode: str = "diagnostic",
    previous_attempt_id: str | None = None,
    question_count: int | None = None,
) -> Quiz:
    get_document_summary(document_id)
    if mode == "diagnostic":
        question_count = question_count or 10
        if question_count not in {5, 10, 20}:
            raise HTTPException(
                status_code=422,
                detail="Số câu quiz phải là 5, 10 hoặc 20.",
            )
        minimum_unique_pages = math.ceil(question_count * 0.75)
    else:
        question_count = 4
        minimum_unique_pages = 2
    generated_by = "fallback"
    trace: list[dict] = []

    preferred_pages: list[int] = []
    if previous_attempt_id:
        previous = store.get_attempt(previous_attempt_id)
        if previous:
            preferred_pages = [
                answer.source_page
                for answer in previous.answers
                if not answer.is_correct
            ]

    if gemini.enabled:
        try:
            raw_questions, trace = gemini.generate_quiz(
                document_id=document_id,
                mode=mode,
                question_count=question_count,
                minimum_unique_pages=minimum_unique_pages,
                previous_attempt_id=previous_attempt_id,
            )
            called = {item.get("tool") for item in trace if isinstance(item, dict)}
            required = {"validate_quiz"}
            if not required.issubset(called):
                raise ValueError(
                    f"Gemini chưa gọi tool bắt buộc: {sorted(required - called)}"
                )
            validation = validate_quiz(
                document_id,
                raw_questions,
                question_count,
                minimum_unique_pages,
            )
            trace.append(
                {
                    "tool": "server_validate_quiz",
                    "arguments": {
                        "document_id": document_id,
                        "expected_count": question_count,
                        "minimum_unique_pages": minimum_unique_pages,
                    },
                    "result": validation,
                }
            )
            if not validation["valid"]:
                raise ValueError(f"Quiz không grounded: {validation['errors']}")
            generated_by = "gemini"
        except Exception as exc:
            if not ALLOW_FALLBACK:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Gemini chưa tạo được quiz hợp lệ. "
                        "Vui lòng thử lại hoặc chọn ít câu hơn. "
                        f"Chi tiết: {exc}"
                    ),
                ) from exc
            raw_questions = _fallback_questions(
                document_id,
                question_count,
                mode,
                preferred_pages,
            )
            trace.append({"event": "gemini_fallback", "reason": str(exc)})
    else:
        if not ALLOW_FALLBACK:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Gemini chưa được cấu hình. Cần bật GEMINI_ENABLED và cung cấp "
                    "GEMINI_API_KEY để tạo quiz bằng AI."
                ),
            )
        raw_questions = _fallback_questions(
            document_id,
            question_count,
            mode,
            preferred_pages,
        )
        trace.append(
            {
                "event": "deterministic_fallback",
                "reason": "Gemini chưa được cấu hình.",
            }
        )

    final_validation = validate_quiz(
        document_id,
        raw_questions,
        question_count,
        minimum_unique_pages,
    )
    if not final_validation["valid"]:
        raise HTTPException(
            status_code=500,
            detail={"message": "Quiz không vượt qua validation.", **final_validation},
        )

    quiz = Quiz(
        quiz_id=str(uuid4()),
        document_id=document_id,
        mode=mode,
        questions=[QuizQuestion.model_validate(item) for item in raw_questions],
        generated_by=generated_by,
        validation_trace=trace,
    )
    store.save_quiz(quiz)
    return quiz


def get_quiz_or_404(quiz_id: str) -> Quiz:
    quiz = store.get_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy quiz.")
    return quiz


def to_public_quiz(quiz: Quiz) -> QuizPublic:
    return QuizPublic(
        quiz_id=quiz.quiz_id,
        document=get_document_summary(quiz.document_id),
        mode=quiz.mode,
        generated_by=quiz.generated_by,
        questions=[
            QuizQuestionPublic(
                question_id=question.question_id,
                question=question.question,
                choices=[
                    ChoicePublic(id=choice.id, text=choice.text)
                    for choice in question.choices
                ],
                source_page=question.source_page,
            )
            for question in quiz.questions
        ],
    )
