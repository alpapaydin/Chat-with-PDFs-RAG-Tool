import uuid
import pickle
from fastapi import UploadFile
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.db.database import SessionLocal
from app.db.models import PDF
from app.core.config import settings

# Initialize Google embeddings
google_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.GOOGLE_API_KEY)
embed_model = LangchainEmbedding(google_embeddings)

async def process_pdf(file: UploadFile):
    # Save the uploaded file temporarily
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        content = await file.read()
        temp_file.write(content)
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
    db = SessionLocal()
    db_pdf = PDF(id=pdf_id, filename=file.filename, vector_store=serialized_index)
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    db.close()
    return pdf_id

def get_pdf_index(pdf_id: str):
    db = SessionLocal()
    db_pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
    if db_pdf is None:
        raise KeyError("PDF not found")
    # Deserialize the index
    index = pickle.loads(db_pdf.vector_store)
    # Update the service context with the current embed_model
    index.embed_model = embed_model
    db.close()
    return index