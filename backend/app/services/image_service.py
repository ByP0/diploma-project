from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator

from bson import ObjectId
from fastapi import UploadFile, status
from gridfs.errors import NoFile

from app.core.config import setting
from app.core.images import ALLOWED_IMAGE_CONTENT_TYPES, build_image_url
from app.db.mongo import db_mongo


class ImageServiceError(Exception):
    def __init__(self, detail: str, status_code: int):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ImageValidationError(ImageServiceError):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(detail, status_code)


class ImageNotFoundError(ImageServiceError):
    def __init__(self, detail: str = "Изображение не найдено."):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


@dataclass(slots=True)
class StoredImage:
    id: str
    filename: str
    content_type: str
    size_bytes: int

    @property
    def url(self) -> str:
        return build_image_url(self.id)


class ImageService:
    def __init__(self) -> None:
        self.bucket = db_mongo.gridfs_bucket

    async def upload(self, file: UploadFile) -> StoredImage:
        filename = (file.filename or "image").strip() or "image"
        content_type = (file.content_type or "").lower().strip()

        if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            allowed_types = ", ".join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))
            raise ImageValidationError(
                f"Поддерживаются только изображения следующих типов: {allowed_types}.",
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        try:
            content = await file.read()
        finally:
            await file.close()

        if not content:
            raise ImageValidationError("Нельзя загрузить пустой файл.")

        size_bytes = len(content)
        if size_bytes > setting.image_max_upload_size_bytes:
            raise ImageValidationError(
                "Файл слишком большой. Уменьшите размер изображения и повторите загрузку.",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        image_id = await self.bucket.upload_from_stream(
            filename,
            content,
            metadata={
                "content_type": content_type,
                "size_bytes": size_bytes,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return StoredImage(
            id=str(image_id),
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
        )

    async def open_download_stream(self, image_id: str):
        object_id = self._parse_object_id(image_id)

        try:
            return await self.bucket.open_download_stream(object_id)
        except NoFile as exc:
            raise ImageNotFoundError() from exc

    async def delete(self, image_id: str) -> None:
        object_id = self._parse_object_id(image_id)

        try:
            await self.bucket.delete(object_id)
        except NoFile as exc:
            raise ImageNotFoundError() from exc

    async def iter_file(self, grid_out) -> AsyncIterator[bytes]:
        while True:
            chunk = await grid_out.readchunk()
            if not chunk:
                break
            yield chunk

    def build_download_headers(self, grid_out, image_id: str) -> dict[str, str]:
        return {
            "Cache-Control": f"public, max-age={setting.image_cache_max_age_seconds}, immutable",
            "Content-Length": str(grid_out.length),
            "ETag": f"\"{image_id}\"",
        }

    def get_media_type(self, grid_out) -> str:
        metadata = getattr(grid_out, "metadata", None) or {}
        return metadata.get("content_type", "application/octet-stream")

    def _parse_object_id(self, image_id: str) -> ObjectId:
        if not ObjectId.is_valid(image_id):
            raise ImageNotFoundError()

        return ObjectId(image_id)
