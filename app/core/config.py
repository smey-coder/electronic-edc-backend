from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Electronic-EDC API"
    APP_ENV: str = "development"

    # Database Settings (MySQL + PyMySQL)
    DATABASE_URL: str

    # Security & JWT Settings
    SECRET_KEY: str = "super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# បង្កើត Instance សម្រាប់ហៅយកទៅប្រើប្រាស់ក្នុងទូទាំង Project
settings = Settings()