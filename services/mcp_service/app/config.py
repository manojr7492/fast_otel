import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Service Configuration
    PROJECT_NAME: str = "MCP LangChain Microservice"
    SERVICE_NAME: str = "mcp-service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8007
    HOST: str = "0.0.0.0"

    # Microservices Endpoints
    CATALOG_SERVICE_URL: str = "http://localhost:8002"
    INVENTORY_SERVICE_URL: str = "http://localhost:8005"
    ORDER_SERVICE_URL: str = "http://localhost:8003"

    # Optional LLM Key
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # OpenTelemetry Tracing
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "mcp-service"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318/v1/traces"
    OTEL_SAMPLING_RATIO: float = 1.0


settings = Settings()

