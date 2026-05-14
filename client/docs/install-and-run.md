# Instalacja i uruchomienie — klient WWW

Lekki front w katalogu nadrzędnym [client/](../): **Vite 6** + **TypeScript**, bez Reacta. Woła endpointy API: `/health`, `/v1/pdf-to-text`, `/v1/to-markdown`, `/v1/markdown-to-docx`, `/v1/plantuml-to-image`, `/v1/mermaid-to-image`. Nawigacja między usługami: **hash** (`#/`, `#/pdf-to-text`, itd.) — zobacz [../../docs/SERVICE_AND_CLIENT_PATTERN.md](../../docs/SERVICE_AND_CLIENT_PATTERN.md).

## Wymagania

| Składnik | Uwagi |
|----------|--------|
| **Node.js 20+** (LTS) | [nodejs.org](https://nodejs.org/) |
| **npm** | Dołączony do Node |
| **Działający backend** `utils-service` | Domyślnie `http://127.0.0.1:8000` — patrz [app/docs/install-and-run.md](../../app/docs/install-and-run.md) |

## Instalacja zależności

Z poziomu katalogu `client/` (obok `package.json`):

```powershell
cd client
npm install
```

## Tryb deweloperski (zalecany)

**Dwa procesy:** backend na porcie 8000 oraz Vite na 5173.

### 1. Backend (terminal 1, z root repozytorium)

```powershell
cd c:\Users\jbienkowsk001\Code\utils-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Front (terminal 2)

```powershell
cd c:\Users\jbienkowsk001\Code\utils-service\client
npm run dev
```

Otwórz w przeglądarce adres z konsoli Vite (zwykle **http://127.0.0.1:5173**).

### Dlaczego nie trzeba CORS lokalnie

Przeglądarka woła **względne** ścieżki (`/v1/...`, `/health`) na hoście i porcie **Vite**. Serwer deweloperski **proxy** przekazuje je na backend (`vite.config.ts`). Dzięki temu origin strony i origin „API” z punktu widzenia przeglądarki to ten sam host (proxy), bez konfiguracji CORS po stronie FastAPI.

```mermaid
flowchart LR
  browser[Przeglądarka]
  vite[Vite_dev_5173]
  api[FastAPI_8000]

  browser -->|"GET /health POST /v1"| vite
  vite -->|proxy| api
```

### Adres backendu (zmienna środowiskowa)

Skopiuj [../.env.example](../.env.example) do `client/.env` i ustaw np.:

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
```

Inny host/port — gdy API nie nasłuchuje na domyślnym `127.0.0.1:8000`.

## Build i podgląd produkcyjny lokalnie

```powershell
cd client
npm run build
npm run preview
```

`preview` używa tego samego proxy co `dev` (patrz `vite.config.ts`).

## Hosting statyczny (`dist/`)

Po `npm run build` katalog `client/dist/` zawiera pliki statyczne. Same `file://` lub hosting bez proxy **nie** przekierują `/v1` na FastAPI — wtedy:

- **nginx (lub podobny):** ten sam host — `/` → pliki z `dist/`, ścieżki `/v1` i `/health` → upstream do FastAPI; **albo**
- **CORS** na backendzie dla domeny frontu (gdy front i API są na różnych originach).

## Funkcje interfejsu

- Przycisk / automatyczne sprawdzenie **`GET /health`**
- Formularz **PDF → tekst** (`POST /v1/pdf-to-text`, query `ocr`) oraz **plik → Markdown** (`POST /v1/to-markdown`)
- **Wybór pliku:** standardowy przycisk systemowy oraz **strefa przeciągnij-i-upuść** (PDF tylko pliki `.pdf` / typ `application/pdf`)
- **Kopiuj:** zapis treści pola wyniku do schowka (`navigator.clipboard`) — wymaga zwykle **HTTPS** lub **`localhost`**; przy braku uprawnień pojawi się podpowiedź (można skopiować ręcznie z pola)
- **Zwiń / pokaż odpowiedź:** zwijanie bloku z polem tekstowym wyniku (treść pozostaje w polu; „Kopiuj” nadal kopiuje aktualną zawartość)

## Typowe problemy

| Objaw | Co sprawdzić |
|--------|----------------|
| „API nieosiągalne” / błąd `/health` | Czy uvicorn działa na `VITE_API_PROXY_TARGET`; czy `.env` w `client/` jest poprawny (wymaga restartu `npm run dev`). |
| 502 / „connection refused” w konsoli sieci | Backend wyłączony lub zły port w `VITE_API_PROXY_TARGET`. |
| Po `build` brak działania na zwykłym hostingu plików | Brak reverse proxy lub CORS — patrz sekcja „Hosting statyczny”. |
| Schowek / „Kopiuj” nie działa | Czy strona jest na `localhost` lub HTTPS; w niektórych przeglądarkach trzeba zezwolić na dostęp do schowka. |
