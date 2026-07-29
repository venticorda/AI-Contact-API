from __future__ import annotations

from loguru import logger


class LogsRepository:
    def log_request(
        self,
        ip: str,
        endpoint: str,
        method: str,
        status: int,
        error: str | None = None,
        ai_response: str | None = None,
    ) -> None:
        log_data = {
            "ip": ip,
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "error": error,
            "ai_response": ai_response,
        }

        msg = "Запрос завершён с ошибкой" if error else "Запрос завершён"
        if status >= 400:
            logger.bind(**log_data).warning(msg)
        else:
            logger.bind(**log_data).info(msg)

        if ai_response:
            logger.bind(**log_data).info(f"Ответ AI: {ai_response}")


logs_repository = LogsRepository()
