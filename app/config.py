import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    ALGORITHM: str = "HS256"

    model_config = {
        "env_file": ".env",
    }


settings = Settings()
