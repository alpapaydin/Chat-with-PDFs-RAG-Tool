from sqlalchemy import Column, String, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    pdfs = relationship("PDF", back_populates="chat")

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    vector_store = Column(LargeBinary)
    chat_id = Column(String, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="pdfs")
    file_hash = Column(String, unique=True, index=True)