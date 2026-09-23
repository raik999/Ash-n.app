from pathlib import Path
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    host: str = "localhost"
    port: int = 8000
    debug: bool = True

    db_host: str = "localhost"
    db_port: int = 5432
    db_username: str = "postgres"
    db_password: str = ""
    database: str = "ashun_db"

    database_url: str | None = None

    jwt_secret: str = "cambia-esta-clave-en-produccion-por-favor"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7

    frontend_url: str = "*"

    upload_dir: Path = BACKEND_DIR / "uploads"
    max_upload_size: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url

        user = quote_plus(self.db_username)
        password = quote_plus(self.db_password)

        credentials = f"{user}:{password}" if password else user

        return f"postgresql+psycopg://{credentials}@{self.db_host}:{self.db_port}/{self.database}"

    @property
    def admin_url(self) -> str:
        user = quote_plus(self.db_username)
        password = quote_plus(self.db_password)
        credentials = f"{user}:{password}" if password else user
        return f"postgresql+psycopg://{credentials}@{self.db_host}:{self.db_port}/postgres"

    @property
    def cors_origins(self) -> list[str]:
        if self.frontend_url.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]


settings = Settings()

settings.upload_dir.mkdir(parents=True, exist_ok=True)
