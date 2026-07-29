from __future__ import annotations

from pydantic import BaseModel, Field


class SentimentData(BaseModel):
    name: str = Field(..., description="Имя контакта", examples=["Иван Петров"])
    email: str = Field(..., description="Email контакта", examples=["ivan@example.com"])
    sentiment: str = Field(
        ...,
        description="Результат анализа тональности",
        examples=["positive", "neutral", "negative", "unknown"],
    )
    reason: str = Field(
        ...,
        description="Объяснение анализа тональности",
        examples=["Комментарий выражает удовлетворение и благодарность"],
    )


class ContactResponse(BaseModel):
    success: bool = Field(..., description="Указывает, был ли запрос успешным")
    message: str = Field(..., description="Сообщение ответа")
    data: SentimentData


class HealthResponse(BaseModel):
    status: str = Field(..., description="Статус здоровья сервиса")
    version: str = Field(..., description="Версия API")
    uptime: float = Field(..., description="Время работы сервиса в секундах")
    ai_status: str = Field(..., description="Статус доступности AI-сервиса")
    db_status: str = Field(..., description="Статус подключения к БД")


class MetricsResponse(BaseModel):
    total_requests: int = Field(..., ge=0, description="Общее количество запросов")
    successful_requests: int = Field(..., ge=0, description="Количество успешных запросов")
    error_requests: int = Field(..., ge=0, description="Количество ошибочных запросов")
    ai_fallback_count: int = Field(..., ge=0, description="Количество откатов AI")


class ContactListItem(BaseModel):
    id: str = Field(..., description="UUID контакта")
    name: str = Field(..., description="Имя")
    email: str = Field(..., description="Email")
    phone: str = Field(..., description="Телефон")
    sentiment: str = Field(..., description="Тональность")
    created_at: str | None = Field(None, description="Дата создания")


class ContactListResponse(BaseModel):
    items: list[ContactListItem]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total_pages: int = Field(..., ge=0)
