from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.core.config import Settings, get_settings
from app.core.uploads import save_upload_to_temp
from app.models.schemas import DocxToMarkdownResponse
from app.services.docx_to_markdown import convert_docx_to_markdown

logger = logging.getLogger(__name__)

router = APIRouter(tags=["docx-markdown"])

_DOCX_CONTENT_TYPES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    }
)


def _is_valid_docx_upload(file: UploadFile) -> bool:
    """Akceptuje upload jeśli nazwa kończy się .docx i content-type jest znany lub nieobecny."""
    if not (file.filename or "").lower().endswith(".docx"):
        return False
    ct = (file.content_type or "").lower()
    return not ct or ct in _DOCX_CONTENT_TYPES


@router.post("/docx-to-markdown", response_model=DocxToMarkdownResponse)
async def docx_to_markdown(
    file: Annotated[UploadFile, File(description="Plik Word (.docx).")],
    settings: Annotated[Settings, Depends(get_settings)],
    comments: Annotated[
        bool,
        Query(
            description="true: track-changes=all + normalizacja (komentarze, usunięcia jako ~~); "
            "false: track-changes=accept (tekst końcowy bez redakcji).",
        ),
    ] = True,
    extract_media: Annotated[
        bool,
        Query(description="true: wyciągnij obrazy do media/ i zwróć ZIP (base64) w odpowiedzi."),
    ] = False,
) -> DocxToMarkdownResponse:
    if not _is_valid_docx_upload(file):
        raise HTTPException(
            status_code=415,
            detail="Oczekiwany plik .docx (application/vnd.openxmlformats-officedocument.wordprocessingml.document).",
        )

    path: Path | None = None
    try:
        path = await save_upload_to_temp(file, settings, suffix=".docx")
        try:
            result = await asyncio.to_thread(
                convert_docx_to_markdown,
                path,
                settings,
                comments=comments,
                extract_media=extract_media,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        return DocxToMarkdownResponse(
            markdown=result.markdown,
            title=result.title,
            media_count=result.media_count,
            media_zip_base64=result.media_zip_base64,
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
