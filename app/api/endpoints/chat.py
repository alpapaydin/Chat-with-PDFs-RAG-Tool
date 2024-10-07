from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.models.schemas import ChatRequest
from app.services.llm_service import chat_with_llm, stream_long_response
from app.core.logging import logger

router = APIRouter()

@router.post("/chat/{pdf_id}")
async def chat_with_pdf(pdf_id: str, chat_request: ChatRequest):
    logger.info(f"Received chat request for PDF ID: {pdf_id}")
    try:
        full_response = await chat_with_llm(pdf_id, chat_request.message)
        return StreamingResponse(stream_long_response(full_response), media_type="text/plain")
    except KeyError:
        raise HTTPException(status_code=404, detail="PDF not found")
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing chat request")