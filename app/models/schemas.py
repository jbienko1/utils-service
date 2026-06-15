from pydantic import BaseModel, Field


class PdfToTextResponse(BaseModel):
    text: str
    page_count: int
    used_ocr: bool = Field(description="True, gdy użyto Tesseract (wymuszenie lub tryb auto).")


class ToMarkdownResponse(BaseModel):
    markdown: str
    title: str | None = None


class DocxToMarkdownResponse(BaseModel):
    markdown: str
    title: str | None = None
    media_count: int = Field(default=0, description="Liczba plików w katalogu media/ po ekstrakcji.")
    media_zip_base64: str | None = Field(
        default=None,
        description="ZIP (base64) z katalogiem media/ — obecny tylko gdy extract_media=true i są obrazy.",
    )
