from __future__ import annotations

import re
from functools import lru_cache

from fastapi import HTTPException
from pypdf import PdfReader

from .config import DOCUMENTS
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

PDF_SYMBOL_MAP = str.maketrans(
    {
        "\ue081": "(",
        "\ue082": ")",
        "\ue088": "-",
        "\ue089": "–",
        "\ue08b": "—",
        "\ue092": ":",
        "\ue09b": "=",
        "\ue09f": "×",
        "\ue0a3": "≥",
    }
)

NON_INSTRUCTIONAL_TITLES = {
    "agenda",
    "sáng",
    "chiều",
    "mục lục",
    "nội dung chương trình",
}

PAGE_TITLE_OVERRIDES = {
    ("day01", 16): "Nguyên tắc sắp xếp và quản lý context",
    ("day01", 21): "Giới hạn của việc học mẫu từ dữ liệu",
    ("day02", 10): "6 câu hỏi khai thác bài toán",
    ("day02", 6): "Đặc điểm bài toán phù hợp để cải tiến bằng AI",
    ("day02", 9): "Cấu trúc Problem Statement",
    ("day02", 12): "Output Metric và Process Metric",
    ("day02", 13): "Ba bước quyết định AI theo PAIR",
    ("day02", 18): "Ba mức giải pháp: Rule / Workflow / Agent",
    ("day02", 22): "Reward function và ma trận Precision / Recall",
    ("day02", 24): "Ngưỡng vận hành và kill-switch",
    ("day02", 25): "Khoảng cách giữa Demo và Production",
    ("day02", 26): "Từ Problem Statement đến Eval Plan",
    ("day02", 28): "Khung quyết định Go / Not Yet / No-Go",
    ("day02", 29): "Các nguyên tắc xác định bài toán AI",
}


def _document_path(document_id: str):
    path = DOCUMENTS.get(document_id)
    if path is None or document_id not in DOCUMENT_META:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Thiếu file {path.name}.")
    return path


def _clean_lines(raw_text: str) -> list[str]:
    raw_text = raw_text.translate(PDF_SYMBOL_MAP)
    raw_text = re.sub(r"[\ue000-\uf8ff]", " ", raw_text)
    return [
        re.sub(r"\s+", " ", line).strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]


def _page_title(lines: list[str], page_number: int) -> str:
    if not lines:
        return f"Trang {page_number}"
    title = lines[0]
    if title.upper().startswith("AI IN ACTION") and len(lines) > 1:
        title = lines[1]
    return title[:110]


@lru_cache(maxsize=4)
def _document_pages(document_id: str) -> list[dict]:
    path = _document_path(document_id)
    reader = PdfReader(str(path))
    pages: list[dict] = []
    for page_number, page in enumerate(reader.pages, 1):
        lines = _clean_lines(page.extract_text() or "")
        content = "\n".join(lines)
        pages.append(
            {
                "page_number": page_number,
                "title": PAGE_TITLE_OVERRIDES.get(
                    (document_id, page_number),
                    _page_title(lines, page_number),
                ),
                "preview": " ".join(lines[1:])[:260] or content[:260],
                "word_count": len(re.findall(r"\w+", content, flags=re.UNICODE)),
                "content": content,
            }
        )
    return pages


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
    title = re.sub(r"\s+", " ", page["title"]).strip().casefold()
    return (
        page["word_count"] >= 45
        and title not in NON_INSTRUCTIONAL_TITLES
        and "agenda" not in title
    )


def retrieve_document_pages(
    document_id: str,
    page_numbers: list[int],
) -> dict:
    unique_pages = list(dict.fromkeys(page_numbers))
    if not unique_pages or len(unique_pages) > 14:
        raise HTTPException(
            status_code=422,
            detail="Cần retrieve từ 1 đến 14 trang mỗi lần.",
        )
    return {
        "document_id": document_id,
        "document_name": _document_path(document_id).name,
        "pages": [
            get_page_source(document_id, page_number)
            for page_number in unique_pages
        ],
    }


@lru_cache(maxsize=4)
def get_document_pdf_bytes(document_id: str) -> bytes:
    return _document_path(document_id).read_bytes()
