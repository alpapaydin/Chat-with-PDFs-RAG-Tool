import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.db.models import PDF

@pytest.mark.asyncio
@patch("app.services.llm_service.get_pdf_index")
@patch("app.services.llm_service.llm")
async def test_chat_with_pdf(mock_llm, mock_get_pdf_index, test_client, db_session):
    # Create a test PDF entry
    pdf = PDF(id="test_id", filename="test.pdf", vector_store=b"test_data")
    db_session.add(pdf)
    db_session.commit()

    mock_index = MagicMock()
    mock_index.as_retriever.return_value.retrieve.return_value = [
        MagicMock(get_content=lambda: "Test content")
    ]
    mock_get_pdf_index.return_value = mock_index
    mock_llm.invoke.return_value = MagicMock(content="Mocked response")

    response = test_client.post("/v1/chat/test_id", json={"message": "Test question"})
    
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_chat_with_nonexistent_pdf(test_client, db_session):
    response = test_client.post("/v1/chat/nonexistent", json={"message": "Hello"})
    assert response.status_code == 404

@pytest.mark.asyncio
@patch("app.services.llm_service.get_pdf_index")
async def test_chat_with_pdf_retrieval_error(mock_get_pdf_index, test_client, db_session):
    mock_get_pdf_index.side_effect = Exception("PDF retrieval error")
    response = test_client.post("/v1/chat/test_id", json={"message": "Test question"})
    assert response.status_code == 500
    assert "Error processing chat request" in response.json()["detail"]