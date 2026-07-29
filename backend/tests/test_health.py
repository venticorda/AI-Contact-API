import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("здоров", "ограничен")
    assert "version" in data
    assert "uptime" in data
    assert data["ai_status"] in ("доступен", "недоступен")
    assert data["db_status"] in ("подключена", "недоступна")
