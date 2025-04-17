from os import getenv

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(getenv("ENV_FILE", "../../.env"))


class Settings(BaseSettings):
    debug: bool
    db_url: str
    bot_url: str
    dicts_path: str


settings = Settings()
