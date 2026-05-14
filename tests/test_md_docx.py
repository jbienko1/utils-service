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
