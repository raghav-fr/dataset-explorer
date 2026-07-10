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

    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection_prefix: str = Field(
        default="dataset_", alias="QDRANT_COLLECTION_PREFIX"
    )

    max_upload_mb: int = Field(default=200, alias="MAX_UPLOAD_MB")
    storage_dir: str = Field(default="app/storage/datasets", alias="STORAGE_DIR")
    reports_dir: str = Field(default="app/storage/reports", alias="REPORTS_DIR")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000", alias="CORS_ORIGINS"
    )

    class Config:
        env_file = ".env"
        populate_by_name = True
        extra = "ignore"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

os.makedirs(settings.storage_dir, exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)
