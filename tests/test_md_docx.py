import shutil

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_markdown_to_docx_returns_docx() -> None:
    client = TestClient(app)
    md_bytes = b"# Title\n\nHello from test.\n"
    res = client.post(
        "/v1/markdown-to-docx",
        files={"file": ("test.md", md_bytes, "text/markdown")},
    )
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument" in res.headers.get("content-type", "")
    assert len(res.content) > 2000
    assert res.content[:2] == b"PK"
    cd = res.headers.get("content-disposition") or ""
    assert "filename*=UTF-8''" in cd


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_markdown_to_docx_unicode_filename_header() -> None:
    client = TestClient(app)
    md_bytes = b"# Title\n\nUnicode filename.\n"
    res = client.post(
        "/v1/markdown-to-docx",
        files={"file": ("zażółć.md", md_bytes, "text/markdown")},
    )
    assert res.status_code == 200
    cd = res.headers.get("content-disposition") or ""
    assert "filename*=UTF-8''" in cd
    assert cd.encode("latin-1")
    assert "za%C5%BC%C3%B3%C5%82%C4%87.docx" in cd  # quoted UTF-8 stem + .docx
