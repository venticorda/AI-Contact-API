from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class ContactRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Полное имя контактного лица",
        examples=["Иван Петров"],
    )
    phone: str = Field(
        ...,
        description="Номер телефона в международном формате",
        examples=["+79261234567"],
    )
    email: str = Field(
        ...,
        description="Email-адрес контактного лица",
        examples=["ivan@example.com"],
    )
    comment: str = Field(
        ...,
        min_length=10,
        max_length=3000,
        description="Комментарий или сообщение",
        examples=["Отличный сервис! Всё очень понравилось. Спасибо!"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        pattern = r"^\+?1?\d{7,15}$"
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "Номер телефона должен быть в международном формате (7-15 цифр, опционально +)"
            )
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v.strip()):
            raise ValueError("Неверный формат email-адреса")
        return v.strip().lower()
