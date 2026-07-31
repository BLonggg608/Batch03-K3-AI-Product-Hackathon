# Reflection: Vai trò Prompt & Golden Set (Đào Quốc Đại - 2A202601285)

## 1. Bức tranh thực tế từ Run 01 (30/07/2026)
- **Nhiệm vụ đảm nhận:** Xây dựng toàn bộ bộ 20 case cố định trong `eval/golden-set.json` (chia thành 4 batch × 5 case) và tối ưu hóa prompt gọi mô hình `gemini-3.1-flash-lite`.
- **Kết quả đo lường:** Đạt **13/20 (65%)**, chưa chạm mức cam kết Quality Bar (≥80%).
- **Phân tích nguyên nhân cụ thể:**
  - **EVAL-02 & EVAL-18:** Bị đánh fail do expected output quá khắt khe về từ khóa (thiếu một số thuật ngữ bắt buộc trong diễn giải của model).
  - **EVAL-11 đến EVAL-15:** Thuộc batch bị ảnh hưởng bởi defect kỹ thuật (hệ thống backend âm thầm tráo sang nhánh fallback dù cấu hình `ALLOW_FALLBACK=false`).

## 2. Bài học đúc kết chuyên môn (Lessons Learned)
- **Prompt Engineering không chỉ là "viết câu lệnh hay", mà là "kiểm soát biên giới hallucination":** Trong hệ thống giáo dục (EdTech), một prompt tốt bắt buộc phải ép model ràng buộc chặt chẽ với trích dẫn gốc (`evidence_quote`) và số trang (`source_page`), tuyệt đối không tự bịa thêm thông tin.
- **Phối hợp chặt chẽ giữa AI Prompt và Backend Validation:** Thất bại của Run 01 cho thấy prompt dù có thiết kế tốt đến đâu cũng sẽ bị vô hiệu hóa nếu hệ thống phần mềm phía sau có lỗi silent fallback. Sự đồng bộ giữa kỹ sư prompt và kỹ sư backend là yếu tố sống còn trước khi đưa sản phẩm ra demo.

## 3. Hành động cải tiến trước ngày Demo (Action Items)
1. **Tinh chỉnh Prompt:** Mở rộng biên độ ngữ nghĩa cho các trường hợp kiểm tra logic thay vì chỉ dò từ khóa cứng nhắc (giải quyết lỗi thiếu expected terms ở EVAL-02 và EVAL-18).
2. **Siết chặt Golden Set:** Giữ vững nguyên tắc *Zero-Tolerance* với các lỗi sai trích dẫn, đảm bảo mọi case chạy lại trong Run tiếp theo phản ánh đúng năng lực thực tế của Gemini sau khi backend đã vá lỗ hổng fallback.
