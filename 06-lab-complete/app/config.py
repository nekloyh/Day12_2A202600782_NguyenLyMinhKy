"""Environment-based application configuration."""
import os
from dataclasses import dataclass, field


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    environment: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )
    agent_api_key: str = field(
        default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-translation-key")
    )
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )
    max_output_tokens: int = field(
        default_factory=lambda: int(os.getenv("MAX_OUTPUT_TOKENS", "600"))
    )
    prompt_token_reserve: int = field(
        default_factory=lambda: int(os.getenv("PROMPT_TOKEN_RESERVE", "500"))
    )
    user_monthly_token_limit: int = field(
        default_factory=lambda: int(os.getenv("USER_MONTHLY_TOKEN_LIMIT", "100000"))
    )
    global_monthly_token_limit: int = field(
        default_factory=lambda: int(os.getenv("MONTHLY_TOKEN_LIMIT", "100000"))
    )
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    history_limit: int = field(
        default_factory=lambda: int(os.getenv("HISTORY_LIMIT", "20"))
    )
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    allowed_origins: list[str] = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )
    require_openai: bool = field(
        default_factory=lambda: env_bool("REQUIRE_OPENAI", False)
    )
    require_redis: bool = field(
        default_factory=lambda: env_bool("REQUIRE_REDIS", False)
    )


settings = Settings()
