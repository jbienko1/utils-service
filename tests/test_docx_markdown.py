import base64
import json
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.services.docx_to_markdown import convert_docx_to_markdown
from app.services.markdown_ast_normalize import normalize_ast_for_gfm, normalize_markdown_html
from app.services.track_changes_postprocess import transform_track_changes_ast

FIXTURES = Path(__file__).resolve().parent / "fixtures"
TRACK_CHANGES_AST = FIXTURES / "track_changes_ast.json"


def _ensure_simple_docx() -> Path:
    path = FIXTURES / "simple.docx"
    if path.is_file():
        return path
    FIXTURES.mkdir(parents=True, exist_ok=True)
    md = FIXTURES / "simple.md"
    md.write_text("# Test\n\nHello world.\n", encoding="utf-8")
    subprocess.run(
        ["pandoc", str(md), "-o", str(path)],
        check=True,
        capture_output=True,
    )
    return path


def _ensure_docx_with_image() -> Path:
    path = FIXTURES / "with_image.docx"
    if path.is_file():
        return path
    FIXTURES.mkdir(parents=True, exist_ok=True)
    png = FIXTURES / "_build_image.png"
    png.write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000a49444154789c6300010000050001"
            "0d0e2db40000000049454e44ae426082"
        )
    )
    md = FIXTURES / "_build_image.md"
    md.write_text(f"![pic]({png.as_posix()})\n", encoding="utf-8")
    subprocess.run(["pandoc", str(md), "-o", str(path)], check=True, capture_output=True)
    return path


def test_transform_track_changes_ast_unit() -> None:
    ast = json.loads(TRACK_CHANGES_AST.read_text(encoding="utf-8"))
    out = transform_track_changes_ast(ast)
    blocks = out["blocks"]
    assert len(blocks) >= 5

    para0 = blocks[0]
    assert para0["t"] == "Para"
    text0 = json.dumps(para0)
    assert "insertion" not in text0
    assert "added" in text0

    para1 = blocks[1]
    assert para1["t"] == "Para"
    assert any(x.get("t") == "Strikeout" for x in para1["c"])

    code_blocks = [b for b in blocks if b.get("t") == "CodeBlock"]
    assert len(code_blocks) == 1
    code_text = code_blocks[0]["c"][1]
    assert "Jan Kowalski" in code_text
    assert "2024-05-09" in code_text
    assert "My comment." in code_text

    strong_para = blocks[4]
    assert strong_para["t"] == "Para"
    strong = next(x for x in strong_para["c"] if x.get("t") == "Strong")
    assert isinstance(strong["c"][0], dict)
    assert any(x.get("t") == "Strikeout" for x in strong["c"])


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_transform_ast_strong_roundtrip_pandoc() -> None:
    ast = json.loads(TRACK_CHANGES_AST.read_text(encoding="utf-8"))
    out = transform_track_changes_ast(ast)
    with tempfile.TemporaryDirectory() as tmp:
        ast_path = Path(tmp) / "ast.json"
        ast_path.write_text(json.dumps(out), encoding="utf-8")
        proc = subprocess.run(
            ["pandoc", str(ast_path), "-f", "json", "-t", "gfm", "--wrap=none"],
            capture_output=True,
            text=True,
            check=False,
        )
    assert proc.returncode == 0, proc.stderr
    assert "important" in proc.stdout
    assert "~~" in proc.stdout


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_normalize_ast_figure_to_image() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wd = Path(tmp)
        png = wd / "x.png"
        png.write_bytes(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                "0000000a49444154789c6300010000050001"
                "0d0e2db40000000049454e44ae426082"
            )
        )
        subprocess.run(
            ["pandoc", "-o", str(wd / "t.docx")],
            input=f"![pic]({png.as_posix()})\n".encode(),
            check=True,
        )
        subprocess.run(
            [
                "pandoc",
                str(wd / "t.docx"),
                "-f",
                "docx",
                "-t",
                "json",
                "--extract-media",
                str(wd),
                "-o",
                str(wd / "a.json"),
            ],
            check=True,
            capture_output=True,
        )
        ast = normalize_ast_for_gfm(json.loads((wd / "a.json").read_text(encoding="utf-8")))
        (wd / "b.json").write_text(json.dumps(ast), encoding="utf-8")
        proc = subprocess.run(
            ["pandoc", str(wd / "b.json"), "-f", "json", "-t", "gfm", "--wrap=none"],
            capture_output=True,
            text=True,
            check=False,
        )
    assert proc.returncode == 0, proc.stderr
    md = normalize_markdown_html(proc.stdout)
    assert "![](media/" in md
    assert "<figure>" not in md
    assert "<img" not in md


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_normalize_ast_link_roundtrip_pandoc() -> None:
    ast = {
        "pandoc-api-version": [1, 23, 1, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Para",
                "c": [
                    {"t": "Str", "c": "See "},
                    {
                        "t": "Link",
                        "c": [
                            ["", [], []],
                            [{"t": "Str", "c": "example"}],
                            ["https://example.com", "title"],
                        ],
                    },
                    {"t": "Str", "c": " for more."},
                ],
            }
        ],
    }
    out = normalize_ast_for_gfm(ast)
    link = out["blocks"][0]["c"][1]
    assert link["t"] == "Link"
    assert len(link["c"]) == 3
    with tempfile.TemporaryDirectory() as tmp:
        ast_path = Path(tmp) / "ast.json"
        ast_path.write_text(json.dumps(out), encoding="utf-8")
        proc = subprocess.run(
            ["pandoc", str(ast_path), "-f", "json", "-t", "gfm", "--wrap=none"],
            capture_output=True,
            text=True,
            check=False,
        )
    assert proc.returncode == 0, proc.stderr
    assert "example" in proc.stdout
    assert "https://example.com" in proc.stdout


def test_html_layout_table_to_stacked() -> None:
    html = (FIXTURES / "layout_table.html").read_text(encoding="utf-8")
    md = normalize_markdown_html(html)
    assert "<table>" not in md
    assert "![Shape](media/image4.png)" in md
    assert "> Niniejszy dokument stanowi **Instrukcję" in md
    assert "> Dokumentacja każdego procesu" in md
    assert "*Macierz RASCI" in md


def test_html_multirow_table_still_pipe() -> None:
    html = """
    <table>
    <tbody>
    <tr><th>A</th><th>B</th></tr>
    <tr><td>1</td><td>2</td></tr>
    </tbody>
    </table>
    """
    md = normalize_markdown_html(html)
    assert "<table>" not in md
    assert "| A | B |" in md
    assert "| 1 | 2 |" in md


def test_html_table_with_colspan_unchanged() -> None:
    html = '<table><tr><td colspan="2">merged</td></tr></table>'
    md = normalize_markdown_html(html)
    assert "<table>" in md
    assert "colspan" in md


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_docx_with_image_extract_media() -> None:
    path = _ensure_docx_with_image()
    settings = Settings()
    result = convert_docx_to_markdown(path, settings, comments=False, extract_media=True)
    assert result.media_count >= 1
    assert result.media_zip_base64 is not None
    assert "![](media/" in result.markdown
    assert "<figure>" not in result.markdown
    raw = base64.b64decode(result.media_zip_base64)
    with zipfile.ZipFile(BytesIO(raw)) as zf:
        names = zf.namelist()
    assert names
    assert all(not n.startswith("media/media/") for n in names)
    assert all(n.startswith("media/") for n in names)


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_docx_to_markdown_service_simple() -> None:
    path = _ensure_simple_docx()
    settings = Settings()
    result = convert_docx_to_markdown(path, settings, comments=False, extract_media=False)
    assert "Hello" in result.markdown
    assert result.media_count == 0
    assert result.media_zip_base64 is None


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_docx_to_markdown_api_simple() -> None:
    path = _ensure_simple_docx()
    client = TestClient(app)
    data = path.read_bytes()
    res = client.post(
        "/v1/docx-to-markdown?comments=false&extract_media=false",
        files={
            "file": (
                "simple.docx",
                data,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert "markdown" in body
    assert "Hello" in body["markdown"]
    assert body["media_zip_base64"] is None


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_docx_to_markdown_rejects_non_docx() -> None:
    client = TestClient(app)
    res = client.post(
        "/v1/docx-to-markdown",
        files={"file": ("test.md", b"# x", "text/markdown")},
    )
    assert res.status_code == 415


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_docx_to_markdown_extract_media_no_images() -> None:
    path = _ensure_simple_docx()
    settings = Settings()
    result = convert_docx_to_markdown(path, settings, comments=False, extract_media=True)
    assert result.media_count == 0
    assert result.media_zip_base64 is None


def test_zip_media_dir_structure() -> None:
    from app.services.docx_to_markdown import _zip_media_dir

    tmp = FIXTURES / "_zip_test_workdir"
    media = tmp / "media"
    media.mkdir(parents=True, exist_ok=True)
    try:
        (media / "img.png").write_bytes(b"\x89PNG\r\n")
        b64 = _zip_media_dir(tmp)
        raw = base64.b64decode(b64)
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            names = zf.namelist()
        assert names == ["media/img.png"]
    finally:
        (media / "img.png").unlink(missing_ok=True)
        media.rmdir()
        tmp.rmdir()
