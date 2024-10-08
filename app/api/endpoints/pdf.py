from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from typing import Optional
from app.services.pdf_processor import process_pdf
from app.core.logging import logger
from app.core.config import settings
from app.auth.auth import get_current_user
from app.db.models import User

router = APIRouter()

# Set the maximum file size (in bytes)
MAX_FILE_SIZE = settings.FILE_SIZE_MB * 1024 * 1024

@router.post("/pdf")
async def upload_pdfs(
    request: Request,
    file: UploadFile = File(...),
    chat_id: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user)
):
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