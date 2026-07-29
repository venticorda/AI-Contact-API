import time

from fastapi import APIRouter
from loguru import logger
from sqlalchemy import text

from app.api.schemas.response import HealthResponse
from app.core.config import settings
from app.database.session import engine

router = APIRouter(prefix="/api", tags=["Health"])

_start_time: float = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка состояния API",
    description="Возвращает текущий статус API, включая время работы, состояние AI-сервиса и БД.",
)
async def health() -> HealthResponse:
    ai_status = "доступен" if settings.openai_api_key else "недоступен"

    db_status = "недоступна"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "подключена"
    except Exception as exc:
        logger.warning("Проверка здоровья: БД недоступна: {}", exc)

    uptime = time.time() - _start_time

    return HealthResponse(
        status="здоров" if db_status == "подключена" else "ограничен",
        version=settings.app_version,
        uptime=round(uptime, 2),
        ai_status=ai_status,
        db_status=db_status,
    )
