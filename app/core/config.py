import os
from pydantic_settings import BaseSettings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings

class AppSettings(BaseSettings):
    PROJECT_NAME: str = "PDF Chatter"
    PROJECT_VERSION: str = "1.0.0"
    GOOGLE_API_KEY: str
    SQLALCHEMY_DATABASE_URL: str
    FILE_SIZE_MB: int = 3  # Maximum allowed file uploads in MB
    CONTEXT_LENGTH: int = 5  # Last n messages to append to context
    SECRET_KEY: str = "top-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"  # Specify the .env file

settings = AppSettings()

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
# Set LLM and embedding models
Settings.llm = Gemini()
Settings.embed_model = GeminiEmbedding()
