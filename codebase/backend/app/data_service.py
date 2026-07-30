from __future__ import annotations

import json
import re
from functools import lru_cache

from fastapi import HTTPException

from .config import DOCUMENTS, KNOWLEDGE_FILES
from .models import DocumentOutline, DocumentSummary, PageSummary


DOCUMENT_META = {
    "day01": {
        "title": "Buổi 1 · AI & LLM Foundation",
        "description": (
            "Nền tảng AI, Transformer, token, context, attention, agent, "
            "model selection và prompt."
        ),
    },
    "day02": {
        "title": "Buổi 2 · Problem Discovery",
        "description": (
            "Problem Discovery, Problem Statement, metric, lựa chọn cấp độ "
            "Rule/Workflow/Agent và evaluation."
        ),
    },
}


def _document_path(document_id: str):
    path = DOCUMENTS.get(document_id)
    if path is None or document_id not in DOCUMENT_META:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Thiếu file {path.name}.")
    return path


def _knowledge_path(document_id: str):
    path = KNOWLEDGE_FILES.get(document_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy knowledge base.")
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Thiếu knowledge base {path.name}.",
        )
    return path


@lru_cache(maxsize=4)
def _knowledge_document(document_id: str) -> dict:
    path = _knowledge_path(document_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge base {path.name} không hợp lệ: {exc}",
        ) from exc

    if payload.get("document_id") != document_id:
        raise HTTPException(
            status_code=500,
            detail=f"document_id trong {path.name} không khớp.",
        )
    pages = payload.get("pages")
    if not isinstance(pages, list) or len(pages) != 29:
        raise HTTPException(
            status_code=500,
            detail=f"{path.name} phải chứa đúng 29 trang.",
        )
    if [page.get("page_number") for page in pages] != list(range(1, 30)):
        raise HTTPException(
            status_code=500,
            detail=f"Số trang trong {path.name} phải liên tục từ 1 đến 29.",
        )
    return payload


@lru_cache(maxsize=4)
def _document_pages(document_id: str) -> list[dict]:
    pages: list[dict] = []
    for raw in _knowledge_document(document_id)["pages"]:
        content = str(raw.get("content", "")).strip()
        evidence = [
            str(item).strip()
            for item in raw.get("evidence", [])
            if str(item).strip()
        ]
        if evidence:
            missing = [
                item
                for item in evidence
                if _normalize(item) not in _normalize(content)
            ]
            if missing:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Evidence trang {raw['page_number']} của {document_id} "
                        "không tồn tại trong content."
                    ),
                )
        summary = str(raw.get("summary", "")).strip()
        topics = [str(item).strip() for item in raw.get("topics", []) if str(item).strip()]
        knowledge_points = [
            str(item).strip()
            for item in raw.get("knowledge_points", [])
            if str(item).strip()
        ]
        pages.append(
            {
                "page_number": int(raw["page_number"]),
                "title": str(raw.get("title") or f"Trang {raw['page_number']}"),
                "preview": summary[:260] or content[:260],
                "word_count": len(re.findall(r"\w+", content, flags=re.UNICODE)),
                "is_instructional": bool(raw.get("is_instructional", False)),
                "exclusion_reason": raw.get("exclusion_reason"),
                "topics": topics,
                "summary": summary,
                "knowledge_points": knowledge_points,
                "evidence": evidence,
                "content": content,
            }
        )
    return pages


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


@lru_cache(maxsize=4)
def get_document_outline(document_id: str) -> dict:
    path = _document_path(document_id)
    pages = _document_pages(document_id)
    meta = DOCUMENT_META[document_id]
    outline = DocumentOutline(
        document_id=document_id,
        document_name=path.name,
        title=meta["title"],
        description=meta["description"],
        page_count=len(pages),
        word_count=sum(page["word_count"] for page in pages),
        pages=[PageSummary.model_validate(page) for page in pages],
    )
    return outline.model_dump()


def list_documents() -> list[DocumentSummary]:
    return [
        DocumentSummary.model_validate(get_document_outline(document_id))
        for document_id in DOCUMENTS
    ]


def get_document_summary(document_id: str) -> DocumentSummary:
    return DocumentSummary.model_validate(get_document_outline(document_id))


def get_page_source(document_id: str, page_number: int) -> dict:
    pages = _document_pages(document_id)
    if page_number < 1 or page_number > len(pages):
        raise HTTPException(status_code=404, detail="Trang không tồn tại.")
    return pages[page_number - 1]


def is_instructional_page(page: dict) -> bool:
    return bool(page.get("is_instructional"))


def retrieve_document_pages(
    document_id: str,
    page_numbers: list[int],
) -> dict:
    unique_pages = list(dict.fromkeys(page_numbers))
    if not unique_pages or len(unique_pages) > 20:
        raise HTTPException(
            status_code=422,
            detail="Cần retrieve từ 1 đến 20 trang mỗi lần.",
        )
    return {
        "document_id": document_id,
        "document_name": _document_path(document_id).name,
        "knowledge_source": _knowledge_path(document_id).name,
        "pages": [
            get_page_source(document_id, page_number)
            for page_number in unique_pages
        ],
    }


def select_quiz_context(
    document_id: str,
    question_count: int,
    preferred_pages: list[int] | None = None,
) -> list[dict]:
    eligible = [
        page for page in _document_pages(document_id) if is_instructional_page(page)
    ]
    if len(eligible) < question_count:
        raise HTTPException(
            status_code=422,
            detail="Knowledge base không đủ trang kiến thức để tạo quiz.",
        )

    selected_numbers = [
        page_number
        for page_number in dict.fromkeys(preferred_pages or [])
        if 1 <= page_number <= 29
        and is_instructional_page(get_page_source(document_id, page_number))
    ]
    remaining = question_count - len(selected_numbers)
    candidates = [
        page for page in eligible if page["page_number"] not in selected_numbers
    ]
    if remaining > 0:
        if remaining == 1:
            indexes = [len(candidates) // 2]
        else:
            indexes = [
                round(index * (len(candidates) - 1) / (remaining - 1))
                for index in range(remaining)
            ]
        selected_numbers.extend(candidates[index]["page_number"] for index in indexes)

    return [
        {
            "page_number": page["page_number"],
            "title": page["title"],
            "topics": page["topics"],
            "summary": page["summary"],
            "knowledge_points": page["knowledge_points"],
            "evidence": page["evidence"],
        }
        for page in (
            get_page_source(document_id, page_number)
            for page_number in selected_numbers[:question_count]
        )
    ]
