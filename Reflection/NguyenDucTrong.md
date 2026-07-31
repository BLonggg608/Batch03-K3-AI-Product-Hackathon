# Reflection — Nguyễn Đức Trọng (2A202601291)

## Vai trò trong nhóm

Tôi phụ trách **Spec + Quality Bar** cho dự án **No Name: Quiz chẩn đoán**.
Deliverable chính của tôi là `spec.md`, tài liệu thống nhất bài toán người dùng,
phạm vi sản phẩm, quyết định AI, các kiểu lỗi và tiêu chuẩn đánh giá chất lượng
trước khi nhóm triển khai và demo.

## Nhiệm vụ được giao

1. **Hoàn thiện đặc tả sản phẩm:** mô tả người dùng mục tiêu, workflow hiện tại,
   core JTBD và problem statement; bảo đảm nhóm giải quyết đúng nhu cầu “kiểm
   tra → phát hiện phần hiểu sai → ôn đúng nội dung”.
2. **Tổng hợp căn cứ chọn giải pháp:** đưa kết quả evidence mining và khảo sát
   vào spec, ghi rõ phương pháp, giới hạn diễn giải và lý do chọn quiz chẩn đoán
   thay cho chatbot hoặc quiz chỉ dựa trên transcript.
3. **Chốt phạm vi và thiết kế:** xác định input, output, quyết định AI trung tâm,
   non-goals và bốn đường đi của trải nghiệm gồm happy path, low-confidence,
   failure và correction.
4. **Xây dựng risk register:** liệt kê các lỗi quan trọng như evidence không tồn
   tại, citation sai trang, đáp án sai dù citation hợp lệ, chẩn đoán lỗ hổng sai
   và silent fallback khi Gemini gặp lỗi.
5. **Định nghĩa Quality Bar:** một lượt đánh giá chỉ đạt khi có ít nhất **80%**
   case PASS, đồng thời áp dụng **zero-tolerance** với câu hỏi, đáp án hoặc
   citation không có trong đúng trang nguồn.
6. **Theo dõi kết quả validation:** cập nhật kết quả golden set, user validation,
   thay đổi sau phản hồi và changelog; không hạ tiêu chuẩn sau khi đã xem kết quả.
7. **Phối hợp với các thành viên:** chuyển yêu cầu trong spec thành tiêu chí có
   thể triển khai và kiểm tra cho phần evidence, prompt, backend validation,
   frontend và kịch bản demo.

## Phần đóng góp của vai trò Spec + Quality Bar

- Giữ cho sản phẩm tập trung vào một lát cắt end-to-end: học viên làm quiz,
  xem phần có thể đang hiểu sai, ôn lại bằng evidence đúng trang và làm quiz
  củng cố.
- Đặt ranh giới rõ ràng: chỉ hỗ trợ nội dung Day 01/Day 02, không làm chatbot
  tự do, không chấm tự luận và không dùng kết quả để kết luận chắc chắn về năng
  lực của học viên.
- Chuyển yêu cầu “AI phải bám nguồn” thành điều kiện kiểm chứng được: mọi
  `evidence_quote` phải tồn tại trong đúng `source_page`; output vi phạm phải bị
  chặn thay vì phát hành cho người dùng.
- Theo dõi hai lượt đánh giá: Run 01 đạt **13/20 (65%)**, Run 02 đạt
  **14/20 (70%)**. Kết quả mới nhất chưa đạt Quality Bar 80%, nhưng điều kiện
  cứng về grounding vẫn được giữ vì evidence sai đã bị backend từ chối.

## AI hỗ trợ như thế nào

AI có thể hỗ trợ tôi rà soát tính nhất quán giữa các phần của spec, nhóm các
kịch bản lỗi, chuẩn hóa cách diễn đạt tiêu chí PASS/FAIL và đối chiếu kết quả
evaluation với Quality Bar. Tuy nhiên, các quyết định về problem statement,
phạm vi, cost-of-error và mức rủi ro chấp nhận được cần do tôi cùng nhóm xem xét
dựa trên bằng chứng thực tế, không giao hoàn toàn cho AI quyết định.

## Bài học rút ra

Bài học lớn nhất của tôi là **một AI Product không thể được đánh giá chỉ bằng tỷ
lệ PASS tổng**. Run 02 tăng từ 65% lên 70%, nhưng vẫn có một batch bị chặn vì
Gemini tạo evidence không tồn tại. Nếu nhóm chỉ tối ưu điểm số hoặc âm thầm dùng
fallback, sản phẩm có thể trông như hoạt động tốt trong khi người học nhận nội
dung sai.

Vì vậy, Quality Bar cần có hai lớp: một ngưỡng chất lượng tổng thể để đo mức hữu
ích và một điều kiện cứng cho lỗi có hậu quả cao. Với sản phẩm giáo dục này,
grounding sai là lỗi không được phép đánh đổi. Tôi cũng học được rằng spec không
phải tài liệu viết một lần rồi kết thúc; nó phải được cập nhật từ evaluation,
phản hồi người dùng và các lỗi quan sát được trong quá trình triển khai.

## Việc cần hoàn thành trước demo

- Đối chiếu lại toàn bộ số liệu và trích dẫn trong `spec.md` với artifact gốc.
- Phối hợp xử lý nguyên nhân các case EVAL-11–15 bị chặn và làm rõ expected terms
  của EVAL-02, sau đó chạy lại nguyên golden set 20 case.
- Kiểm tra demo có đủ happy path và failure path “evidence không tồn tại”.
- Xác nhận UI dùng ngôn ngữ thận trọng như “có thể đang nhầm”, không khẳng định
  chắc chắn lỗ hổng kiến thức của người học.
- Ghi kết quả chạy lại và phản hồi user retest vào bảng validation/changelog,
  giữ nguyên Quality Bar 80% và điều kiện zero-tolerance.
