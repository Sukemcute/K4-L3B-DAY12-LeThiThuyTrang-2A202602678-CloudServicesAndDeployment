# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: điền câu trả lời bên dưới mỗi câu hỏi.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Lê Thị Thùy Trang  Mã học viên: 2A202602678

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Nếu để giá trị mặc định là `"changeme"`, khi mình deploy lên cloud (hoặc chạy môi trường production) mà sơ ý quên chưa cấu hình biến môi trường `AGENT_API_KEY`, ứng dụng vẫn sẽ khởi động bình thường như không có chuyện gì xảy ra. Hậu quả là bất kỳ ai trên Internet cũng có thể dùng key mặc định `"changeme"` để gọi vào endpoint `/ask`, làm lộ thông tin hoặc spam cạn sạch hạn mức API và tiền của mình. 

Ngược lại, khi áp dụng triết lý Fail Fast (không có key là app dừng ngay lập tức từ bước load config), container sẽ crash ngay khi vừa bật lên và platform (Render/Docker) sẽ báo đỏ báo lỗi deploy failed. Nhờ vậy mình lập tức nhận ra mình quên set biến môi trường để vào điền lại ngay, triệt tiêu hoàn toàn nguy cơ lọt lỗ hổng bảo mật ngớ ngẩn này ra môi trường thật.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng log JSON mình thu được thực tế từ terminal:
```json
{"timestamp": "2026-09-29T04:11:28.123456Z", "level": "info", "event": "ask_completed", "message": "Processed ask request successfully", "pid": 1, "service": "day12-agent", "user_id": "sv-test", "tokens_in": 3, "tokens_out": 37, "cost_usd": 2.265e-05, "history_length": 0}
```

Hai việc mình có thể làm với dòng log cấu trúc này mà `print("đã trả lời xong")` bó tay:
1. **Đẩy vào hệ thống quản lý log tập trung để lọc và vẽ biểu đồ tự động**: Các công cụ như Datadog, ELK Stack, Grafana Loki có thể tự động bóc tách (parse) các trường số như `tokens_in`, `tokens_out`, `cost_usd`. Từ đó mình dễ dàng tạo dashboard theo dõi tổng chi phí theo giờ/ngày theo thời gian thực và cài đặt alert cảnh báo khi chi phí tăng đột biến. Dùng `print` thì chỉ là text thô, máy không thể tự động tổng hợp số liệu được nếu không viết parser regex phức tạp.
2. **Truy vết và audit theo từng người dùng cụ thể**: Khi có sự cố hoặc người dùng thắc mắc, mình có thể query chính xác `user_id == "sv-test"` để xem bạn này đã hỏi bao nhiêu câu, tốn bao nhiêu token, chi phí tích lũy ra sao và tiến trình nào (`pid`) xử lý. `print("đã trả lời xong")` không hề có ngữ cảnh ai gọi, lúc mấy giờ và tốn bao nhiêu tài nguyên.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 485 MB |
| Multi-stage | 184 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Dung lượng giảm được tới hơn 300 MB chủ yếu là nhờ loại bỏ được những thành phần sau ở stage cuối:
- **Trình biên dịch và thư viện build**: Các gói như `gcc`, `build-essential`, header files cần thiết để compile một số thư viện Python chỉ nằm lại ở stage `builder`.
- **Cache của trình quản lý gói**: Thư mục cache `/root/.cache/pip` sinh ra khi chạy lệnh `pip install` được giữ ở builder chứ không bị copy sang stage runtime.
- **Base image gọn gàng**: Stage cuối dùng base `python:3.11-slim` chỉ chứa đúng môi trường runtime tối thiểu và copy mỗi thư mục ảo `/opt/venv` đã đóng gói sẵn cùng mã nguồn `app/`, giúp image vừa nhẹ vừa khởi động cực nhanh khi scale.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

- Khi chỉ sửa code trong `app/main.py` rồi build lại:
  + Các layer đầu tiên: `FROM python:3.11-slim`, `WORKDIR /app`, `COPY requirements.txt .`, và quan trọng nhất là `RUN pip install ...` đều được Docker tái sử dụng từ cache (`CACHED`) vì file `requirements.txt` không hề đổi.
  + Chỉ có layer `COPY app/ ./app/` và các layer cấp quyền sau nó mới bị chạy lại vì file code đã thay đổi. Thời gian build lại chỉ mất chưa đầy 2 giây.
- Nếu đặt `COPY . .` lên trước `RUN pip install`:
  + Mỗi lần sửa dù chỉ 1 ký tự trong file code, toàn bộ layer `COPY . .` sẽ bị thay đổi checksum.
  + Docker sẽ làm mất hiệu lực (bust) toàn bộ cache từ bước đó trở đi, buộc lệnh `RUN pip install` phải chạy lại từ đầu — phải download và cài đặt lại toàn bộ thư viện mỗi lần sửa code, làm quá trình build chậm đi gấp hàng chục lần.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

- Chuỗi sự kiện leo thang đặc quyền:
  1. Kẻ tấn công phát hiện một lỗ hổng trong code Python (ví dụ: thực thi lệnh qua `os.system` không validate, hoặc lỗ hổng RCE từ thư viện bên thứ ba).
  2. Kẻ tấn công inject được payload và mở được một reverse shell bên trong container.
  3. Nếu container đang chạy bằng quyền mặc định `root` (UID 0), shell đó có toàn quyền root trong container: có thể đọc ghi file nhạy cảm, can thiệp socket, hoặc cài thêm công cụ khai thác.
  4. Từ quyền root bên trong, kẻ tấn công khai thác tiếp các lỗ hổng container breakout (ví dụ lỗ hổng của Linux kernel, chia sẻ volume mount không an toàn, hoặc truy cập Docker socket) để thoát ra ngoài máy host. Lúc này trên máy host kẻ tấn công cũng tương đương quyền root của hệ thống.
- Lệnh `USER appuser` (UID 10001) cắt đứt chuỗi này ngay tại bước 3:
  Kẻ tấn công khi RCE vào container chỉ có quyền của một user thông thường không có đặc quyền. User này không có quyền ghi vào thư mục hệ thống, không thể chạy lệnh quản trị, và thiếu các Linux Capabilities cần thiết để thực hiện các cuộc tấn công vượt ngục container (container breakout).

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Người dùng có thể gửi tối đa **20 request** chỉ trong vòng 2 giây liên tiếp!

Cách đạt được con số đó (lỗ hổng boundary spike của fixed window):
- Giả sử hệ thống reset bộ đếm vào đúng đầu mỗi phút (giây 00).
- Người dùng đợi đến giây `59` của phút trước rồi dồn dập gửi 10 request. Hệ thống kiểm tra thấy trong phút đó người dùng chưa vượt quá 10 req nên cho qua cả 10.
- Ngay 1 giây sau, đồng hồ bước sang giây `00` của phút tiếp theo, bộ đếm tự động reset về 0. Người dùng lập tức xả tiếp 10 request nữa. Hệ thống thấy phút mới này người dùng mới gửi 10 req nên lại tiếp tục cho qua.
- Như vậy, chỉ từ giây `59` đến giây `00` (đúng 2 giây), server đã phải hứng chịu tới 20 request, gấp đôi tải cho phép. Thuật toán Sliding Window với Redis ZSET giải quyết triệt để vấn đề này vì luôn tính tổng request trong khoảng lùi 60 giây kể từ thời điểm request hiện tại.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

- **Điểm khác nhau cốt lõi**:
  + Rate limit bảo vệ **tính sẵn sàng tức thì của hạ tầng** (chống nghẽn CPU, RAM, nghẽn mạng) bằng cách kiểm soát **tần suất gọi API trong một khoảng thời gian ngắn** (ví dụ tối đa 10 req/phút).
  + Cost guard bảo vệ **ngân sách tài chính dài hạn** (chống cháy túi vì tiền gọi LLM API) bằng cách theo dõi **tổng chi phí tích lũy theo tháng**, tính theo lượng token tiêu thụ thực tế.

- **Tình huống Rate limit cho qua nhưng Cost guard phải chặn**:
  Người dùng gửi đúng 1 câu hỏi duy nhất trong ngày (hoàn toàn không vi phạm 10 req/phút). Nhưng trong các tuần trước người dùng này đã hỏi nhiều và tích lũy chi phí đạt ngưỡng $10.0 của tháng -> Cost guard lập tức chặn với mã `402 Payment Required`.

- **Tình huống Cost guard cho qua nhưng Rate limit phải chặn**:
  Đầu tháng người dùng mới dùng hết $0.02 / $10.0 (ngân sách còn rất nhiều). Nhưng họ dùng script gửi liên tục 15 câu hỏi ngắn chỉ trong vòng 3 giây -> Chi phí thì vẫn dưới hạn mức, nhưng Rate limit sẽ chặn các request từ thứ 11 trở đi với mã `429 Too Many Requests` để tránh làm sập server.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Thứ tự các sự kiện sẽ diễn ra như sau:
1. Redis gặp sự cố mạng hoặc restart trong 30 giây.
2. Cả 3 container gọi kiểm tra sức khỏe thì thấy Redis không phản hồi nên endpoint trả về `503 Service Unavailable`.
3. Bộ điều phối (Docker Compose/Kubernetes/Render) thấy health check trả về lỗi liên tiếp nên đánh giá cả 3 container của app đều đã bị hỏng/treo (unhealthy).
4. Bộ điều phối lập tức ra lệnh kill và restart lại toàn bộ 3 container của ứng dụng.
5. Khi container khởi động lại, Redis vẫn chưa online xong, container lại fail health check và tiếp tục bị restart liên tục theo vòng lặp (crash loop). Toàn bộ hệ thống bị sập hoàn toàn, các endpoint tĩnh hoặc logic không dùng Redis cũng bị chết theo.
-> Việc tách riêng giúp `/health` (liveness) giữ container sống, còn `/ready` (readiness) chỉ tạm thời ngắt traffic của người dùng tới container cho đến khi Redis phục hồi mà không phải khởi động lại container vô ích.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

- Khi dùng Redis (Stateless):
  Mỗi lần gửi câu hỏi mới, dù request rơi vào bất kỳ instance nào trong cụm 3 container thì `history_length` vẫn tăng đều đặn: `0 -> 2 -> 4 -> 6 -> 8...`. Cả 3 container đều chia sẻ chung một nguồn dữ liệu tại Redis nên hội thoại luôn liền mạch.
- Nếu lưu trong dict Python trong bộ nhớ RAM của app (Stateful):
  Con số `history_length` sẽ nhảy lộn xộn và không tăng đều. Ví dụ:
  + Request 1 rơi vào container A: `history_length = 0` (lưu vào dict của A).
  + Request 2 load-balancer chuyển sang container B: `history_length` lại là `0` vì RAM của B chưa có dữ liệu của user này. Agent trả lời như thể chưa từng nói chuyện với user.
  + Request 3 lại chuyển sang container C: `history_length` lại là `0`.
  + Request 4 quay lại trúng container A: `history_length` mới nhảy lên `2`.
  Trải nghiệm người dùng sẽ bị hỏng hoàn toàn vì agent lúc nhớ lúc quên tùy theo request rẽ vào đâu.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

- **Thông báo lỗi gặp phải**:
  Khi deploy lên Render, endpoint `/health` trả về `200 OK` nhưng endpoint `/ready` lại trả về lỗi `503 Service Unavailable` với body:
  `{"status":"not ready","redis":false}`
- **Cách tìm ra nguyên nhân**:
  Mình dùng script Python kiểm tra thử kết nối tới Upstash Redis qua URL hiện tại thì gặp lỗi `redis.exceptions.ConnectionError: Connection closed by server`. Đọc kỹ tài liệu Upstash thì thấy Upstash bắt buộc kết nối bảo mật mã hóa SSL/TLS qua cổng 6379, do đó giao thức bắt buộc phải là `rediss://` (hai chữ s) thay vì `redis://` như khi chạy Docker local ở máy.
- **Cách khắc phục**:
  Mình vào tab **Environment** trên dashboard của Render, sửa lại biến `REDIS_URL` từ `redis://default:...` thành `rediss://default:...`. Render tự động deploy lại phiên bản mới, và sau đó kiểm tra lại `/ready` đã trả về ngay `200 OK` với `{"status":"ready","redis":true}`.
