from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .attempt_service import compare_progress, get_attempt_or_404, grade_attempt
from .config import (
    ALLOW_FALLBACK,
    DOCUMENTS,
    FRONTEND_ORIGIN,
    GEMINI_ENABLED,
    GEMINI_MODEL,
)
from .data_service import get_document_outline, list_documents
from .models import (
    AttemptResult,
    DocumentOutline,
    DocumentSummary,
    GenerateQuizRequest,
    GenerateReinforcementRequest,
    GenerateReviewRequest,
    GradeAttemptRequest,
    ProgressComparison,
    QuizPublic,
    ReviewPackage,
)
from .quiz_service import create_quiz, get_quiz_or_404, to_public_quiz
from .review_service import create_review
from .store import store


app = FastAPI(
    title="VLearn Deck Quiz API",
    version="3.0.0",
    description="Tạo quiz bao quát toàn bộ slide deck của một ngày.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        dict.fromkeys(
            [
                FRONTEND_ORIGIN,
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3010",
                "http://127.0.0.1:3010",
            ]
        )
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    missing = [key for key, path in DOCUMENTS.items() if not path.exists()]
    return {
        "status": "ok" if not missing else "degraded",
        "gemini_enabled": GEMINI_ENABLED,
        "gemini_model": GEMINI_MODEL,
        "fallback_enabled": ALLOW_FALLBACK,
        "missing_documents": missing,
    }


@app.get("/api/documents", response_model=list[DocumentSummary])
def documents() -> list[DocumentSummary]:
    return list_documents()


@app.get(
    "/api/documents/{document_id}/outline",
    response_model=DocumentOutline,
)
def document_outline(document_id: str) -> DocumentOutline:
    return DocumentOutline.model_validate(get_document_outline(document_id))


@app.post("/api/quizzes/generate", response_model=QuizPublic)
def generate_quiz(request: GenerateQuizRequest) -> QuizPublic:
    return to_public_quiz(
        create_quiz(
            request.document_id,
            question_count=request.question_count,
        )
    )


@app.get("/api/quizzes/{quiz_id}", response_model=QuizPublic)
def quiz_detail(quiz_id: str) -> QuizPublic:
    return to_public_quiz(get_quiz_or_404(quiz_id))


@app.post("/api/attempts/grade", response_model=AttemptResult)
def submit_attempt(request: GradeAttemptRequest) -> AttemptResult:
    return grade_attempt(request)


@app.get("/api/attempts/{attempt_id}", response_model=AttemptResult)
def attempt_detail(attempt_id: str) -> AttemptResult:
    return get_attempt_or_404(attempt_id)


@app.post("/api/reviews/generate", response_model=ReviewPackage)
def generate_review(request: GenerateReviewRequest) -> ReviewPackage:
    return create_review(request.attempt_id)


@app.get("/api/reviews/{attempt_id}", response_model=ReviewPackage)
def review_detail(attempt_id: str) -> ReviewPackage:
    review = store.get_review_by_attempt(attempt_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Chưa có gói ôn tập.")
    return review


@app.post("/api/reinforcement/generate", response_model=QuizPublic)
def generate_reinforcement(
    request: GenerateReinforcementRequest,
) -> QuizPublic:
    attempt = get_attempt_or_404(request.attempt_id)
    quiz = create_quiz(
        document_id=attempt.document_id,
        mode="reinforcement",
        previous_attempt_id=attempt.attempt_id,
    )
    return to_public_quiz(quiz)


@app.get(
    "/api/progress/{reinforcement_attempt_id}",
    response_model=ProgressComparison,
)
def progress(reinforcement_attempt_id: str) -> ProgressComparison:
    return compare_progress(reinforcement_attempt_id)


@app.get("/api/documents/{document_id}")
def document_file(document_id: str) -> FileResponse:
    path = DOCUMENTS.get(document_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
        content_disposition_type="inline",
    )
