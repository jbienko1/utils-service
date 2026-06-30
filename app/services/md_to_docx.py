from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import Settings

logger = logging.getLogger(__name__)


def convert_markdown_path_to_docx(path: Path, settings: Settings) -> bytes:
    """
    Konwertuje plik Markdown na DOCX przez Pandoc.
    Zwraca bajty pliku .docx.
    """
    if not shutil.which("pandoc"):
        raise RuntimeError(
            "Brak programu Pandoc w PATH. Zainstaluj Pandoc (https://pandoc.org/installing.html) "
            "lub użyj obrazu Docker z zainstalowanym pandoc."
        )

    out_dir = settings.temp_dir
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    fd_out, out_raw = tempfile.mkstemp(suffix=".docx", dir=out_dir)
    os.close(fd_out)
    out_path = Path(out_raw)
    try:
        proc = subprocess.run(
            [
                "pandoc",
                "-f",
                "markdown",
                "-t",
                "docx",
                "-o",
                str(out_path),
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=float(settings.pandoc_timeout_sec),
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip() or f"kod wyjścia {proc.returncode}"
            logger.warning("pandoc failed: %s", err)
            raise RuntimeError(f"Konwersja Pandoc nie powiodła się: {err}")
        return out_path.read_bytes()
    finally:
        out_path.unlink(missing_ok=True)
