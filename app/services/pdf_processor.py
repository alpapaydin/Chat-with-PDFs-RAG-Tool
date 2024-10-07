import uuid
import pickle
from fastapi import UploadFile
from llama_index import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from llama_index.vector_stores import SimpleVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.node_parser import SentenceSplitter
from llama_index.embeddings import LangchainEmbedding
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.db.database import SessionLocal
from app.db.models import PDF

# Initialize Google embeddings
google_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
embed_model = LangchainEmbedding(google_embeddings)

async def process_pdf(file: UploadFile):
    # Save the uploaded file temporarily
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        content = await file.read()
        temp_file.write(content)
    # Use LlamaIndex to load and process the PDF
    documents = SimpleDirectoryReader(input_files=[temp_file_path]).load_data()
    # Create a SentenceSplitter
    sentence_splitter = SentenceSplitter(
        chunk_size=1024,
        chunk_overlap=200,
        paragraph_separator="\n\n",
        secondary_chunking_regex="[^,.;。？！]+[,.;。？！]?"
    )
    # Create a service context with the sentence splitter and Google embeddings
    service_context = ServiceContext.from_defaults(
        node_parser=sentence_splitter,
        embed_model=embed_model,
        llm=None  # We're not using an LLM for indexing
    )
    # Create a SimpleVectorStore
    vector_store = SimpleVectorStore()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    # Create an index from the documents
    index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context,
        service_context=service_context
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
    index.service_context.embed_model = embed_model
    db.close()
    return index