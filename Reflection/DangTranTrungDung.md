# Reflection Cá Nhân - Đặng Trần Trung Dũng

**Dự án:** VLearn Focus (Quiz Chẩn Đoán)
**Vai trò trong nhóm:** Backend + Validation

## 1. Phần tôi đã làm trong dự án
Trong dự án này, tôi chịu trách nhiệm chính về phần kiến trúc Backend và kiểm soát chất lượng đầu ra của AI. Cụ thể:
- **Xây dựng API Backend:** Sử dụng FastAPI để tạo các endpoint giao tiếp giữa Frontend và hệ thống AI (Gemini).
- **Thiết kế hệ thống Validation-as-a-Tool:** Biến các hàm kiểm tra logic của Python thành Tool cho Gemini sử dụng. Nổi bật nhất là hàm `validate_quiz`, ép Gemini phải tự gọi tool để kiểm tra câu hỏi nó vừa sinh ra, nếu lỗi phải tự đọc mã lỗi và sửa lại trước khi trả kết quả cho người dùng.
- **Grounded Validation (Chống ảo giác):** Code logic kiểm tra cứng, bắt buộc trường `evidence_quote` do AI sinh ra phải match 100% (chính xác từng chữ) với nội dung trong file gốc (`source_page`). Nếu AI bịa kiến thức hoặc trích dẫn sai trang, lập tức bắn lỗi `EVIDENCE_NOT_FOUND_IN_PAGE` và từ chối.
- **Quản lý Cấu hình & Fallback:** Xử lý cơ chế retry khi gọi API Gemini bị lỗi (503/502) và chặn đứng các luồng fallback rác để đảm bảo tính minh bạch.

## 2. AI đã hỗ trợ tôi như thế nào?
Xuyên suốt quá trình làm việc, tôi đã áp dụng triệt để Vibe-Coding với sự hỗ trợ của các công cụ AI (Claude, Cursor, Gemini):
- **Tốc độ code (Velocity):** AI giúp tôi viết boilerplate code cho FastAPI, thiết lập Pydantic models (`QuizQuestion`) và các hàm CRUD với CSDL rất nhanh.
- **Giải quyết vấn đề khó (Problem-solving):** Khi gặp vấn đề với việc Gemini thỉnh thoảng sinh ra JSON bị kẹp trong Markdown (text block), AI đã gợi ý cho tôi các cách viết regex/parser chuẩn xác để bóc tách JSON an toàn.
- **Debugging:** AI đóng vai trò như một người pair-programming để cùng tôi truy vết nguyên nhân lỗi 502/503 timeout khi gọi API Gemini và gợi ý tăng biến timeout/retry.

## 3. Một bài học sâu sắc từ case fail của nhóm
Bài học lớn nhất của tôi đến từ đợt chạy **Golden Set Run 01**. 
Ban đầu, tôi đã cẩn thận cấu hình `ALLOW_FALLBACK=false` ở biến môi trường vì muốn hệ thống thà báo lỗi minh bạch còn hơn trả về kết quả rác. Tuy nhiên, khi chạy thử, 5 cases (EVAL-11 đến EVAL-15) vẫn âm thầm bị đẩy vào nhánh fallback và bị hệ thống Eval đánh FAIL toàn bộ. 

**Bài học rút ra:** 
1. **Đừng bao giờ tin tưởng vào code fallback mặc định hoặc "hộp đen" của API.** Dù đã cài biến môi trường, một ngóc ngách nào đó trong `review_service.py` vẫn lén bắt exception và trả về data giả. Sự cố này dạy tôi rằng hệ thống AI Product cần được log chi tiết và minh bạch ở mọi ngóc ngách, lỗi ở đâu phải raise Exception thẳng ra ở đó.
2. **Luật cứng luôn thắng Prompt mềm.** Dù có viết prompt đe dọa LLM "Tuyệt đối không được bịa chữ" bao nhiêu lần đi nữa, nó vẫn có xác suất ảo giác. Cách duy nhất để xây dựng lòng tin (Trust) trong AI Product là dùng **Code Logic (Python)** để soi lỗi LLM. Cơ chế check string `evidence_quote` đã chứng minh hiệu quả tuyệt đối trong dự án này.
