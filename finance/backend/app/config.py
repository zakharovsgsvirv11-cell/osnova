from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/finance.db"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Google Sheets
    google_service_account_key: str = ""
    google_sheet_id: str = ""
    google_sheet_range: str = "Sheet1!A:Z"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:80"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
