from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.core.config import Settings
from app.core.uploads import save_upload_to_temp, suffix_from_upload


def _upload(filename: str | None) -> MagicMock:
    f = MagicMock(spec=UploadFile)
    f.filename = filename
    return f


# --- suffix_from_upload ---

def test_suffix_known_extension_in_allowed() -> None:
    f = _upload("diagram.puml")
    result = suffix_from_upload(f, frozenset({".puml", ".txt"}), default=".puml")
    assert result == ".puml"


def test_suffix_unknown_extension_returns_default() -> None:
    f = _upload("diagram.pdf")
    result = suffix_from_upload(f, frozenset({".puml", ".txt"}), default=".puml")
    assert result == ".puml"


def test_suffix_no_extension_returns_default() -> None:
    f = _upload("noext")
    result = suffix_from_upload(f, frozenset({".puml"}), default=".puml")
    assert result == ".puml"


def test_suffix_none_filename_returns_default() -> None:
    f = _upload(None)
    result = suffix_from_upload(f, frozenset({".puml"}), default=".puml")
    assert result == ".puml"


def test_suffix_empty_allowed_returns_any_extension() -> None:
    """Gdy allowed jest puste, akceptujemy dowolne rozszerzenie z nazwy pliku."""
    f = _upload("report.xlsx")
    result = suffix_from_upload(f, frozenset(), default=".bin")
    assert result == ".xlsx"


def test_suffix_empty_allowed_no_ext_returns_default() -> None:
    f = _upload("noext")
    result = suffix_from_upload(f, frozenset(), default=".bin")
    assert result == ".bin"


def test_suffix_uppercase_normalized() -> None:
    f = _upload("Diagram.PUML")
    result = suffix_from_upload(f, frozenset({".puml"}), default=".puml")
    assert result == ".puml"


def test_suffix_mermaid_md_accepted() -> None:
    f = _upload("chart.md")
    result = suffix_from_upload(f, frozenset({".mmd", ".mermaid", ".md", ".txt"}), default=".mmd")
    assert result == ".md"


def test_suffix_markdown_txt_accepted() -> None:
    f = _upload("notes.txt")
    result = suffix_from_upload(f, frozenset({".md", ".markdown", ".txt"}), default=".md")
    assert result == ".txt"


# --- save_upload_to_temp: wczesne odrzucanie przez file.size ---

def _make_upload_file(content: bytes, size: int | None = None) -> MagicMock:
    f = MagicMock(spec=UploadFile)
    f.size = size if size is not None else len(content)
    data = iter([content, b""])
    f.read = AsyncMock(side_effect=lambda n: next(data))
    return f


@pytest.mark.asyncio
async def test_save_upload_rejects_by_content_length() -> None:
    """file.size > limit → ValueError przed transferem (nie czyta danych)."""
    settings = Settings(max_upload_bytes=10)
    f = _make_upload_file(b"x" * 20, size=20)
    with pytest.raises(ValueError, match="UTILS_MAX_UPLOAD_BYTES"):
        await save_upload_to_temp(f, settings, suffix=".bin")
    # read nie powinno być wywołane — odrzucenie przed transferem
    f.read.assert_not_called()


@pytest.mark.asyncio
async def test_save_upload_rejects_during_stream_when_no_content_length() -> None:
    """Brak file.size → rozmiar sprawdzany podczas odczytu chunks."""
    settings = Settings(max_upload_bytes=5)
    f = _make_upload_file(b"x" * 20, size=None)
    with pytest.raises(ValueError, match="UTILS_MAX_UPLOAD_BYTES"):
        await save_upload_to_temp(f, settings, suffix=".bin")


@pytest.mark.asyncio
async def test_save_upload_accepts_within_limit() -> None:
    settings = Settings(max_upload_bytes=1024)
    content = b"hello world"
    f = _make_upload_file(content)
    path = await save_upload_to_temp(f, settings, suffix=".txt")
    try:
        assert path.exists()
        assert path.read_bytes() == content
    finally:
        path.unlink(missing_ok=True)
