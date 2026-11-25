# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     # App Settings
#     APP_NAME: str = "Electronic-EDC API"
#     APP_ENV: str = "development"

#     # Database Settings (MySQL + PyMySQL)
#     DATABASE_URL: str

#     # Security & JWT Settings
#     SECRET_KEY: str = "super_secret_key_change_in_production"
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

#     # Pydantic Settings Configuration
#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         extra="ignore"
#     )


# # បង្កើត Instance សម្រាប់ហៅយកទៅប្រើប្រាស់ក្នុងទូទាំង Project
# settings = Settings()


from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):

    # MySQL Database
    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    @property
    def DATABASE_URL(self):
        return URL.create(
            drivername="mysql+pymysql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )


settings = Settings()
