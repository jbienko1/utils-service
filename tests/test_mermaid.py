import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.mermaid_render import is_mermaid_cli_available


def test_mermaid_rejects_non_source_extension() -> None:
    client = TestClient(app)
    res = client.post(
        "/v1/mermaid-to-image",
        files={"file": ("diagram.pdf", b"graph TD\nA-->B\n", "application/pdf")},
    )
    assert res.status_code == 415


@pytest.mark.skipif(not is_mermaid_cli_available(), reason="Mermaid CLI (mmdc) not available")
def test_mermaid_to_svg() -> None:
    client = TestClient(app)
    src = b"graph TD\n  A-->B\n"
    res = client.post(
        "/v1/mermaid-to-image?format=svg",
        files={"file": ("diagram.mmd", src, "text/plain")},
    )
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers.get("content-type", "")
    body = res.content.decode("utf-8")
    assert "<svg" in body.lower()


@pytest.mark.skipif(not is_mermaid_cli_available(), reason="Mermaid CLI (mmdc) not available")
def test_mermaid_to_png() -> None:
    client = TestClient(app)
    src = b"graph LR\n  X-->Y\n"
    res = client.post(
        "/v1/mermaid-to-image?format=png",
        files={"file": ("d.mmd", src, "text/plain")},
    )
    assert res.status_code == 200
    assert "image/png" in res.headers.get("content-type", "")
    assert res.content[:8] == b"\x89PNG\r\n\x1a\n"
