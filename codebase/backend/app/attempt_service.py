from __future__ import annotations

import math
from uuid import uuid4

from fastapi import HTTPException

from .models import AnswerResult, AttemptResult, GradeAttemptRequest, ProgressComparison
from .quiz_service import get_quiz_or_404
from .store import store


def grade_attempt(request: GradeAttemptRequest) -> AttemptResult:
    quiz = get_quiz_or_404(request.quiz_id)
    submitted = {answer.question_id: answer.selected_answer for answer in request.answers}
    if len(submitted) != len(request.answers):
        raise HTTPException(status_code=422, detail="Mỗi câu chỉ được trả lời một lần.")
    if set(submitted) != {question.question_id for question in quiz.questions}:
        raise HTTPException(status_code=422, detail="Cần trả lời đầy đủ quiz.")

    results: list[AnswerResult] = []
    for question in quiz.questions:
        selected = submitted[question.question_id]
        choice_map = {choice.id: choice for choice in question.choices}
        if selected not in choice_map:
            raise HTTPException(status_code=422, detail="Đáp án không hợp lệ.")
        is_correct = selected == question.correct_answer
        results.append(
            AnswerResult(
                question_id=question.question_id,
                question=question.question,
                selected_answer=selected,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                explanation=question.explanation,
                misconception=(
                    None if is_correct else choice_map[selected].misconception
                ),
                evidence_quote=question.evidence_quote,
                source_page=question.source_page,
            )
        )

    score = sum(answer.is_correct for answer in results)
    total = len(results)
    required = math.ceil(total * 0.75)
    attempt = AttemptResult(
        attempt_id=str(uuid4()),
        quiz_id=quiz.quiz_id,
        learner_id=request.learner_id,
        document_id=quiz.document_id,
        mode=quiz.mode,
        score=score,
        total=total,
        percentage=round(score / total * 100),
        mastery_status="passed" if score >= required else "not_yet",
        answers=results,
        parent_attempt_id=request.parent_attempt_id,
    )
    store.save_attempt(attempt)
    return attempt


def get_attempt_or_404(attempt_id: str) -> AttemptResult:
    attempt = store.get_attempt(attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt làm quiz.")
    return attempt


def compare_progress(reinforcement_attempt_id: str) -> ProgressComparison:
    after = get_attempt_or_404(reinforcement_attempt_id)
    if not after.parent_attempt_id:
        raise HTTPException(status_code=400, detail="Đây không phải quiz củng cố.")
    before = get_attempt_or_404(after.parent_attempt_id)
    if before.document_id != after.document_id:
        raise HTTPException(status_code=400, detail="Hai lượt làm không cùng tài liệu.")
    delta = after.percentage - before.percentage
    message = (
        f"Bạn đã cải thiện {delta} điểm phần trăm."
        if delta > 0
        else "Kết quả chưa tăng; hãy ôn lại evidence của các câu còn sai."
    )
    return ProgressComparison(
        document_id=after.document_id,
        diagnostic_attempt_id=before.attempt_id,
        reinforcement_attempt_id=after.attempt_id,
        before_percentage=before.percentage,
        after_percentage=after.percentage,
        delta_percentage_points=delta,
        message=message,
    )
