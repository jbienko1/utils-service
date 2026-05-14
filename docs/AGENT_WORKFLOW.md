# Workflow agenta — utils-service

Szczegóły dla agentów implementujących lub rozszerzających repozytorium.

## Model architektoniczny

- **Router** (`app/api/v1/*.py`): parametry żądania, `Depends(get_settings)`, mapowanie wyjątków na `HTTPException`, brak bezpośredniego I/O poza wywołaniem serwisu / `uploads`.
- **Serwis** (`app/services/*.py`): czysta logika (ścieżki `Path`, biblioteki zewnętrzne). Zwraca dane lub rzuca wyjątki sensowne dla warstwy API.
- **Core** (`app/core/`): konfiguracja globalna, helpery współdzielone (upload do temp).

```text
HTTP  →  api/v1/*  →  services/*  →  biblioteki (fitz, markitdown, pytesseract, pandoc, plantuml)
              ↓
         core/config, core/uploads
```

## Dodawanie nowego endpointu `/v1/...`

Szczegółowa checklista (backend + klient + docs): [SERVICE_AND_CLIENT_PATTERN.md](SERVICE_AND_CLIENT_PATTERN.md).

1. Utwórz router w `app/api/v1/<nazwa>.py` (`APIRouter(tags=[...])`).
2. Zarejestruj w `app/main.py`: `app.include_router(<moduł>.router, prefix="/v1")`.
3. Jeśli potrzebna logika biznesowa — nowy moduł w `app/services/`.
4. Modele JSON odpowiedzi — dopisz do `app/models/schemas.py` i użyj `response_model=`.
5. Uzupełnij dokumentację zgodnie z sekcją [Aktualizacja dokumentacji po zmianach](#aktualizacja-dokumentacji-po-zmianach) (obowiązkowo m.in. przy zmianie kontraktu HTTP lub kodów odpowiedzi).

## Aktualizacja dokumentacji po zmianach

**Zasada:** dokumentacja jest częścią dostarczenia — agent **aktualizuje ją razem z kodem**, zanim uzna zadanie za zakończone.

| Zmiana w kodzie | Zaktualizuj m.in. |
|-----------------|-------------------|
| Endpointy, parametry, odpowiedzi, kody błędów | [app/docs/api.md](../app/docs/api.md); opisy w kodzie (`summary` / `description`, tagi OpenAPI); upewnij się, że `/docs` i `/openapi.json` są spójne z intencją. |
| Nowe lub zmienione przepływy / moduły | [app/docs/architecture.md](../app/docs/architecture.md); ewent. diagramy Mermaid. |
| Nowe lub zmienione `UTILS_*` / `.env` | [README.md](../README.md) (tabela zmiennych); [app/docs/architecture.md](../app/docs/architecture.md) (sekcja konfiguracji); [app/docs/install-and-run.md](../app/docs/install-and-run.md) (przykład `.env`). |
| Docker / zależności systemowe | [Dockerfile](../Dockerfile); [README.md](../README.md); [app/docs/install-and-run.md](../app/docs/install-and-run.md) (Docker, Tesseract). |
| Zmiany w `client/` (front) | [client/docs/README.md](../client/docs/README.md), [client/docs/install-and-run.md](../client/docs/install-and-run.md), [client/docs/AGENTS.md](../client/docs/AGENTS.md); skrót [client/README.md](../client/README.md); ewent. [README.md](../README.md) (sekcja „Klient WWW”). |
| Nowa usługa (pełny przepływ backend + front) | [docs/SERVICE_AND_CLIENT_PATTERN.md](SERVICE_AND_CLIENT_PATTERN.md) — upewnij się, że checklista jest spełniona. |

**Indeks** dokumentacji dla człowieka: [app/docs/README.md](../app/docs/README.md) oraz [client/docs/README.md](../client/docs/README.md) (front). Nie zostawiaj rozjazdu między kodem a `api.md` / `README.md` / `install-and-run.md` (backend) ani `client/docs/*` (front).

## Konfiguracja (`UTILS_*`)

Źródło prawdy: `app/core/config.py` (`Settings`).

- Nowe pole: dodaj do `Settings` z sensownym `default` i opisem w `Field`.
- Dokumentacja dla człowieka: zsynchronizuj [README.md](../README.md) (sekcja zmiennych), [app/docs/architecture.md](../app/docs/architecture.md) oraz — jeśli dotyczy publicznego kontraktu — [app/docs/api.md](../app/docs/api.md).

## PDF i OCR

- Ekstrakcja: `app/services/pdf_extract.py` — PyMuPDF (`fitz`) + opcjonalnie Tesseract.
- Parametr `ocr`: `off` | `on` | `auto` (query w `pdf.py`).
- Zmiany algorytmu OCR / progów auto — tylko w `pdf_extract` i ewent. nowych polach `Settings`, nie w routerze.

## Markitdown

- Owijka: `app/services/markitdown_convert.py` — `MarkItDown().convert(path)`.
- Wynik: `DocumentConverterResult` — używamy `markdown` / `text_content` / `title`. Przy zmianie wersji biblioteki sprawdź atrybuty w runtime (test smoke).

## Klient WWW (`client/`)

- **Stack:** Vite + TypeScript, brak Reacta; wejście [client/index.html](../client/index.html), logika [client/src/main.ts](../client/src/main.ts).
- **Proxy:** [client/vite.config.ts](../client/vite.config.ts) — `/v1`, `/health` → `VITE_API_PROXY_TARGET` (domyślnie `http://127.0.0.1:8000`).
- **Dokumentacja:** indeks [client/docs/README.md](../client/docs/README.md); instalacja / troubleshooting [client/docs/install-and-run.md](../client/docs/install-and-run.md); agenci [client/docs/AGENTS.md](../client/docs/AGENTS.md); skrót w [client/README.md](../client/README.md).
- Po zmianach w frontcie zaktualizuj **`client/docs/*`** (oraz skrót w `client/README.md`) zgodnie z tabelą [Aktualizacja dokumentacji po zmianach](#aktualizacja-dokumentacji-po-zmianach).

## Docker

- Obraz: [Dockerfile](../Dockerfile) — Tesseract (eng, pol), poppler dla zależności konwersji.
- Po dodaniu natywnych zależności systemowych zaktualizuj Dockerfile i README.

## Język i styl

- Interfejs użytkownika API (komunikaty `detail`, opisy w `Field`) może być po polsku — spójnie z istniejącym kodem.
- Komentarze: zwięźle, tylko gdy logika nie jest oczywista z nazw.

## TODO backlog (parametryzacja API)

Lista **niezamówionych** pomysłów na przyszłe iteracje — wybierz punkt z uzasadnieniem produktowym, zaprojektuj kontrakt (OpenAPI), zaimplementuj i **zaktualizuj dokumentację** (`api.md`, `install-and-run.md` itd.).

### `POST /v1/pdf-to-text`

- **Zakres stron** — query np. `pages=1-3,5` (mniejszy koszt przy dużych PDF).
- **DPI / język OCR per request** — nadpisanie `UTILS_OCR_DPI` / `UTILS_OCR_LANG` (np. nagłówek lub query); uwaga na bezpieczeństwo (DoS) — limity i autoryzacja.
- **Tesseract `config`** — ekspozycja PSM/OEM (`--psm`, `--oem`) dla lepszej jakości tabel / bloków tekstu.
- **Tryb ekstrakcji PyMuPDF** — np. `blocks` vs zwykły tekst, opcjonalnie layout; wymaga definicji formatu odpowiedzi (JSON vs plain text).
- **Ścieżka do binarki Tesseract** — `UTILS_TESSERACT_CMD` lub integracja z `pytesseract.pytesseract.tesseract_cmd`.

### `POST /v1/to-markdown`

- **Opcje `MarkItDown(...)`** — np. `enable_plugins`, sesja HTTP, integracja Azure Document Intelligence (endpoint + credential przez **tylko** zmienne środowiskowe, nie przez niezaufane query).
- **`StreamInfo`** — jawne podanie `mimetype` / `extension` / `charset` (query lub JSON obok pliku), gdy klient wysyła `application/octet-stream`.
- **Profil konwersji** — predefiniowane nazwy (`?profile=minimal`) mapowane na zestaw opcji po stronie serwera (stabilniejsze niż dziesiątki flag w URL).

### Wspólne / infrastruktura

- **Limit stron / czasu** na żądanie — ochrona przed kosztownym OCR całego dokumentu.
- **Wersjonowanie** — nowe parametry pod `/v2`, aby nie łamać klientów `/v1`.

## Czego unikać

- Trzymania stanu między żądaniami (usługa ma być stateless).
- Logowania pełnej treści uploadowanych plików.
- Zwiększania limitu uploadu bez uzasadnienia (DoS / pamięć).
