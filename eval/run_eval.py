from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "codebase" / "backend"
OUT_DIR = ROOT / "eval"
GOLDEN_SET_PATH = OUT_DIR / "golden-set.json"

# Keep evaluation objects separate from the demo database.
os.environ.setdefault("DATABASE_PATH", str(OUT_DIR / "eval.sqlite3"))
os.environ["ALLOW_FALLBACK"] = "false"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import ALLOW_FALLBACK, GEMINI_ENABLED, GEMINI_MODEL  # noqa: E402
from app.data_service import get_page_source, is_instructional_page  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Choice, Quiz, QuizQuestion  # noqa: E402
from app.store import store  # noqa: E402


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def require_success(response, label: str) -> None:
    try:
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"{label} failed: {response.status_code} {response.text}"
        ) from exc


def load_golden_set() -> dict:
    payload = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if len(cases) != 20:
        raise ValueError(f"Golden set must contain exactly 20 cases, found {len(cases)}.")
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Golden set contains duplicate case IDs.")
    return payload


def evidence_for_page(document_id: str, page_number: int) -> str:
    page = get_page_source(document_id, page_number)
    if not page["is_instructional"] or not page["evidence"]:
        raise ValueError(f"Page {page_number} is not an eligible evidence page.")
    return page["evidence"][0]


def build_quiz(document_id: str, cases: list[dict], batch_number: int) -> Quiz:
    questions = []
    for index, case in enumerate(cases, start=1):
        evidence_quote = evidence_for_page(document_id, case["source_page"])
        questions.append(
            QuizQuestion(
                question_id=f"GOLDEN-B{batch_number}-Q{index:02d}",
                question=case["question"],
                choices=[
                    Choice(id="A", text=case["correct_answer"], misconception=None),
                    Choice(
                        id="B",
                        text=case["student_answer"],
                        misconception=case["misconception"],
                    ),
                    Choice(id="C", text="Không đủ thông tin để kết luận.", misconception=None),
                    Choice(id="D", text="Cả ba đáp án trên đều đúng.", misconception=None),
                ],
                correct_answer="A",
                explanation=case["correct_answer"],
                evidence_quote=evidence_quote,
                source_page=case["source_page"],
            )
        )
    quiz = Quiz(
        quiz_id=str(uuid4()),
        document_id=document_id,
        mode="diagnostic",
        questions=questions,
        generated_by="gemini",
        validation_trace=[
            {
                "event": "fixed_golden_set_fixture",
                "batch_number": batch_number,
                "case_ids": [case["case_id"] for case in cases],
            }
        ],
    )
    store.save_quiz(quiz)
    return quiz


def text_contains_terms(text: str, terms: list[str]) -> bool:
    normalized = normalize(text)
    return all(normalize(term) in normalized for term in terms)


def run_batch(
    client: TestClient,
    document_id: str,
    cases: list[dict],
    batch_number: int,
) -> dict:
    quiz = build_quiz(document_id, cases, batch_number)
    attempt_response = client.post(
        "/api/attempts/grade",
        json={
            "quiz_id": quiz.quiz_id,
            "learner_id": "golden-set-eval",
            "answers": [
                {"question_id": question.question_id, "selected_answer": "B"}
                for question in quiz.questions
            ],
        },
    )
    require_success(attempt_response, f"grade batch {batch_number}")
    attempt = attempt_response.json()

    review_response = client.post(
        "/api/reviews/generate",
        json={"attempt_id": attempt["attempt_id"]},
    )
    require_success(review_response, f"review batch {batch_number}")
    review = review_response.json()

    review_text = " ".join(
        [
            review["possible_gap"],
            review["wrong_answer_explanation"],
            *[point["text"] for point in review["key_points"]],
        ]
    )
    review_pages = {point["source_page"] for point in review["key_points"]}
    review_grounded = all(
        normalize(point["evidence_quote"])
        in normalize(get_page_source(document_id, point["source_page"])["content"])
        and is_instructional_page(
            get_page_source(document_id, point["source_page"])
        )
        for point in review["key_points"]
    )

    rows = []
    for case in cases:
        terms_found = text_contains_terms(review_text, case["expected_terms"])
        page_covered = case["source_page"] in review_pages
        generated_by_gemini = review["generated_by"] == "gemini"
        passed = (
            terms_found
            and page_covered
            and review_grounded
            and generated_by_gemini
        )
        rows.append(
            {
                **case,
                "pass": passed,
                "checks": {
                    "provider_success": True,
                    "expected_terms_found": terms_found,
                    "source_page_covered": page_covered,
                    "review_evidence_grounded": review_grounded,
                    "review_generated_by_gemini": generated_by_gemini,
                },
                "observed": {
                    "possible_gap": review["possible_gap"],
                    "review_pages": sorted(review_pages),
                    "generated_by": review["generated_by"],
                },
            }
        )

    return {
        "batch_number": batch_number,
        "quiz_id": quiz.quiz_id,
        "attempt_id": attempt["attempt_id"],
        "review_id": review["review_id"],
        "review_generated_by": review["generated_by"],
        "rows": rows,
    }


def failed_batch(cases: list[dict], batch_number: int, error: Exception) -> dict:
    message = str(error)
    return {
        "batch_number": batch_number,
        "review_generated_by": "error",
        "error": message,
        "rows": [
            {
                **case,
                "pass": False,
                "checks": {
                    "provider_success": False,
                    "expected_terms_found": False,
                    "source_page_covered": False,
                    "review_evidence_grounded": False,
                    "review_generated_by_gemini": False,
                },
                "observed": {
                    "generated_by": "error",
                    "error": message,
                },
            }
            for case in cases
        ],
    }


def run_eval(batch_size: int = 5) -> dict:
    golden_set = load_golden_set()
    document_id = golden_set["document_id"]
    cases = golden_set["cases"]
    client = TestClient(app)
    health = client.get("/api/health").json()

    batches = []
    rows = []
    for offset in range(0, len(cases), batch_size):
        batch_cases = cases[offset : offset + batch_size]
        batch_number = (offset // batch_size) + 1
        try:
            batch = run_batch(
                client,
                document_id,
                batch_cases,
                batch_number=batch_number,
            )
        except Exception as exc:
            batch = failed_batch(batch_cases, batch_number, exc)
        rows.extend(batch.pop("rows"))
        batches.append(batch)

    passed = sum(row["pass"] for row in rows)
    return {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "model": GEMINI_MODEL,
        "gemini_enabled": GEMINI_ENABLED,
        "fallback_enabled": ALLOW_FALLBACK,
        "health": health,
        "golden_set": str(GOLDEN_SET_PATH.relative_to(ROOT)),
        "document_id": document_id,
        "total_cases": len(rows),
        "batch_size": batch_size,
        "score": f"{passed}/{len(rows)}",
        "batches": batches,
        "rows": rows,
    }


def write_outputs(result: dict) -> None:
    (OUT_DIR / "run-01.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# Eval run 01",
        "",
        f"- Run at: {result['run_at']}",
        f"- Model: {result['model']}",
        f"- Gemini enabled: {result['gemini_enabled']}",
        f"- Fallback enabled: {result['fallback_enabled']}",
        f"- Golden set: `{result['golden_set']}`",
        f"- Document: {result['document_id']}",
        f"- Batch design: {len(result['batches'])} x {result['batch_size']} fixed cases",
        f"- Result: {result['score']}",
        "",
        "| Case | Type | Result | Page | Failed checks |",
        "|---|---|---|---:|---|",
    ]
    for row in result["rows"]:
        failed = [key for key, ok in row["checks"].items() if not ok]
        lines.append(
            f"| {row['case_id']} | {row['situation_type']} | "
            f"{'PASS' if row['pass'] else 'FAIL'} | {row['source_page']} | "
            f"{', '.join(failed) if failed else '-'} |"
        )
    lines.extend(
        [
            "",
            "Full inputs, expected criteria, observed outputs, and all failures "
            "are stored in `eval/run-01.json`.",
        ]
    )
    (OUT_DIR / "run-01.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    try:
        output = run_eval()
    except Exception as exc:
        output = {
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "model": GEMINI_MODEL,
            "gemini_enabled": GEMINI_ENABLED,
            "fallback_enabled": ALLOW_FALLBACK,
            "score": "0/20",
            "error": str(exc),
            "rows": [],
        }
        (OUT_DIR / "run-01.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (OUT_DIR / "run-01.md").write_text(
            "\n".join(
                [
                    "# Eval run 01",
                    "",
                    f"- Run at: {output['run_at']}",
                    f"- Model: {output['model']}",
                    "- Result: 0/20",
                    f"- Error: {output['error']}",
                    "",
                    "The run did not produce 20 measurable AI outputs. Fix the error "
                    "and rerun `python eval/run_eval.py`.",
                ]
            ),
            encoding="utf-8",
        )
        raise
    else:
        write_outputs(output)
        print(f"Eval result: {output['score']}")
        print("Wrote eval/run-01.md and eval/run-01.json")
