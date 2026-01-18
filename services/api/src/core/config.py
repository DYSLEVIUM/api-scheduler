from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )

    database_url: str
    dev: int = 0
    debug: int = 1
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "api-scheduler-queue"

    log_level: str = "INFO"
    loki_url: str | None = None

    otel_endpoint: str | None = None
    otel_service_name: str = "api-scheduler"


settings = Settings()
