from __future__ import annotations

from fastapi import HTTPException

from .data_service import get_document_outline, retrieve_document_pages
from .store import store
from .validation import validate_quiz


def get_attempt_result(attempt_id: str) -> dict:
    attempt = store.get_attempt(attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt làm quiz.")
    return attempt.model_dump()


TOOL_FUNCTIONS = {
    "get_document_outline": get_document_outline,
    "retrieve_document_pages": retrieve_document_pages,
    "get_attempt_result": get_attempt_result,
    "validate_quiz": validate_quiz,
}


TOOL_DECLARATIONS = [
    {
        "name": "get_document_outline",
        "description": (
            "Lấy outline toàn bộ deck gồm tiêu đề, preview và số từ của từng trang. "
            "Dùng để lập coverage plan trước khi tạo quiz."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "enum": ["day01", "day02"],
                }
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "retrieve_document_pages",
        "description": (
            "Retrieve text đầy đủ của các trang đã chọn từ outline. Đây là evidence "
            "để tạo câu hỏi và citation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "enum": ["day01", "day02"],
                },
                "page_numbers": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 1,
                    "maxItems": 14,
                },
            },
            "required": ["document_id", "page_numbers"],
        },
    },
    {
        "name": "get_attempt_result",
        "description": "Lấy câu đúng, câu sai và evidence của một lượt làm quiz.",
        "parameters": {
            "type": "object",
            "properties": {"attempt_id": {"type": "string"}},
            "required": ["attempt_id"],
        },
    },
    {
        "name": "validate_quiz",
        "description": (
            "Kiểm tra evidence, trang citation, schema và độ bao phủ nhiều phần "
            "trong toàn bộ deck."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "enum": ["day01", "day02"],
                },
                "questions": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "expected_count": {"type": "integer"},
                "minimum_unique_pages": {"type": "integer"},
            },
            "required": [
                "document_id",
                "questions",
                "expected_count",
                "minimum_unique_pages",
            ],
        },
    },
]
