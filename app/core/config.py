from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="UTILS_", env_file=".env", extra="ignore")

    max_upload_bytes: int = Field(default=50 * 1024 * 1024, description="Maks. rozmiar pliku uploadu.")
    temp_dir: Path | None = Field(default=None, description="Katalog plików tymczasowych (domyślnie systemowy).")
    ocr_lang: str = Field(default="eng", description="Języki Tesseract, np. eng lub eng+pol.")
    ocr_dpi: int = Field(default=200, ge=72, le=400)
    # Jeśli tekst natywny jest krótszy niż ta liczba znaków na stronę (średnio), tryb auto użyje OCR.
    ocr_auto_chars_per_page_threshold: int = Field(default=30, ge=0)
    pandoc_timeout_sec: int = Field(
        default=120,
        ge=5,
        le=600,
        description="Timeout wywołania Pandoc (markdown → docx) w sekundach.",
    )
    plantuml_timeout_sec: int = Field(
        default=120,
        ge=5,
        le=600,
        description="Timeout wywołania PlantUML (render diagramu) w sekundach.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
