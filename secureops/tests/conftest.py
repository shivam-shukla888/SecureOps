import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.security.rate_limit import rate_limiter

TEST_API_KEY = "test-secret-api-key-12345"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", TEST_API_KEY)
    monkeypatch.setattr(settings, "MAX_REQUEST_SIZE_BYTES", 1024 * 1024)
    monkeypatch.setattr(settings, "MAX_REQUEST_LENGTH_CHARS", 4000)
    rate_limiter.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {TEST_API_KEY}"}
