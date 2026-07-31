from __future__ import annotations

import re
from uuid import uuid4

from fastapi import HTTPException

from .attempt_service import get_attempt_or_404
from .config import ALLOW_FALLBACK
from .data_service import get_document_summary, get_page_source
from .gemini_service import gemini
from .models import KeyPoint, ReviewPackage
from .store import store


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _fallback_review(attempt_id: str) -> tuple[dict, list[dict]]:
    attempt = get_attempt_or_404(attempt_id)
    wrong = [answer for answer in attempt.answers if not answer.is_correct]
    focus = wrong or attempt.answers
    misconceptions = [
        answer.misconception for answer in wrong if answer.misconception
    ]
    return (
        {
            "possible_gap": (
                "Người học có thể đang nhầm: "
                + "; ".join(dict.fromkeys(misconceptions))
                if misconceptions
                else "Chưa thấy lỗ hổng rõ ràng trong lượt làm này."
            ),
            "key_points": [
                {
                    "text": answer.explanation,
                    "evidence_quote": answer.evidence_quote,
                    "source_page": answer.source_page,
                }
                for answer in focus
            ],
            "wrong_answer_explanation": " ".join(
                answer.explanation for answer in focus
            ),
        },
        [{"event": "deterministic_fallback"}],
    )


def _validate_payload(payload: dict, document_id: str) -> None:
    points = payload.get("key_points")
    if not isinstance(points, list) or not points:
        raise ValueError("Gói ôn tập thiếu key_points.")
    for point in points:
        if not isinstance(point, dict):
            raise ValueError("Key point sai schema.")
        page_number = point.get("source_page")
        if not isinstance(page_number, int):
            raise ValueError("Key point thiếu source_page.")
        page = get_page_source(document_id, page_number)
        evidence = _normalize(str(point.get("evidence_quote", "")))
        if len(evidence) < 12 or evidence not in _normalize(page["content"]):
            raise ValueError("Evidence ôn tập không tồn tại trong trang nguồn.")


def create_review(attempt_id: str) -> ReviewPackage:
    existing = store.get_review_by_attempt(attempt_id)
    if existing:
        return existing
    attempt = get_attempt_or_404(attempt_id)
    document = get_document_summary(attempt.document_id)
    generated_by = "fallback"

    if gemini.enabled:
        try:
            payload, trace = gemini.generate_review(attempt_id)
            called = {item.get("tool") for item in trace if isinstance(item, dict)}
            required = {"get_attempt_result", "retrieve_document_pages"}
            if not required.issubset(called):
                raise ValueError(
                    f"Gemini chưa gọi tool bắt buộc: {sorted(required - called)}"
                )
            if not isinstance(payload, dict):
                raise ValueError("Gemini không trả JSON object.")
            _validate_payload(payload, attempt.document_id)
            generated_by = "gemini"
        except Exception as exc:
            if not ALLOW_FALLBACK:
                raise HTTPException(
                    status_code=502,
                    detail=f"Gemini chưa tạo được gói ôn tập hợp lệ: {exc}",
                ) from exc
            payload, trace = _fallback_review(attempt_id)
            trace.append({"event": "gemini_fallback", "reason": str(exc)})
    else:
        payload, trace = _fallback_review(attempt_id)

    seen: set[tuple[int, str]] = set()
    key_points: list[KeyPoint] = []
    for item in payload["key_points"]:
        key = (item["source_page"], _normalize(item["evidence_quote"]))
        if key in seen:
            continue
        seen.add(key)
        key_points.append(KeyPoint.model_validate(item))

    review = ReviewPackage(
        review_id=str(uuid4()),
        attempt_id=attempt_id,
        document_id=attempt.document_id,
        document_title=document.title,
        possible_gap=payload.get(
            "possible_gap",
            "Bạn có thể đang nhầm một số ý trong tài liệu.",
        ),
        key_points=key_points,
        wrong_answer_explanation=payload.get(
            "wrong_answer_explanation",
            "Hãy đối chiếu evidence của từng câu.",
        ),
        generated_by=generated_by,
        tool_trace=trace,
    )
    store.save_review(review)
    return review
