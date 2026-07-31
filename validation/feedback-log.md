# User Validation Log — No Name

## Trạng thái

- Số người đã thử prototype: **5**
- Mục tiêu của nhóm: **ít nhất 5 người**
- Trạng thái: **Đã đạt mục tiêu số lượng người thử ban đầu**
- Phạm vi đã thử: tạo quiz, làm bài, xem kết quả, kiểm tra citation và làm lại quiz

Năm phản hồi dưới đây là bằng chứng ban đầu, chưa đủ để đại diện cho toàn bộ học
viên. Phản hồi của Lê Minh Khiêm và Nguyễn Hoàng Quân được lưu nguyên văn; ba
phản hồi còn lại là ý kiến do nhóm tóm tắt sau khi hỏi người thử, không phải
trích dẫn nguyên văn.

## Người thử 1 — Lê Minh Khiêm

- Tác vụ liên quan: làm quiz, xem kết quả và kiểm tra lại nội dung bằng citation.
- Phản hồi nguyên văn:

> “Có trích dẫn số trang nguyên văn giúp mình mở PDF ra check lại ngay lập tức.
> Cảm giác rất yên tâm vì không sợ AI bịa kiến thức.”

- Quan sát/rút ra: citation theo trang giúp người dùng đối chiếu lại nguồn nhanh
  và tạo cảm giác an tâm hơn khi sử dụng nội dung do AI tạo.
- Quyết định của nhóm: giữ cách hiển thị `evidence_quote` và liên kết tới đúng
  trang PDF trên màn hình kết quả và ôn tập.
- Trạng thái: giữ nguyên thiết kế; cần kiểm tra thêm với những người thử khác.

## Người thử 2 — Nguyễn Hoàng Quân

- Tác vụ liên quan: hoàn thành quiz rồi chọn làm lại quiz.
- Phản hồi nguyên văn:

> “Khi chọn làm lại quiz thì có những câu bị trùng với lần làm trước đó mặc dù
> họ làm đúng câu hỏi đó.”

- Vấn đề: câu người dùng đã trả lời đúng vẫn xuất hiện lại trong quiz tiếp theo.
- Mức nghiêm trọng: **Trung bình** — không làm hỏng toàn bộ flow nhưng khiến
  người học phải lặp lại phần đã nắm vững và làm giảm giá trị cá nhân hóa.
- Thay đổi đã làm:
  - Không lặp lại nội dung câu hỏi hoặc evidence của câu đã trả lời đúng trong
    cùng một chuỗi làm bài.
  - Câu trả lời sai vẫn được phép xuất hiện lại sau bước ôn tập để kiểm tra việc
    củng cố kiến thức.
  - Khi một câu từng sai được trả lời đúng ở lượt sau, câu đó sẽ bị loại khỏi
    các lượt tiếp theo trong chuỗi.
  - Khi người dùng quay về trang chính và chọn bài mới, lịch sử loại trừ của
    chuỗi cũ không còn được áp dụng.
- Bằng chứng kỹ thuật: backend nối các lượt bằng `parent_attempt_id`; validation
  loại `question` và `evidence_quote` đã trả lời đúng. Automated tests kiểm tra
  cả trường hợp đạt tuyệt đối và trường hợp còn câu sai.
- Trạng thái: **Đã sửa bằng code và automated test; chưa có phản hồi kiểm thử lại
  từ người dùng sau thay đổi.**

## Người thử 3 — Lương Đăng Doanh

- Tác vụ liên quan: chọn bài, tạo quiz và hoàn thành các câu hỏi trên giao diện.
- Phản hồi do nhóm tóm tắt: giao diện dễ nhìn, bố cục câu hỏi và các lựa chọn rõ
  ràng nên người dùng có thể thao tác mà không cần hướng dẫn thêm.
- Quan sát/rút ra: cách trình bày hiện tại hỗ trợ người dùng tập trung vào từng
  câu hỏi và theo dõi tiến độ làm bài.
- Quyết định của nhóm: giữ bố cục card câu hỏi, trạng thái lựa chọn và thanh tiến
  độ; tiếp tục kiểm tra khả năng hiển thị trên màn hình nhỏ.

## Người thử 4 — Đỗ Tuấn Kiệt

- Tác vụ liên quan: làm quiz và đối chiếu câu hỏi, đáp án với nội dung slide.
- Phản hồi do nhóm tóm tắt: các câu hỏi bám đúng kiến thức có trong slide, không
  tạo cảm giác hỏi sang nội dung ngoài bài học.
- Quan sát/rút ra: grounding theo trang và evidence giúp phạm vi câu hỏi rõ ràng
  hơn đối với người học.
- Quyết định của nhóm: giữ validation bắt buộc đối với `source_page` và
  `evidence_quote`; output không có evidence hợp lệ tiếp tục bị chặn.

## Người thử 5 — Trần Công Chiến

- Tác vụ liên quan: xem kết quả, đọc phần tổng hợp kiến thức và gói ôn tập sau
  khi hoàn thành quiz.
- Phản hồi do nhóm tóm tắt: phần tổng hợp kiến thức trong slide giúp người dùng
  nhận ra nội dung cần xem lại thay vì phải đọc lại toàn bộ tài liệu.
- Quan sát/rút ra: flow từ câu sai sang key point và citation thể hiện rõ giá trị
  ôn tập cá nhân hóa của sản phẩm.
- Quyết định của nhóm: giữ phần `possible_gap`, các key point và citation; tiếp
  tục dùng ngôn ngữ “có thể đang nhầm” để tránh khẳng định quá mức.

## Tổng hợp thay đổi từ feedback

Nhóm đã cải thiện cơ chế tạo quiz tiếp theo để không lặp lại câu hỏi hoặc
evidence của những câu học viên đã trả lời đúng. Các câu trả lời sai vẫn có thể
xuất hiện lại sau bước ôn tập để kiểm tra việc học lại. Lịch sử chỉ áp dụng trong
cùng chuỗi làm bài và được đặt lại khi người dùng quay về trang chính. Thay đổi
này giúp tránh việc học viên phải làm lại phần đã nắm vững nhưng vẫn giữ được
mục tiêu củng cố phần kiến thức còn sai.
