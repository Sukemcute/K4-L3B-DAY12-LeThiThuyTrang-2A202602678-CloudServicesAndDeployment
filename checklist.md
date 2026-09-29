# Checklist Thực Hiện Lab 12: Hạ Tầng Cloud & Deployment
> **Học viên:** Lê Thị Thùy Trang | **MSSV:** 2A202602678  
> **Repository:** `K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment`  
> **Thang điểm:** 100 điểm bắt buộc (CP1-CP5: 85đ + Exercises: 15đ) + 10 điểm Bonus CI/CD  
> **Mục tiêu:** Đạt tối đa điểm, tuân thủ 100% quy định an toàn bảo mật, không bị trừ điểm oan.

---

## ⚠️ Nguyên Tắc Sống Còn & Phòng Tránh Bị Trừ Điểm

- [x] **Tên repository**: Phải đúng 100% mẫu `K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment` *(sai tên bị trừ 5 điểm)*.
- [ ] **Bảo mật file `.env`**: Tuyệt đối **KHÔNG commit file `.env`** *(vi phạm bị trừ 10 điểm và hủy secret)*. Chỉ commit `.env.example`.
- [ ] **Bảo mật Secret/API Key**: Không dán giá trị API key / secret vào bất kỳ đâu trong repo (`DEPLOYMENT.md`, `README.md`, code, commit message, ảnh chụp màn hình).
- [ ] **Commit đều đặn**: Tạo commit riêng sau mỗi Checkpoint (CP0 -> CP5). Không dồn toàn bộ bài vào 1 commit duy nhất.
- [ ] **Hiểu rõ code**: Nắm chắc cơ chế hoạt động của từng đoạn code để trả lời phỏng vấn Lab Coach *(không giải thích được bị hủy điểm phần đó)*.

---

## Phase 0: Khởi Tạo Môi Trường & Baseline (CP0 — Start +20 phút)

- [x] **Tạo môi trường ảo Python & cài đặt dependencies**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- [x] **Khởi tạo file cấu hình `.env`**:
  ```powershell
  Copy-Item .env.example .env
  ```
- [x] **Sinh `AGENT_API_KEY` ngẫu nhiên và lưu vào `.env`**:
  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [x] **Khởi động Redis**:
  ```powershell
  docker compose up -d redis
  docker compose ps
  ```
- [x] **Chạy baseline test**:
  ```powershell
  pytest tests/ -v -m "not docker"
  ```
- [x] **Commit CP0**:
  ```powershell
  git commit -m "checkpoint 0: setup environment"
  ```

---

## Phase 1: 12-Factor Config, Health & Logging (CP1 — 15/15 điểm | ĐÃ HOÀN THÀNH ✅)

- [x] **1.1. Cấu hình [app/config.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/config.py)**:
  - Khai báo đủ 6 trường trong `Settings`:
    - `port: int = 8000`
    - `agent_api_key: str` (**KHÔNG CÓ GIÁ TRỊ MẶC ĐỊNH** để Fail-Fast)
    - `redis_url: str = "redis://localhost:6379/0"`
    - `rate_limit_per_minute: int = 10`
    - `monthly_budget_usd: float = 10.0`
    - `log_level: str = "INFO"`
- [x] **1.2. Structured JSON Logging [app/logging_utils.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/logging_utils.py)**:
  - Cài đặt hàm `log_event(event, level="info", **fields)`
  - Dict gồm `event`, `level` (chuyển `.lower()`), `timestamp` (`utc_now_iso()`), và merge `fields`
  - Ghi ra stdout trên **một dòng duy nhất** (`json.dumps(..., ensure_ascii=False)`, không `indent`)
  - Trả về chính chuỗi JSON đó
- [x] **1.3. Liveness Probe `/health` trong [app/main.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/main.py)**:
  - Nếu `lifecycle.shutting_down == True` -> trả về `JSONResponse(status_code=503, content={"status": "shutting_down"})`
  - Ngược lại -> trả về `{"status": "ok", "service": SERVICE_NAME, "version": SERVICE_VERSION}` (200 OK)
  - `/health` không nhận dependency nào và không gọi Redis/DB
- [x] **Kiểm thử Checkpoint 1**:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_cp1.py -v` (13/13 test PASS)
- [ ] **Commit CP1**:
  ```powershell
  git add app/ config.py logging_utils.py main.py checklist.md
  git commit -m "CP1: 12-Factor config, structured logging and health endpoint"
  ```

---

## Phase 2: Docker Production-Ready (CP2 — 15/15 điểm | ĐÃ HOÀN THÀNH ✅)

- [x] **2.1. Cập nhật [.dockerignore](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/.dockerignore)**:
  - Bổ sung: `.env`, `.env.*`, `.git`, `.gitignore`, `__pycache__`, `.venv`, `*.pyc`, `*.pyo`, `.pytest_cache`, `.agent`
  - Đảm bảo không ignore `app/`, `utils/`, `requirements.txt`
- [x] **2.2. Viết lại [Dockerfile](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/Dockerfile) chuẩn Production**:
  - Stage 1 (`builder`): Base `python:3.11-slim`, `COPY requirements.txt .`, `RUN pip install --no-cache-dir --prefix=/install -r requirements.txt`
  - Stage 2 (`runtime`): Base `python:3.11-slim`, `COPY --from=builder /install /usr/local`
  - Copy mã nguồn sau: `COPY app ./app`, `COPY utils ./utils`
  - Tạo non-root user: `RUN useradd --create-home --uid 10001 appuser` và chuyển `USER appuser`
  - Thêm chỉ thị `HEALTHCHECK`:
    ```dockerfile
    HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
        CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1
    ```
  - Đọc cổng linh hoạt từ `$PORT`:
    ```dockerfile
    CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
    ```
- [x] **2.3. Bổ sung service `agent` vào [docker-compose.yml](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/docker-compose.yml)**:
  - `build: .`
  - `ports: ["8000:8000"]`
  - `depends_on: redis`
  - `environment`: `AGENT_API_KEY: ${AGENT_API_KEY}`, `REDIS_URL: redis://redis:6379/0`
  - Thêm healthcheck gọi `/health`
- [x] **Kiểm thử Checkpoint 2**:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_cp2.py -v` (16/16 test PASS)
  - `docker images day12-agent:prod`: kích thước **184MB** (đạt tiêu chuẩn < 500MB)
  - `docker compose ps`: Cả 2 service `agent` và `redis` đều healthy
  - `curl http://localhost:8000/health`: 200 OK
- [ ] **Commit CP2**:
  ```powershell
  git add Dockerfile docker-compose.yml .dockerignore
  git commit -m "CP2: Multi-stage Dockerfile, non-root user, and docker-compose stack"
  ```

---

## Phase 3: API Security — Auth, Rate Limit, Cost Guard (CP3 — 20 điểm | Start +160 phút)

- [ ] **3.1. Xác thực API Key [app/auth.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/auth.py)**:
  - Đọc `x_api_key` và `x_user_id` từ Header
  - Lấy secret từ `get_settings().agent_api_key`
  - So sánh bằng `secrets.compare_digest(x_api_key, expected_key)` (chống timing attack)
  - Không khớp / thiếu -> raise `HTTPException(status_code=401, detail="invalid or missing API key")`
  - Khớp -> trả về `x_user_id` hoặc `ANONYMOUS_USER`
- [ ] **3.2. Rate Limiting Sliding Window [app/rate_limiter.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/rate_limiter.py)**:
  - `hit_count(user_id, now)`: Dọn rác `zremrangebyscore(key, 0, now - WINDOW_SECONDS)` rồi trả về `zcard(key)`
  - `check(user_id, now)`:
    - Kiểm tra `hit_count >= self.limit` -> raise `HTTPException(status_code=429, detail="rate limit exceeded", headers={"Retry-After": str(WINDOW_SECONDS)})`
    - Nếu chưa vượt: Ghi nhận bằng `zadd(key, {f"{now}:{uuid.uuid4().hex}": now})`, sau đó đặt TTL `expire(key, WINDOW_SECONDS)`
- [ ] **3.3. Cost Guard [app/cost_guard.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/cost_guard.py)**:
  - `spent(user_id, month)`: đọc từ Redis key `cost:<user>:<month>`, nếu None trả về `0.0`, ép kiểu float
  - `check(user_id, estimated_cost, month)`: nếu `spent + estimated_cost > self.budget` -> raise `HTTPException(status_code=402, detail="monthly budget exceeded")`
  - `record(user_id, cost, month)`: gọi `incrbyfloat(key, cost)` và `expire(key, KEY_TTL_SECONDS)`
- [ ] **3.4. Ghép nối endpoint `/ask` trong [app/main.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/main.py)**:
  - Thứ tự luồng: `limiter.check` -> `guard.check` -> `store.get_history` -> `ask_llm` -> `store.append` x 2 -> `guard.record` -> `log_event` -> return dict đúng format
- [ ] **Kiểm thử Checkpoint 3**:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_cp3.py -v
  ```
- [ ] **Commit CP3**:
  ```powershell
  git add app/
  git commit -m "CP3: Authentication, sliding-window rate limit, and cost guard"
  ```

---

## Phase 4: Scaling & Reliability (CP4 — 20 điểm | Start +200 phút)

- [ ] **4.1. Tách State vào Redis Store [app/store.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/store.py)**:
  - `ping()`: bọc trong try-except, trả về bool `True`/`False`
  - `append(user_id, role, content)`: `rpush`, `ltrim(key, -HISTORY_MAX_MESSAGES, -1)`, `expire(key, HISTORY_TTL_SECONDS)`
  - `get_history(user_id)`: `lrange(key, 0, -1)`, deserialize `json.loads` từng item
- [ ] **4.2. Readiness Probe `/ready` trong [app/main.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/main.py)**:
  - Nếu `lifecycle.shutting_down == True` -> 503 `{"status": "shutting_down"}`
  - Nếu `store.ping() == False` -> 503 `{"status": "not ready", "redis": False}`
  - Nếu sẵn sàng -> 200 `{"status": "ready", "redis": True}`
- [ ] **4.3. Graceful Shutdown [app/lifecycle.py](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/app/lifecycle.py)**:
  - `install()`: đăng ký cho SIGTERM & SIGINT, lưu handler cũ
  - `request_shutdown(signum, frame)`: bật cờ `shutting_down = True`, gọi lại handler cũ
- [ ] **Kiểm thử Checkpoint 4**:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_cp4.py -v
  ```
- [ ] **Commit CP4**:
  ```powershell
  git add app/
  git commit -m "CP4: Redis store, readiness probe, and graceful shutdown lifecycle"
  ```

---

## Phase 5: Cloud Deployment (CP5 — 15 điểm | Start +230 phút)

- [ ] **5.1. Triển khai dịch vụ lên Cloud (Railway hoặc Render)**
- [ ] **5.2. Hoàn thiện tài liệu [DEPLOYMENT.md](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/DEPLOYMENT.md)**
- [ ] **5.3. Bổ sung 2 ảnh minh chứng vào `screenshots/`**: `dashboard.png`, `health.png`
- [ ] **5.4. Kiểm thử Checkpoint 5**:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_cp5.py -v
  ```
- [ ] **Commit CP5**:
  ```powershell
  git add DEPLOYMENT.md screenshots/
  git commit -m "CP5: Deploy to cloud, document deployment and screenshots"
  ```

---

## Phase 6: Hoàn Thiện Phiếu Phản Ánh [exercises.md](file:///d:/Sukem/VinUni/Lab/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment/exercises.md) (15 điểm | 10 câu)

- [ ] Điền Họ tên và Mã học viên ở đầu file `exercises.md`.
- [ ] Trả lời đủ 10 câu hỏi suy ngẫm và xóa sạch placeholder `> *Câu trả lời của bạn*`.
- [ ] **Commit Exercises**:
  ```powershell
  git add exercises.md
  git commit -m "Complete all 10 reflection exercises"
  ```

---

## Phase 7 (Bonus): CI/CD với GitHub Actions (+10 điểm | Tùy chọn)

- [ ] Tạo `.github/workflows/ci.yml` và cấu hình CI test, build, deploy
- [ ] Thêm badge vào `README.md`
- [ ] Kiểm tra: `.\.venv\Scripts\python.exe -m pytest tests/test_bonus_cicd.py -v`
- [ ] **Commit Bonus**:
  ```powershell
  git add .github/ README.md
  git commit -m "Bonus: Add CI/CD GitHub Actions workflow and status badge"
  ```

---

## Phase 8: Rà Soát Cuối Cùng & Nộp Bài

- [ ] Chạy chấm điểm tự động: `.\.venv\Scripts\python.exe grade.py`
- [ ] Kiểm tra bảo mật git: `git ls-files | grep -E '(^|/)\.env$|\.(pem|key)$'` (không lộ `.env`)
- [ ] Push toàn bộ commit lên GitHub: `git push origin main`
- [ ] Nộp link repo lên Codelab: `https://github.com/Sukemcute/K4-L3B-DAY12-LeThiThuyTrang-2A202602678-CloudServicesAndDeployment`
