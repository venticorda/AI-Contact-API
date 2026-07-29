import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    logs_dir: Path = settings.logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        level="DEBUG" if settings.debug else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    json_format = (
        '{{"time":"{time:YYYY-MM-DD HH:mm:ss.SSS}","level":"{level}",'
        '"name":"{name}","function":"{function}","line":{line},'
        '"message":"{message}"}}'
    )

    logger.add(
        logs_dir / "app_{time:YYYY-MM-DD}.log",
        level="DEBUG" if settings.debug else "INFO",
        format=json_format,
        rotation="1 day",
        retention="30 days",
        compression="gz",
    )

    logger.add(
        logs_dir / "errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format=json_format,
        rotation="1 day",
        retention="30 days",
        compression="gz",
    )

    logger.add(
        logs_dir / "ai_{time:YYYY-MM-DD}.log",
        level="INFO",
        format=json_format,
        rotation="1 day",
        retention="30 days",
        compression="gz",
        filter=lambda record: record.get("extra", {}).get("component") == "ai",
    )

    logger.info("Логирование настроено. Директория логов: {}", logs_dir)
