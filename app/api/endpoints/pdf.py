from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.services.pdf_processor import process_pdf
from app.core.logging import logger
from app.core.config import get_settings
from app.auth.auth import get_current_user
from app.db.database import get_db
from app.db.models import User, Chat

router = APIRouter()

# Set the maximum file size (in bytes)
MAX_FILE_SIZE = get_settings().FILE_SIZE_MB * 1024 * 1024

@router.post("/pdf")
async def upload_pdfs(
    request: Request,
    file: UploadFile = File(...),
    chat_id: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if chat_id:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()  # Implement this function to query the database
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
    # Check file size
    file_size = await file.read()
    await file.seek(0)  # Reset file pointer to the beginning
    if len(file_size) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File size exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024):.2f} MB")
    logger.info(f"Received file: {file.filename}")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    try:
        pdf_id, chat_id = await process_pdf(file, chat_id, current_user)
        logger.info(f"PDF processed successfully. ID: {pdf_id}, Chat ID: {chat_id}")
        return {"pdf_id": pdf_id, "chat_id": chat_id}
    except HTTPException as he:
        logger.error(f"Error processing PDF: {str(he)}", exc_info=True)
        raise he
    except Exception as e:
        logger.error(f"Unexpected error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error processing PDF: {str(e)}")