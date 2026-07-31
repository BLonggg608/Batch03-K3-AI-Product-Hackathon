# Reflection — Trần Hà Bảo Long (2A202601189)

## Vai trò trong nhóm

Frontend + demo: xây dựng và hoàn thiện luồng sử dụng trên Next.js, từ chọn bài học, làm quiz, xem kết quả đến ôn tập; đồng thời chuẩn bị luồng demo sản phẩm.

## Phần làm cá nhân

- Hoàn thiện giao diện trang chính và đổi tên sản phẩm thành **No Name**. Tôi đơn giản hóa màn hình chọn bài: chỉ giữ nút tạo quiz, giới hạn lựa chọn 5 hoặc 10 câu và bỏ các thông tin kỹ thuật không cần thiết như số trang, số từ hay mô tả về knowledge base.
- Chỉnh sửa giao diện làm quiz để nội dung và các lựa chọn dài hiển thị rõ ràng hơn, sửa lỗi tiếng Việt, bổ sung trạng thái tiến độ, số câu chưa trả lời và nút nộp bài phù hợp trên cả máy tính lẫn thiết bị di động.
- Hoàn thiện luồng sau khi nộp bài: nếu làm đúng toàn bộ thì người học có thể làm lại quiz hoặc về trang chính; nếu còn câu sai thì được chuyển sang phần ôn tập trước khi làm quiz củng cố.
- Cải thiện giao diện ôn tập, cách hiển thị nội dung tổng hợp, trích dẫn bằng chứng từ slide và các nút điều hướng để người học dễ theo dõi.
- Cập nhật kịch bản smoke test cho luồng chính nhằm hỗ trợ kiểm tra nhanh các màn hình quan trọng trước khi demo.

Các phần chính tôi làm nằm trong `codebase/frontend/app/page.tsx`, `codebase/frontend/app/quiz/[quizId]/page.tsx`, `codebase/frontend/app/result/[attemptId]/page.tsx`, `codebase/frontend/app/review/[attemptId]/page.tsx`, `codebase/frontend/app/globals.css` và `codebase/frontend/scripts/smoke.mjs`.

## AI hỗ trợ thế nào

Tôi sử dụng Codex để hỗ trợ rà soát các component, tìm lỗi hiển thị tiếng Việt, đề xuất cách tổ chức trạng thái giao diện, chỉnh CSS responsive và kiểm tra lỗi TypeScript. AI cũng giúp đối chiếu nhanh các màn hình trong toàn bộ luồng để phát hiện những chỗ thiếu nhất quán.

Tuy nhiên, tôi vẫn trực tiếp quyết định thông tin nào cần giữ hoặc loại khỏi giao diện, cách người học di chuyển giữa quiz — kết quả — ôn tập, và cách chuyển phản hồi của người thử nghiệm thành thay đổi cụ thể. Sau khi chỉnh sửa, phần frontend đã vượt qua lệnh kiểm tra TypeScript; tôi không coi đây là bằng chứng rằng toàn bộ luồng production đã được kiểm thử hoàn chỉnh.

## Một bài học từ case fail của nhóm

Phản hồi của Nguyễn Hoàng Quân cho thấy khi chọn làm lại quiz, hệ thống vẫn có thể đưa lại câu mà người học đã trả lời đúng. Dù từng màn hình có thể trông ổn, lỗi ở cách chuyển trạng thái giữa các màn hình vẫn làm trải nghiệm cá nhân hóa trở nên thiếu thuyết phục.

Từ case này, tôi rút ra rằng kiểm thử frontend không nên chỉ kiểm tra giao diện tĩnh mà phải đi hết các nhánh hành vi thực tế: làm đúng toàn bộ, làm sai rồi ôn tập, làm lại quiz và quay về trang chính. Đặc biệt, trạng thái lịch sử câu hỏi phải được thể hiện nhất quán với logic sản phẩm: câu đã làm đúng không nên lặp lại trong cùng một chuỗi học, còn câu làm sai có thể xuất hiện lại để củng cố kiến thức.
