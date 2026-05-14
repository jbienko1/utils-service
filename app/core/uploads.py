from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings

logger = logging.getLogger(__name__)


async def save_upload_to_temp(
    file: UploadFile,
    settings: Settings,
    suffix: str,
) -> Path:
    """Zapisuje upload do pliku tymczasowego; usuwa plik przy błędzie zapisu."""
    base = settings.temp_dir
    if base is not None:
        base.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(suffix=suffix, dir=base)
    path = Path(raw)
    total = 0
    chunk_size = 1024 * 1024
    try:
        import os

        os.close(fd)
        with path.open("wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    raise ValueError("Plik przekracza UTILS_MAX_UPLOAD_BYTES.")
                out.write(chunk)
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise
