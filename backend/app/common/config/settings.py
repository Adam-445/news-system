from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 1
    api_key: str
    environment: str = "production"
    log_level: str = "INFO"
    log_format: str = "json"

    initial_admin_username: str = "admin_user"
    initial_admin_email: str = "admin@email.com"
    initial_admin_password: str = "TestPass123!"

    allow_db_seed_in_prod: str = "False"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()
