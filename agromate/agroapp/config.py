from os import getenv

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(getenv("ENV_FILE", ".env"))

class Settings(BaseSettings):
    debug: bool
    db_url: str
    bot_url: str
    llm_api_base_url: str
    llm_api_key: str
    configs_path: str
    dicts_path: str
    report_template_path: str
    google_credentials_path: str
    google_drive_folder_url: str
    google_drive_folder_dumped: bool
    team_name: str

settings = Settings()
