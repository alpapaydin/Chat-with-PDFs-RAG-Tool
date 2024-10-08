from pydantic import BaseModel
from datetime import datetime

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class ChatInfo(BaseModel):
    id: str

class PDFInfo(BaseModel):
    id: str
    filename: str

class MessageInfo(BaseModel):
    content: str
    is_user: bool
    timestamp: datetime