from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.schemas.contact import ContactRequest
from app.api.schemas.response import ContactResponse, SentimentData
from app.core.exceptions import RateLimitExceededError
from app.repositories.metrics_repository import MetricsRepository
from app.services.contact_service import ContactService
from app.services.rate_limit import RateLimiter

router = APIRouter(prefix="/api", tags=["Contact"])


async def get_rate_limiter() -> RateLimiter:
    return RateLimiter()


async def get_metrics_repository() -> MetricsRepository:
    return MetricsRepository()


async def get_contact_service() -> ContactService:
    return ContactService()


@router.post(
    "/contact",
    response_model=ContactResponse,
    summary="Отправить контактную форму",
    description=(
        "Валидирует данные контактной формы, выполняет AI-анализ тональности "
        "комментария, логирует запрос, обновляет метрики и отправляет "
        "email-уведомления владельцу и пользователю."
    ),
    responses={
        200: {
            "description": "Контактная форма успешно обработана",
            "model": ContactResponse,
        },
        400: {
            "description": "Ошибка валидации",
        },
        429: {
            "description": "Превышен лимит запросов",
        },
    },
)
async def submit_contact(
    request: Request,
    body: ContactRequest,
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    contact_service: Annotated[ContactService, Depends(get_contact_service)],
    metrics_repository: Annotated[MetricsRepository, Depends(get_metrics_repository)],
) -> ContactResponse | JSONResponse:
    ip_address = request.client.host if request.client else "unknown"

    try:
        await rate_limiter.check(ip_address)
    except RateLimitExceededError as exc:
        metrics_repository.increment_error()
        logger.warning("Превышен лимит запросов для IP: {}", ip_address)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": str(exc)},
        )

    try:
        result = await contact_service.process_contact(
            name=body.name,
            phone=body.phone,
            email=body.email,
            comment=body.comment,
        )
        return ContactResponse(**result)

    except Exception as exc:
        metrics_repository.increment_error()
        logger.error("Ошибка обработки контакта: {}", exc)
        return ContactResponse(
            success=False,
            message="Произошла внутренняя ошибка",
            data=SentimentData(
                name=body.name,
                email=body.email,
                sentiment="unknown",
                reason="Ошибка обработки",
            ),
        )
