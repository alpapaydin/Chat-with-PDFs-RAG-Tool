import uuid
import pickle
from fastapi import UploadFile, HTTPException
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.db.database import get_db
from app.db.models import PDF
from app.core.config import settings
import PyPDF2
import os

# Initialize Google embeddings
google_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.GOOGLE_API_KEY)
embed_model = LangchainEmbedding(google_embeddings)

async def process_pdf(file: UploadFile):
    # Save the uploaded file temporarily
    temp_file_path = f"/tmp/{file.filename}"
    try:
        with open(temp_file_path, "wb") as temp_file:
            # Read and write the file in chunks
            chunk_size = 1024 * 1024  # 1 MB chunks
            while chunk := await file.read(chunk_size):
                temp_file.write(chunk)
        
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
            embed_model=embed_model,
        )
        
        # Generate a unique ID for this PDF
        pdf_id = str(uuid.uuid4())
        
        # Serialize the entire index
        serialized_index = pickle.dumps(index)
        
        # Store in the database
        db = next(get_db())
        db_pdf = PDF(id=pdf_id, filename=file.filename, vector_store=serialized_index)
        db.add(db_pdf)
        db.commit()
        db.refresh(db_pdf)
        
        return pdf_id
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def get_pdf_index(pdf_id: str):
    db = next(get_db())
    db_pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
    if db_pdf is None:
        raise KeyError("PDF not found")
    # Deserialize the index
    index = pickle.loads(db_pdf.vector_store)
    index.embed_model = embed_model
    return index