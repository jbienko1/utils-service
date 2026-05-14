# utils-service

Lekka usługa **FastAPI** z małymi endpointami REST:

- `POST /v1/pdf-to-text` — tekst z PDF (PyMuPDF); opcjonalnie **OCR** (Tesseract).
- `POST /v1/to-markdown` — konwersja obsługiwanych typów plików do Markdown ([markitdown](https://github.com/microsoft/markitdown)).
- `POST /v1/markdown-to-docx` — konwersja Markdown / tekstu do DOCX (**Pandoc**).
- `POST /v1/plantuml-to-image` — wizualizacja diagramu **PlantUML** (SVG lub PNG).

## Dokumentacja

- Architektura i dokumentacja dla człowieka (backend): [app/docs/README.md](app/docs/README.md) — m.in. [install-and-run.md](app/docs/install-and-run.md), [architecture.md](app/docs/architecture.md), [api.md](app/docs/api.md).
- Wzorzec dodawania usługi REST + strony w kliencie: [docs/SERVICE_AND_CLIENT_PATTERN.md](docs/SERVICE_AND_CLIENT_PATTERN.md).
- Klient WWW (front): [client/docs/README.md](client/docs/README.md) — [install-and-run.md](client/docs/install-and-run.md), [AGENTS.md](client/docs/AGENTS.md).
- Instrukcje dla kolejnych agentów AI: [AGENTS.md](AGENTS.md) oraz [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md).

## Wymagania

- Python **3.11+**
- Do OCR: zainstalowany **Tesseract** oraz pakiety językowe zgodne z `UTILS_OCR_LANG` (np. na Windows instalator z [GitHub Tesseract](https://github.com/UB-Mannheim/tesseract/wiki); w Dockerze obraz instaluje `tesseract-ocr` + `eng` + `pol`).
- Do **Markdown → DOCX:** zainstalowany [**Pandoc**](https://pandoc.org/installing.html) w `PATH` (w obrazie Docker `pandoc` jest dołączony w Dockerfile). **Docker nie jest obowiązkowy** — możesz pracować lokalnie z Pandoc + `uvicorn` tak jak z innymi narzędziami.
- Do **PlantUML → obraz:** w `PATH` muszą być **`plantuml`** (zwykle z JRE) oraz **`dot`** z pakietu **Graphviz** (w Dockerze instalowane w Dockerfile).

## Instalacja i uruchomienie

Szczegółowa instrukcja (venv, Windows/Linux, Docker, `.env`, weryfikacja, **parametryzacja konwerterów**): [app/docs/install-and-run.md](app/docs/install-and-run.md).

Skrót (PowerShell):

```powershell
cd ścieżka\do\utils-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI / Swagger UI: `http://127.0.0.1:8000/docs`.

### Docker

Z katalogu repozytorium (po zbudowaniu obrazu):

```powershell
docker build -t utils-service .
docker run --rm -p 8000:8000 utils-service
```

## Klient WWW (`client/`)

Osobna aplikacja Vite + TypeScript: nawigacja **hash** (`#/`, `#/pdf-to-text`, `#/to-markdown`, `#/markdown-to-docx`, `#/plantuml`). Szczegóły: [client/docs/install-and-run.md](client/docs/install-and-run.md).

## Endpointy (skrót)

Odpowiedź JSON dla PDF: `text`, `page_count`, `used_ocr`. Dla `to-markdown`: `markdown`, `title` (opcjonalnie).

### `POST /v1/markdown-to-docx`

- Formularz: pole `file` — `.md`, `.markdown` lub `.txt` (albo `text/markdown` / `text/plain`).
- Odpowiedź: `200` — plik **DOCX** (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`), nagłówek `Content-Disposition: attachment`.

### `POST /v1/plantuml-to-image`

- Formularz: pole `file` — źródło `.puml` / `.plantuml` / `.txt` itd.; query **`format`**: `svg` (domyślnie) lub `png`.
- Odpowiedź: `200` — treść **SVG** lub **PNG**.

### `GET /health`

`{"status":"ok"}`.

## Zmienne środowiskowe (`UTILS_*`)

| Zmienna | Znaczenie | Domyślnie |
|---------|-----------|-----------|
| `UTILS_MAX_UPLOAD_BYTES` | Maks. rozmiar uploadu (bajty) | `52428800` (50 MiB) |
| `UTILS_TEMP_DIR` | Katalog plików tymczasowych (opcjonalnie) | (systemowy) |
| `UTILS_OCR_LANG` | Języki Tesseract, np. `eng+pol` | `eng` |
| `UTILS_OCR_DPI` | DPI renderu stron przy OCR | `200` |
| `UTILS_OCR_AUTO_CHARS_PER_PAGE_THRESHOLD` | W trybie `ocr=auto`: jeśli średnio mniej znaków na stronę niż ta wartość, uruchamiany jest OCR | `30` |
| `UTILS_PANDOC_TIMEOUT_SEC` | Timeout wywołania Pandoc (`markdown-to-docx`), sekundy | `120` |
| `UTILS_PLANTUML_TIMEOUT_SEC` | Timeout wywołania PlantUML (`plantuml-to-image`), sekundy | `120` |

Pełniejszy opis: [app/docs/install-and-run.md](app/docs/install-and-run.md) oraz [app/docs/architecture.md](app/docs/architecture.md).
