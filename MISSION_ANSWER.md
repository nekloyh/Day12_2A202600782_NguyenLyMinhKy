# Day 12 Lab - Mission Answers

> **Student Name:** Nguyễn Lý Minh Kỳ 
> **Student ID:** 2A202600782  
> **Date:** 12-06-2026

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. API key và database URL bị hardcode, dễ lộ khi đẩy code lên gitHub
2. Không có config management, các cấu hình nằm trực tiếp trong code
3. Dùng print thay cho logging 
4. In API key ra log
5. Không có health check để hệ thống theo dõi trạng thái ứng dụng
6. Host và port bị hardcode
7. Luôn ở debug mode và reload, không phù hợp với production
8. Không xử lý graceful shutdown 


### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode trong app.py | Đọc từ env và quản lý trong config.py | Dễ thay đổi theo môi trường và tránh lộ secret |
| Logging | Dùng print | JSON | Dễ tìm kiếm, phân tích và theo dõi lỗi |
| Health check | Không có | Có health và ready | Giúp platform kiểm tra và restart khi cần |
| Shutdown | Tắt đột ngột | Graceful shutdown | Hạn chế mất dữ liệu và gián đoạn request |
| Host/Port | Cố định port 8000 | Đọc từ env, host 0.0.0.0 | Chạy được trong container và trên cloud |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11`.
2. Working directory: `/app`.
3. Copy `requirements.txt` trước để tận dụng Docker layer cache. Khi code đổi nhưng dependencies không đổi, Docker không cần cài lại package.
4. `CMD` là lệnh mặc định và có thể bị ghi đè khi chạy container. `ENTRYPOINT` là lệnh chính, thường được giữ cố định.

### Exercise 2.2: Build and run
- Image develop build và chạy thành công, endpoint `/health` phản hồi trạng thái `ok`.

### Exercise 2.3: Multi-stage build
- Stage 1 (`builder`): cài build tools và toàn bộ Python dependencies.
- Stage 2 (`runtime`): chỉ lấy dependencies và source code cần để chạy ứng dụng.
- Image nhỏ hơn vì không chứa compiler, build tools và các file trung gian.

#### Image size comparison
- Develop: 1.66 GB
- Production: 234 MB
- Difference: giảm khoảng 86%

### Exercise 2.4: Docker Compose stack
- Các service: `nginx`, `agent`, `redis` và `qdrant`.
- Client gửi request vào Nginx, Nginx chuyển tiếp đến Agent. Agent kết nối Redis để cache/rate limit và Qdrant để lưu, tìm kiếm vector.

```text
Client -> Nginx -> Agent -> Redis
                         -> Qdrant
```

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://day12-ex3-782.onrender.com
- Screenshot: [Log deployment](03-cloud-deployment/screenshot/log.png)
- Health check: Passed
- Screenshot: [Health check](03-cloud-deployment/screenshot/terminal.png)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- API key: thiếu key trả `401`, key sai trả `403`, key đúng trả `200`.
- JWT: đăng nhập qua `/auth/token` và gọi `/ask` thành công bằng Bearer token.
- Rate limiting dùng Sliding Window: user `10 request/phút`, admin `100 request/phút`; vượt giới hạn trả `429`.
- Screenshots: [API key](04-api-gateway/screenshot/develop.png), [JWT và rate limit](04-api-gateway/screenshot/production.png).

### Exercise 4.4: Cost guard implementation
- Ước tính chi phí từ số input/output token và kiểm tra budget trước khi gọi LLM.
- Theo dõi budget theo user và toàn hệ thống; trả `402` khi user hết budget, `503` khi global budget hết.
- Bản demo lưu usage trong memory; production nên chuyển sang Redis để dùng chung giữa nhiều instance.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- `/health` kiểm tra liveness; `/ready` trả `503` khi agent chưa sẵn sàng hoặc đang shutdown.
- Graceful shutdown nhận `SIGTERM`, ngừng nhận request mới và chờ request đang xử lý hoàn thành.
- Conversation history được lưu trong Redis để các instance dùng chung state.
- Nginx phân phối request round-robin tới ba agent instance.
- `test_stateless.py` kiểm tra nhiều instance vẫn đọc được cùng session history từ Redis.

## Part 6: Final Project

### Vietnamese-Korean Travel Honorific Translator
- Dịch câu tiếng Việt trong môi trường du lịch sang tiếng Hàn trang trọng.
- Trả kèm phiên âm, mức kính ngữ, giải thích ngữ pháp và ghi chú văn hóa.
- Dùng OpenAI `gpt-4o-mini` với Structured Outputs.
- Có API key, rate limit `10 request/phút`, token guard global và per-user `100.000 token/tháng`.
- Lịch sử dịch lưu trong Redis; có health check, readiness và structured logging.
- Docker multi-stage chạy non-root; deploy bằng Render Blueprint.
- URL: `https://YOUR-RENDER-SERVICE.onrender.com`
- Evidence: [Deployment guide](06-lab-complete/DEPLOYMENT.md)
