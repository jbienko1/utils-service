from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.core.config import Settings, get_settings
from app.core.uploads import save_upload_to_temp
from app.models.schemas import PdfToTextResponse
from app.services import pdf_extract

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pdf"])


@router.post("/pdf-to-text", response_model=PdfToTextResponse)
async def pdf_to_text(
    file: Annotated[UploadFile, File(description="Plik PDF.")],
    settings: Settings = Depends(get_settings),
    ocr: Annotated[
        Literal["off", "on", "auto"],
        Query(description="off: tylko tekst z PDF; on: Tesseract na każdej stronie; auto: OCR gdy mało tekstu."),
    ] = "off",
) -> PdfToTextResponse:
    if file.content_type and file.content_type not in (
        "application/pdf",
        "application/x-pdf",
    ):
        # część klientów wysyła octet-stream — akceptujemy, jeśli nazwa kończy się na .pdf
        name = (file.filename or "").lower()
        if not name.endswith(".pdf"):
            raise HTTPException(
                status_code=415,
                detail="Oczekiwany typ application/pdf lub plik .pdf.",
            )

    path: Path | None = None
    try:
        path = await save_upload_to_temp(file, settings, suffix=".pdf")
        try:
            text, page_count, used_ocr = await asyncio.to_thread(
                pdf_extract.extract_pdf_text, path, settings, ocr
            )
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        return PdfToTextResponse(text=text, page_count=page_count, used_ocr=used_ocr)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
