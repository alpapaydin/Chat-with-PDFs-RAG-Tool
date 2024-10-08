import pytest
import io
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db, init_db, get_engine, get_session_local
from app.core.config import AppSettings, override_settings, get_settings
from unittest.mock import patch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Test settings
test_db_url = "sqlite:///./TEST.db"
test_settings = AppSettings(
    SQLALCHEMY_DATABASE_URL=test_db_url,
)

# Create test database engine
test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override get_db function for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def remove_test_db():
    if os.path.exists("./TEST.db"):
        os.remove("./TEST.db")
        print("Removed existing TEST.db file")

@pytest.fixture(scope="module")
def test_app():
    # Remove existing TEST.db if it exists
    remove_test_db()

    # Clear caches
    get_engine.cache_clear()
    get_session_local.cache_clear()
    get_settings.cache_clear()
    
    # Set up
    override_settings(test_settings)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    
    # Patch get_settings to return test_settings
    with patch('app.db.database.get_settings', return_value=test_settings):
        with patch('app.core.config.get_settings', return_value=test_settings):
            init_db()  # Initialize the test database
            client = TestClient(app)
            yield client
    
def create_sample_pdf(content):
    pdf_content = io.BytesIO()
    c = canvas.Canvas(pdf_content, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, content)
    c.save()
    pdf_content.seek(0)
    return pdf_content

@pytest.fixture(scope="module")
def test_chat_id(test_app):
    pdf_content = create_sample_pdf("This is a test PDF file for testing purposes.")
    response = test_app.post("/v1/pdf", files={"file": ("test.pdf", pdf_content)})
    assert response.status_code == 200
    return response.json()["chat_id"]

def test_upload_pdf(test_app):
    pdf_content = create_sample_pdf("This is a test PDF file for testing purposes.")
    response = test_app.post("/v1/pdf", files={"file": ("test.pdf", pdf_content)})
    assert response.status_code == 200
    assert "pdf_id" in response.json()
    assert "chat_id" in response.json()

def test_upload_non_pdf(test_app):
    non_pdf_content = io.BytesIO(b"This is not a PDF")
    response = test_app.post("/v1/pdf", files={"file": ("test.txt", non_pdf_content)})
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

def test_chat_with_pdf(test_app, test_chat_id):
    response = test_app.post(f"/v1/chat/{test_chat_id}", json={"message": "Test question"})
    assert response.status_code == 200
    assert "answer" in response.text.lower()

def test_chat_with_nonexistent_pdf(test_app):
    response = test_app.post("/v1/chat/nonexistent_id", json={"message": "Test question"})
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_full_flow(test_app, test_chat_id):
    # Upload another PDF to the same chat
    pdf_content = create_sample_pdf("This is another test PDF file for the same chat.")
    upload_response = test_app.post("/v1/pdf", files={"file": ("test2.pdf", pdf_content)}, data={"chat_id": test_chat_id})
    assert upload_response.status_code == 200
    assert upload_response.json()["chat_id"] == test_chat_id
    
    # Chat with the uploaded PDFs
    chat_response = test_app.post(f"/v1/chat/{test_chat_id}", json={"message": "What are the contents of the PDFs?"})
    assert chat_response.status_code == 200
    assert "test pdf file" in chat_response.text.lower()

def test_error_handling(test_app):
    with patch("app.services.pdf_processor.process_pdf", side_effect=Exception("Test error")):
        response = test_app.post("/v1/pdf", files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.5"))})
        assert response.status_code == 400

def test_get_chats(test_app, test_chat_id):
    response = test_app.get("/v1/chats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert any(chat["id"] == test_chat_id for chat in response.json())

def test_get_chat_pdfs(test_app, test_chat_id):
    response = test_app.get(f"/v1/chat/{test_chat_id}/pdfs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert all("id" in pdf and "filename" in pdf for pdf in response.json())

def test_upload_duplicate_pdf(test_app, test_chat_id):
    pdf_content = create_sample_pdf("This is a duplicate PDF.")
    # Upload the PDF for the first time
    response1 = test_app.post("/v1/pdf", files={"file": ("duplicate.pdf", pdf_content)}, data={"chat_id": test_chat_id})
    assert response1.status_code == 200
    # Try to upload the same PDF again
    pdf_content.seek(0)
    response2 = test_app.post("/v1/pdf", files={"file": ("duplicate.pdf", pdf_content)}, data={"chat_id": test_chat_id})
    assert response2.status_code == 400
    assert "This PDF has already been added to this chat" in response2.json()["detail"]

def test_upload_pdf_new_chat(test_app):
    pdf_content = create_sample_pdf("This is a PDF for a new chat.")
    response = test_app.post("/v1/pdf", files={"file": ("new_chat.pdf", pdf_content)})
    assert response.status_code == 200
    assert "pdf_id" in response.json()
    assert "chat_id" in response.json()

def test_upload_multiple_pdfs_same_chat(test_app, test_chat_id):
    pdf_content1 = create_sample_pdf("This is the first PDF in a multi-PDF test.")
    pdf_content2 = create_sample_pdf("This is the second PDF in a multi-PDF test.")
    
    response1 = test_app.post("/v1/pdf", files={"file": ("multi1.pdf", pdf_content1)}, data={"chat_id": test_chat_id})
    assert response1.status_code == 200
    
    response2 = test_app.post("/v1/pdf", files={"file": ("multi2.pdf", pdf_content2)}, data={"chat_id": test_chat_id})
    assert response2.status_code == 200
    
    pdfs_response = test_app.get(f"/v1/chat/{test_chat_id}/pdfs")
    assert pdfs_response.status_code == 200
    assert len(pdfs_response.json()) >= 2

def test_chat_with_multiple_pdfs(test_app, test_chat_id):
    response = test_app.post(f"/v1/chat/{test_chat_id}", json={"message": "Summarize the content of all PDFs"})
    assert response.status_code == 200
    assert "test pdf file" in response.text.lower()
    assert "multi-pdf test" in response.text.lower()

# New tests for authentication

def test_register_user(test_app):
    response = test_app.post("/v1/auth/register", json={"username": "anewuser", "password": "testpassword"})
    assert response.status_code == 200
    assert "message" in response.json()

def test_register_existing_user(test_app):
    response = test_app.post("/v1/auth/register", json={"username": "anewuser", "password": "testpassword"})
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_login_user(test_app):
    response = test_app.post("/v1/auth/token", data={"username": "anewuser", "password": "testpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()

def test_login_invalid_credentials(test_app):
    response = test_app.post("/v1/auth/token", data={"username": "anewtuser", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.fixture
def auth_headers(test_app):
    response = test_app.post("/v1/auth/token", data={"username": "anewuser", "password": "testpassword"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_upload_pdf_authenticated(test_app, auth_headers):
    pdf_content = create_sample_pdf("This is an authenticated PDF upload.")
    response = test_app.post("/v1/pdf", files={"file": ("auth_test.pdf", pdf_content)}, headers=auth_headers)
    assert response.status_code == 200
    assert "pdf_id" in response.json()
    assert "chat_id" in response.json()

def test_get_chats_authenticated(test_app, auth_headers):
    response = test_app.get("/v1/chats", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_chat_with_pdf_authenticated(test_app, test_chat_id, auth_headers):
    response = test_app.post(f"/v1/chat/{test_chat_id}", json={"message": "Test authenticated question"}, headers=auth_headers)
    assert response.status_code == 200
    assert "answer" in response.text.lower()

def test_get_chat_pdfs_authenticated(test_app, test_chat_id, auth_headers):
    response = test_app.get(f"/v1/chat/{test_chat_id}/pdfs", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_upload_large_pdf(test_app):
    settings = get_settings()
    # Create a PDF slightly larger than the limit
    large_pdf_content = b"%PDF-1.5\n" + b"A" * (settings.FILE_SIZE_MB * 1024 * 1024 + 1024)  # Just 1KB over the limit
    response = test_app.post("/v1/pdf", files={"file": ("large.pdf", io.BytesIO(large_pdf_content), "application/pdf")})
    assert response.status_code == 413
    assert "File size exceeds the limit" in response.json()["detail"]

def test_chat_with_empty_message(test_app, test_chat_id):
    response = test_app.post(f"/v1/chat/{test_chat_id}", json={"message": ""})
    assert response.status_code == 500

def test_upload_pdf_invalid_chat_id(test_app):
    pdf_content = create_sample_pdf("This is a test PDF for an invalid chat ID.")
    response = test_app.post("/v1/pdf", files={"file": ("invalid_chat.pdf", pdf_content)}, data={"chat_id": "invalid_id"})
    assert response.status_code == 404
    assert "Chat not found" in response.json()["detail"]