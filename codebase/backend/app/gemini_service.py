from __future__ import annotations

import json
import re
import time
from typing import Any

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_ENABLED, GEMINI_MODEL
from .data_service import get_document_pdf_bytes
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
        source_pdf: bytes | None = None,
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
        message: str | list[str | types.Part] = prompt
        if source_pdf:
            message = [
                prompt,
                types.Part.from_bytes(data=source_pdf, mime_type="application/pdf"),
            ]
            trace.append(
                {
                    "event": "full_document_pdf_attached",
                    "mime_type": "application/pdf",
                    "byte_count": len(source_pdf),
                }
            )

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
            response = chat.send_message(message)
            for _ in range(6):
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
            raise RuntimeError("Gemini vượt quá số vòng function calling.")
        finally:
            client.close()

    def generate_quiz(
        self,
        document_id: str,
        mode: str,
        question_count: int,
        minimum_unique_pages: int,
        previous_attempt_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        personalization = (
            f"Gọi get_attempt_result({previous_attempt_id}) và tập trung vào các "
            "trang/evidence của câu sai; không cần bao quát lại toàn bộ deck."
            if previous_attempt_id
            else (
                "Quiz chẩn đoán phải bao quát các phần chính từ đầu, giữa và cuối "
                "deck; không tập trung quá nhiều câu vào một chủ đề."
            )
        )
        prompt = f"""
Bạn tạo quiz tiếng Việt từ TOÀN BỘ file slide {document_id}.
Loại: {mode}. Số câu: {question_count}. Tối thiểu {minimum_unique_pages} trang nguồn.

QUY TRÌNH BẮT BUỘC:
1. Gọi get_document_outline("{document_id}") để xem toàn bộ 29 trang.
2. {personalization}
3. Chọn các trang đại diện cho những chủ đề chính rồi gọi retrieve_document_pages.
4. Tạo đúng {question_count} câu, mỗi câu 4 lựa chọn A-D.
5. Mỗi câu phải có evidence_quote nguyên văn từ trang được retrieve.
6. Gọi validate_quiz với minimum_unique_pages={minimum_unique_pages}. Nếu invalid,
   sửa và gọi lại.
7. Chỉ khi valid=true mới trả JSON thuần:
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
- Tuyệt đối không dùng trang bìa, agenda, lịch trình, footer, thông tin hành chính
  hoặc hướng dẫn hoạt động làm nguồn câu hỏi.
- Chỉ hỏi kiến thức: khái niệm, cơ chế, nguyên nhân, hệ quả, so sánh, quy trình,
  tiêu chí lựa chọn hoặc cách áp dụng.
- Không hỏi kiểu meta như “nội dung nào được nêu/đề cập”, “theo slide”, “ở đầu
  slide” hoặc nhắc tới vị trí/trang của tài liệu trong câu hỏi.
- Các câu chẩn đoán phải phân bố trên nhiều chủ đề và nhiều trang.
- Distractor phải hợp lý nhưng chỉ có một đáp án đúng.
"""
        payload, trace = self._run(
            prompt,
            {
                "get_document_outline",
                "retrieve_document_pages",
                "get_attempt_result",
                "validate_quiz",
            }
            if previous_attempt_id
            else {
                "get_document_outline",
                "retrieve_document_pages",
                "validate_quiz",
            },
            get_document_pdf_bytes(document_id),
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
