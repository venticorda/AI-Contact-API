from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.schemas.response import MetricsResponse
from app.repositories.metrics_repository import MetricsRepository

router = APIRouter(prefix="/api", tags=["Metrics"])


async def get_metrics_repository() -> MetricsRepository:
    return MetricsRepository()


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Получить метрики API",
    description=(
        "Возвращает агрегированную статистику использования API, "
        "включая общее количество запросов, успешных запросов, "
        "ошибочных запросов и количество откатов AI."
    ),
    responses={
        200: {
            "description": "Метрики получены успешно",
            "model": MetricsResponse,
        },
    },
)
async def get_metrics(
    metrics_repository: Annotated[MetricsRepository, Depends(get_metrics_repository)],
) -> MetricsResponse:
    data = metrics_repository.get_metrics()
    return MetricsResponse(**data)
