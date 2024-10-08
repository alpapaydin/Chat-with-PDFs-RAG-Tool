from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from functools import lru_cache

Base = declarative_base()

@lru_cache()
def get_engine():
    url = get_settings().SQLALCHEMY_DATABASE_URL
    print(f"Creating engine with URL: {url}")
    return create_engine(url)

@lru_cache()
def get_session_local():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    engine = get_engine()
    print(f"Initializing database with URL: {engine.url}")
    Base.metadata.create_all(bind=engine)