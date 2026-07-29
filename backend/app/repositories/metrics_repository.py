from __future__ import annotations

import json
from threading import Lock

from loguru import logger

from app.core.config import settings


class MetricsRepository:
    def __init__(self) -> None:
        self._file_path = settings.metrics_dir / "metrics.json"
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self._file_path.exists():
            self._write({
                "total_requests": 0,
                "successful_requests": 0,
                "error_requests": 0,
                "ai_fallback_count": 0,
            })

    def _read(self) -> dict:
        try:
            data = json.loads(self._file_path.read_text())
            return {
                "total_requests": data.get("total_requests", 0),
                "successful_requests": data.get("successful_requests", 0),
                "error_requests": data.get("error_requests", 0),
                "ai_fallback_count": data.get("ai_fallback_count", 0),
            }
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Не удалось прочитать метрики: {e}")
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "error_requests": 0,
                "ai_fallback_count": 0,
            }

    def _write(self, data: dict) -> None:
        try:
            self._file_path.write_text(json.dumps(data, indent=2))
        except OSError as e:
            logger.error(f"Не удалось записать метрики: {e}")

    def get_metrics(self) -> dict:
        with self._lock:
            return self._read()

    def increment_total(self) -> None:
        with self._lock:
            data = self._read()
            data["total_requests"] += 1
            self._write(data)

    def increment_success(self) -> None:
        with self._lock:
            data = self._read()
            data["successful_requests"] += 1
            self._write(data)

    def increment_error(self) -> None:
        with self._lock:
            data = self._read()
            data["error_requests"] += 1
            self._write(data)

    def increment_ai_fallback(self) -> None:
        with self._lock:
            data = self._read()
            data["ai_fallback_count"] += 1
            self._write(data)


metrics_repository = MetricsRepository()
