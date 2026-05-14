# utils-service — wskazówki dla agentów (Cursor / AI)

Ten plik jest **punktem startu**: co przeczytać dalej, jak uruchomić projekt i gdzie wprowadzać zmiany.

## Szybki start

1. Katalog repozytorium: `utils-service` (root zawiera `pyproject.toml` i pakiet `app/`).
2. Zależności: `pip install -e ".[dev]"` (lub `pip install -e .`).
3. Serwer: `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`  
   (preferuj `python -m uvicorn`, jeśli skrypt `uvicorn` nie jest w `PATH`).
4. OpenAPI: po starcie otwórz `http://127.0.0.1:8000/docs`.

## Co czytać przed zmianami

| Dokument | Przeznaczenie |
|----------|----------------|
| [docs/SERVICE_AND_CLIENT_PATTERN.md](docs/SERVICE_AND_CLIENT_PATTERN.md) | Checklista: nowa usługa REST + strona w kliencie (Vite) |
| [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md) | Jak dodać endpoint, warstwy kodu, typowe pułapki |
| [app/docs/README.md](app/docs/README.md) | Indeks dokumentacji dla człowieka |
| [app/docs/install-and-run.md](app/docs/install-and-run.md) | Instalacja, uruchomienie, Docker, `.env`, parametryzacja konwerterów |
| [app/docs/api.md](app/docs/api.md) | Opis endpointów, kody błędów, standardy (OpenAPI); uzupełnienie `/docs` i `/openapi.json` |
| [client/docs/AGENTS.md](client/docs/AGENTS.md) | Klient WWW (`client/`): Vite, proxy, skrypty npm — gdy pracujesz nad frontem |
| [README.md](README.md) | Skrót: Docker, zmienne `UTILS_*` |

## Struktura kodu (skrót)

- `app/main.py` — instancja FastAPI, mount routerów `/v1`, `/health`.
- `app/api/v1/` — routery HTTP (cienkie: walidacja, statusy, brak ciężkiej logiki).
- `app/services/` — logika domenowa (PDF, markitdown, Pandoc / MD→DOCX, PlantUML, Mermaid).
- `app/core/` — konfiguracja (`Settings`, prefiks `UTILS_`), zapis uploadów do temp.
- `app/models/schemas.py` — modele odpowiedzi Pydantic.
- `client/` — osobny front (**Vite** + TypeScript), własny `package.json`; dokumentacja w `client/docs/`.

## Zasady pracy (obowiązujące)

- **Minimalny zakres diffu** — zmieniaj tylko to, czego wymaga zadanie; nie refaktoruj „przy okazji”.
- **Dokumentacja po zmianach** — po każdej zmianie wpływającej na zachowanie usługi lub frontu (API, konfiguracja, architektura, Docker, zależności, przepływy, **`client/`**) **zaktualizuj dokumentację w tym samym zestawie zmian**. Konkretna lista plików i sytuacji: [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md#aktualizacja-dokumentacji-po-zmianach).
- **Nowa usługa REST** — krok po kroku: [docs/SERVICE_AND_CLIENT_PATTERN.md](docs/SERVICE_AND_CLIENT_PATTERN.md) (router `app/api/v1/`, serwis `app/services/`, `app/main.py`, dokumentacja, front).
- **Sekrety** — nie commituj `.env`; `Settings` ładuje opcjonalnie `.env` lokalnie.
- **Pliki tymczasowe** — endpointy z uploadem używają `save_upload_to_temp`; zawsze `unlink` w `finally`.
- **OCR** — wymaga zainstalowanego Tesseract; błędy OCR mapuj na sensowne `HTTPException` (wzór w `app/api/v1/pdf.py`).

## Testy ręczne / smoke

Po zmianach warto odpalić import i krótki test klienta (np. `httpx` / `TestClient`):

```python
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
assert c.get("/health").status_code == 200
```

Szczegóły workflow: [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md). **Backlog pomysłów na parametryzację API:** sekcja [TODO backlog (parametryzacja API)](docs/AGENT_WORKFLOW.md#todo-backlog-parametryzacja-api) w tym pliku.
