# Architektura utils-service

## Cel systemu

**utils-service** to lekka aplikacja HTTP (REST) udostępniająca zestaw małych, niezależnych usług pomocniczych. Obecnie:

1. **PDF → tekst** — ekstrakcja tekstu z pliku PDF.
2. **Plik → Markdown** — konwersja obsługiwanych formatów do Markdown za pomocą biblioteki Microsoft **markitdown**.
3. **Markdown → DOCX** — konwersja `.md` / `.markdown` / `.txt` do dokumentu Word przez **Pandoc** (binarka w `PATH` lub w obrazie Docker).

Usługa jest **bezstanowa**: nie przechowuje trwale uploadów; przetwarzanie odbywa się na plikach tymczasowych usuwanych po żądaniu.

## Stos technologiczny

| Warstwa | Technologia |
|---------|-------------|
| HTTP / API | [FastAPI](https://fastapi.tiangolo.com/) |
| Serwer ASGI | [Uvicorn](https://www.uvicorn.org/) |
| Konfiguracja | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (prefiks `UTILS_`) |
| PDF (tekst natywny) | [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`) |
| PDF (OCR) | [Tesseract](https://github.com/tesseract-ocr/tesseract) przez [pytesseract](https://github.com/madmaze/pytesseract); render stron do obrazu przez PyMuPDF + [Pillow](https://python-pillow.org/) |
| Konwersja do Markdown | [markitdown](https://github.com/microsoft/markitdown) |
| Markdown → DOCX | [Pandoc](https://pandoc.org/) (CLI, `subprocess`) |

## Widok logiczny (moduły)

```mermaid
flowchart TB
  subgraph http [Warstwa_HTTP]
    main[main.py]
    r_pdf[api_v1_pdf]
    r_md[api_v1_markdown]
    r_docx[api_v1_md_docx]
  end
  subgraph core [Warstwa_rdzenia]
    cfg[core_config]
    upl[core_uploads]
  end
  subgraph svc [Warstwa_uslug]
    pdfx[services_pdf_extract]
    mdc[services_markitdown_convert]
    pandoc[services_md_to_docx]
  end
  main --> r_pdf
  main --> r_md
  main --> r_docx
  r_pdf --> cfg
  r_pdf --> upl
  r_pdf --> pdfx
  r_md --> cfg
  r_md --> upl
  r_md --> mdc
  r_docx --> cfg
  r_docx --> upl
  r_docx --> pandoc
  r_pdf --> schemas[models_schemas]
  r_md --> schemas
```

## Struktura katalogów `app/`

| Ścieżka | Rola |
|---------|------|
| `app/main.py` | Tworzenie aplikacji FastAPI, rejestracja routerów pod `/v1`, endpoint `GET /health`. |
| `app/api/v1/pdf.py` | `POST /v1/pdf-to-text` — upload PDF, parametr zapytania `ocr`. |
| `app/api/v1/markdown.py` | `POST /v1/to-markdown` — upload pliku do konwersji. |
| `app/api/v1/md_docx.py` | `POST /v1/markdown-to-docx` — upload `.md` / `.markdown` / `.txt`, odpowiedź binarna DOCX. |
| `app/core/config.py` | `Settings`: limity, katalog temp, język i DPI OCR, próg trybu `auto`, timeout Pandoc. |
| `app/core/uploads.py` | Zapis strumienia uploadu do pliku tymczasowego z limitem rozmiaru. |
| `app/services/pdf_extract.py` | Ekstrakcja tekstu (natywnie / OCR / auto). |
| `app/services/markitdown_convert.py` | Wywołanie `MarkItDown` na ścieżce pliku. |
| `app/services/md_to_docx.py` | Wywołanie `pandoc` (wejście Markdown, wyjście DOCX w pamięci). |
| `app/models/schemas.py` | Modele odpowiedzi JSON (`PdfToTextResponse`, `ToMarkdownResponse`). |

## Przepływ żądania (upload → odpowiedź)

```mermaid
sequenceDiagram
  participant Klient
  participant Router
  participant Uploads
  participant Serwis
  participant FS as Plik_tymczasowy

  Klient->>Router: POST multipart file
  Router->>Uploads: save_upload_to_temp
  Uploads->>FS: zapis chunkami do limitu
  Uploads-->>Router: Path
  Router->>Serwis: extract / convert / pandoc Path
  Serwis-->>Router: wynik
  Router->>FS: unlink w finally
  Router-->>Klient: JSON lub plik binarny
```

## Endpointy (kontrakt wysokiego poziomu)

| Metoda i ścieżka | Wejście | Wyjście |
|------------------|---------|---------|
| `GET /health` | — | `{"status":"ok"}` |
| `POST /v1/pdf-to-text` | `multipart/form-data`: pole `file`; query `ocr`: `off` / `on` / `auto` | JSON: `text`, `page_count`, `used_ocr` |
| `POST /v1/to-markdown` | `multipart/form-data`: pole `file` | JSON: `markdown`, `title` (opcjonalnie) |
| `POST /v1/markdown-to-docx` | `multipart/form-data`: pole `file` (`.md`, `.markdown`, `.txt` lub odpowiedni `Content-Type`) | `200`: treść DOCX (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`), nagłówek `Content-Disposition: attachment` |

Kody błędów typowe: `413` (przekroczony rozmiar), `415` (nie-PDF przy PDF lub niewłaściwy typ przy MD→DOCX), `422` (błąd konwersji markitdown), `503` (np. wymuszone OCR bez działającego Tesseract, lub brak/nie działa Pandoc przy MD→DOCX).

## Logika PDF i OCR

- **`ocr=off`**: wyłącznie tekst osadzony w PDF (`page.get_text()`).
- **`ocr=on`**: każda strona renderowana do bitmapy, następnie Tesseract (`pytesseract.image_to_string`). Wymaga zainstalowanego silnika Tesseract i pakietów językowych zgodnych z `UTILS_OCR_LANG`.
- **`ocr=auto`**: jeśli ekstrakcja natywna daje mało znaków w stosunku do liczby stron (próg `UTILS_OCR_AUTO_CHARS_PER_PAGE_THRESHOLD`), próbuje OCR; przy niepowodzeniu OCR wraca do tekstu natywnego i `used_ocr=false`.

## Konfiguracja środowiska

Wszystkie zmienne mają prefiks **`UTILS_`** (patrz `Settings` w `app/core/config.py` oraz tabela w głównym `README.md`):

- limit rozmiaru uploadu,
- opcjonalny katalog plików tymczasowych,
- parametry OCR (język, DPI, próg auto),
- timeout Pandoc (`UTILS_PANDOC_TIMEOUT_SEC`).

## Wdrożenie kontenerowe

[Dockerfile](../../Dockerfile) bazuje na obrazie Python slim (Debian), instaluje m.in. **tesseract-ocr** (pakiety językowe eng/pol), **pandoc** (Markdown→DOCX) oraz **poppler-utils** (często wymagane lub pomocnicze przy łańcuchach konwersji dokumentów). Aplikacja startuje jako `uvicorn app.main:app` na porcie `8000`.

Instrukcja krok po kroku (build, run, porty): [install-and-run.md](install-and-run.md).

## Rozszerzalność

Nowe „małe usługi” dodaje się przez:

1. nowy router w `app/api/v1/`,
2. opcjonalnie nowy moduł w `app/services/`,
3. wpis w `app/main.py`.

Prefiks wersjonowania API (`/v1`) pozwala w przyszłości wprowadzić `/v2` bez łamania istniejących klientów.

## Dokumentacja API

- Opis dla człowieka (endpointy, kody błędów, standardy): [api.md](api.md).
- **OpenAPI 3** generowane przez FastAPI: po uruchomieniu serwera `/openapi.json`, interfejsy `/docs` (Swagger UI) oraz `/redoc` (ReDoc).

## Bezpieczeństwo i eksploatacja (uwagi)

- Brak uwierzytelniania w szkielecie — jeśli usługa jest publiczna, należy umieścić ją za reverse proxy z kontrolą dostępu / rate limitem.
- Limity rozmiaru pliku ograniczają ryzyko wyczerpania pamięci; przy dużych PDF-ach OCR jest kosztowny obliczeniowo — warto monitorować timeouty i obciążenie CPU.
