import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def mock_pdf_file():
    return MagicMock(filename="test.pdf", read=lambda: b"Test PDF content")

@patch("app.services.pdf_processor.SimpleDirectoryReader")
@patch("app.services.pdf_processor.VectorStoreIndex")
@patch("app.services.pdf_processor.SessionLocal")
@patch("app.services.pdf_processor.pickle.dumps")
def test_upload_pdf(mock_pickle_dumps, mock_session, mock_vector_store_index, mock_simple_directory_reader, mock_pdf_file):
    mock_simple_directory_reader.return_value.load_data.return_value = ["Test document"]
    mock_vector_store_index.from_documents.return_value = MagicMock()
    mock_session.return_value.__enter__.return_value = MagicMock()
    mock_pickle_dumps.return_value = b"serialized_index"

    response = client.post("/v1/pdf", files={"file": ("test.pdf", mock_pdf_file.read(), "application/pdf")})
    
    assert response.status_code == 200
    assert "pdf_id" in response.json()

@patch("app.services.pdf_processor.SimpleDirectoryReader")
def test_upload_non_pdf(mock_simple_directory_reader):
    mock_simple_directory_reader.side_effect = Exception("Invalid file type")

    response = client.post("/v1/pdf", files={"file": ("test.txt", b"This is not a PDF", "text/plain")})
    assert response.status_code == 400