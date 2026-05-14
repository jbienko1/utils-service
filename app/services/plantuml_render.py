from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal

from app.core.config import Settings

logger = logging.getLogger(__name__)


class PlantumlSourceError(Exception):
    """Błąd diagramu PlantUML (np. składnia) — mapowanie na HTTP 422."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _plantuml_command_line(path: Path, flag: str) -> list[str]:
    """
    Buduje argv dla subprocess. Na Windowsie CreateProcess nie uruchamia .bat/.cmd
    jako głównego obrazu procesu — wtedy używamy ``cmd /c`` (patrz WinError 2).
    """
    exe = shutil.which("plantuml")
    if not exe:
        raise RuntimeError(
            "Brak programu plantuml w PATH. Zainstaluj PlantUML (np. pakiet plantuml + JRE, "
            "na Debianie/Ubuntu: plantuml i graphviz) lub użyj obrazu Docker."
        )
    resolved = Path(exe).resolve()
    tail = ["-charset", "UTF-8", flag, str(path)]
    if sys.platform == "win32" and resolved.suffix.lower() in (".bat", ".cmd"):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", str(resolved), *tail]
    return [str(resolved), *tail]


def render_plantuml_path(
    path: Path,
    settings: Settings,
    image_format: Literal["svg", "png"],
) -> bytes:
    """
    Renderuje plik źródłowy PlantUML do SVG lub PNG (CLI `plantuml`).
    Usuwa plik wynikowy obok źródła po odczycie bajtów.
    """
    flag = "-tsvg" if image_format == "svg" else "-tpng"
    out_path = path.with_suffix(".svg" if image_format == "svg" else ".png")
    try:
        argv = _plantuml_command_line(path, flag)
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=float(settings.plantuml_timeout_sec),
            check=False,
            cwd=str(path.parent),
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip() or f"kod wyjścia {proc.returncode}"
            logger.warning("plantuml failed: %s", err)
            raise PlantumlSourceError(f"PlantUML: {err}")
        if not out_path.is_file():
            raise RuntimeError("PlantUML nie utworzył pliku wynikowego.")
        return out_path.read_bytes()
    finally:
        out_path.unlink(missing_ok=True)
