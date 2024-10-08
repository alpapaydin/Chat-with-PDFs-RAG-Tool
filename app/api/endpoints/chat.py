from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.models.schemas import ChatRequest
from app.services.llm_service import chat_with_llm, stream_long_response
from app.core.logging import logger
from app.db.database import get_db
from app.db.models import Chat, PDF, Message
from typing import List
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class ChatInfo(BaseModel):
    id: str

class PDFInfo(BaseModel):
    id: str
    filename: str

class MessageInfo(BaseModel):
    content: str
    is_user: bool
    timestamp: datetime

@router.get("/chats", response_model=List[ChatInfo])
async def get_chats():
    db = next(get_db())
    chats = db.query(Chat).all()
    return [ChatInfo(id=chat.id) for chat in chats]

@router.get("/chat/{chat_id}/pdfs", response_model=List[PDFInfo])
async def get_chat_pdfs(chat_id: str):
    db = next(get_db())
    pdfs = db.query(PDF).filter(PDF.chat_id == chat_id).all()
    if not pdfs:
        raise HTTPException(status_code=404, detail="No PDFs found for this chat")
    return [PDFInfo(id=pdf.id, filename=pdf.filename) for pdf in pdfs]

@router.get("/chat/{chat_id}/messages", response_model=List[MessageInfo])
async def get_chat_messages(chat_id: str):
    db = next(get_db())
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
    return [MessageInfo(content=msg.content, is_user=msg.is_user, timestamp=msg.timestamp) for msg in messages]

@router.post("/chat/{chat_id}")
async def chat_with_pdfs(chat_id: str, chat_request: ChatRequest):
    logger.info(f"Received chat request for Chat ID: {chat_id}")
    try:
        db = next(get_db())
        
        # Save user message
        user_message = Message(id=str(uuid.uuid4()), chat_id=chat_id, content=chat_request.message, is_user=True)
        db.add(user_message)
        db.commit()

        full_response = await chat_with_llm(chat_id, chat_request.message)
        
        # Save bot response
        bot_message = Message(id=str(uuid.uuid4()), chat_id=chat_id, content=full_response, is_user=False)
        db.add(bot_message)
        db.commit()

        return StreamingResponse(stream_long_response(full_response), media_type="text/plain")
    except KeyError:
        raise HTTPException(status_code=404, detail="Chat not found or no PDFs associated with this chat")
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing chat request")