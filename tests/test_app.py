import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

client = TestClient(app)

@pytest.fixture(scope="module")
def test_chat_id():
    pdf_content = create_sample_pdf("This is a test PDF file for testing purposes.")
    response = client.post("/v1/pdf", files={"file": ("test.pdf", pdf_content)})
    assert response.status_code == 200
    return response.json()["chat_id"]

def create_sample_pdf(content):
    pdf_content = io.BytesIO()
    c = canvas.Canvas(pdf_content, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, content)
    c.save()
    pdf_content.seek(0)
    return pdf_content

def test_upload_pdf():
    pdf_content = create_sample_pdf("This is a test PDF file for testing purposes.")
    response = client.post("/v1/pdf", files={"file": ("test.pdf", pdf_content)})
    assert response.status_code == 200
    assert "pdf_id" in response.json()
    assert "chat_id" in response.json()

def test_upload_non_pdf():
    non_pdf_content = io.BytesIO(b"This is not a PDF")
    response = client.post("/v1/pdf", files={"file": ("test.txt", non_pdf_content)})
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

def test_chat_with_pdf(test_chat_id):
    response = client.post(f"/v1/chat/{test_chat_id}", json={"message": "Test question"})
    assert response.status_code == 200
    assert "answer" in response.text.lower()

def test_chat_with_nonexistent_pdf():
    response = client.post("/v1/chat/nonexistent_id", json={"message": "Test question"})
    assert response.status_code == 404
    assert "Chat not found or no PDFs associated with this chat" in response.json()["detail"]

@pytest.mark.asyncio
async def test_full_flow(test_chat_id):
    # Upload another PDF to the same chat
    pdf_content = create_sample_pdf("This is another test PDF file for the same chat.")
    upload_response = client.post("/v1/pdf", files={"file": ("test2.pdf", pdf_content)}, data={"chat_id": test_chat_id})
    assert upload_response.status_code == 200
    assert upload_response.json()["chat_id"] == test_chat_id
    
    # Chat with the uploaded PDFs
    chat_response = client.post(f"/v1/chat/{test_chat_id}", json={"message": "What are the contents of the PDFs?"})
    assert chat_response.status_code == 200
    assert "test pdf file" in chat_response.text.lower()

def test_error_handling():
    with patch("app.services.pdf_processor.process_pdf", side_effect=Exception("Test error")):
        response = client.post("/v1/pdf", files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.5"))})
        assert response.status_code == 400

def test_get_chats(test_chat_id):
    response = client.get("/v1/chats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert any(chat["id"] == test_chat_id for chat in response.json())

def test_get_chat_pdfs(test_chat_id):
    response = client.get(f"/v1/chat/{test_chat_id}/pdfs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert all("id" in pdf and "filename" in pdf for pdf in response.json())

def test_upload_duplicate_pdf(test_chat_id):
    pdf_content = create_sample_pdf("This is a duplicate PDF.")
    # Upload the PDF for the first time
    response1 = client.post("/v1/pdf", files={"file": ("duplicate.pdf", pdf_content)}, data={"chat_id": test_chat_id})
    assert response1.status_code == 200
    # Try to upload the same PDF again
    pdf_content.seek(0)
    response2 = client.post("/v1/pdf", files={"file": ("duplicate.pdf", pdf_content)}, data={"chat_id": test_chat_id})
    assert response2.status_code == 400
    assert "This PDF has already been added to this chat" in response2.json()["detail"]

def test_upload_pdf_new_chat():
    pdf_content = create_sample_pdf("This is a PDF for a new chat.")
    response = client.post("/v1/pdf", files={"file": ("new_chat.pdf", pdf_content)})
    assert response.status_code == 200
    assert "pdf_id" in response.json()
    assert "chat_id" in response.json()

def test_upload_multiple_pdfs_same_chat(test_chat_id):
    pdf_content1 = create_sample_pdf("This is the first PDF in a multi-PDF test.")
    pdf_content2 = create_sample_pdf("This is the second PDF in a multi-PDF test.")
    
    response1 = client.post("/v1/pdf", files={"file": ("multi1.pdf", pdf_content1)}, data={"chat_id": test_chat_id})
    assert response1.status_code == 200
    
    response2 = client.post("/v1/pdf", files={"file": ("multi2.pdf", pdf_content2)}, data={"chat_id": test_chat_id})
    assert response2.status_code == 200
    
    pdfs_response = client.get(f"/v1/chat/{test_chat_id}/pdfs")
    assert pdfs_response.status_code == 200
    assert len(pdfs_response.json()) >= 2

def test_chat_with_multiple_pdfs(test_chat_id):
    response = client.post(f"/v1/chat/{test_chat_id}", json={"message": "Summarize the content of all PDFs"})
    assert response.status_code == 200
    assert "test pdf file" in response.text.lower()
    assert "multi-pdf test" in response.text.lower()