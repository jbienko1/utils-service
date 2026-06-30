from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.core.uploads import save_upload_to_temp, suffix_from_upload
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


def _content_disposition_attachment(display_name: str) -> str:
    """RFC 5987: `filename` tylko ASCII (nagłówki HTTP / latin-1); pełna nazwa w `filename*=UTF-8''`."""
    star = quote(display_name, encoding="utf-8")
    stem = Path(display_name).stem
    ascii_stem = "".join(
        c if 32 <= ord(c) <= 126 and c not in {'\\', '"'} else "_" for c in stem
    )
    ascii_stem = re.sub(r"_+", "_", ascii_stem).strip("._") or "document"
    if len(ascii_stem) > 80:
        ascii_stem = ascii_stem[:80]
    ascii_fallback = f"{ascii_stem}.docx"
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{star}"


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
        suffix = suffix_from_upload(
            file,
            frozenset({".md", ".markdown", ".txt"}),
            default=".md",
        )
        path = await save_upload_to_temp(file, settings, suffix=suffix)
        try:
            docx_bytes = await asyncio.to_thread(convert_markdown_path_to_docx, path, settings)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        out_name = _safe_download_filename(file.filename)
        return Response(
            content=docx_bytes,
            media_type=_DOCX_MEDIA,
            headers={"Content-Disposition": _content_disposition_attachment(out_name)},
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
