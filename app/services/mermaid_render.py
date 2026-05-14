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


class MermaidSourceError(Exception):
    """Błąd składni / renderu Mermaid (stderr mmdc) — mapowanie na HTTP 422."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _local_mmdc_path() -> Path | None:
    base = _repo_root() / "mermaid-cli" / "node_modules" / ".bin"
    if sys.platform == "win32":
        for name in ("mmdc.cmd", "mmdc.exe", "mmdc"):
            p = base / name
            if p.is_file():
                return p
    else:
        p = base / "mmdc"
        if p.is_file():
            return p
    return None


def _resolve_mmdc() -> Path:
    local = _local_mmdc_path()
    if local is not None:
        return local.resolve()
    found = shutil.which("mmdc")
    if found:
        return Path(found).resolve()
    raise RuntimeError(
        "Brak Mermaid CLI (`mmdc`). W katalogu projektu uruchom: `cd mermaid-cli && npm install`, "
        "albo zainstaluj globalnie: `npm install -g @mermaid-js/mermaid-cli`."
    )


def is_mermaid_cli_available() -> bool:
    try:
        _resolve_mmdc()
        return True
    except RuntimeError:
        return False


def _mmdc_argv(mmdc: Path, in_path: Path, out_path: Path) -> list[str]:
    tail = ["-i", str(in_path), "-o", str(out_path)]
    if sys.platform == "win32" and mmdc.suffix.lower() in (".bat", ".cmd"):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", str(mmdc), *tail]
    return [str(mmdc), *tail]


def _mermaid_subprocess_env(settings: Settings) -> dict[str, str]:
    env = dict(os.environ)
    if settings.puppeteer_executable_path is not None:
        env["PUPPETEER_EXECUTABLE_PATH"] = str(settings.puppeteer_executable_path.resolve())
        env["PUPPETEER_SKIP_CHROMIUM_DOWNLOAD"] = "true"
    return env


def render_mermaid_path(
    path: Path,
    settings: Settings,
    image_format: Literal["svg", "png"],
) -> bytes:
    """
    Renderuje plik źródłowy Mermaid (mmdc). Usuwa plik wynikowy po odczycie.
    Wymaga Node + @mermaid-js/mermaid-cli; przeglądarkę podaje UTILS_PUPPETEER_EXECUTABLE_PATH
    (lub domyślne pobranie Chromium przez Puppeteer, jeśli nie ustawiono SKIP — niezalecane w Dockerze).
    """
    mmdc = _resolve_mmdc()
    out_suffix = ".svg" if image_format == "svg" else ".png"
    out_path = path.with_suffix(out_suffix)
    argv = _mmdc_argv(mmdc, path, out_path)
    env = _mermaid_subprocess_env(settings)
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=float(settings.mermaid_timeout_sec),
            check=False,
            cwd=str(path.parent),
            env=env,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip() or f"kod wyjścia {proc.returncode}"
            logger.warning("mmdc failed: %s", err)
            raise MermaidSourceError(f"Mermaid: {err}")
        if not out_path.is_file():
            raise RuntimeError("Mermaid CLI nie utworzył pliku wynikowego.")
        return out_path.read_bytes()
    finally:
        out_path.unlink(missing_ok=True)
