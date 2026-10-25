"""
Приложение FastAPI: Markdown → PDF через Typst с настраиваемыми стилевыми профилями.
Сервис конвертации Markdown в PDF (Typst). Тестирование: Swagger UI /docs.
"""

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.elements import get_element_routers
from app.api.upload import IMAGES_DIR, router as upload_router
from app.api.generate import router as generate_router
from app.api.profiles import router as profiles_router
from app.api.registry import router as registry_router
from app.api.title_pages import router as title_pages_router
from app.database import init_db

import app.models.sqlalchemy as _orm_models  # noqa: F401 — регистрация ORM для create_all

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PIZDo — Markdown to PDF (Typst)",
    description="Конвертация Markdown в PDF с настраиваемыми стилевыми профилями. API для профилей и генерации PDF.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles_router)
app.include_router(registry_router)
app.include_router(generate_router)
app.include_router(title_pages_router)
app.include_router(upload_router)
for element_router in get_element_routers():
    app.include_router(element_router)

# Раздача загруженных изображений (./images -> /images)
_imgs = Path(IMAGES_DIR)
_imgs.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(_imgs)), name="images")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Перехват необработанных исключений: логируем стектрейс, возвращаем 500 без деталей."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health() -> dict[str, str]:
    """Проверка доступности сервиса."""
    return {"status": "ok"}
