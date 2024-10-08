# conftest.py
import pytest
from unittest.mock import patch
from app.core.config import settings

@pytest.fixture(autouse=True)
def set_test_database_url():
    with patch.object(settings, 'SQLALCHEMY_DATABASE_URL', "sqlite:///./testapp.db"):
        # Optional: Print to verify that the URL is changed
        print(f"Test DB URL set to: {settings.SQLALCHEMY_DATABASE_URL}")
        yield  # This allows the test to run with the patched settings
