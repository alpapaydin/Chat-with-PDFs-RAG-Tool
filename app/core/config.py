import os
from pydantic_settings import BaseSettings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings
from functools import lru_cache

class AppSettings(BaseSettings):
    PROJECT_NAME: str = "PDF Chatter"
    PROJECT_VERSION: str = "1.0.0"
    GOOGLE_API_KEY: str
    SQLALCHEMY_DATABASE_URL: str
    FILE_SIZE_MB: int = 3
    CONTEXT_LENGTH: int = 5
    SECRET_KEY: str = "top-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_llm_settings()

    def _setup_llm_settings(self):
        os.environ["GOOGLE_API_KEY"] = self.GOOGLE_API_KEY
        Settings.llm = Gemini()
        Settings.embed_model = GeminiEmbedding()

_settings = None

@lru_cache()
def get_settings():
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings

def override_settings(new_settings: AppSettings):
    global _settings
    _settings = new_settings
    get_settings.cache_clear()

settings = get_settings()