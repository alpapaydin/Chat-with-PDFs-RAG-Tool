from sqlalchemy import Column, String, LargeBinary, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime, timezone

class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    pdfs = relationship("PDF", back_populates="chat")
    messages = relationship("Message", back_populates="chat")

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    vector_store = Column(LargeBinary)
    chat_id = Column(String, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="pdfs")
    file_hash = Column(String, unique=True, index=True)

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    chat_id = Column(String, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="messages")
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    is_user = Column(Boolean, default=True)