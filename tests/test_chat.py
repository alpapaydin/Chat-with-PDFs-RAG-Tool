import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def mock_pdf_id():
    return "test_pdf_id"

@patch("app.services.llm_service.get_pdf_index")
@patch("app.services.llm_service.ChatGoogleGenerativeAI")
def test_chat_with_pdf(mock_chat_google, mock_get_pdf_index, mock_pdf_id):
    mock_index = MagicMock()
    mock_index.as_retriever.return_value.retrieve.return_value = [
        MagicMock(get_content=lambda: "Test content 1"),
        MagicMock(get_content=lambda: "Test content 2"),
    ]
    response = client.post(f"/v1/chat/{mock_pdf_id}", json={"message": "Test question"})

    assert response.status_code == 200

def test_chat_with_nonexistent_pdf():
    response = client.post("/v1/chat/nonexistent", json={"message": "Hello"})
    assert response.status_code == 404