from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Literal

import fitz
from PIL import Image

from app.core.config import Settings

logger = logging.getLogger(__name__)


def extract_native_text(path: Path) -> tuple[str, int]:
    doc = fitz.open(path)
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text())
        return "\n\n".join(parts), doc.page_count
    finally:
        doc.close()


def extract_ocr_text(path: Path, settings: Settings) -> tuple[str, int]:
    import pytesseract

    doc = fitz.open(path)
    try:
        parts: list[str] = []
        for page in doc:
            pix = page.get_pixmap(dpi=settings.ocr_dpi)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            parts.append(pytesseract.image_to_string(img, lang=settings.ocr_lang))
        return "\n\n".join(parts), doc.page_count
    finally:
        doc.close()


def _should_use_auto_ocr(native_text: str, page_count: int, settings: Settings) -> bool:
    if page_count <= 0:
        return False
    stripped = native_text.strip()
    if not stripped:
        return True
    threshold = settings.ocr_auto_chars_per_page_threshold * page_count
    return len(stripped) < threshold


def extract_pdf_text(
    path: Path,
    settings: Settings,
    ocr: Literal["off", "on", "auto"] = "off",
) -> tuple[str, int, bool]:
    """
    Zwraca (tekst, liczba_stron, uzyto_ocr).
    """
    native, page_count = extract_native_text(path)

    if ocr == "on":
        try:
            ocr_text, pc = extract_ocr_text(path, settings)
            return ocr_text, pc, True
        except Exception as e:
            logger.exception("OCR failed")
            raise RuntimeError(
                "OCR nie powiódł się. Upewnij się, że zainstalowany jest silnik Tesseract "
                "i pakiety językowe zgodne z UTILS_OCR_LANG."
            ) from e

    if ocr == "auto":
        if _should_use_auto_ocr(native, page_count, settings):
            try:
                ocr_text, pc = extract_ocr_text(path, settings)
                return ocr_text, pc, True
            except Exception as e:
                logger.warning("Auto OCR failed, falling back to native text: %s", e)
                return native, page_count, False
        return native, page_count, False

    return native, page_count, False
