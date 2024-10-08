from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.endpoints import pdf, chat
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import engine
from app.db.models import Base
import os

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API routes
app.include_router(pdf.router, prefix="/v1", tags=["pdf"])
app.include_router(chat.router, prefix="/v1", tags=["chat"])

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)