from os import getenv

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(getenv("ENV_FILE", "../../.env"))


class Settings(BaseSettings):
    debug: bool
    bot_token: str
    app_url: str


settings = Settings()
