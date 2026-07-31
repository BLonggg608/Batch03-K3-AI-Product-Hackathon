# Reflection — Nguyễn Quang Minh (2A202601955)

## Vai trò trong nhóm

Tôi phụ trách **Evidence mining** cho dự án "No Name: Quiz chẩn đoán" (hướng A —
VLearn). Phần việc của tôi là đi tìm bằng chứng định lượng từ
`data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` để chứng
minh pain point trước khi nhóm chốt lát cắt, cụ thể là các số liệu và trích dẫn
nguyên văn nằm trong `spec.md` §1.

## Phần mình đã làm

- Lọc `role=student` trong 1.261 tin nhắn, đếm số dòng chứa các nhóm từ khóa
  ("giải thích"/"là gì"/"tại sao", "tóm tắt"/"tóm gọn"/"summary",
  "quiz"/"bài tập"/"câu hỏi"/"kiểm tra") và số `user_id` duy nhất tương ứng
  (571/238, 132/97, 33/29).
- Kiểm tra tỷ lệ câu trả lời tutor không có citation (46,2%) và tần suất
  trường `misconceptions` không được dùng ở toàn bộ 1.261 lượt, cùng số lần
  tutor chủ động hỏi kiểm tra hiểu bài (3/1.261) — đây là ba con số quyết định
  hướng đi của nhóm, vì chúng cho thấy AI Tutor hiện tại thiên về giải thích
  chứ không khép kín vòng "kiểm tra → phát hiện sai → ôn lại".
- Chọn 5 ví dụ nguyên văn kèm mã hội thoại/lượt (C0002/T0330, C0003/T1201,
  C0013/T0990, C0015/T0811, C0006/T0058) để minh họa mà không dán nguyên văn dài,
  đúng cam kết bảo mật dữ liệu.
- Ghi lại phương pháp đếm (lọc → tìm từ khóa không phân biệt hoa thường → đếm
  dòng và user_id duy nhất, không cộng gộp các nhóm giao nhau) để người chấm
  kiểm lại được, thay vì chỉ đưa con số cuối.

## AI hỗ trợ thế nào

Tôi dùng AI (Claude Code) chủ yếu ở việc viết truy vấn lọc/đếm trên file CSV
lớn và soát lại cách diễn đạt số liệu trong spec sao cho không suy diễn quá
mức (ví dụ: không được nói "64% học viên cần quiz" khi thực ra đó là hành vi
đếm được trong chatlog, không phải kết quả khảo sát). AI giúp tôi chạy nhanh
nhiều biến thể từ khóa và đối chiếu số liệu, nhưng phần quyết định từ khóa nào
phản ánh đúng nhu cầu "tự kiểm tra hiểu bài" và diễn giải giới hạn của phương
pháp đếm (§1: "không được diễn giải thành tỷ lệ xác nhận sản phẩm") là tôi tự
làm, vì đây là chỗ dễ bị thổi phồng bằng chứng nếu để AI viết tự do.

## Một bài học từ case fail của nhóm

Ở Run 01 (`eval/run-01.md`), 5 case EVAL-11–15 bị đánh FAIL không phải vì
grounding hay đáp án sai, mà vì `review_service` âm thầm rơi vào nhánh
`fallback` dù cấu hình toàn cục đặt `ALLOW_FALLBACK=false`. Bài học của tôi là:
**một con số tổng hợp (13/20 — 65%) có thể che giấu một nguyên nhân lỗi hoàn
toàn khác với chất lượng AI thực sự** — nếu chỉ nhìn tỷ lệ pass mà không mở
bảng chi tiết theo từng case, nhóm sẽ hiểu sai vấn đề (tưởng model yếu, trong
khi thực chất là một service không tuân thủ đúng cấu hình lỗi minh bạch). Điều
này áp dụng ngược lại vào phần evidence mining tôi làm: một con số đếm được
(ví dụ 571 tin có từ khóa "giải thích") cũng có thể bị hiểu sai nếu không đi
kèm phương pháp và giới hạn diễn giải rõ ràng. Từ đó tôi rút ra nguyên tắc là
luôn ghi phương pháp kiểm lại được cạnh mọi con số, để người khác (hoặc chính
mình sau này) không nhầm tương quan với nguyên nhân.