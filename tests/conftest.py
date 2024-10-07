import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)

@pytest.fixture(scope="module")
def test_pdf():
    # Create a simple PDF for testing
    from reportlab.pdfgen import canvas
    from io import BytesIO

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 100, "This is a test PDF")
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer