# Dokumentacja API (utils-service)

Instalacja i uruchomienie serwera (żeby działały adresy poniżej): [install-and-run.md](install-and-run.md).

## Standardy opisu API REST

W praktyce branżowej **de facto standardem** opisu HTTP/REST jest **OpenAPI Specification** (wcześniej „Swagger”):

- wersje **3.0.x** i **3.1** w formacie **YAML** lub **JSON**;
- opisuje ścieżki, metody, parametry, treść żądania/odpowiedzi, kody HTTP, schematy danych (często z odwołaniem do **JSON Schema**);
- z jednego pliku generuje się interaktywną dokumentację (**Swagger UI**, **ReDoc**, **Stoplight** itd.) oraz klienty i testy.

Powiązane (ogólniejsze) normy i konwencje:

- **RFC 9110** (HTTP Semantics) — semantyka metod, statusów, nagłówków (dokumentacja ludzka często odwołuje się do „kiedy 400 vs 422 vs 415”).
- **Problem Details for HTTP APIs** (**RFC 9457**, dawniej RFC 7807) — ujednolicony format błędu (`application/problem+json`). Ten serwis obecnie zwraca błędy FastAPI jako JSON z polem `detail`; pełna zgodność z RFC 9457 wymagałaby osobnego modelu odpowiedzi.

**AsyncAPI** dotyczy głównie zdarzeń / brokerów (nie klasycznego REST) — tutaj nie dotyczy.

### Jak to jest zrobione w tym projekcie

Aplikacja jest w **FastAPI**, które **automatycznie buduje specyfikację OpenAPI 3** i udostępnia:

| Zasób | Adres (po uruchomieniu lokalnie) |
|--------|----------------------------------|
| Specyfikacja OpenAPI (JSON) | `http://127.0.0.1:8000/openapi.json` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |

Ten plik (`api.md`) jest **dokumentacją towarzyszącą** dla człowieka; **źródłem prawdy dla kontraktu maszynowego** pozostaje wygenerowany OpenAPI (zsynchronizowany z kodem: modele Pydantic, typy odpowiedzi, parametry).

---

## Przegląd endpointów

### `GET /health`

**Cel:** sprawdzenie, czy proces odpowiada (liveness).

**Odpowiedź:** `200` — `application/json`

```json
{ "status": "ok" }
```

---

### `POST /v1/pdf-to-text`

**Cel:** wyciągnięcie tekstu z pliku PDF.

**Żądanie:**

- `Content-Type: multipart/form-data`
- pole formularza: **`file`** — plik PDF
- query: **`ocr`** — `off` (domyślnie) | `on` | `auto`
  - `off` — tylko tekst osadzony w PDF (PyMuPDF)
  - `on` — OCR (Tesseract) na każdej stronie
  - `auto` — OCR, gdy tekst natywny jest zbyt krótki (wg konfiguracji serwera)

**Odpowiedź:** `200` — `application/json` — schema `PdfToTextResponse`

| Pole | Typ | Znaczenie |
|------|-----|-----------|
| `text` | string | Wyekstrahowany tekst |
| `page_count` | integer | Liczba stron |
| `used_ocr` | boolean | Czy użyto Tesseract |

**Typowe błędy:**

| Kod | Kiedy |
|-----|--------|
| `413` | Plik większy niż `UTILS_MAX_UPLOAD_BYTES` |
| `415` | Content-Type nie wskazuje na PDF i nazwa pliku nie kończy się na `.pdf` |
| `503` | Wymuszone OCR (`on`) lub auto-OCR, a Tesseract / język niedostępny |

---

### `POST /v1/to-markdown`

**Cel:** konwersja obsługiwanego typu pliku do Markdown ([markitdown](https://github.com/microsoft/markitdown)).

**Żądanie:**

- `Content-Type: multipart/form-data`
- pole formularza: **`file`** — dokument (format zależny od możliwości markitdown)

**Odpowiedź:** `200` — `application/json` — schema `ToMarkdownResponse`

| Pole | Typ | Znaczenie |
|------|-----|-----------|
| `markdown` | string | Treść Markdown |
| `title` | string lub null | Opcjonalny tytuł z konwertera |

**Typowe błędy:**

| Kod | Kiedy |
|-----|--------|
| `413` | Przekroczony limit rozmiaru uploadu |
| `422` | Konwersja się nie powiodła (np. nieobsługiwany lub uszkodzony plik) |

---

### `POST /v1/markdown-to-docx`

**Cel:** konwersja pliku Markdown lub zwykłego tekstu do dokumentu **DOCX** ([Pandoc](https://pandoc.org/)).

**Żądanie:**

- `Content-Type: multipart/form-data`
- pole formularza: **`file`** — rozszerzenia `.md`, `.markdown`, `.txt` (lub typy `text/markdown`, `text/plain`; `application/octet-stream` jest akceptowane, jeśli zawartość jest zgodna z walidacją routera)

**Odpowiedź:** `200` — `application/vnd.openxmlformats-officedocument.wordprocessingml.document` — plik Word do pobrania; nagłówek `Content-Disposition` z polami `filename` (ASCII) oraz `filename*=UTF-8''…` (RFC 5987), żeby poprawna nazwa z polskimi znakami nie powodowała błędu kodowania nagłówka.

**Typowe błędy:**

| Kod | Kiedy |
|-----|--------|
| `413` | Przekroczony limit rozmiaru uploadu (`UTILS_MAX_UPLOAD_BYTES` — patrz [README.md](../../README.md)); zmniejsz plik lub zwiększ limit i zrestartuj serwer. |
| `415` | Nieprawidłowy typ MIME / rozszerzenie (oczekiwane Markdown / zwykły tekst) |
| `503` | Pandoc niedostępny w `PATH` lub błąd konwersji (komunikat w `detail`) |

---

### `POST /v1/plantuml-to-image`

**Cel:** renderowanie diagramu **PlantUML** do **SVG** lub **PNG** (CLI `plantuml`, wymaga JRE; wiele typów diagramów wymaga też **Graphviz** w `PATH`).

**Żądanie:**

- `Content-Type: multipart/form-data`
- pole formularza: **`file`** — `.puml`, `.plantuml`, `.pu`, `.iuml`, `.txt` (lub `text/plain` / `text/x-puml`)
- query **`format`**: `svg` (domyślnie) lub `png`

**Odpowiedź:** `200` — `image/svg+xml` (SVG) lub `image/png` (PNG).

**Uwaga bezpieczeństwa:** źródło PlantUML może zawierać dyrektywy typu `!include` / `!import` odczytujące pliki z dysku serwera. Nie przekazuj niezaufanego źródła na produkcji bez izolacji.

**Typowe błędy:**

| Kod | Kiedy |
|-----|--------|
| `413` | Przekroczony limit rozmiaru uploadu |
| `415` | Nieprawidłowy typ MIME / rozszerzenie |
| `422` | Błąd składni lub przetwarzania diagramu (stderr PlantUML) |
| `503` | Brak `plantuml` w `PATH` lub brak pliku wynikowego |

---

### `POST /v1/mermaid-to-image`

**Cel:** renderowanie diagramu **Mermaid** do **SVG** lub **PNG** ([Mermaid CLI](https://github.com/mermaid-js/mermaid-cli), `mmdc`; pod spodem Puppeteer / headless Chrome).

**Żądanie:**

- `Content-Type: multipart/form-data`
- pole formularza: **`file`** — `.mmd`, `.mermaid`, `.md`, `.txt` (lub `text/plain` / `text/markdown`)
- query **`format`**: `svg` (domyślnie) lub `png`

**Odpowiedź:** `200` — `image/svg+xml` (SVG) lub `image/png` (PNG).

**Konfiguracja przeglądarki:** przy ustawieniu `UTILS_PUPPETEER_EXECUTABLE_PATH` serwis przekazuje do `mmdc` zmienną `PUPPETEER_EXECUTABLE_PATH` oraz `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true` (brak pobierania Chromium z sieci). W Dockerze ustaw ścieżkę do zainstalowanego w obrazie Chromium/Chrome.

**Typowe błędy:**

| Kod | Kiedy |
|-----|--------|
| `413` | Przekroczony limit rozmiaru uploadu |
| `415` | Nieprawidłowy typ MIME / rozszerzenie |
| `422` | Błąd składni lub renderu (stderr `mmdc`) |
| `503` | Brak `mmdc` (lokalnie: `cd mermaid-cli && npm install`) lub brak pliku wynikowego / brak działającej przeglądarki dla Puppeteer |

---

## Wersjonowanie

Prefiks **`/v1`** zarezerwowany jest na stabilny publiczny kontrakt. Ewentualne zmiany niezgodne wstecz powinny iść pod **`/v2`**, nie podmieniając zachowania `/v1`.

---

## Uwagi dla integracji

- **Brak uwierzytelniania** w szkielecie — jeśli usługa jest wystawiona poza zaufanyą siecią, należy ją chronić (np. API gateway, mTLS, VPN).
- **Limity rozmiaru** — konfigurowalne przez `UTILS_MAX_UPLOAD_BYTES` (patrz główny `README.md`).
