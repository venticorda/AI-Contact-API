from __future__ import annotations

from loguru import logger

from app.ai.service import analyze_sentiment as ai_analyze
from app.api.schemas.response import ContactResponse, SentimentData
from app.database.models import Contact
from app.database.session import async_session_factory
from app.repositories.metrics_repository import metrics_repository
from app.services.email_service import email_service


class ContactService:
    async def process_contact(
        self,
        name: str,
        phone: str,
        email: str,
        comment: str,
    ) -> dict:
        metrics_repository.increment_total()

        sentiment_result = await ai_analyze(comment)
        sentiment = sentiment_result.sentiment
        reason = sentiment_result.reason

        if sentiment == "unknown":
            metrics_repository.increment_ai_fallback()

        logger.info(f"Контакт от {name} ({email}) | Тональность: {sentiment}")

        async with async_session_factory() as session:
            contact = Contact(
                name=name,
                phone=phone,
                email=email,
                comment=comment,
                sentiment=sentiment,
                reason=reason,
            )
            session.add(contact)
            await session.commit()
            logger.info(f"Контакт сохранён в БД: {contact.id}")

        email_service.send_owner_notification(
            name=name,
            email=email,
            phone=phone,
            comment=comment,
            sentiment=sentiment,
        )

        email_service.send_user_copy(
            name=name,
            to_email=email,
            comment=comment,
            sentiment=sentiment,
        )

        metrics_repository.increment_success()

        return ContactResponse(
            success=True,
            message="Контактная форма успешно обработана",
            data=SentimentData(
                name=name,
                email=email,
                sentiment=sentiment,
                reason=reason,
            ),
        ).model_dump()
