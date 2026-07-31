# AI SPEC — No Name: Quiz chẩn đoán

Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở  
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới

> Trạng thái sau CP3: prototype đã có golden set Day 1 gồm 20 case và đã chạy
> Run 01 với cấu hình Gemini, đạt 13/20 (65%). Ba batch được Gemini tạo review;
> một batch rơi vào fallback và bị tính FAIL. Nhóm đã có survey khám phá vấn đề
> với 14 phản hồi; user validation trên prototype vẫn chưa thực hiện.

## §1. User & Job

- **Job executor:** học viên đang học lại nội dung của Day 01 hoặc Day 02.
- **Workflow hiện tại:** mở slide → đọc/tìm đoạn chưa hiểu → hỏi AI Tutor, bạn học
  hoặc tự đọc lại → vẫn khó biết chính xác mình hiểu sai ý nào → tự chọn phần để ôn.
- **Core JTBD:** Khi vừa học xong một bài, học viên muốn kiểm tra mình đang hiểu sai
  phần nào và ôn đúng phần đó để không phải đọc lại toàn bộ slide.
- **Problem statement (không chứa AI):** Học viên chưa có một vòng kiểm tra ngắn,
  có căn cứ theo từng trang, để phát hiện phần kiến thức mình hiểu sai và ôn lại
  đúng chỗ trước khi chuyển sang bài tiếp theo.

### Bằng chứng — chuẩn B (mining data)

Nguồn: `data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv` và
`data/vlearn-pack/chatlog/DATA_DICTIONARY.md`.

- Tập dữ liệu có 1.261 cặp tin nhắn học viên–tutor, từ 369 học viên và 585 hội
  thoại trong giai đoạn 22–29/07/2026.
- 46,2% câu trả lời tutor không có citation; người học khó tự kiểm lại nguồn.
- Trường `misconceptions` không được dùng ở cả 1.261 lượt; tutor hiện tại chưa tạo
  ra tín hiệu có cấu trúc về chỗ học viên hiểu sai.
- Tutor chỉ hỏi câu kiểm tra hiểu bài ở 3/1.261 lượt, nên flow chủ yếu giải thích
  chứ chưa khép kín vòng “kiểm tra → phát hiện sai → ôn lại”.
- Mining từ 1.261 tin nhắn học viên bằng tìm kiếm không phân biệt hoa thường:
  571 tin từ 238 `user_id` ẩn danh có “giải thích”, “là gì” hoặc “tại sao”;
  132 tin từ 97 `user_id` ẩn danh có “tóm tắt”, “tóm gọn” hoặc “summary”; 33
  tin từ 29 `user_id` ẩn danh nhắc “quiz”, “bài tập”, “câu hỏi” hoặc “kiểm tra”.
  Đây là thống kê hành vi trong chatlog, không phải số người tham gia survey và
  không được diễn giải thành tỷ lệ xác nhận sản phẩm.

Ví dụ nguyên văn (giữ ngắn, tham chiếu bằng mã hội thoại/lượt):

1. C0002/T0330: “cách xử lý ngữ cảnh”
2. C0003/T1201: “tóm tắt”
3. C0013/T0990: “"Context" là gì”
4. C0015/T0811: “Designt Pattern ReAct là gì có lưu ý gì về nó?”
5. C0006/T0058: “xem bài tập thực hành lab day 2 chiều nay ở đaau”

Phương pháp kiểm lại: lọc `role=student`, tìm các nhóm từ khóa nêu trên trong
`content`, đếm số dòng và số `user_id` duy nhất. Các nhóm có thể giao nhau; không
cộng chúng thành một tổng.

### Bằng chứng — survey khám phá vấn đề

Survey có 14 phản hồi. Ở câu multi-select “Nếu có tự kiểm tra, bạn thường làm
bằng cách nào?”, 9/14 người (64,3%) chọn **“Hỏi AI Tutor trên VLearn”**, cao nhất
trong 5 lựa chọn. Ba cách gồm tự đặt câu hỏi, làm lại quiz cũ và hỏi bạn bè/TA
đều có 7/14 người chọn (50%). Cách tính là lọc câu trả lời của câu multi-select,
đếm số người tick từng lựa chọn rồi chia cho tổng 14 phản hồi; vì được chọn nhiều
đáp án nên các tỷ lệ không cộng thành 100%.

Ở câu “mức độ khó xác định điểm yếu kiến thức”, điểm trung bình là **3,79/5**;
9/14 người (64,3%) chọn mức 4/5. Hai kết quả cùng cho thấy AI Tutor đã là cách tự
kiểm tra phổ biến trong mẫu khảo sát nhỏ này, nhưng người học vẫn gặp khó khăn
trong việc xác định chính xác điểm yếu kiến thức. Đây là bằng chứng trực tiếp cho
khoảng trống mà quiz chẩn đoán và gói ôn theo câu sai hướng tới.

Giới hạn diễn giải: mẫu chỉ có 14 phản hồi nên không đại diện cho toàn bộ học
viên; survey cho thấy nhu cầu và workflow hiện tại, chưa chứng minh prototype
giải quyết được vấn đề. File hoặc link dữ liệu survey gốc cần được nhóm bổ sung
vào repo để người chấm có thể kiểm lại phép đếm.

## §2. Impact & quyết định chọn

Nhóm đã cân nhắc ba hướng chính:

| Hướng | Dữ liệu chính | Giá trị có thể tạo | Scope/rủi ro trong hackathon | Quyết định |
|---|---|---|---|---|
| Chỉ dùng transcript để tạo quiz | Transcript các buổi học | Bám lời giảng và ví dụ trên lớp | Transcript dài, khó gắn mỗi câu với citation theo đúng trang slide và cần thêm bước làm sạch/chia đoạn | Chưa chọn cho prototype đầu |
| Dùng chatlog để làm chatbot hỗ trợ | 1.261 lượt hỏi–đáp VLearn; 571 tin từ 238 `user_id` có nhu cầu giải thích | Đáp ứng workflow hỏi–đáp vốn đã phổ biến | Gần trùng AI Tutor hiện tại; khó chứng minh người học đã hiểu chỉ từ một câu trả lời | Không chọn |
| Dùng knowledge context chi tiết từ slide để tạo quiz chẩn đoán, gói ôn và quiz củng cố | Hai slide deck đã được chuẩn hóa theo trang; survey 9/14 dùng AI Tutor để tự kiểm tra nhưng mức khó xác định điểm yếu trung bình 3,79/5 | Tạo vòng khép kín “làm quiz → phát hiện câu sai → ôn đúng trang → làm quiz củng cố” | Scope rõ, citation kiểm tra được và khả thi trong thời gian ngắn; vẫn có rủi ro câu sai chưa chắc phản ánh đúng misconception | **Chọn** |

Sau khi cân đối scope và deadline, nhóm chọn làm quiz từ nội dung slide trước,
rồi dựa vào kết quả để tạo gói ôn tập cá nhân hóa và quiz củng cố. Hướng này có
workflow rõ, làm được trong thời gian hackathon, thể hiện một quyết định AI cụ
thể và tạo giá trị học tập có thể kiểm tra theo trang nguồn.

Quyết định cũng phù hợp với bằng chứng vấn đề: 9/14 người khảo sát đã dùng AI
Tutor để tự kiểm tra, nhưng mức khó xác định điểm yếu vẫn trung bình 3,79/5;
chatlog đồng thời cho thấy `misconceptions` không được ghi nhận ở 1.261 lượt và
câu hỏi kiểm tra hiểu bài chỉ xuất hiện ở 3/1.261 lượt.

- **Giả thuyết nguy hiểm nhất:** trả lời sai quiz thực sự phản ánh lỗ hổng kiến
  thức, thay vì do câu hỏi/distractor kém. Golden set và validation với học viên
  phải kiểm tra giả thuyết này.

## §3. Giải pháp tương tự đã nghiên cứu

| Giải pháp | Flow quan sát/đối chiếu | Đáng học | Đáng né | No Name khác gì |
|---|---|---|---|---|
| NotebookLM | Người dùng thêm nguồn rồi hỏi/khai thác nội dung theo nguồn | Đặt căn cứ gần output để người dùng tự kiểm | Một câu trả lời có nguồn vẫn chưa chứng minh người học đã hiểu | Bắt người học trả lời quiz trước rồi mới xác định phần cần ôn |
| Quizlet | Học bằng thẻ/câu hỏi và lặp lại nội dung | Vòng làm bài ngắn, phản hồi ngay | Nội dung sinh ra có thể không khớp đúng deck của khóa nếu nguồn/grounding yếu | Mỗi câu có `evidence_quote` và `source_page`, backend kiểm tra trước khi phát hành |
| VLearn AI Tutor hiện tại | Học viên bôi đoạn và hỏi; tutor giải thích/trả lời | Có sẵn ngữ cảnh tài liệu và phù hợp workflow trong lớp | 46,2% câu trả lời không citation; gần như không hỏi kiểm tra hiểu bài | Chuyển từ hỏi–đáp sang chẩn đoán–ôn tập–quiz củng cố |

## §4. Thiết kế

- **Lát cắt MỘT CÂU:** Khi một học viên hoàn thành quiz của một ngày học, AI dùng
  các câu trả lời sai để quyết định phần kiến thức có thể bị hổng và tạo gói ôn
  tập có trích dẫn đúng trang, giúp học viên ôn đúng chỗ trước quiz củng cố.
- **Quyết định AI trung tâm:** xác định `possible_gap` và các `key_points` cần ôn
  từ câu sai; model dùng là **`gemini-3.1-flash-lite`**.
- **Input:** `attempt_id`, các câu đúng/sai, misconception gắn với lựa chọn, nội
  dung knowledge theo trang của Day 01/Day 02.
- **Output:** lỗ hổng có thể có, giải thích câu sai, các ý cần ôn kèm
  `evidence_quote` và `source_page`, sau đó là quiz củng cố giữ cùng số câu
  5 hoặc 10 như lượt trước.
- **Lịch sử trong một chuỗi làm bài:** câu đã trả lời đúng bị loại khỏi các quiz
  tiếp theo; câu trả lời sai được phép xuất hiện lại sau ôn tập. Chuỗi được nối
  bằng `parent_attempt_id`; khi về trang chính và chọn bài mới, quiz không mang
  parent nên lịch sử loại trừ cũ không còn được áp dụng.

### Non-goals

1. Không làm chatbot hỏi–đáp tự do hoặc trả lời mọi kiến thức ngoài hai deck.
2. Không chấm bài tự luận, dự đoán năng lực tổng quát hay xếp hạng học viên.
3. Không thay giảng viên/TA quyết định điểm số, deadline hoặc chuẩn đầu ra.
4. Không tự tạo citation, kiến thức, ví dụ hoặc số liệu không tồn tại trong nguồn.

### Mức prototype và automation

- **Mức prototype:** [ ] Sketch  [ ] Mock  [x] Working.
- **Phần thật:** Next.js gọi REST API FastAPI; backend đọc knowledge JSON của hai
  deck, lưu quiz/attempt/review trong SQLite, chấm đáp án bằng logic xác định,
  kiểm tra evidence và citation ở server.
- **Phần phụ thuộc cấu hình:** Gemini thật chỉ chạy khi có `GEMINI_API_KEY` và
  `GEMINI_ENABLED=true`. Mặc định `ALLOW_FALLBACK=false`: lỗi AI được báo minh
  bạch ở luồng tạo quiz. Run 01 phát hiện riêng `review_service` vẫn âm thầm
  chuyển sang fallback khi Gemini lỗi; đây là defect cần sửa trước demo, và mọi
  output fallback bị tính FAIL trong evaluation.
- **Automation:** [ ] augment  [x] conditional  [ ] automate.
- **Lý do theo cost-of-error:** AI được tự tạo gói ôn khi output vượt validation;
  output thiếu căn cứ bị chặn. Nếu để lọt câu hỏi/đáp án sai, học viên khó phát
  hiện và có thể học sai, nên không tự động phát hành vô điều kiện.

### §4b. Nguyên tắc đã áp dụng

| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| HAX G1 — Làm rõ hệ thống làm được gì | Trang đầu giới hạn lựa chọn ở Day 01/Day 02 và flow quiz–ôn–củng cố; không trình bày như chatbot đa năng |
| HAX G2 — Làm rõ hệ thống làm tốt đến đâu | Mỗi câu và mỗi key point hiển thị evidence/citation để học viên tự mở PDF kiểm lại |
| HAX G10 — Thu hẹp phạm vi khi nghi ngờ | Chỉ retrieve trang `is_instructional=true`; thiếu knowledge/API hoặc output không hợp lệ thì báo lỗi thay vì làm liều |
| HAX G11 — Giải thích vì sao | Kết quả nêu đáp án, misconception, explanation và đoạn evidence đã dùng |
| PAIR — Explainability & Trust | Citation không do model tự đặt: backend xác nhận quote tồn tại đúng trang |
| PAIR — Errors & Graceful Failure | `ALLOW_FALLBACK=false` ở cấu hình sản phẩm; lỗi Gemini/validation đi theo đường báo lỗi minh bạch |
| PAIR — Feedback & Control | Học viên tự chọn ngày học và số lượng câu; có thể mở PDF nguồn để đối chiếu trước khi tiếp tục |

## §5. Kiểu lỗi — 4 lớp chỗ khó và kịch bản

| # | Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc |
|---:|---|---|---|---|
| 1 | Model viết evidence nghe hợp lý nhưng không có trong trang | Nguồn sự thật | Backend từ chối toàn bộ quiz/review, không hiển thị cho học viên; log `EVIDENCE_NOT_FOUND_IN_PAGE` | G2, G10 |
| 2 | Model trích đúng câu nhưng gắn sai `source_page` | Nguồn sự thật | Validation đối chiếu quote với đúng trang, từ chối và báo lỗi | G2, Explainability |
| 3 | Trang chỉ là agenda/bìa hoặc không có kiến thức đủ để hỏi | Mơ hồ/thiếu thông tin | Loại trang bằng `is_instructional=false`; không đoán nội dung | G10 |
| 4 | Một câu sai có thể do nhiều misconception khác nhau | Mơ hồ/thiếu thông tin | Dùng cụm “có thể đang hổng/nhầm”, đưa evidence để tự kiểm; không khẳng định chẩn đoán chắc chắn | G2, G10 |
| 5 | Người dùng muốn quiz về kiến thức ngoài Day 01/Day 02 | Ngoài phạm vi | Không sinh nội dung; chỉ cho chọn hai tài liệu đang hỗ trợ | G1, G10 |
| 6 | Người dùng muốn xem đáp án trước khi nộp | Ngoài thẩm quyền | API public không trả `correct_answer` trước khi chấm; chỉ hiện sau khi nộp đủ câu | G1, Feedback & Control |
| 7 | Model tạo đáp án sai nhưng evidence có thật | Đặc thù domain | Kiểm tay trong golden set; nếu phát hiện thì đánh fail dù schema/citation hợp lệ và giữ hệ thống ở mức conditional | G2, G11 |
| 8 | Gói ôn tập suy ra sai lỗ hổng khiến học viên ôn lệch | Đặc thù domain | Hiển thị “possible gap”, câu sai và căn cứ; cho học viên mở nguồn, không dùng kết quả để chấm điểm chính thức | G2, Explainability |
| 9 | Gemini lỗi khi tạo review nhưng service âm thầm trả fallback | Hành vi khi lỗi — đã quan sát ở Run 01 | Không tính là output AI đạt; sửa service để trả lỗi minh bạch khi `ALLOW_FALLBACK=false` | G10, Graceful Failure |

Failure đáng sợ nhất khi demo là **câu trả lời sai nhưng có citation đúng định
dạng**, vì người học dễ tin hơn và backend không thể phát hiện chỉ bằng schema.
Case này bắt buộc có trong golden set và vòng chấm tay.

## §6. Bốn đường đi của trải nghiệm

- **Happy path:** học viên chọn Day 01/Day 02 và 5/10 câu → quiz được validate
  → học viên nộp đủ → xem câu sai và evidence → tạo gói ôn → làm quiz củng cố
  cùng số câu
  → xem so sánh trước–sau.
- **Low-confidence (⚠):** chỉ một đáp án sai hoặc tín hiệu có nhiều cách hiểu →
  dùng ngôn ngữ “có thể đang nhầm”, chỉ đưa key point bám nguồn và mời học viên
  mở trang gốc kiểm lại; không gắn nhãn năng lực chắc chắn.
- **Failure/không cứu (⛔):** Gemini, knowledge base hoặc validation lỗi →
  dừng phát hành output và hiển thị thông báo thử lại; không dùng quiz mẫu nếu
  `ALLOW_FALLBACK=false`.
- **Correction (user sửa):** học viên mở citation/PDF, đối chiếu đáp án và có thể
  tạo lượt quiz mới; prototype hiện chưa có nút báo “citation sai”, đây là hạng
  mục cần validation và backlog.
- **Ngoài phạm vi (🚫):** yêu cầu kiến thức ngoài hai deck hoặc xin đáp án trước
  khi nộp → từ chối ở boundary API/UI, hướng người dùng quay về chọn tài liệu.
- **Case đặc thù domain (🧠):** citation đúng nhưng diễn giải/đáp án sai → coi là
  hard failure; không dùng review đó để khẳng định học viên đã hiểu sai.

## §7. Kiểm thử

### Các chiều chất lượng và định nghĩa kiểm chứng

Một case chỉ **đạt tổng** khi đạt tất cả điều kiện bắt buộc áp dụng cho case đó:

| Chiều | Điều kiện PASS kiểm chứng được | Điều kiện FAIL |
|---|---|---|
| Grounding | Mọi `evidence_quote` tồn tại nguyên văn sau chuẩn hóa khoảng trắng trong đúng `source_page`; trang thuộc tài liệu đã chọn | Có ít nhất một quote không tồn tại, sai trang hoặc lấy từ trang không instructional |
| Đúng kiến thức | Câu hỏi có đúng một đáp án suy ra trực tiếp từ evidence; explanation không mâu thuẫn nguồn | Đáp án sai, nhiều đáp án cùng đúng, hoặc thêm kiến thức không có căn cứ |
| Chẩn đoán hữu ích | `possible_gap` liên hệ trực tiếp ít nhất một câu sai/misconception và dùng ngôn ngữ không khẳng định quá mức | Nêu lỗ hổng không liên quan, bỏ qua toàn bộ câu sai, hoặc kết luận chắc chắn về năng lực |
| Đúng phạm vi | Chỉ dùng Day 01/Day 02, không lộ đáp án trước khi nộp và không dùng trang hành chính | Làm theo yêu cầu ngoài nguồn/thẩm quyền |
| Hành vi khi lỗi | Input/output thiếu hoặc invalid bị chặn, có lỗi minh bạch và không giả làm kết quả AI thành công | Trả quiz/review bịa hoặc âm thầm tráo fallback |
| Hình thức quiz | Đủ số câu yêu cầu, mỗi câu 4 lựa chọn A–D, ID duy nhất, coverage đạt rule server | Sai schema, trùng câu, sai số lượng hoặc coverage không đạt |

### Golden set

- **Quy mô cam kết:** 20 case trong `eval/`.
- **Cơ cấu:** 8 case thường; 8 case khó (mỗi lớp ở §5 ít nhất 2 case); 4 case
  hiếm/kết hợp lỗi.
- **Nguồn bộ thử:** 20/20 case do nhóm tự xây dựng từ nội dung slide Day 1.
  Hiện chưa có artifact xác nhận case nào bắt nguồn từ quan sát người dùng hoặc
  log tự dùng thử, nên chưa khai các case này là “quan sát thực tế”.
- **Trạng thái:** `eval/golden-set.json` chứa 20 case cố định, không trùng ID
  hoặc trang nguồn; runner chia thành 4 batch × 5 case để gọi review nhưng vẫn
  chấm trên cùng một golden set qua mọi lần chạy.

### Quality bar — chốt tại thời điểm commit spec

> **Đạt khi ≥80% case trong toàn bộ golden set PASS, đồng thời không có bất kỳ
> lần nào phát hành câu hỏi, đáp án hoặc citation chứa thông tin không có trong
> đúng trang nguồn.**

Điều kiện cứng tính cả trường hợp citation có vẻ hợp lý nhưng sai trang. Nếu một
case vi phạm điều kiện cứng, lượt chạy không đạt quality bar dù tỷ lệ tổng ≥80%.

### Kết quả các lượt chạy

| Lượt | Model/cấu hình | Đạt/tổng | Tỷ lệ | Điều kiện cứng | Kết luận |
|---|---|---:|---:|---|---|
| Run 01 — 30/07/2026 | `gemini-3.1-flash-lite`; `ALLOW_FALLBACK=false`; 4 batch × 5 case cố định | 13/20 | 65% | Đạt: không có evidence/citation sai trang trong output đã chấm | **Chưa đạt** quality bar ≥80% |

Run 01 có 7 case fail. EVAL-02 và EVAL-18 không chứa đủ các thuật ngữ bắt buộc
trong expected output. Năm case EVAL-11–15 thuộc cùng batch bị đánh fail vì
review được tạo bởi nhánh `fallback` thay vì Gemini, dù cấu hình toàn cục đặt
`ALLOW_FALLBACK=false`. Đây là dấu hiệu cần sửa `review_service` để không âm
thầm dùng fallback khi Gemini lỗi. Bảng đầy đủ, bao gồm toàn bộ case fail, nằm
trong `eval/run-01.md`; output và từng check chi tiết nằm trong
`eval/run-01.json`.

## §8. Phân công & kế hoạch

### Phân công có tên

| Phần | Người chịu trách nhiệm | Deliverable |
|---|---|---|
| Spec + quality bar | Nguyễn Đức Trọng | `spec.md` |
| Evidence mining | Nguyễn Quang Minh | truy vấn đếm + trích dẫn mã hội thoại |
| Prompt + golden set | Đào Quốc Đại | prompt Gemini + `eval/` |
| Backend + validation | Đặng Trần Trung Dũng | FastAPI, tool calling, grounded validation |
| Frontend + demo | Trần Hà Bảo Long | Next.js flow + demo script |

### Trạng thái validation

| Loại validation | Trạng thái hiện tại | Bằng chứng | Kết luận được phép |
|---|---|---|---|
| Technical validation | Đã triển khai | Backend kiểm tra schema, số lượng câu, trang instructional, `evidence_quote` có tồn tại trong đúng `source_page`, coverage và ID trùng | Có thể kết luận output qua được các kiểm tra kỹ thuật đã định nghĩa |
| Evaluation với golden set | Đã chạy Run 01 | `eval/run-01.md` và `eval/run-01.json`: 13/20 PASS | Chất lượng AI hiện đạt 65%, chưa đạt quality bar 80% |
| User validation | **Chưa thực hiện** | Chưa có người thử, quote, biên bản quan sát hoặc feedback log trong `validation/` | Chưa được kết luận sản phẩm dễ dùng, hữu ích hoặc tạo niềm tin đúng mức |

Nhóm chưa khai trên willing user vì chưa có người tham gia được xác nhận. Kế
hoạch CP5 là mời ít nhất 5 người ngoài nhóm làm một quiz ngắn, quan sát trực tiếp
và hỏi ba câu:

1. Sau khi xem kết quả, bạn có chỉ ra được chính xác phần nào cần ôn lại không?
2. Citation có giúp bạn kiểm tra đáp án trong slide nhanh và tin đúng mức hơn không?
3. Có câu hỏi, đáp án hoặc chẩn đoán nào sai/khó hiểu; nếu có, sai ở đâu?

Nếu thực hiện được, nhóm sẽ lưu quote nguyên văn, quan sát, vấn đề, mức nghiêm
trọng và thay đổi sau feedback trong `validation/`. Trước khi có các artifact
này, mọi nhận định về trải nghiệm người dùng chỉ là giả thuyết, không phải kết
quả validation.

### Tiến độ và kế hoạch trước demo

1. **CP3 — đã hoàn thành:** tạo 20 case cố định từ Day 1, chốt expected output,
   chạy đủ bộ với `gemini-3.1-flash-lite` được cấu hình; 3/4 batch có review từ
   Gemini và 1/4 batch dùng fallback nên bị tính FAIL. Lưu đủ 13 PASS và 7 FAIL
   trong `eval/run-01.md` và `eval/run-01.json`.
2. **Trước CP4:** demo một happy path và failure “evidence không tồn tại”; kiểm
   tra các kịch bản §5, bao gồm defect fallback đã thấy ở Run 01.
3. **Trước CP5 — chưa thực hiện:** tuyển ít nhất 5 người ngoài nhóm dùng thử,
   ghi nhận quote/quan sát thật và cập nhật changelog từ feedback; không khai
   số người hoặc kết luận trải nghiệm trước khi có log.
4. **Trước CP6:** sửa nhánh fallback của review, làm rõ expected terms cho
   EVAL-02/EVAL-18 rồi chạy lại nguyên golden set; không thay đổi quality bar
   80% và điều kiện zero-tolerance.

### Multi-prototype

Không làm multi-prototype trong lát cắt này. Nhóm ưu tiên kiểm chứng một flow
working end-to-end và grounding thay vì chia thời gian cho hai UI khác nhau.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao / bằng chứng |
|---|---|---|
| 31/07/2026 — làm rõ quyết định | Ghi lại ba hướng đã cân nhắc: transcript tạo quiz, chatlog làm chatbot, và knowledge context theo slide | Chọn hướng slide → quiz chẩn đoán → gói ôn → quiz củng cố vì workflow rõ, citation kiểm tra được và vừa scope hackathon |
| 31/07/2026 — bổ sung evidence | Thêm survey khám phá vấn đề gồm 14 phản hồi vào bằng chứng và ma trận impact | 9/14 dùng AI Tutor để tự kiểm tra; điểm khó xác định điểm yếu trung bình 3,79/5, trong đó 9/14 chọn mức 4/5 |
| 30/07/2026 — chốt N1 | Chọn lát cắt quiz chẩn đoán → gói ôn tập theo câu sai | Chatlog cho thấy `misconceptions` chưa được dùng và tutor gần như không hỏi kiểm tra hiểu bài |
| 30/07/2026 — chốt N1 | Chọn conditional automation; server validate evidence/citation | Sai kiến thức có cost-of-error khó tự phát hiện |
| 30/07/2026 — chốt N1 | Chốt quality bar ≥80% + zero-tolerance với nội dung/citation không có trong đúng trang | Đây là lỗi làm người học tin sai; không được hạ bar sau khi đo |
| 30/07/2026 — CP3 Run 01 | Tạo golden set cố định 20 case từ các trang 3–22 của Day 1; chạy 4 batch × 5 | Đủ 20 input/expected output, không trùng ID hoặc trang; bảng đầy đủ trong `eval/run-01.md` |
| 30/07/2026 — CP3 Run 01 | Ghi nhận 13/20 PASS (65%), chưa đạt bar 80%; grounding/citation không sai | EVAL-02 và EVAL-18 thiếu expected terms; EVAL-11–15 bị fallback thay vì Gemini |
| 30/07/2026 — CP3 Run 01 | Đưa defect silent fallback của `review_service` vào backlog ưu tiên | Cấu hình `ALLOW_FALLBACK=false` nhưng một batch review vẫn trả `generated_by=fallback`; evaluation đã tính cả 5 case là FAIL |
| Sau CP5 | **[CẬP NHẬT thay đổi từ feedback hoặc lý do giữ nguyên]** | Trỏ tới log trong `validation/` |
