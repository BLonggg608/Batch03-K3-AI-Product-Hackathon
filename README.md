# VLearn Deck Quiz — Project README

Đây là README kỹ thuật cho prototype "VLearn Deck Quiz" (phiên bản MVP) — một ứng dụng tạo quiz và gói ôn tập từ knowledge JSON trích xuất sẵn từ slide bài giảng. File này mô tả mục đích, kiến trúc, cách chạy, API và những điểm cần chú ý khi phát triển.

## Tổng quan

- Mục tiêu: Tạo quiz chẩn đoán và củng cố dựa trên nội dung từng slide (knowledge JSON), đảm bảo mỗi câu có evidence nguyên văn và citation trang.
- Công nghệ: `FastAPI` (backend, Python + Pydantic), `Next.js` + TypeScript (frontend), SQLite (store), Google Gemini (tùy chọn) cho sinh câu hỏi.
- Dữ liệu: `codebase/backend/knowledge/*.json` (29 trang mỗi deck) và PDF gốc trong `data/vlearn-pack/slides` để người dùng mở citation.

## Tác vụ chính của hệ thống

1. Chọn bộ slide (day01 / day02).
2. Backend đọc knowledge JSON, chọn các trang instructional và phân bố context.
3. Gửi context cho Gemini (nếu bật) để tạo quiz; gọi các tool server-side (`validate_quiz`) khi cần.
4. Nếu Gemini không khả dụng, có cơ chế fallback deterministic (cấu hình bằng `ALLOW_FALLBACK`).
5. Lưu quiz, lưu attempt, sinh gói review cho các câu sai, và tạo quiz củng cố.

## Cấu trúc quan trọng (đường dẫn trong repo)

- `codebase/backend/app/main.py` — entrypoint FastAPI và route API.
- `codebase/backend/app/quiz_service.py` — logic tạo quiz, kết hợp Gemini và fallback.
- `codebase/backend/app/gemini_service.py` — lớp tương tác với Google Gemini và orchestration của tool calls.
- `codebase/backend/app/data_service.py` — xử lý và validate knowledge JSON, chọn context, trả outline/page.
- `codebase/backend/app/validation.py` — luật kiểm tra quiz (evidence, coverage, schema).
- `codebase/backend/app/store.py` — lưu trữ đơn giản bằng SQLite cho quiz/attempt/review.
- `codebase/frontend/` — ứng dụng Next.js hiển thị quiz, gửi request đến backend.

## Thiết lập nhanh (Windows)

1. Backend

```powershell
cd codebase\backend
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

`backend/.env` tối thiểu:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_ENABLED=true
ALLOW_FALLBACK=false
FRONTEND_ORIGIN=http://localhost:3000
```

2. Frontend

```powershell
cd codebase\frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Mở `http://localhost:3000` để truy cập UI.

## API chính (tóm tắt)

- `GET /api/health` — trạng thái + config (Gemini, fallback).
- `GET /api/documents` — danh sách tài liệu (day01/day02).
- `GET /api/documents/{id}/outline` — outline từng trang.
- `GET /api/documents/{id}` — trả file PDF để hiển thị citation.
- `POST /api/quizzes/generate` — tạo quiz (payload: `document_id`, `question_count`).
- `POST /api/attempts/grade` — chấm attempt (payload: `quiz_id`, `answers`).
- `POST /api/reviews/generate` — sinh gói ôn tập từ `attempt_id`.
- `POST /api/reinforcement/generate` — tạo quiz củng cố từ attempt.
- `GET /api/progress/{attempt_id}` — so sánh trước/sau cho củng cố.

API docs: `http://localhost:8000/docs`.

## Các điểm kỹ thuật quan trọng

- Grounding: Mỗi `QuizQuestion` bắt buộc có `evidence_quote` tồn tại nguyên văn trong `content` của `source_page`. Backend validate chặt chẽ.
- Coverage: Tối thiểu 75% câu phải tới từ các trang nguồn khác nhau (đảm bảo trải bài).
- Gemini orchestration: `gemini_service` sử dụng function-calling để cho phép model gọi các tool server-side (`validate_quiz`, `retrieve_document_pages`, `get_attempt_result`).
- Fallback: Nếu `GEMINI_ENABLED=false` hoặc Gemini lỗi, hệ thống có fallback deterministic tạo câu dựa trên evidence trong knowledge JSON — chỉ bật khi `ALLOW_FALLBACK=true`.
- Store: `store.py` lưu objects dạng JSON trong SQLite `data/vlearn_focus.sqlite3`.

## Chạy test & kiểm tra

Backend:

```powershell
cd codebase\backend
pytest -q
```

Frontend: typecheck và build

```powershell
cd codebase\frontend
npm run typecheck
npm run build
```

Smoke test (khi cả hai server chạy):

```powershell
cd codebase\frontend\scripts
node smoke.mjs
```

## Lưu ý bảo mật & dữ liệu

- Không commit `GEMINI_API_KEY` hay các bí mật vào git.
- Dữ liệu trong `data/` là nội dung hackathon đã ẩn danh — tuân thủ quy định sử dụng nội dung.
- Khi chia sẻ kết quả, chỉ trích xuất những phần evidence ngắn cần thiết.

## Cách đọc mã nhanh — checklist cho reviewer

1. Mở `codebase/backend/app/data_service.py` để hiểu schema `knowledge/*.json`.
2. Kiểm tra `validation.py` để nắm luật business (evidence, coverage, choice ids).
3. Đọc `quiz_service.py` để xem flow tạo quiz (gemini vs fallback) và cách lưu `Quiz`.
4. Đọc `gemini_service.py` để hiểu orchestration và tool-call pattern.
5. Mở `codebase/frontend/app/quiz/[quizId]/page.tsx` (giao diện quiz) và `lib/api.ts` (client API).

## Muốn tôi làm gì tiếp theo?

- Tôi có thể: (A) commit README này trực tiếp; (B) thêm phần hướng dẫn deploy Docker; (C) viết script chạy demo tự động. Chọn một hoặc yêu cầu chỉnh sửa.

---
Phiên bản README tự động tạo bởi trợ lý; nếu cần, tôi sẽ tinh chỉnh nội dung theo yêu cầu nhóm.
