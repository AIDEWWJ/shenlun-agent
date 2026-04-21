from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "申论 Agent"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "shenlun_agent"
    database_url: str | None = None

    default_model_provider: str = "openai"
    default_model_name: str = "gpt-4.1-mini"
    default_temperature: float = 0.3

    email_code_expire_minutes: int = 10

    jwt_secret_key: str = "change-this-in-dev"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
