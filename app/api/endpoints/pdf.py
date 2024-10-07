from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_processor import process_pdf
from app.core.logging import logger

router = APIRouter()

@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    logger.info(f"Receiving PDF upload: {file.filename}")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    try:
        pdf_id = await process_pdf(file)
        logger.info(f"PDF processed successfully. ID: {pdf_id}")
        return {"pdf_id": pdf_id}
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")