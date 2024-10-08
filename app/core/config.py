import os
from pydantic_settings import BaseSettings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings

class AppSettings(BaseSettings):
    PROJECT_NAME: str = "PDF Chat API"
    PROJECT_VERSION: str = "1.0.0"
    GOOGLE_API_KEY: str

    class Config:
        env_file = ".env"

settings = AppSettings()
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
Settings.llm=Gemini()
Settings.embed_model=GeminiEmbedding()