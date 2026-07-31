from __future__ import annotations

import json
import re
import time
from typing import Any

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_ENABLED, GEMINI_MODEL
from .data_service import select_quiz_context
from .store import store
from .tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


class GeminiOrchestrator:
    REQUEST_TIMEOUT_MS = 60_000
    OVERALL_TIMEOUT_SECONDS = 180

    @property
    def enabled(self) -> bool:
        return GEMINI_ENABLED

    def _run(
        self,
        prompt: str,
        allowed_tools: set[str],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        declarations = [
            types.FunctionDeclaration(
                name=item["name"],
                description=item["description"],
                parametersJsonSchema=item["parameters"],
            )
            for item in TOOL_DECLARATIONS
            if item["name"] in allowed_tools
        ]
        trace: list[dict[str, Any]] = []

        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=self.REQUEST_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
        deadline = time.monotonic() + self.OVERALL_TIMEOUT_SECONDS
        try:
            chat = client.chats.create(
                model=GEMINI_MODEL,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    tools=[types.Tool(functionDeclarations=declarations)],
                ),
            )
            response = chat.send_message(prompt)
            while True:
                calls = response.function_calls or []
                if not calls:
                    return parse_json_response(response.text or "{}"), trace

                function_responses: list[types.Part] = []
                for call in calls:
                    name = call.name or ""
                    arguments = dict(call.args or {})
                    if name not in allowed_tools or name not in TOOL_FUNCTIONS:
                        result: dict[str, Any] = {
                            "error": f"Tool {name} không được phép."
                        }
                    else:
                        try:
                            result = TOOL_FUNCTIONS[name](**arguments)
                        except Exception as exc:
                            result = {"error": str(exc)}
                    trace.append(
                        {
                            "tool": name,
                            "arguments": arguments,
                            "result": result,
                        }
                    )
                    function_responses.append(
                        types.Part.from_function_response(name=name, response=result)
                    )
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Gemini vượt quá 180 giây."
                    )
                response = chat.send_message(function_responses)
        finally:
            client.close()

    def generate_quiz(
        self,
        document_id: str,
        mode: str,
        question_count: int,
        minimum_unique_pages: int,
        previous_attempt_id: str | None = None,
        excluded_questions: list[str] | None = None,
        excluded_evidence: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        preferred_pages: list[int] = []
        if previous_attempt_id:
            previous = store.get_attempt(previous_attempt_id)
            if previous:
                preferred_pages = [
                    answer.source_page
                    for answer in previous.answers
                    if not answer.is_correct
                ]
        context_candidates = select_quiz_context(
            document_id,
            20 if excluded_evidence else question_count,
            preferred_pages,
        )
        blocked_evidence = {
            " ".join(item.split()).casefold() for item in excluded_evidence or []
        }
        context = []
        for page in context_candidates:
            allowed_evidence = [
                item
                for item in page["evidence"]
                if " ".join(item.split()).casefold() not in blocked_evidence
            ]
            if not allowed_evidence:
                continue
            context.append({**page, "evidence": allowed_evidence})
            if len(context) == question_count:
                break
        if len(context) < question_count:
            raise ValueError("Không còn đủ nội dung mới để tạo quiz trong phiên này.")
        context_json = json.dumps(context, ensure_ascii=False)
        exclusions_json = json.dumps(
            {
                "questions": excluded_questions or [],
                "evidence_quotes": excluded_evidence or [],
            },
            ensure_ascii=False,
        )
        personalization = (
            "Đây là quiz củng cố; context đã ưu tiên các trang của câu trả lời sai."
            if previous_attempt_id
            else (
                "Context đã được backend chọn phân bố từ đầu đến cuối bài để tránh "
                "bias vào một chủ đề."
            )
        )
        prompt = f"""
Bạn tạo quiz tiếng Việt từ KNOWLEDGE CONTEXT đã được nhóm chuẩn bị trước cho
tài liệu {document_id}. Không có file PDF trong request này.
Loại: {mode}. Số câu: {question_count}. Tối thiểu {minimum_unique_pages} trang nguồn.

{personalization}

KNOWLEDGE CONTEXT — đây là nguồn duy nhất được phép sử dụng:
{context_json}

NỘI DUNG ĐÃ TRẢ LỜI ĐÚNG, TUYỆT ĐỐI KHÔNG ĐƯỢC LẶP LẠI:
{exclusions_json}

QUY TRÌNH BẮT BUỘC:
1. Tạo đúng {question_count} câu, mỗi câu 4 lựa chọn A-D.
2. Mỗi câu dùng một knowledge point và evidence của đúng source_page trong context.
3. evidence_quote phải sao chép NGUYÊN VĂN một phần tử trong mảng evidence.
4. Gọi validate_quiz với minimum_unique_pages={minimum_unique_pages}. Nếu invalid,
   sửa và gọi lại.
5. Chỉ khi valid=true mới trả JSON thuần:
{{"questions":[{{
  "question_id":"{document_id.upper()}-Q01",
  "question":"...",
  "choices":[{{"id":"A","text":"...","misconception":null}}],
  "correct_answer":"A",
  "explanation":"...",
  "evidence_quote":"Đoạn nguyên văn trong tài liệu",
  "source_page":1
}}]}}

RÀNG BUỘC:
- Không tự tạo tình huống, số liệu hoặc kiến thức ngoài tài liệu.
- Đáp án đúng phải suy ra trực tiếp từ evidence_quote.
- Chỉ hỏi kiến thức: khái niệm, cơ chế, nguyên nhân, hệ quả, so sánh, quy trình,
  tiêu chí lựa chọn hoặc cách áp dụng.
- Không hỏi kiểu meta như “nội dung nào được nêu/đề cập”, “theo slide”, “ở đầu
  slide” hoặc nhắc tới vị trí/trang của tài liệu trong câu hỏi.
- Các câu chẩn đoán phải phân bố trên nhiều chủ đề và nhiều trang.
- Distractor phải hợp lý nhưng chỉ có một đáp án đúng.
"""
        payload, trace = self._run(prompt, {"validate_quiz"})
        trace.insert(
            0,
            {
                "event": "curated_knowledge_context",
                "document_id": document_id,
                "source_pages": [page["page_number"] for page in context],
                "context_characters": len(context_json),
            },
        )
        questions = payload.get("questions")
        if not isinstance(questions, list):
            raise ValueError("Gemini không trả questions hợp lệ.")
        return questions, trace

    def generate_review(
        self,
        attempt_id: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        attempt = store.get_attempt(attempt_id)
        if attempt is None:
            raise ValueError("Không tìm thấy lượt làm.")
        prompt = f"""
Tạo gói ôn tập tiếng Việt cho attempt {attempt_id}.
1. Gọi get_attempt_result.
2. Retrieve đúng các trang nguồn của câu sai bằng retrieve_document_pages.
3. Chỉ dùng evidence trong tài liệu, không thêm ví dụ bên ngoài.
4. Mỗi key point có evidence_quote nguyên văn và source_page.
Trả JSON thuần:
{{
 "possible_gap":"...",
 "key_points":[{{"text":"...","evidence_quote":"...","source_page":1}}],
 "wrong_answer_explanation":"..."
}}
"""
        return self._run(
            prompt,
            {"get_attempt_result", "retrieve_document_pages"},
        )


gemini = GeminiOrchestrator()
