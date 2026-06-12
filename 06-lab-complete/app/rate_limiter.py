"""Redis-backed sliding-window rate limiter with local fallback."""
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException

from app.config import settings


class RateLimiter:
    def __init__(self):
        self.redis = None
        self.windows: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()
        if settings.redis_url:
            try:
                import redis

                client = redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                self.redis = client
            except Exception:
                self.redis = None

    @property
    def backend(self) -> str:
        return "redis" if self.redis else "memory"

    def check(self, identity: str) -> None:
        now = time.time()
        if self.redis:
            key = f"rate-limit:{identity}"
            script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window_start = now - 60
            local limit = tonumber(ARGV[2])
            redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
            local count = redis.call('ZCARD', key)
            if count >= limit then
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                return {0, math.ceil(60 - (now - tonumber(oldest[2])))}
            end
            redis.call('ZADD', key, now, ARGV[3])
            redis.call('EXPIRE', key, 60)
            return {1, limit - count - 1}
            """
            member = f"{now:.9f}:{uuid.uuid4().hex}"
            allowed, value = self.redis.eval(
                script,
                1,
                key,
                now,
                settings.rate_limit_per_minute,
                member,
            )
            if int(allowed) == 0:
                self._raise_limit(max(1, int(value)))
            return

        with self.lock:
            window = self.windows[identity]
            while window and window[0] <= now - 60:
                window.popleft()
            if len(window) >= settings.rate_limit_per_minute:
                retry_after = max(1, int(window[0] + 60 - now) + 1)
                self._raise_limit(retry_after)
            window.append(now)

    @staticmethod
    def _raise_limit(retry_after: int) -> None:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


rate_limiter = RateLimiter()
