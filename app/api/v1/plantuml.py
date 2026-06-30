from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.core.uploads import save_upload_to_temp, suffix_from_upload
from app.services.plantuml_render import PlantumlSourceError, render_plantuml_path

router = APIRouter(tags=["plantuml"])

_MEDIA = {
    "svg": "image/svg+xml; charset=utf-8",
    "png": "image/png",
}


def _is_plantuml_like_upload(file: UploadFile) -> bool:
    ct = (file.content_type or "").lower()
    if ct in ("text/plain", "text/x-puml"):
        return True
    name = (file.filename or "").lower()
    return name.endswith((".puml", ".plantuml", ".pu", ".txt", ".iuml"))


@router.post("/plantuml-to-image")
async def plantuml_to_image_endpoint(
    file: Annotated[UploadFile, File(description="Źródło PlantUML (.puml, .plantuml, .txt).")],
    settings: Annotated[Settings, Depends(get_settings)],
    image_format: Annotated[
        Literal["svg", "png"],
        Query(alias="format", description="Format obrazu: svg (domyślnie) lub png."),
    ] = "svg",
) -> Response:
    if file.content_type and file.content_type not in (
        "text/plain",
        "text/x-puml",
        "application/octet-stream",
    ):
        if not _is_plantuml_like_upload(file):
            raise HTTPException(
                status_code=415,
                detail="Oczekiwany plik .puml / .plantuml / .pu / .txt lub typ text/plain.",
            )

    path: Path | None = None
    try:
        suffix = suffix_from_upload(
            file,
            frozenset({".puml", ".plantuml", ".pu", ".txt", ".iuml"}),
            default=".puml",
        )
        path = await save_upload_to_temp(file, settings, suffix=suffix)
        try:
            image_bytes = await asyncio.to_thread(render_plantuml_path, path, settings, image_format)
        except PlantumlSourceError as e:
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
