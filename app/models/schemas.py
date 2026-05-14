from pydantic import BaseModel, Field


class PdfToTextResponse(BaseModel):
    text: str
    page_count: int
    used_ocr: bool = Field(description="True, gdy użyto Tesseract (wymuszenie lub tryb auto).")


class ToMarkdownResponse(BaseModel):
    markdown: str
    title: str | None = None
