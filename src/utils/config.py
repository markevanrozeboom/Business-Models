"""Configuration management using Pydantic settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Anthropic API Configuration
    anthropic_api_key: str
    default_model: str = "claude-sonnet-4-5-20250929"
    default_max_tokens: int = 4096
    default_temperature: float = 0.7

    # System Configuration
    log_level: str = "INFO"
    environment: str = "development"

    # Workflow Configuration
    completeness_threshold: float = 80.0
    confidence_threshold: float = 70.0
    enable_human_review: bool = True

    # Output Configuration
    output_dir: str = "./outputs"
    reports_dir: str = "./reports"
    models_dir: str = "./models"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Agent Configuration
    max_retries: int = 3
    retry_delay: float = 2.0
    agent_timeout: int = 300  # seconds


# Global settings instance
settings = Settings()
