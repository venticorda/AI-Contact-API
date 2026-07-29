import os
import shutil

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.database.session import init_db
from app.main import app


@pytest.fixture(autouse=True)
async def _clean_state():
    if settings.rate_limit_dir.exists():
        shutil.rmtree(settings.rate_limit_dir)
    settings.rate_limit_dir.mkdir(parents=True, exist_ok=True)
    if settings.metrics_dir.exists():
        shutil.rmtree(settings.metrics_dir)
    settings.metrics_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
