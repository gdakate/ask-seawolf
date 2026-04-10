"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://sbu_user:sbu_pass@localhost:5432/sbu_assistant"
    database_url_sync: str = "postgresql://sbu_user:sbu_pass@localhost:5432/sbu_assistant"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    admin_default_email: str = "admin@stonybrook.edu"
    admin_default_password: str = "admin123"

    # AI Provider
    ai_provider: str = "mock"  # mock, openai, bedrock
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    # Storage
    storage_backend: str = "local"  # local, s3
    local_storage_path: str = "/data/storage"
    s3_bucket: str = "sbu-assistant-docs"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = ""

    # App
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Embedding dimensions
    embedding_dimensions: int = 384

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
