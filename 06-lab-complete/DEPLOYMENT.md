# Deployment Information

## Project

Vietnamese-Korean Travel Honorific Translator

## Public URL

https://vietnamese-korean-travel-translator.onrender.com

## Platform

Render

## Test Commands

```bash
curl https://vietnamese-korean-travel-translator.onrender.com/health
curl https://vietnamese-korean-travel-translator.onrender.com/ready

curl -X POST https://vietnamese-korean-travel-translator.onrender.com/translate \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","text":"Cho tôi xem thực đơn","situation":"restaurant"}'

curl https://vietnamese-korean-travel-translator.onrender.com/usage/demo \
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

## Deployment Result

- Render service status: Live
- Readiness endpoint: `200 OK`
- Translation provider: OpenAI
- Model: `gpt-4o-mini`
- Token usage is tracked in Redis.

## Evidence

- [Production readiness and translation result](screenshot/ex6-deployment-redacted.png)
