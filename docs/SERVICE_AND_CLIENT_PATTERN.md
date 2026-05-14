# Wzorzec: nowa usługa REST + strona w kliencie

Ten dokument to **checklista** przy dodawaniu kolejnej małej usługi do `utils-service` (FastAPI) oraz odpowiadającej jej podstrony w kliencie Vite (`client/`).

Powiązane: [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md), [AGENTS.md](../AGENTS.md), [app/docs/architecture.md](../app/docs/architecture.md).

## Backend

1. **Serwis** (`app/services/<nazwa>.py`) — logika na `Path` / bytes; bez bezpośredniego HTTP; sensowne wyjątki (`ValueError`, `RuntimeError` itd.).
2. **Router** (`app/api/v1/<nazwa>.py`) — `APIRouter`, walidacja uploadu (`UploadFile`, rozmiar przez `save_upload_to_temp`), mapowanie wyjątków na `HTTPException`, `unlink` pliku tymczasowego w `finally`.
3. **Rejestracja** w [`app/main.py`](../app/main.py): `app.include_router(..., prefix="/v1")`.
4. **Konfiguracja** — jeśli potrzebne nowe limity: pola w [`app/core/config.py`](../app/core/config.py) z prefiksem `UTILS_` (udokumentuj w [`README.md`](../README.md) i [`app/docs/install-and-run.md`](../app/docs/install-and-run.md)).
5. **Zależności systemowe** — jeśli wymagana binarka (np. Pandoc, Tesseract): wpisz w [`Dockerfile`](../Dockerfile), opisz instalację lokalną w [`app/docs/install-and-run.md`](../app/docs/install-and-run.md) (Docker jest **opcjonalny**; lokalnie wystarczy narzędzie w `PATH`).
6. **Testy** (`tests/test_*.py`) — `TestClient`; przy zewnętrznych binarkach rozważ `pytest.mark.skipif(not shutil.which(...))`.
7. **Dokumentacja** — [`app/docs/api.md`](../app/docs/api.md), [`app/docs/architecture.md`](../app/docs/architecture.md), skrót w [`README.md`](../README.md) jeśli zmienia się lista endpointów lub zmienne środowiskowe.

## Klient (Vite + TypeScript)

Routing oparty o **hash** (`#/…`), żeby statyczny hosting i prosty serwer plików działały bez konfiguracji SPA po stronie serwera.

1. **Ścieżka** — ustal `fragment`, np. `#/moja-usluga` (spójnie z [`client/src/router.ts`](../client/src/router.ts)).
2. **Strona** — nowy moduł w `client/src/pages/<nazwa>.ts` eksportujący funkcję `render…(root: HTMLElement)` (wstawia HTML do `root`, podpina handlery).
3. **Wspólne** — logika HTTP, plików, schowka: `client/src/lib/*.ts`; szkielet nagłówka / nawigacji: [`client/src/layout.ts`](../client/src/layout.ts).
4. **Style** — jeśli potrzeba nowych komponentów UI, dopisz reguły w [`client/src/style.css`](../client/src/style.css).
5. **Dokumentacja frontu** — [`client/docs/install-and-run.md`](../client/docs/install-and-run.md), ewent. [`client/docs/AGENTS.md`](../client/docs/AGENTS.md).

<span id="textarea-file-upload"></span>

### Usługa z treścią jako plik (textarea + upload)

Gdy endpoint przyjmuje pole `file`, a w UI chcesz **wkleić źródło** oraz **opcjonalnie** wybrać lub upuścić plik (jak PDF / Markdown):

- **HTML** — wewnątrz `<form>`: blok `.file-area` zawiera `.dropzone` (tekst zachęty), `.file-name` (etykieta wybranego pliku, `aria-live="polite"`) oraz `<input type="file" name="file" …>` z sensownym `accept`.
- **DnD i walidacja rozszerzeń** — po zbudowaniu formularza wywołaj `wireDropzone(form, { mode: …, err })` z [`client/src/lib/files.ts`](../client/src/lib/files.ts). Tryb (`DropzoneMode`) musi odpowiadać regułom backendu dla uploadu (np. `plantumlSource`, `mermaidSource`, `markdownSource`, `pdf`). Komunikaty błędów z dropu trafiają w przekazany element `err` (zwykle ten sam `<p class="err">` co błędy submitu / API).
- **Submit** — jeśli `input[name="file"]` ma wybrany plik z `size > 0`, do `FormData` dodaj ten plik jako `file`. W przeciwnym razie wyślij treść z **textarea** jako `Blob` z domyślną nazwą pliku zgodną z oczekiwaniami API (np. `diagram.puml`, `diagram.mmd`).
- **Zmiana pliku** — przy `change` na `input[name="file"]` wczytaj zawartość pliku do textarea (żeby użytkownik widział to samo, co poleci na serwer).

## Odpowiedzi inne niż JSON

Dla plików binarnych (np. DOCX): `Response` / `StreamingResponse` z właściwym `media_type` i `Content-Disposition: attachment`. W kliencie: `fetch` → `res.blob()` → tymczasowy `URL.createObjectURL` + programowe kliknięcie `<a download>`; nazwa pliku z nagłówka `Content-Disposition`, jeśli jest.

## Weryfikacja przed zamknięciem PR

- `pytest` (z root repozytorium, po `pip install -e ".[dev]"`).
- `npm run build` w katalogu `client/`.
