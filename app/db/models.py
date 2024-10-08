from sqlalchemy import Column, String, LargeBinary, ForeignKey, DateTime, Text, Boolean, Table
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime, timezone
import uuid

chat_pdf_association = Table('chat_pdf_association', Base.metadata,
    Column('chat_id', String, ForeignKey('chats.id')),
    Column('pdf_id', String, ForeignKey('pdfs.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    chats = relationship("Chat", back_populates="user")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", back_populates="chats")
    pdfs = relationship("PDF", secondary=chat_pdf_association, back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    vector_store = Column(LargeBinary)
    chats = relationship("Chat", secondary=chat_pdf_association, back_populates="pdfs")
    file_hash = Column(String, unique=True, index=True)

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    chat_id = Column(String, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="messages")
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    is_user = Column(Boolean, default=True)