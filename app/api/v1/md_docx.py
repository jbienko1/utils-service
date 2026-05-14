from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.core.uploads import save_upload_to_temp
from app.services.md_to_docx import convert_markdown_path_to_docx

router = APIRouter(tags=["markdown-docx"])

_DOCX_MEDIA = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _is_markdown_like_upload(file: UploadFile) -> bool:
    ct = (file.content_type or "").lower()
    if ct in ("text/markdown", "text/x-markdown", "text/plain"):
        return True
    name = (file.filename or "").lower()
    return name.endswith((".md", ".markdown", ".txt"))


def _safe_download_filename(filename: str | None) -> str:
    if not filename:
        return "document.docx"
    stem = Path(filename).stem
    stem = re.sub(r"[^\w.\-]+", "_", stem, flags=re.UNICODE).strip("._") or "document"
    if len(stem) > 80:
        stem = stem[:80]
    return f"{stem}.docx"


@router.post("/markdown-to-docx")
async def markdown_to_docx_endpoint(
    file: Annotated[UploadFile, File(description="Plik Markdown (.md, .markdown) lub zwykły tekst (.txt).")],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    if file.content_type and file.content_type not in (
        "text/markdown",
        "text/x-markdown",
        "text/plain",
        "application/octet-stream",
    ):
        if not _is_markdown_like_upload(file):
            raise HTTPException(
                status_code=415,
                detail="Oczekiwany plik .md / .markdown / .txt lub typ text/markdown, text/plain.",
            )

    path: Path | None = None
    try:
        suffix = Path(file.filename or "upload.md").suffix.lower()
        if suffix not in (".md", ".markdown", ".txt", ""):
            suffix = ".md"
        path = await save_upload_to_temp(file, settings, suffix=suffix or ".md")
        try:
            docx_bytes = convert_markdown_path_to_docx(path, settings)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        out_name = _safe_download_filename(file.filename)
        return Response(
            content=docx_bytes,
            media_type=_DOCX_MEDIA,
            headers={
                "Content-Disposition": f'attachment; filename="{out_name}"',
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
