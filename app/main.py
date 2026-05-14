from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.v1 import markdown, md_docx, pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="utils-service",
    description="Drobne usługi REST: PDF → tekst, pliki → Markdown, Markdown → DOCX (Pandoc).",
    version="0.1.0",
)

app.include_router(pdf.router, prefix="/v1")
app.include_router(markdown.router, prefix="/v1")
app.include_router(md_docx.router, prefix="/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
