from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "E-Commerce Order Microservice"
    SERVICE_NAME: str = "order-service"
    PORT: int = 8003
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # MySQL Database Settings
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "fastapi_order_db"

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    # OpenTelemetry & Jaeger
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "order-service"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318/v1/traces"
    OTEL_EXPORTER_OTLP_PROTOCOL: str = "http/protobuf"
    OTEL_SAMPLING_RATIO: float = 1.0
    LOG_FORMAT: str = "json"

    # Inter-Service Communication Endpoints
    PRODUCT_SERVICE_URL: str = "http://localhost:8002"
    INVENTORY_SERVICE_URL: str = "http://localhost:8005"
    PAYMENT_SERVICE_URL: str = "http://localhost:8004"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8006"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def async_database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    @property
    def fallback_sqlite_url(self) -> str:
        return "sqlite+aiosqlite:///fastapi_order_db.sqlite"


settings = Settings()

