from __future__ import annotations

import logging
from pathlib import Path

from markitdown import MarkItDown

logger = logging.getLogger(__name__)


def convert_file_to_markdown(path: Path) -> tuple[str, str | None]:
    md = MarkItDown()
    result = md.convert(str(path))
    # Różne wersje markitdown: część eksponuje `markdown`, inne tylko `text_content`.
    markdown = (
        getattr(result, "markdown", None)
        or getattr(result, "text_content", None)
        or ""
    )
    title = getattr(result, "title", None)
    return markdown, title
