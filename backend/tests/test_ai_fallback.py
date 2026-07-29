import pytest
from httpx import AsyncClient

from app.ai.service import SentimentResult, analyze_sentiment


@pytest.mark.asyncio
async def test_ai_fallback_no_api_key() -> None:
    result: SentimentResult = await analyze_sentiment("Тестовый комментарий без API-ключа.")
    assert result.sentiment == "unknown"
    assert result.reason == "AI недоступен"
    assert result.fallback_used is True


@pytest.mark.asyncio
async def test_contact_endpoint_without_ai(client: AsyncClient) -> None:
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
    assert data["data"]["sentiment"] in ("unknown", "positive", "neutral", "negative")
