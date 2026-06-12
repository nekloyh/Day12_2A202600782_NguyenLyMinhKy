"""Redis-backed translation history with local fallback."""
import json

from app.config import settings


class HistoryStore:
    def __init__(self):
        self.redis = None
        self.memory: dict[str, list[dict]] = {}
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
        return f"translation-history:{user_id}"

    def append(self, user_id: str, record: dict) -> None:
        if self.redis:
            key = self._key(user_id)
            self.redis.lpush(key, json.dumps(record, ensure_ascii=False))
            self.redis.ltrim(key, 0, settings.history_limit - 1)
            self.redis.expire(key, 30 * 24 * 3600)
            return
        history = self.memory.setdefault(user_id, [])
        history.insert(0, record)
        del history[settings.history_limit:]

    def get(self, user_id: str) -> list[dict]:
        if self.redis:
            return [
                json.loads(item)
                for item in self.redis.lrange(self._key(user_id), 0, -1)
            ]
        return self.memory.get(user_id, [])

    def delete(self, user_id: str) -> None:
        if self.redis:
            self.redis.delete(self._key(user_id))
        self.memory.pop(user_id, None)

    def close(self) -> None:
        if self.redis:
            self.redis.close()


history_store = HistoryStore()
