from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PDF Chat API"
    PROJECT_VERSION: str = "1.0.0"
    GOOGLE_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()

import os

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY