# Deployment Information

## Project

Vietnamese-Korean Travel Honorific Translator

## Public URL

`https://YOUR-RENDER-SERVICE.onrender.com`

## Platform

Render

## Test Commands

```bash
curl https://YOUR-RENDER-SERVICE.onrender.com/health
curl https://YOUR-RENDER-SERVICE.onrender.com/ready

curl -X POST https://YOUR-RENDER-SERVICE.onrender.com/translate \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","text":"Cho tôi xem thực đơn","situation":"restaurant"}'

curl https://YOUR-RENDER-SERVICE.onrender.com/usage/demo \
  -H "X-API-Key: YOUR_KEY"
```

## Environment Variables

- `AGENT_API_KEY`
- `OPENAI_API_KEY` (secret)
- `OPENAI_MODEL=gpt-4o-mini`
- `ENVIRONMENT=production`
- `REQUIRE_OPENAI=true`
- `REQUIRE_REDIS=true`
- `REDIS_URL` (generated from Render Key Value)
- `RATE_LIMIT_PER_MINUTE=10`
- `MONTHLY_TOKEN_LIMIT=100000`
- `USER_MONTHLY_TOKEN_LIMIT=100000`
- `MAX_OUTPUT_TOKENS=600`
- `HISTORY_LIMIT=20`

## Evidence

- Deployment dashboard: `screenshots/render-dashboard.png`
- Health check: `screenshots/health.png`
- Translation result: `screenshots/translation.png`
