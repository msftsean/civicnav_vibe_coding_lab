"""Configuration module for CivicNav.

Uses pydantic-settings to bind environment variables to typed settings.
All Azure services use DefaultAzureCredential for authentication.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Azure OpenAI Configuration
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # Azure AI Search Configuration
    azure_search_endpoint: str = ""
    azure_search_index: str = "civicnav-index"

    # Application Configuration
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Performance Configuration
    search_top_k: int = 5
    embedding_dimensions: int = 1536

    @property
    def is_configured(self) -> bool:
        """Check if required Azure services are configured."""
        return bool(self.azure_openai_endpoint and self.azure_search_endpoint)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
