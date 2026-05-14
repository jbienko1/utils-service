# Klient WWW — wskazówki dla agentów (Cursor / AI)

Pracujesz w katalogu **`client/`** — osobna aplikacja Node (Vite), niezależna od pakietu Python `app/`.

## Szybki start

1. **Node 20+** i `npm` w PATH.
2. Z katalogu `client/`: `npm install`.
3. Backend API uruchomiony (domyślnie `http://127.0.0.1:8000`) — root repo, `python -m uvicorn app.main:app ...`.
4. `npm run dev` — wejście na URL z konsoli Vite (port **5173**).

## Co czytać

| Dokument | Przeznaczenie |
|----------|----------------|
| [docs/install-and-run.md](install-and-run.md) | Instalacja, proxy, build, produkcja, troubleshooting (dla człowieka) |
| [docs/README.md](README.md) | Indeks dokumentacji klienta |
| [../vite.config.ts](../vite.config.ts) | Proxy `/v1`, `/health` → `VITE_API_PROXY_TARGET` |
| [../../docs/AGENT_WORKFLOW.md](../../docs/AGENT_WORKFLOW.md) | Workflow całego repo + tabela aktualizacji dokumentacji |
| [../../docs/SERVICE_AND_CLIENT_PATTERN.md](../../docs/SERVICE_AND_CLIENT_PATTERN.md) | Checklista: nowy endpoint + podstrona w kliencie |
| [../../AGENTS.md](../../AGENTS.md) | Punkt startu dla pracy nad backendem i repo |

## Struktura `client/`

| Ścieżka | Rola |
|---------|------|
| `package.json` | Skrypty: `dev`, `build` (`tsc --noEmit` + `vite build`), `preview` |
| `vite.config.ts` | Port dev 5173, `loadEnv`, proxy na backend |
| `index.html` | Punkt wejścia HTML |
| `src/main.ts` | Bootstrap: `startRouter()` (hash `#/…`) |
| `src/router.ts` | Mapowanie ścieżki hash → strony |
| `src/layout.ts` | Wspólny szkielet (nagłówek, nawigacja, stopka) |
| `src/pages/*.ts` | HTML + logika formularzy dla poszczególnych usług |
| `src/lib/*.ts` | Wspólne helpery (`fetch`, pliki, UI) |
| `src/style.css` | Style |
| `.env.example` | Szablon `VITE_API_PROXY_TARGET` |

## Zasady pracy

- **Minimalny diff** — tylko zmiany potrzebne do zadania.
- **Dokumentacja po zmianach** — po zmianie zachowania frontu, proxy, portów lub wymagań Node: zaktualizuj [install-and-run.md](install-and-run.md), [README.md](../README.md) (skrót), ewent. [../../docs/AGENT_WORKFLOW.md](../../docs/AGENT_WORKFLOW.md) (sekcja klient). Pełna tabela: [Aktualizacja dokumentacji](../../docs/AGENT_WORKFLOW.md#aktualizacja-dokumentacji-po-zmianach).
- **Ścieżki API** — trzymaj względne URL (`/v1/...`), żeby działał proxy Vite; unikaj twardych `http://127.0.0.1:8000` w `fetch` (CORS poza dev).
- **Typy** — `tsc --noEmit` jest w `npm run build`; po większych zmianach uruchom `npm run build` lokalnie.
- **Textarea + upload** — formularze z polem tekstowym i opcjonalnym plikiem (dropzone, priorytet pliku przy submitcie): [Usługa z treścią jako plik (textarea + upload)](../../docs/SERVICE_AND_CLIENT_PATTERN.md#textarea-file-upload).

## Typowe pułapki

- Hosting tylko `dist/` **bez** reverse proxy — żądania `/v1` nie trafią na FastAPI.
- Zmiana `.env` w `client/` — wymaga **restartu** `npm run dev` / `preview`.
- Rozjazd wersji Node między CI a dev — trzymaj spójność z `engines` (opcjonalnie dopisz w `package.json`, jeśli wprowadzicie politykę wersji).
- **`navigator.clipboard`** — może być zablokowany poza `localhost`/HTTPS; UI pokazuje komunikat zastępczy.
