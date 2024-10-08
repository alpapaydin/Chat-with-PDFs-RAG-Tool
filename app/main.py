from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.endpoints import pdf, chat, auth
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.database import get_engine
from app.db.models import Base
import os

app = FastAPI(title=get_settings().PROJECT_NAME, version=get_settings().PROJECT_VERSION)

setup_logging()

# Create database tables
Base.metadata.create_all(bind=get_engine())

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API routes
app.include_router(pdf.router, prefix="/v1", tags=["pdf"])
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(static_dir, "favicon.ico"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)