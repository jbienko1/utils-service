from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.core.uploads import save_upload_to_temp
from app.services.mermaid_render import MermaidSourceError, render_mermaid_path

router = APIRouter(tags=["mermaid"])

_MEDIA = {
    "svg": "image/svg+xml; charset=utf-8",
    "png": "image/png",
}


def _is_mermaid_like_upload(file: UploadFile) -> bool:
    ct = (file.content_type or "").lower()
    if ct in ("text/plain", "text/markdown"):
        return True
    name = (file.filename or "").lower()
    return name.endswith((".mmd", ".mermaid", ".md", ".txt"))


@router.post("/mermaid-to-image")
async def mermaid_to_image_endpoint(
    file: Annotated[UploadFile, File(description="Źródło Mermaid (.mmd, .mermaid, .md, .txt).")],
    settings: Annotated[Settings, Depends(get_settings)],
    image_format: Annotated[
        Literal["svg", "png"],
        Query(alias="format", description="Format obrazu: svg (domyślnie) lub png."),
    ] = "svg",
) -> Response:
    if file.content_type and file.content_type not in (
        "text/plain",
        "text/markdown",
        "application/octet-stream",
    ):
        if not _is_mermaid_like_upload(file):
            raise HTTPException(
                status_code=415,
                detail="Oczekiwany plik .mmd / .mermaid / .md / .txt lub typ text/plain / text/markdown.",
            )

    path: Path | None = None
    try:
        suffix = Path(file.filename or "diagram.mmd").suffix.lower()
        if suffix not in (".mmd", ".mermaid", ".md", ".txt", ""):
            suffix = ".mmd"
        path = await save_upload_to_temp(file, settings, suffix=suffix or ".mmd")
        try:
            image_bytes = render_mermaid_path(path, settings, image_format)
        except MermaidSourceError as e:
            raise HTTPException(status_code=422, detail=e.message) from e
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        return Response(
            content=image_bytes,
            media_type=_MEDIA[image_format],
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
