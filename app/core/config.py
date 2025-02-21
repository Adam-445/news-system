from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    database_url: str
    redis_url: str

    jwt_secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    api_key: str
    environment: str = "development"
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = SettingsConfigDict(env_file=".env.docker", extra="ignore")


settings = Settings()
