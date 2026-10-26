"""
POST /upload-image — загрузка изображения в локальное хранилище проекта.
GET /image-assets — список зарегистрированных путей изображений.
Изображения сохраняются в ./images/ с именем {uuid}.{ext}, пути записываются в таблицу image_assets.
"""

import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.sqlalchemy.image_asset import ImageAsset

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

# Разрешить только изображения
_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
_ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}
_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Папка images относительно корня проекта (работает и в Docker с volume ./images:/app/images)
IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / "images"


def _ensure_images_dir() -> Path:
    """Создаёт папку images, если её нет."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    return IMAGES_DIR


def _safe_filename(ext: str) -> str:
    """Генерирует безопасное имя файла: UUID + расширение."""
    ext_lower = ext.lower()
    if ext_lower not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported extension: {ext}")
    return f"{uuid.uuid4().hex}{ext_lower}"


def _validate_no_path_traversal(filename: str) -> None:
    """Запрет path traversal в имени файла."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Path traversal not allowed")


@router.post("/upload-image")
async def upload_image(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | int]:
    """
    Загружает изображение в локальное хранилище.
    Возвращает {"id": int, "path": "images/uuid.ext"}. Вставка в редактор: /image-assets/{id}/file.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    # Проверка расширения
    ext_match = re.search(r"\.([a-zA-Z0-9]+)$", file.filename)
    ext = f".{ext_match.group(1).lower()}" if ext_match else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported extension. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}",
        )

    # Проверка MIME-типа
    if file.content_type:
        base_type = file.content_type.split(";")[0].strip().lower()
        if base_type not in _ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported content type")

    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {_MAX_FILE_SIZE // (1024 * 1024)} MB)",
        )

    safe_name = _safe_filename(ext)
    _validate_no_path_traversal(safe_name)

    images_dir = _ensure_images_dir()
    target_path = images_dir / safe_name
    target_path.write_bytes(content)

    # Относительный путь для Markdown: images/uuid.ext
    path = f"images/{safe_name}"

    # Запись в таблицу image_assets
    asset = ImageAsset(
        path=path,
        original_filename=file.filename,
    )
    session.add(asset)
    await session.flush()

    logger.info("Uploaded image: %s (id=%s)", path, asset.id)
    return {"id": asset.id, "path": path}


@router.get("/image-assets/{asset_id}/file")
async def get_image_asset_file(
    asset_id: int,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """
    Отдаёт файл изображения по id. В Markdown вставляется URL вида /image-assets/{id}/file.
    """
    result = await session.execute(select(ImageAsset).where(ImageAsset.id == asset_id))
    asset = result.scalars().one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="Image not found")
    if ".." in asset.path or not asset.path.startswith("images/"):
        raise HTTPException(status_code=404, detail="Invalid path")
    path = IMAGES_DIR / Path(asset.path).name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_type = None
    suffix = path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        media_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
        }.get(suffix)
    return FileResponse(path, media_type=media_type)


@router.get("/image-assets")
async def list_image_assets(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str | int | None]]:
    """
    Возвращает список зарегистрированных изображений (id, path, created_at) для выбора в редакторе.
    """
    result = await session.execute(select(ImageAsset).order_by(ImageAsset.created_at.desc()))
    rows = result.scalars().all()
    return [
        {
            "id": row.id,
            "path": row.path,
            "original_filename": row.original_filename,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
