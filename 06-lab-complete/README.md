# Vietnamese-Korean Travel Honorific Translator

REST API dịch các câu tiếng Việt thường gặp trong du lịch sang tiếng Hàn trang
trọng. Mỗi kết quả gồm bản dịch, phiên âm, mức kính ngữ, giải thích ngữ pháp và
ghi chú văn hóa.

## Tính năng

- Ngữ cảnh: khách sạn, nhà hàng, giao thông, mua sắm và khẩn cấp.
- API key authentication.
- Sliding-window rate limit 10 request/phút/user.
- OpenAI `gpt-4o-mini` với Structured Outputs.
- Token guard 100.000 token/tháng cho toàn project và mỗi user, tính cả input/output.
- Lịch sử trong Redis, fallback memory khi chạy không có Redis.
- Health/readiness endpoints, structured logging và graceful shutdown.
- Multi-stage Docker image, non-root runtime và Render Blueprint.

## Chạy local

```bash
cp .env.example .env
# Điền OPENAI_API_KEY và AGENT_API_KEY trong .env, không commit file này.
docker compose up --build
```

Test:

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/translate \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","text":"Tôi muốn đặt phòng","situation":"hotel"}'

curl -H "X-API-Key: YOUR_AGENT_API_KEY" \
  http://localhost:8000/history/demo

curl -H "X-API-Key: YOUR_AGENT_API_KEY" \
  http://localhost:8000/usage/demo
```

## Chạy không dùng Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
AGENT_API_KEY=dev-translation-key uvicorn app.main:app --reload
```

## Deploy Render

1. Push repository lên GitHub.
2. Render Dashboard -> New -> Blueprint.
3. Chọn repository và nhập Blueprint path `06-lab-complete/render.yaml`.
4. Nhập `OPENAI_API_KEY` và một `AGENT_API_KEY` mạnh khi Render yêu cầu.
5. Không dùng giá trị mẫu `dev-translation-key` trên production.
6. Test `/health`, `/translate`, `/history/{user_id}` và `/usage/{user_id}`.

Blueprint tạo cả Web Service và Render Key Value. `REDIS_URL` được nối tự động,
vì vậy history, rate limit và token guard dùng chung giữa các instance.

Render Key Value free dùng `persistenceMode: off`. Dữ liệu quota có thể reset
nếu dịch vụ Redis được tạo lại. Muốn guardrail 100.000 token bền vững tuyệt đối,
hãy dùng Key Value plan có persistence; OpenAI billing alerts chỉ nên là lớp cảnh báo bổ sung.
