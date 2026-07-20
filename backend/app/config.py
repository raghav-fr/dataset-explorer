from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free", alias="OPENROUTER_MODEL")
    openrouter_embedding_model: str = Field(
        default="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        alias="OPENROUTER_EMBEDDING_MODEL",
    )

    max_upload_mb: int = Field(default=50, alias="MAX_UPLOAD_MB")

    # Local filesystem storage (used as fallback when Redis is not configured)
    storage_dir: str = Field(default="/tmp/datasets", alias="STORAGE_DIR")
    reports_dir: str = Field(default="/tmp/reports", alias="REPORTS_DIR")

    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000", alias="CORS_ORIGINS"
    )

    # Upstash Redis (serverless-friendly, HTTP-based)
    upstash_redis_rest_url: str = Field(default="", alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: str = Field(default="", alias="UPSTASH_REDIS_REST_TOKEN")

    # Dataset TTL in Redis (seconds). Default: 24 hours.
    dataset_ttl_seconds: int = Field(default=86400, alias="DATASET_TTL_SECONDS")

    class Config:
        env_file = ".env"
        populate_by_name = True
        extra = "ignore"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_redis(self) -> bool:
        """Return True if Upstash Redis credentials are configured."""
        return bool(self.upstash_redis_rest_url and self.upstash_redis_rest_token)


settings = Settings()

# Only create local dirs when running in non-serverless mode (i.e. not on Vercel).
# On Vercel, /tmp is ephemeral but writable; we create dirs lazily in dataset_store.
if not os.environ.get("VERCEL"):
    os.makedirs(settings.storage_dir, exist_ok=True)
    os.makedirs(settings.reports_dir, exist_ok=True)
