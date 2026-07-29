import json
import time
from pathlib import Path

from loguru import logger

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError


class RateLimiter:
    def __init__(self) -> None:
        self._dir: Path = settings.rate_limit_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_requests: int = settings.rate_limit_max
        self._window_seconds: int = settings.rate_limit_window

    async def check(self, ip_address: str) -> None:
        file_path = self._dir / f"{ip_address}.json"
        now = time.time()

        if not file_path.exists():
            self._save_records(file_path, [(now, 1)])
            return

        records = self._load_records(file_path)
        records = [(ts, cnt) for ts, cnt in records if now - ts < self._window_seconds]

        total_requests = sum(cnt for _, cnt in records)
        if total_requests >= self._max_requests:
            logger.warning("Превышен лимит запросов для IP: {}", ip_address)
            raise RateLimitExceededError(
                f"Превышен лимит запросов. Максимум {self._max_requests} запросов за {self._window_seconds} секунд."
            )

        records.append((now, 1))
        self._save_records(file_path, records)

    def _load_records(self, file_path: Path) -> list[tuple[float, int]]:
        try:
            data = json.loads(file_path.read_text())
            return [(item["timestamp"], item["count"]) for item in data]
        except (json.JSONDecodeError, KeyError, OSError):
            return []

    def _save_records(self, file_path: Path, records: list[tuple[float, int]]) -> None:
        data = [{"timestamp": ts, "count": cnt} for ts, cnt in records]
        file_path.write_text(json.dumps(data))
