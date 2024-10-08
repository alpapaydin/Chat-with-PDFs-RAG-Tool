import uuid
import pickle
import hashlib
from fastapi import UploadFile, HTTPException
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.storage.storage_context import StorageContext
from app.db.database import get_db
from app.db.models import PDF, Chat
import PyPDF2
import os

async def process_pdf(file: UploadFile, chat_id: str = None):
    content = await file.read()
    file_hash = hashlib.md5(content).hexdigest()

    db = next(get_db())
    
    # Check if this file has already been uploaded
    existing_pdf = db.query(PDF).filter(PDF.file_hash == file_hash).first()
    if existing_pdf:
        if chat_id:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                chat = Chat(id=chat_id)
                db.add(chat)
            if existing_pdf not in chat.pdfs:
                chat.pdfs.append(existing_pdf)
            else:
                raise HTTPException(status_code=400, detail="This PDF has already been added to this chat")
            db.commit()
        else:
            # If no chat_id provided, we'll create a new chat for this existing PDF
            new_chat = Chat(id=str(uuid.uuid4()))
            db.add(new_chat)
            new_chat.pdfs.append(existing_pdf)
            db.commit()
            chat_id = new_chat.id
        pdf_id = existing_pdf.id
        db.close()
        return pdf_id, chat_id

    # If the file doesn't exist, process it
    temp_file_path = f"/tmp/{file.filename}"
    try:
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(content)
        
        # Validate PDF
        with open(temp_file_path, "rb") as pdf_file:
            try:
                PyPDF2.PdfReader(pdf_file)
            except PyPDF2.errors.PdfReadError:
                raise ValueError("Invalid PDF file")

        # Use LlamaIndex to load and process the PDF
        documents = SimpleDirectoryReader(input_files=[temp_file_path]).load_data()
        
        # Create a SimpleVectorStore
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create an index from the documents
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
        )
        
        # Generate a unique ID for this PDF
        pdf_id = str(uuid.uuid4())
        
        # Serialize the entire index
        serialized_index = pickle.dumps(index)
        
        # Create a new PDF instance
        new_pdf = PDF(id=pdf_id, filename=file.filename, vector_store=serialized_index, file_hash=file_hash)
        db.add(new_pdf)

        if chat_id:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                chat = Chat(id=chat_id)
                db.add(chat)
            chat.pdfs.append(new_pdf)
        else:
            new_chat = Chat(id=str(uuid.uuid4()))
            db.add(new_chat)
            new_chat.pdfs.append(new_pdf)
            chat_id = new_chat.id

        db.commit()
        return pdf_id, chat_id
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        db.close()
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def get_chat_indices(chat_id: str):
    db = next(get_db())
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat or not chat.pdfs:
        raise KeyError("No PDFs found for this chat")
    indices = []
    for pdf in chat.pdfs:
        index = pickle.loads(pdf.vector_store)
        indices.append(index)
    db.close()
    return indices