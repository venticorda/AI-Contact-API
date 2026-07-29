import json
from typing import Final

from httpx import AsyncClient, ConnectError, TimeoutException
from loguru import logger

from app.core.config import settings

OPENAI_API_URL: Final[str] = "https://api.openai.com/v1/chat/completions"
REQUEST_TIMEOUT: Final[int] = 15


async def analyze_sentiment_via_openai(comment: str) -> dict | None:
    if not settings.openai_api_key:
        logger.warning("API-ключ OpenAI не настроен")
        return None

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты ассистент анализа тональности текста. "
                    "Определи тональность сообщения. "
                    "Ответь в формате JSON с ключами 'sentiment' "
                    "(один из: positive, neutral, negative) "
                    "и 'reason' (краткое объяснение на русском)."
                ),
            },
            {"role": "user", "content": comment},
        ],
        "temperature": 0.0,
        "max_tokens": 150,
    }

    try:
        async with AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
            return result

    except ConnectError:
        logger.warning("Ошибка подключения к OpenAI API")
    except TimeoutException:
        logger.warning("Тайм-аут запроса к OpenAI API")
    except Exception as exc:
        logger.warning("Ошибка OpenAI API: {}", exc)

    return None
