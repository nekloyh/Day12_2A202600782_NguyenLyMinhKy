"""Monthly per-user token guard with Redis-backed atomic reservations."""
import math
import threading
import time
from dataclasses import dataclass

from fastapi import HTTPException

from app.config import settings


@dataclass(frozen=True)
class TokenReservation:
    user_id: str
    user_key: str
    global_key: str
    reserved_tokens: int


class TokenGuard:
    def __init__(self):
        self.redis = None
        self.memory: dict[str, int] = {}
        self.lock = threading.Lock()
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

    def ping(self) -> bool:
        if not self.redis:
            return False
        try:
            return bool(self.redis.ping())
        except Exception:
            return False

    @staticmethod
    def _key(user_id: str) -> str:
        return f"token-usage:user:{user_id}:{time.strftime('%Y-%m')}"

    @staticmethod
    def _global_key() -> str:
        return f"token-usage:global:{time.strftime('%Y-%m')}"

    @staticmethod
    def _estimated_input_tokens(text: str) -> int:
        # Conservative estimate for Vietnamese plus the fixed translation prompt.
        return math.ceil(len(text) / 2) + settings.prompt_token_reserve

    def reserve(self, user_id: str, text: str) -> TokenReservation:
        amount = self._estimated_input_tokens(text) + settings.max_output_tokens
        user_key = self._key(user_id)
        global_key = self._global_key()

        if self.redis:
            script = """
            local user_current = tonumber(redis.call('GET', KEYS[1]) or '0')
            local global_current = tonumber(redis.call('GET', KEYS[2]) or '0')
            local amount = tonumber(ARGV[1])
            local user_limit = tonumber(ARGV[2])
            local global_limit = tonumber(ARGV[3])
            if user_current + amount > user_limit or global_current + amount > global_limit then
                return -1
            end
            redis.call('INCRBY', KEYS[1], amount)
            local updated = redis.call('INCRBY', KEYS[2], amount)
            redis.call('EXPIRE', KEYS[1], 2764800)
            redis.call('EXPIRE', KEYS[2], 2764800)
            return updated
            """
            used = int(self.redis.eval(
                script,
                2,
                user_key,
                global_key,
                amount,
                settings.user_monthly_token_limit,
                settings.global_monthly_token_limit,
            ))
        else:
            with self.lock:
                user_current = self.memory.get(user_key, 0)
                global_current = self.memory.get(global_key, 0)
                if (
                    user_current + amount > settings.user_monthly_token_limit
                    or global_current + amount > settings.global_monthly_token_limit
                ):
                    used = -1
                else:
                    self.memory[user_key] = user_current + amount
                    used = global_current + amount
                    self.memory[global_key] = used

        if used < 0:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Monthly token limit exceeded",
                    "global_limit": settings.global_monthly_token_limit,
                    "user_limit": settings.user_monthly_token_limit,
                    "resets": "first day of next month UTC",
                },
            )
        return TokenReservation(
            user_id=user_id,
            user_key=user_key,
            global_key=global_key,
            reserved_tokens=amount,
        )

    def commit(
        self,
        reservation: TokenReservation,
        input_tokens: int,
        output_tokens: int,
    ) -> dict:
        actual = input_tokens + output_tokens
        adjustment = actual - reservation.reserved_tokens

        if self.redis:
            user_used = int(self.redis.incrby(reservation.user_key, adjustment))
            global_used = int(self.redis.incrby(reservation.global_key, adjustment))
        else:
            with self.lock:
                user_used = max(
                    0,
                    self.memory.get(reservation.user_key, 0) + adjustment,
                )
                global_used = max(
                    0,
                    self.memory.get(reservation.global_key, 0) + adjustment,
                )
                self.memory[reservation.user_key] = user_used
                self.memory[reservation.global_key] = global_used

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": actual,
            "user_monthly_used_tokens": user_used,
            "user_monthly_remaining_tokens": max(
                0,
                settings.user_monthly_token_limit - user_used,
            ),
            "global_monthly_used_tokens": global_used,
            "global_monthly_limit_tokens": settings.global_monthly_token_limit,
            "global_monthly_remaining_tokens": max(
                0,
                settings.global_monthly_token_limit - global_used,
            ),
        }

    def release(self, reservation: TokenReservation) -> None:
        if self.redis:
            self.redis.incrby(reservation.user_key, -reservation.reserved_tokens)
            self.redis.incrby(reservation.global_key, -reservation.reserved_tokens)
        else:
            with self.lock:
                for key in (reservation.user_key, reservation.global_key):
                    current = self.memory.get(key, 0)
                    self.memory[key] = max(
                        0,
                        current - reservation.reserved_tokens,
                    )

    def usage(self, user_id: str) -> dict:
        user_key = self._key(user_id)
        global_key = self._global_key()
        if self.redis:
            user_used = int(self.redis.get(user_key) or 0)
            global_used = int(self.redis.get(global_key) or 0)
        else:
            with self.lock:
                user_used = self.memory.get(user_key, 0)
                global_used = self.memory.get(global_key, 0)
        return {
            "user_id": user_id,
            "month": time.strftime("%Y-%m"),
            "user_used_tokens": user_used,
            "user_limit_tokens": settings.user_monthly_token_limit,
            "global_used_tokens": global_used,
            "global_limit_tokens": settings.global_monthly_token_limit,
            "global_remaining_tokens": max(
                0,
                settings.global_monthly_token_limit - global_used,
            ),
        }


token_guard = TokenGuard()
