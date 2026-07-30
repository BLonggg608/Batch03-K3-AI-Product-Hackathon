from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
CODEBASE_DIR = BACKEND_DIR.parent
REPO_DIR = CODEBASE_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
KNOWLEDGE_DIR = BACKEND_DIR / "knowledge"
SLIDES_DIR = REPO_DIR / "data" / "vlearn-pack" / "slides"
DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(DATA_DIR / "vlearn_focus.sqlite3"))
)

load_dotenv(BACKEND_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_ENABLED = (
    os.getenv("GEMINI_ENABLED", "true").strip().lower() in {"1", "true", "yes"}
    and bool(GEMINI_API_KEY)
)
ALLOW_FALLBACK = os.getenv("ALLOW_FALLBACK", "false").strip().lower() in {
    "1",
    "true",
    "yes",
}
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").strip()


DOCUMENTS = {
    "day01": SLIDES_DIR / "d1-slide-hackathon.pdf",
    "day02": SLIDES_DIR / "d2-slide-hackathon.pdf",
}

KNOWLEDGE_FILES = {
    "day01": KNOWLEDGE_DIR / "day01.json",
    "day02": KNOWLEDGE_DIR / "day02.json",
}
