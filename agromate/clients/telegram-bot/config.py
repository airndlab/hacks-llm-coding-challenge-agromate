from os import getenv

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(getenv("ENV_FILE", ".env"))


class Settings(BaseSettings):
    debug: bool
    bot_token: str
    app_url: str
    bot_configs_path: str   # Путь к конфигурационным файлам по умолчанию
    ocr_api_key: str  # API ключ для OpenAI Vision
    audio_api_key: str = ""  # API ключ для OpenAI Audio API, если пусто - используем ocr_api_key


settings = Settings()
# Если audio_api_key не указан, используем тот же ключ, что и для OCR
if not settings.audio_api_key:
    settings.audio_api_key = settings.ocr_api_key
