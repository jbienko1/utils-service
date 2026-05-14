# Instalacja i uruchamianie (utils-service)

Dokument skrócony dla człowieka. Skrót w repozytorium: [README.md](../../README.md). Zmienne środowiskowe: ta sama tabela co w README oraz sekcja poniżej.

## Wymagania wstępne

| Składnik | Kiedy potrzebny |
|----------|------------------|
| **Python 3.11+** | Zawsze |
| **Tesseract OCR** (+ pakiety językowe) | Tylko jeśli używasz `ocr=on` lub `ocr=auto` na PDF |
| **Pandoc** (w `PATH`) | Tylko dla `POST /v1/markdown-to-docx` |
| **Docker** (opcjonalnie) | Uruchomienie w kontenerze zgodnym z [Dockerfile](../../Dockerfile); w obrazie są m.in. Tesseract (dla OCR) i Pandoc (dla MD→DOCX) — **nie musisz** używać Dockera, jeśli masz te narzędzia lokalnie |

Na **Windows** Tesseract można zainstalować m.in. z [wikii UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki); upewnij się, że `tesseract` jest w `PATH` (lub skonfiguruj `pytesseract` — obecnie serwis zakłada domyślne wykrywanie binarki przez bibliotekę).

## Instalacja (środowisko wirtualne)

### Windows (PowerShell)

```powershell
cd ścieżka\do\utils-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

Opcjonalnie narzędzia deweloperskie:

```powershell
pip install -e ".[dev]"
```

### Linux / macOS (bash)

```bash
cd /ścieżka/do/utils-service
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Uruchomienie serwera deweloperskiego

Z aktywnym venv i **katalogiem roboczym ustawionym na root repozytorium** (tam gdzie jest `pyproject.toml`):

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Dlaczego `python -m uvicorn`: skrypt `uvicorn.exe` często trafia do `Scripts` poza `PATH` na Windowsie — forma modułowa zawsze używa interpretera z aktywnego venv.

**Adresy po starcie:**

| URL | Opis |
|-----|------|
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI (OpenAPI) |
| [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | ReDoc |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | Specyfikacja OpenAPI (JSON) |
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Szybki test liveness |

## Konfiguracja przez plik `.env` (opcjonalnie)

W katalogu głównym projektu możesz utworzyć plik `.env` (nie commituj go). `Settings` ładuje go automatycznie — prefiks zmiennych: **`UTILS_`**.

Przykład:

```env
UTILS_MAX_UPLOAD_BYTES=20971520
UTILS_OCR_LANG=eng+pol
UTILS_OCR_DPI=200
UTILS_PANDOC_TIMEOUT_SEC=120
UTILS_TEMP_DIR=C:\temp\utils-service
```

Pełna lista pól: `app/core/config.py`; tabela skrótowa: [README.md](../../README.md).

## Docker (produkcja / CI / spójne środowisko)

Z root repozytorium:

```bash
docker build -t utils-service .
docker run --rm -p 8000:8000 utils-service
```

Serwer nasłuchuje na porcie **8000** w kontenerze. Obraz instaluje m.in. Tesseract (angielski + polski) i **poppler-utils** (pomocniczo przy łańcuchach konwersji dokumentów).

## Weryfikacja po instalacji

```powershell
python -c "from app.main import app; print(app.title)"
curl http://127.0.0.1:8000/health
```

(lub `Invoke-WebRequest` w PowerShellu).

---

## Parametryzacja narzędzi konwersji

Pytanie brzmi zwykle: **czy biblioteki pod spodem da się „stroić”**, i **czy da się to zrobić z poziomu tej usługi REST**.

### Poziom HTTP (to, co dziś wystawiamy)

| Endpoint | Parametry z żądania |
|----------|---------------------|
| `POST /v1/pdf-to-text` | **`ocr`**: `off` / `on` / `auto` — wybór ścieżki natywnej vs OCR oraz heurystyki auto. |
| `POST /v1/to-markdown` | Tylko **plik** — brak dodatkowych query/body pod markitdown (uproszczenie kontraktu). |

### Poziom serwera (`UTILS_*` w `Settings`)

Dotyczy głównie **PDF + OCR** i limitów:

- `UTILS_OCR_LANG`, `UTILS_OCR_DPI`, `UTILS_OCR_AUTO_CHARS_PER_PAGE_THRESHOLD` — sterują zachowaniem Tesseract i progiem trybu `auto`.
- `UTILS_PANDOC_TIMEOUT_SEC` — limit czasu wywołania Pandoc przy `markdown-to-docx`.
- `UTILS_MAX_UPLOAD_BYTES`, `UTILS_TEMP_DIR` — limity i miejsce zapisu uploadu.

To są **parametry uruchomieniowe procesu** (jedna wartość na instancję serwera), a nie per-request — chyba że w przyszłości dodasz mapowanie nagłówków / kontekstu na ustawienia (obecnie nie ma).

### Poziom bibliotek (możliwości techniczne vs ten projekt)

- **PyMuPDF** — bogate API (np. wycinek stron, inne tryby ekstrakcji). W tym repozytorium używany jest **wąski podzbiór** (`get_text`, render pod OCR). Rozszerzenie = zmiana kodu w `app/services/pdf_extract.py`.
- **Tesseract (pytesseract)** — silnik obsługuje m.in. **język**, **PSM/ OEM** przez `config`, niestandardowe ścieżki do `tessdata`. Część jest pokryta przez `UTILS_OCR_LANG` / DPI; reszta wymagałaby **nowych pól w `Settings`** lub parametrów API.
- **markitdown** — konstruktor `MarkItDown(...)` i wywołania `convert*` przyjmują opcje (pluginy, integracje z Azure Document Intelligence, `StreamInfo` przy strumieniach itd.). Ten serwis tworzy **`MarkItDown()` domyślnie** i woła `convert(path)` — **brak wystawienia tych opcji w REST**. Można to dodać jako nowe pola query/body lub profile konfiguracyjne, jeśli zajdzie potrzeba.

**Podsumowanie:** narzędzia **pozwalają** na szeroką parametryzację na poziomie bibliotek; **w tej usłudze** na zewnątrz jest jawny parametr **`ocr`** dla PDF oraz **zmienne środowiskowe** dla OCR i limitów; **markitdown** jest uruchamiany w trybie domyślnym bez dodatkowych przełączników w API.
