from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.api.models.schemas import ChatRequest, ChatInfo, PDFInfo, MessageInfo
from sqlalchemy.orm import Session
from app.services.llm_service import chat_with_llm, stream_long_response
from app.core.logging import logger
from app.db.database import get_db
from app.db.models import Chat, Message, User
from typing import List, Optional
import uuid
from app.auth.auth import get_current_user

router = APIRouter()

@router.get("/chats", response_model=List[ChatInfo])
async def get_chats(current_user: User = Depends(get_current_user)):
    db = next(get_db())
    if current_user:
        chats = db.query(Chat).filter(Chat.user_id == current_user.id).all()
    else:
        chats = db.query(Chat).filter(Chat.user_id == None).all()
    db.close()
    return [ChatInfo(id=chat.id) for chat in chats]

@router.get("/chat/{chat_id}/pdfs", response_model=List[PDFInfo])
async def get_chat_pdfs(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    # If the chat belongs to a user, ensure the current user is authorized
    if chat.user_id is not None:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        if chat.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    pdfs = chat.pdfs
    return [PDFInfo(id=pdf.id, filename=pdf.filename) for pdf in pdfs]

@router.get("/chat/{chat_id}/messages", response_model=List[MessageInfo])
async def get_chat_messages(chat_id: str, current_user: User = Depends(get_current_user)):
    db = next(get_db())
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        db.close()
        raise HTTPException(status_code=404, detail="Chat not found")
    if current_user and chat.user_id != current_user.id:
        db.close()
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    if not current_user and chat.user_id is not None:
        db.close()
        raise HTTPException(status_code=403, detail="This chat belongs to an authenticated user")
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).all()
    db.close()
    return [MessageInfo(content=msg.content, is_user=msg.is_user, timestamp=msg.timestamp) for msg in messages]

@router.post("/chat/{chat_id}")
async def chat_with_pdfs(
    chat_id: str, 
    chat_request: ChatRequest, 
    current_user: Optional[User] = Depends(get_current_user)
):
    logger.info(f"Received chat request for Chat ID: {chat_id}")
    try:
        db = next(get_db())
        chat = db.query(Chat).filter(Chat.id == chat_id).first()

        if not chat:
            db.close()
            raise HTTPException(status_code=404, detail="Chat not found")

        # Check if the chat belongs to a user
        if chat.user_id:
            # If the chat belongs to a user, ensure the current user is authorized
            if not current_user or current_user.id != chat.user_id:
                db.close()
                raise HTTPException(status_code=403, detail="Not authorized to access this chat")
        else:
            # If it's an anonymous chat, anyone can access it
            pass

        user_message = Message(
            id=str(uuid.uuid4()), 
            chat_id=chat_id, 
            content=chat_request.message, 
            is_user=True
        )
        db.add(user_message)
        db.commit()

        full_response = await chat_with_llm(chat_id, chat_request.message)
        
        bot_message = Message(
            id=str(uuid.uuid4()), 
            chat_id=chat_id, 
            content=full_response, 
            is_user=False
        )
        db.add(bot_message)
        db.commit()
        db.close()

        return StreamingResponse(stream_long_response(full_response), media_type="text/plain")
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing chat request")