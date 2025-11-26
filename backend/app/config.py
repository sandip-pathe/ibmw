"""
Application configuration using Pydantic Settings.
Loads from environment variables with validation.
"""
from functools import lru_cache
import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # RSS Scraper Feature Flag
    enable_rss_scraper: bool = False
    """Application settings with environment variable loading."""

    def __getattr__(self, name):
        return getattr(super(), name)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    app_name: str = "Fintech Compliance Engine"
    api_version: str = "v1"


    # Database
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", ""),
        description="Neon Postgres connection string (asyncpg or psycopg)"
    )
    neon_data_api_url: str = Field(..., description="Neon Data API URL")
    neon_api_key: str = Field(..., description="Neon API Key")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Stack Auth
    stack_jwks_url: str = Field(..., description="Stack JWKS URL")

    # GitHub App (for webhooks)
    github_app_id: int = Field(..., description="GitHub App ID")
    github_private_key_path: Path = Field(..., description="Path to GitHub App private key")
    github_webhook_secret: str = Field(..., description="GitHub webhook secret")
    github_api_url: str = "https://api.github.com"

    # GitHub OAuth App (for user repo access)
    github_oauth_client_id: str = Field(..., description="GitHub OAuth App Client ID")
    github_oauth_client_secret: str = Field(..., description="GitHub OAuth App Client Secret")
    github_oauth_redirect_uri: str = Field(..., description="GitHub OAuth App Redirect URI")

    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_deployment_embedding: str = "text-embedding-3-small"
    azure_openai_deployment_llm: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-02-15-preview"

    # OpenAI (fallback)
    openai_api_key: Optional[str] = None

    # Embeddings provider
    embeddings_provider: Literal["azure", "openai"] = "azure"
    embedding_dimension: int = 1536
    embedding_batch_size: int = 100

    # LLM provider
    llm_provider: Literal["azure", "openai"] = "azure"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000

    # Azure Blob Storage
    blob_enabled: bool = True
    blob_connection_string: Optional[str] = None
    blob_container_name: str = "compliance-data"

    # Azure Document Intelligence
    enable_doc_intelligence: bool = False
    azure_document_intelligence_endpoint: Optional[str] = None
    azure_document_intelligence_key: Optional[str] = None

    # Feature flags
    enable_github_checks: bool = False
    enable_demo_seed: bool = False
    enable_metrics: bool = False

    # Security
    admin_api_key: str = Field(..., description="Admin API key for protected endpoints")

    # Storage
    local_storage_path: Path = Path("./storage")
    temp_clone_path: Path = Path("./storage/temp")
    max_file_size_mb: int = 10

    # Code parsing
    supported_languages: list[str] = Field(
        default=[
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "rust",
            "cpp",
            "c",
        ]
    )
    max_chunk_tokens: int = 1500
    min_chunk_tokens: int = 50

    # Job queue
    queue_name: str = "compliance:jobs"
    job_timeout: int = 3600  # 1 hour
    max_job_retries: int = 3

    # Rate limiting
    rate_limit_embeddings: int = 3500  # per minute
    rate_limit_llm: int = 500  # per minute

    # Cache TTL (seconds)
    cache_ttl_embeddings: int = 86400  # 24 hours
    cache_ttl_nl_summary: int = 86400  # 24 hours

    # Analysis
    top_k_similar_chunks: int = 10
    similarity_threshold: float = 0.7

    # Monitoring
    sentry_dsn: Optional[str] = None

    @field_validator("github_private_key_path")
    @classmethod
    def validate_private_key_exists(cls, v: Path) -> Path:
        """Validate that GitHub private key file exists."""
        if not v.exists():
            raise ValueError(f"GitHub private key not found at: {v}")
        return v

    @field_validator("local_storage_path", "temp_clone_path")
    @classmethod
    def create_storage_dirs(cls, v: Path) -> Path:
        """Create storage directories if they don't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]
