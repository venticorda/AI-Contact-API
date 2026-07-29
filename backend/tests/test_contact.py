import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_contact_endpoint_success(client: AsyncClient) -> None:
    contact_data = {
        "name": "Иван Петров",
        "phone": "+79261234567",
        "email": "ivan@example.com",
        "comment": "Это валидный комментарий с достаточным количеством символов для валидации.",
    }
    response = await client.post("/api/contact", json=contact_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sentiment" in data["data"]
    assert "reason" in data["data"]


@pytest.mark.asyncio
async def test_contact_endpoint_validation_error(client: AsyncClient) -> None:
    contact_data = {
        "name": "J",
        "phone": "invalid",
        "email": "not-an-email",
        "comment": "short",
    }
    response = await client.post("/api/contact", json=contact_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rate_limit_exceeded(client: AsyncClient) -> None:
    contact_data = {
        "name": "Иван Петров",
        "phone": "+79261234567",
        "email": "ivan@example.com",
        "comment": "Это валидный комментарий с достаточным количеством символов для валидации.",
    }

    for _ in range(5):
        response = await client.post("/api/contact", json=contact_data)
        assert response.status_code == 200

    response = await client.post("/api/contact", json=contact_data)
    assert response.status_code == 429
