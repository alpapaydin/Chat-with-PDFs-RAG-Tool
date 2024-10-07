from sqlalchemy import Column, String, LargeBinary
from .database import Base

class PDF(Base):
    __tablename__ = "pdfs"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    vector_store = Column(LargeBinary)  # Stores serialized FAISS index