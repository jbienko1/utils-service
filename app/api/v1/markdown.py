from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import Settings, get_settings
from app.core.uploads import save_upload_to_temp, suffix_from_upload
from app.models.schemas import ToMarkdownResponse
from app.services import markitdown_convert

logger = logging.getLogger(__name__)

router = APIRouter(tags=["markdown"])


@router.post("/to-markdown", response_model=ToMarkdownResponse)
async def to_markdown(
    file: Annotated[UploadFile, File(description="Plik do konwersji (formaty obsługiwane przez markitdown).")],
    settings: Settings = Depends(get_settings),
) -> ToMarkdownResponse:
    suffix = suffix_from_upload(file, frozenset(), default=".bin")
    path: Path | None = None
    try:
        path = await save_upload_to_temp(file, settings, suffix=suffix)
        try:
            markdown, title = await asyncio.to_thread(
                markitdown_convert.convert_file_to_markdown, path
            )
        except Exception as e:
            logger.exception("markitdown conversion failed")
            raise HTTPException(
                status_code=422,
                detail=f"Konwersja nie powiodła się: {e!s}",
            ) from e
        return ToMarkdownResponse(markdown=markdown, title=title)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
