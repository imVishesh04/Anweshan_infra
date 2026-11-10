import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

# Ensure backend is on sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

TEST_DB_NAME = "anweshan_test"


@pytest.fixture(scope="session")
def temp_upload_dir():
    d = tempfile.mkdtemp(prefix="anweshan_test_uploads_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def configure_test_env(temp_upload_dir, monkeypatch):
    monkeypatch.setenv("DB_NAME", TEST_DB_NAME)
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("UPLOAD_DIR", str(temp_upload_dir))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("COOKIE_SAMESITE", "lax")
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("JWT_SECRET", "super_secret_test_key_at_least_32_characters_long_12345")
    monkeypatch.setenv("ADMIN_PASSWORD", "test_admin_password_123")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://test")

    from app.config import get_settings
    from app.storage import reset_storage

    get_settings.cache_clear()
    reset_storage()


@pytest.fixture
async def app_client(temp_upload_dir):
    from app.config import get_settings
    from app.storage import reset_storage
    from server import app

    settings = get_settings()
    reset_storage()

    # Pre-clean test database
    mongo_client = AsyncMongoClient(settings.MONGO_URL)
    await mongo_client.drop_database(TEST_DB_NAME)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    # Cleanup after test
    await mongo_client.drop_database(TEST_DB_NAME)
    await mongo_client.close()


@pytest.fixture
async def authenticated_admin(app_client):
    """Logs in and returns the client with session cookies already set."""
    res = await app_client.post(
        "/api/admin/login",
        json={"password": "test_admin_password_123"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res.status_code == 200
    return app_client
