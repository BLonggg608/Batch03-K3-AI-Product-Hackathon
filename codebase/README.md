# VLearn Deck Quiz — MVP

Ứng dụng có đúng hai lựa chọn:

- **Ngày 1** — toàn bộ `d1-slide-hackathon.pdf` gồm 29 trang.
- **Ngày 2** — toàn bộ `d2-slide-hackathon.pdf` gồm 29 trang.

Khi học viên chọn một ngày, hệ thống đọc toàn bộ file PDF, tạo quiz tổng hợp trên
nhiều phần của bài, phân tích câu sai, tạo gói ôn tập và sinh quiz củng cố.

## Flow

1. Chọn bộ slide ngày 1 hoặc ngày 2.
2. Gemini nhận toàn bộ file PDF và gọi `get_document_outline`.
3. Model chọn các phần đại diện từ đầu, giữa và cuối tài liệu.
4. `retrieve_document_pages` lấy nội dung đầy đủ của các trang cần dùng.
5. Học viên chọn 5, 10 hoặc 20 câu; Gemini tạo đúng số câu đã chọn.
6. `validate_quiz` kiểm tra coverage, evidence nguyên văn và citation.
7. Học viên làm quiz, xem đáp án và evidence theo từng trang.
8. Gói ôn tập tập trung vào các trang liên quan đến câu sai.
9. Quiz củng cố gồm 4 câu; kết quả được so sánh với lần đầu.

## Kiến trúc

```text
Next.js + TypeScript
        │ REST
FastAPI + Pydantic
        ├── pypdf: outline và text của 29 trang
        ├── SQLite: quiz, attempt, review
        └── Gemini API
              ├── toàn bộ PDF (multimodal)
              ├── get_document_outline
              ├── retrieve_document_pages
              ├── get_attempt_result
              └── validate_quiz
```

### Retrieval và grounding

Retrieval được thực hiện ở cấp tài liệu:

1. Gemini xem outline của toàn bộ 29 trang.
2. Chọn các trang đại diện cho những chủ đề chính.
3. Retrieve text đầy đủ của các trang đó.
4. Mỗi câu phải có:

```json
{
  "evidence_quote": "Đoạn nguyên văn trong tài liệu",
  "source_page": 11
}
```

Backend từ chối quiz nếu:

- Evidence không tồn tại trong trang được trích dẫn.
- Số câu không khớp lựa chọn 5, 10 hoặc 20.
- Quiz không đạt độ phủ tối thiểu 75% số câu trên các trang nguồn khác nhau.
- Câu hỏi lấy nguồn từ agenda, lịch trình hoặc phần hành chính.
- Câu hỏi meta như “nội dung nào được nêu/đề cập” thay vì hỏi kiến thức.
- Citation sai trang hoặc schema đáp án không hợp lệ.

Nếu Gemini lỗi, fallback vẫn chọn các trang phân bố xuyên suốt tài liệu và hiển thị
rõ `generated_by: fallback`.

## Chạy backend

```powershell
cd codebase\backend
C:\Users\ADMIN\miniconda3\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
C:\Users\ADMIN\miniconda3\python.exe -m uvicorn app.main:app --reload --port 8000
```

`backend\.env`:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_ENABLED=true
ALLOW_FALLBACK=false
FRONTEND_ORIGIN=http://localhost:3000
```

`ALLOW_FALLBACK=false` là cấu hình mặc định của sản phẩm: nếu Gemini không tạo
được quiz hợp lệ, API báo lỗi thay vì trả một quiz không do AI sinh. Chỉ bật
fallback khi chạy test hoặc demo offline có chủ đích.

API docs: `http://localhost:8000/docs`.

## Chạy frontend

```powershell
cd codebase\frontend
npm.cmd install
Copy-Item .env.local.example .env.local
npm.cmd run dev
```

Mở `http://localhost:3000`.

## API chính

| Method | Endpoint | Công dụng |
|---|---|---|
| GET | `/api/documents` | Trả đúng hai lựa chọn ngày 1/ngày 2 |
| GET | `/api/documents/{id}/outline` | Outline 29 trang |
| POST | `/api/quizzes/generate` | Tạo quiz tổng hợp 5, 10 hoặc 20 câu |
| POST | `/api/attempts/grade` | Chấm bài |
| POST | `/api/reviews/generate` | Tạo gói ôn tập từ câu sai |
| POST | `/api/reinforcement/generate` | Tạo 4 câu củng cố |
| GET | `/api/progress/{attempt_id}` | So sánh trước–sau |
| GET | `/api/documents/{id}` | Mở PDF nguồn |

Payload tạo quiz:

```json
{
  "document_id": "day02",
  "question_count": 10
}
```

## Kiểm thử

```powershell
cd codebase\backend
C:\Users\ADMIN\miniconda3\python.exe -m pytest -q

cd ..\frontend
npm.cmd run typecheck
npm.cmd run build
npm.cmd audit --omit=dev
```

Khi hai server đang chạy:

```powershell
npm.cmd run smoke
```

Smoke test xác nhận trang chủ có hai tài liệu, chọn quiz 10 câu và đi hết flow ngày 2.
