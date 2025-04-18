from os import getenv

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(getenv("ENV_FILE", ".env"))


class Settings(BaseSettings):
    debug: bool
    bot_token: str
    app_url: str
    bot_configs_path: str   # Путь к конфигурационным файлам по умолчанию
    ocr_api_key: str  # API ключ для OpenAI


settings = Settings()
