from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Iterator

from .config import DATABASE_PATH
from .models import AttemptResult, Quiz, ReviewPackage


class Store:
    def __init__(self) -> None:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(DATABASE_PATH)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS objects (
                    object_type TEXT NOT NULL,
                    object_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _save(self, object_type: str, object_id: str, payload: dict) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO objects
                (object_type, object_id, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    object_type,
                    object_id,
                    json.dumps(payload, ensure_ascii=False),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def _get(self, object_type: str, object_id: str) -> dict | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT payload FROM objects
                WHERE object_type = ? AND object_id = ?
                """,
                (object_type, object_id),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save_quiz(self, quiz: Quiz) -> None:
        self._save("quiz", quiz.quiz_id, quiz.model_dump())

    def get_quiz(self, quiz_id: str) -> Quiz | None:
        payload = self._get("quiz", quiz_id)
        if not payload:
            return None
        try:
            return Quiz.model_validate(payload)
        except Exception:
            return None

    def save_attempt(self, attempt: AttemptResult) -> None:
        self._save("attempt", attempt.attempt_id, attempt.model_dump())

    def get_attempt(self, attempt_id: str) -> AttemptResult | None:
        payload = self._get("attempt", attempt_id)
        if not payload:
            return None
        try:
            return AttemptResult.model_validate(payload)
        except Exception:
            return None

    def save_review(self, review: ReviewPackage) -> None:
        self._save("review", review.review_id, review.model_dump())

    def get_review_by_attempt(self, attempt_id: str) -> ReviewPackage | None:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT payload FROM objects WHERE object_type = 'review'"
            ).fetchall()
        for row in rows:
            try:
                review = ReviewPackage.model_validate(json.loads(row[0]))
            except Exception:
                continue
            if review.attempt_id == attempt_id:
                return review
        return None


store = Store()
