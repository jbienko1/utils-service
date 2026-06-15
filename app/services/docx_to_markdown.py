from __future__ import annotations

import base64
import io
import json
import logging
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.services.markdown_ast_normalize import normalize_ast_for_gfm, normalize_markdown_html
from app.services.track_changes_postprocess import meta_title, transform_track_changes_ast

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocxToMarkdownResult:
    markdown: str
    title: str | None
    media_count: int
    media_zip_base64: str | None


def convert_docx_to_markdown(
    path: Path,
    settings: Settings,
    *,
    comments: bool = True,
    extract_media: bool = False,
) -> DocxToMarkdownResult:
    if not shutil.which("pandoc"):
        raise RuntimeError(
            "Brak programu Pandoc w PATH. Zainstaluj Pandoc (https://pandoc.org/installing.html) "
            "lub użyj obrazu Docker z zainstalowanym pandoc."
        )

    timeout = float(settings.pandoc_timeout_sec)
    with tempfile.TemporaryDirectory() as tmp_raw:
        work_dir = Path(tmp_raw)
        ast_path = work_dir / "ast.json"
        md_path = work_dir / "output.md"
        media_root = work_dir / "media"

        track = "all" if comments else "accept"
        cmd_read: list[str] = [
            "pandoc",
            str(path),
            "-f",
            "docx",
            "-t",
            "json",
            f"--track-changes={track}",
            "-o",
            str(ast_path),
        ]
        if extract_media:
            cmd_read.extend(["--extract-media", str(work_dir)])

        _run_pandoc(cmd_read, timeout, work_dir)

        ast = json.loads(ast_path.read_text(encoding="utf-8"))
        if comments:
            ast = transform_track_changes_ast(ast)
        ast = normalize_ast_for_gfm(ast)
        ast_path.write_text(json.dumps(ast), encoding="utf-8")

        cmd_write = [
            "pandoc",
            str(ast_path),
            "-f",
            "json",
            "-t",
            "gfm",
            "--wrap=none",
            "-o",
            str(md_path),
        ]
        _run_pandoc(cmd_write, timeout, work_dir)

        markdown = normalize_markdown_html(md_path.read_text(encoding="utf-8"))
        title = meta_title(ast)
        media_count = 0
        media_zip_base64: str | None = None
        if extract_media and media_root.is_dir():
            files = [p for p in media_root.rglob("*") if p.is_file()]
            media_count = len(files)
            if media_count > 0:
                media_zip_base64 = _zip_media_dir(work_dir)

        return DocxToMarkdownResult(
            markdown=markdown,
            title=title,
            media_count=media_count,
            media_zip_base64=media_zip_base64,
        )


def _run_pandoc(cmd: list[str], timeout: float, cwd: Path) -> None:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(cwd),
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"kod wyjścia {proc.returncode}"
        logger.warning("pandoc failed: %s", err)
        raise RuntimeError(f"Konwersja Pandoc nie powiodła się: {err}")


def _zip_media_dir(work_dir: Path) -> str:
    media_root = work_dir / "media"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(media_root.rglob("*")):
            if not file_path.is_file():
                continue
            arcname = file_path.relative_to(work_dir)
            zf.write(file_path, arcname.as_posix())
    return base64.b64encode(buf.getvalue()).decode("ascii")
