import hashlib
import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    BLOCKED_MIME_TYPES = {
        "application/x-executable",
        "application/x-msdownload",
        "application/x-sh",
        "text/x-shellscript",
        "application/x-bat",
    }

    async def validate_file(self, file: UploadFile) -> None:
        # Check extension
        if file.filename:
            ext = Path(file.filename).suffix.lower().lstrip(".")
            if ext not in settings.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неподдерживаемый формат файла: .{ext}. "
                           f"Разрешены: {', '.join(settings.ALLOWED_EXTENSIONS)}",
                )

        # Check MIME type
        content_type = file.content_type or ""
        if content_type in self.BLOCKED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Загрузка исполняемых файлов запрещена",
            )

        # Check size by reading first chunk
        chunk = await file.read(settings.MAX_FILE_SIZE + 1)
        if len(chunk) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл превышает максимальный размер {settings.MAX_FILE_SIZE // 1024 // 1024} МБ",
            )
        # Seek back
        await file.seek(0)

    async def save_upload(self, file: UploadFile) -> Tuple[str, str]:
        """Save uploaded file. Returns (file_path, sha256_hash)."""
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename or "file").suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / unique_name

        sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
                await f.write(chunk)

        return str(file_path), sha256.hexdigest()

    async def check_duplicate(self, file_hash: str, db: AsyncSession):
        """Return existing certificate if file hash matches."""
        from app.models.certificate import Certificate
        result = await db.execute(
            select(Certificate).where(Certificate.file_hash == file_hash)
        )
        return result.scalar_one_or_none()

    def calculate_file_hash(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def generate_preview(self, file_path: str) -> Optional[str]:
        """Generate JPEG preview for a file. Returns preview path or None."""
        preview_dir = Path(settings.PREVIEW_DIR)
        preview_dir.mkdir(parents=True, exist_ok=True)

        file_path_obj = Path(file_path)
        preview_name = f"{file_path_obj.stem}_preview.jpg"
        preview_path = preview_dir / preview_name

        ext = file_path_obj.suffix.lower()

        try:
            if ext == ".pdf":
                return self._preview_pdf(file_path, str(preview_path))
            else:
                return self._preview_image(file_path, str(preview_path))
        except Exception as e:
            logger.warning(f"Failed to generate preview for {file_path}: {e}")
            return None

    def _preview_pdf(self, file_path: str, preview_path: str) -> Optional[str]:
        try:
            import fitz
            doc = fitz.open(file_path)
            page = doc[0]
            mat = fitz.Matrix(150 / 72, 150 / 72)
            pix = page.get_pixmap(matrix=mat)
            pix.save(preview_path)
            doc.close()
            return preview_path
        except Exception as e:
            logger.error(f"PDF preview error: {e}")
            return None

    def _preview_image(self, file_path: str, preview_path: str) -> Optional[str]:
        try:
            from PIL import Image
            img = Image.open(file_path)
            img.thumbnail((800, 1200), Image.Resampling.LANCZOS)
            img = img.convert("RGB")
            img.save(preview_path, "JPEG", quality=85)
            return preview_path
        except Exception as e:
            logger.error(f"Image preview error: {e}")
            return None
