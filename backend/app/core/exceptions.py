from __future__ import annotations


class AppError(Exception):
    status_code: int = 500
    detail: str = "Внутренняя ошибка сервера"

    def __init__(self, detail: str | None = None, status_code: int | None = None) -> None:
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class RateLimitExceededError(AppError):
    def __init__(self, detail: str = "Превышен лимит запросов. Попробуйте позже.") -> None:
        super().__init__(detail=detail, status_code=429)


class ValidationError(AppError):
    def __init__(self, detail: str = "Ошибка валидации") -> None:
        super().__init__(detail=detail, status_code=422)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Ресурс не найден") -> None:
        super().__init__(detail=detail, status_code=404)
