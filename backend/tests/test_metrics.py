import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] >= 0
    assert data["successful_requests"] >= 0
    assert data["error_requests"] >= 0
    assert data["ai_fallback_count"] >= 0


@pytest.mark.asyncio
async def test_metrics_updates_after_contact(client: AsyncClient) -> None:
    metrics_before = await client.get("/api/metrics")
    before = metrics_before.json()

    contact_data = {
        "name": "Тестовый пользователь",
        "phone": "+79261234567",
        "email": "test@example.com",
        "comment": "Это тестовый комментарий с достаточным количеством символов для валидации.",
    }
    await client.post("/api/contact", json=contact_data)

    metrics_after = await client.get("/api/metrics")
    after = metrics_after.json()

    assert after["total_requests"] == before["total_requests"] + 1
