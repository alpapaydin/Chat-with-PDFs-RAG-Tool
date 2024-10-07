import pytest

@pytest.mark.asyncio
async def test_upload_pdf(test_client, test_pdf):
    response = test_client.post("/v1/pdf", files={"file": ("test.pdf", test_pdf, "application/pdf")})
    assert response.status_code == 200
    assert "pdf_id" in response.json()

def test_upload_non_pdf(test_client):
    response = test_client.post("/v1/pdf", files={"file": ("test.txt", b"This is not a PDF", "text/plain")})
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]
