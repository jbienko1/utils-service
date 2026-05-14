import shutil

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.skipif(not shutil.which("plantuml"), reason="PlantUML CLI not installed")
def test_plantuml_to_svg() -> None:
    client = TestClient(app)
    src = b"@startuml\nAlice -> Bob: hello\n@enduml\n"
    res = client.post(
        "/v1/plantuml-to-image?format=svg",
        files={"file": ("diagram.puml", src, "text/plain")},
    )
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers.get("content-type", "")
    body = res.content.decode("utf-8")
    assert "<svg" in body.lower() or "svg" in body.lower()


@pytest.mark.skipif(not shutil.which("plantuml"), reason="PlantUML CLI not installed")
def test_plantuml_to_png() -> None:
    client = TestClient(app)
    src = b"@startuml\nBob -> Alice: ok\n@enduml\n"
    res = client.post(
        "/v1/plantuml-to-image?format=png",
        files={"file": ("d.puml", src, "text/plain")},
    )
    assert res.status_code == 200
    assert "image/png" in res.headers.get("content-type", "")
    assert res.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_plantuml_rejects_non_source_extension() -> None:
    client = TestClient(app)
    res = client.post(
        "/v1/plantuml-to-image",
        files={"file": ("diagram.pdf", b"@startuml\n@enduml\n", "application/pdf")},
    )
    assert res.status_code == 415
