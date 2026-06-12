"""Vietnamese to Korean honorific translator for tourism situations."""
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.rate_limiter import rate_limiter
from app.storage import history_store
from app.token_guard import token_guard
from app.translator import SITUATIONS, translate


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(message)s",
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
is_ready = False
request_count = 0
error_count = 0


class TranslationRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=80)
    text: str = Field(..., min_length=1, max_length=500)
    situation: str = Field(
        default="general",
        description=f"Tourism context: {', '.join(SITUATIONS)}",
    )


class TranslationResponse(BaseModel):
    translation: str
    romanization: str
    honorific_level: str
    explanation: str
    cultural_note: str
    situation: str
    provider: str
    model: str
    token_usage: dict
    created_at: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global is_ready
    if settings.require_openai and not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    if settings.require_redis and (
        history_store.backend != "redis"
        or token_guard.backend != "redis"
        or rate_limiter.backend != "redis"
    ):
        raise RuntimeError("Redis is required but unavailable")
    if settings.environment == "production" and settings.agent_api_key == "dev-translation-key":
        raise RuntimeError("AGENT_API_KEY must be changed in production")

    logger.info(json.dumps({"event": "startup", "storage": history_store.backend}))
    is_ready = True
    yield
    is_ready = False
    history_store.close()
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title="Korean Travel Honorific Translator",
    description="Translate Vietnamese into polite Korean for tourism situations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    global request_count, error_count
    started = time.time()
    request_count += 1
    try:
        response: Response = await call_next(request)
    except Exception:
        error_count += 1
        raise

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round((time.time() - started) * 1000, 1),
    }))
    return response


@app.get("/")
def root():
    return {
        "name": "Korean Travel Honorific Translator",
        "description": "Vietnamese to polite Korean translation with explanations",
        "situations": SITUATIONS,
        "docs": "/docs",
    }


@app.post("/translate", response_model=TranslationResponse)
def translate_text(
    body: TranslationRequest,
    api_key: str = Depends(verify_api_key),
):
    if body.situation not in SITUATIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown situation. Choose one of: {', '.join(SITUATIONS)}",
        )

    rate_limiter.check(f"{api_key[:8]}:{body.user_id}")
    reservation = token_guard.reserve(body.user_id, body.text)
    try:
        result, provider_usage = translate(body.text, body.situation)
    except Exception as exc:
        token_guard.release(reservation)
        logger.exception(json.dumps({"event": "translation_failed"}))
        raise HTTPException(status_code=502, detail="Translation provider failed") from exc

    token_usage = token_guard.commit(
        reservation,
        provider_usage["input_tokens"],
        provider_usage["output_tokens"],
    )
    created_at = datetime.now(timezone.utc).isoformat()

    record = {
        "input": body.text,
        **result,
        "provider": provider_usage["provider"],
        "model": settings.openai_model if provider_usage["provider"] == "openai" else "local-phrasebook",
        "token_usage": token_usage,
        "created_at": created_at,
    }
    history_store.append(body.user_id, record)
    return record


@app.get("/history/{user_id}")
def get_history(user_id: str, _api_key: str = Depends(verify_api_key)):
    return {
        "user_id": user_id,
        "storage": history_store.backend,
        "translations": history_store.get(user_id),
    }


@app.delete("/history/{user_id}")
def delete_history(user_id: str, _api_key: str = Depends(verify_api_key)):
    history_store.delete(user_id)
    return {"deleted": True, "user_id": user_id}


@app.get("/usage/{user_id}")
def get_token_usage(user_id: str, _api_key: str = Depends(verify_api_key)):
    return token_guard.usage(user_id)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "requests": request_count,
        "errors": error_count,
        "translation_provider": "openai" if settings.openai_api_key else "phrasebook",
        "model": settings.openai_model,
    }


@app.get("/ready")
def ready():
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service is not ready")
    if settings.require_redis and (
        not history_store.ping() or not token_guard.ping()
    ):
        raise HTTPException(status_code=503, detail="Redis is unavailable")
    return {
        "ready": True,
        "storage": history_store.backend,
        "rate_limiter": rate_limiter.backend,
        "token_guard": token_guard.backend,
    }
