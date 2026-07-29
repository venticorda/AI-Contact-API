from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import contact, contacts, health, metrics
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.session import close_db, init_db
from app.middlewares.logging import LoggingMiddleware

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация БД...")
    await init_db()
    logger.info("БД готова")
    yield
    logger.info("Закрытие подключений к БД...")
    await close_db()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-grade Contact API с AI-анализом тональности, "
        "ограничением запросов, email-уведомлениями, метриками и PostgreSQL."
    ),
    contact={
        "name": "Разработчик",
        "url": "https://github.com",
        "email": "developer@example.com",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Необработанное исключение: {} | Путь: {}", exc, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )


app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(contact.router)
app.include_router(contacts.router)


STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / "index.html")


def run() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
