# VLearn Deck Quiz — MVP

Ứng dụng có đúng hai lựa chọn:

- **Ngày 1** — toàn bộ `d1-slide-hackathon.pdf` gồm 29 trang.
- **Ngày 2** — toàn bộ `d2-slide-hackathon.pdf` gồm 29 trang.

Nội dung hai PDF đã được nhóm chuẩn hóa trước thành knowledge JSON theo từng
trang. Khi học viên chọn một ngày, backend chỉ lấy các phần kiến thức cần thiết
cho Gemini tạo quiz, sau đó phân tích câu sai và sinh gói ôn tập.

## Flow

1. Chọn bộ slide ngày 1 hoặc ngày 2.
2. Backend đọc `knowledge/day01.json` hoặc `knowledge/day02.json`.
3. Backend chọn các trang kiến thức phân bố từ đầu đến cuối bài; agenda và trang
   hành chính đã được đánh dấu loại bỏ.
4. Học viên chọn 5, 10 hoặc 20 câu; Gemini chỉ nhận knowledge context tương ứng.
5. Gemini tạo đúng số câu và gọi `validate_quiz`.
6. Backend kiểm tra lại coverage, evidence nguyên văn và citation.
7. Học viên làm quiz, xem đáp án và evidence theo từng trang.
8. Gói ôn tập tập trung vào các trang liên quan đến câu sai.
9. Quiz củng cố gồm 4 câu; kết quả được so sánh với lần đầu.

## Kiến trúc

```text
Next.js + TypeScript
        │ REST
FastAPI + Pydantic
        ├── knowledge/*.json: nội dung đã chuẩn hóa theo trang
        ├── PDF gốc: chỉ dùng để học viên mở citation
        ├── SQLite: quiz, attempt, review
        └── Gemini API
              ├── knowledge context đã retrieve
              └── validate_quiz
```

### Retrieval và grounding

Mỗi knowledge page lưu `title`, `topics`, `summary`, `knowledge_points`,
`evidence`, `content` và cờ `is_instructional`.

1. Backend loại các trang có `is_instructional=false`.
2. Chọn đều các trang còn lại trên toàn bộ bài.
3. Chỉ gửi các knowledge chunks đã chọn cho Gemini, không upload lại PDF.
4. Mỗi câu phải dùng một evidence có sẵn:

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

Với `ALLOW_FALLBACK=false`, nếu Gemini lỗi thì API báo lỗi minh bạch; ứng dụng
không thay quiz AI bằng quiz mẫu.

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

| Method | Endpoint                      | Công dụng                           |
| ------ | ----------------------------- | ----------------------------------- |
| GET    | `/api/documents`              | Trả đúng hai lựa chọn ngày 1/ngày 2 |
| GET    | `/api/documents/{id}/outline` | Outline 29 trang                    |
| POST   | `/api/quizzes/generate`       | Tạo quiz tổng hợp 5, 10 hoặc 20 câu |
| POST   | `/api/attempts/grade`         | Chấm bài                            |
| POST   | `/api/reviews/generate`       | Tạo gói ôn tập từ câu sai           |
| POST   | `/api/reinforcement/generate` | Tạo 4 câu củng cố                   |
| GET    | `/api/progress/{attempt_id}`  | So sánh trước–sau                   |
| GET    | `/api/documents/{id}`         | Mở PDF nguồn                        |

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
