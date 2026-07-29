from dataclasses import dataclass

from loguru import logger

from app.ai.client import analyze_sentiment_via_openai


@dataclass(frozen=True)
class SentimentResult:
    sentiment: str
    reason: str
    fallback_used: bool


DEFAULT_FALLBACK = SentimentResult(
    sentiment="unknown",
    reason="AI недоступен",
    fallback_used=True,
)


async def analyze_sentiment(comment: str) -> SentimentResult:
    result = await analyze_sentiment_via_openai(comment)
    if result is None:
        logger.bind(component="ai").warning(
            "AI вернул None, используется fallback. Длина комментария: {}",
            len(comment),
        )
        return DEFAULT_FALLBACK

    sentiment = result.get("sentiment", "unknown")
    reason = result.get("reason", "Объяснение не предоставлено")

    logger.bind(component="ai").info(
        "Тональность: {} | Причина: {} | Длина комментария: {}",
        sentiment,
        reason,
        len(comment),
    )

    if sentiment not in ("positive", "neutral", "negative"):
        return DEFAULT_FALLBACK

    return SentimentResult(
        sentiment=sentiment,
        reason=reason,
        fallback_used=False,
    )
