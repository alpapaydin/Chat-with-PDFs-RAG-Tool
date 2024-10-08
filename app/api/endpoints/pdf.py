from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import Optional
from app.services.pdf_processor import process_pdf
from app.core.logging import logger

router = APIRouter()

@router.post("/pdf")
async def upload_pdfs(
    request: Request,
    file: UploadFile = File(...),
    chat_id: Optional[str] = Form(None)
):
    form = await request.form()
    logger.info(f"Received file: {file}")

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        pdf_id, chat_id = await process_pdf(file, chat_id)
        logger.info(f"PDF processed successfully. ID: {pdf_id}, Chat ID: {chat_id}")
        return {"pdf_id": pdf_id, "chat_id": chat_id}
    except HTTPException as he:
        logger.error(f"Error processing PDF: {str(he)}", exc_info=True)
        raise he
    except Exception as e:
        logger.error(f"Unexpected error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error processing PDF: {str(e)}")