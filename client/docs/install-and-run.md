# Instalacja i uruchomienie — klient WWW

Lekki front w katalogu nadrzędnym [client/](../): **Vite 6** + **TypeScript**, bez Reacta. Woła endpointy API: `/health`, `/v1/pdf-to-text`, `/v1/to-markdown`, `/v1/docx-to-markdown`, `/v1/markdown-to-docx`, `/v1/plantuml-to-image`, `/v1/mermaid-to-image`. Nawigacja między usługami: **hash** (`#/`, `#/pdf-to-text`, itd.) — zobacz [../../docs/SERVICE_AND_CLIENT_PATTERN.md](../../docs/SERVICE_AND_CLIENT_PATTERN.md).

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

## Uruchamianie przez PM2 (opcjonalnie)

Zamiast dwóch terminali możesz zarządzać procesami przez [PM2](https://pm2.keymetrics.io/) — backend i front uruchamiasz **osobno**. Konfiguracja: [`ecosystem.config.cjs`](../../ecosystem.config.cjs) w root repozytorium.

### Wymagania

1. PM2 globalnie: `npm install -g pm2`
2. Backend: `.venv` + `pip install -e .` (patrz [app/docs/install-and-run.md](../../app/docs/install-and-run.md))
3. Front: `npm install` w katalogu `client/` (powyżej)

### Backend (osobno)

Z root repozytorium:

```powershell
pm2 start ecosystem.config.cjs --only utils-api
# skrót: npm run pm2:api
```

API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

### Front — tryb dev (osobno)

```powershell
pm2 start ecosystem.config.cjs --only utils-client-dev
# skrót: npm run pm2:client:dev
```

UI: **http://127.0.0.1:5173** (proxy do API jak przy `npm run dev`).

### Front — tryb preview (osobno)

Najpierw zbuduj front:

```powershell
cd client
npm run build
cd ..
```

Potem:

```powershell
pm2 start ecosystem.config.cjs --only utils-client-preview
# skrót: npm run pm2:client:preview
```

UI: **http://127.0.0.1:4173** (proxy jak przy `npm run preview`).

### Tabela: aplikacja PM2 → URL

| Aplikacja PM2 | Port | Adres w przeglądarce |
|---------------|------|----------------------|
| `utils-api` | 8000 | API / Swagger — nie interfejs WWW |
| `utils-client-dev` | 5173 | http://127.0.0.1:5173 |
| `utils-client-preview` | 4173 | http://127.0.0.1:4173 |

Backend musi działać (`utils-api`), zanim front połączy się z `/health` i `/v1`.

### Przydatne komendy PM2

```powershell
pm2 status
pm2 logs utils-client-dev
pm2 restart utils-api
pm2 stop utils-api
pm2 delete utils-client-dev
```

Logi procesów trafiają do `logs/pm2/` (katalog ignorowany przez git).

Przy niestandardowym hoście API ustaw `VITE_API_PROXY_TARGET` w `client/.env` i zrestartuj proces frontu (`pm2 restart utils-client-dev` lub `utils-client-preview`).

## Dostęp przez reverse proxy (publiczna domena)

Gdy front (`npm run dev`, `npm run preview` lub PM2) stoi za nginx / Cloudflare i otwierasz go spod publicznej domeny (np. `https://example.allowedhosts.dev`), Vite 6 może zwrócić:

> Blocked request. This host ("example.allowedhosts.dev") is not allowed.

To zabezpieczenie Vite: nagłówek `Host` z reverse proxy musi być na liście dozwolonych hostów. Są **dwa sposoby** — wystarczy jeden.

### Sposób 1: `allowedHosts` w `vite.config.ts`

W [`client/vite.config.ts`](../vite.config.ts) dodaj domenę w sekcji `server` (tryb dev) i opcjonalnie `preview`:

```typescript
server: {
  port: 5173,
  allowedHosts: ["example.allowedhosts.dev"],
  // ...
},
preview: {
  port: 4173,
  allowedHosts: ["example.allowedhosts.dev"],
  // ...
},
```

Suffix subdomen: wpis `.allowedhosts.dev` pozwala na `example.allowedhosts.dev`, `foo.allowedhosts.dev` itd.

### Sposób 2: zmienna środowiskowa (bez edycji `vite.config.ts`)

Vite 6 umożliwia dodanie hostów przez env — wygodne na serwerze, gdy domena nie powinna trafić do repozytorium.

W `client/.env` (patrz [`.env.example`](../.env.example)):

```env
__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS=example.allowedhosts.dev
```

Wiele hostów oddziel przecinkami: `host1.example.com,host2.example.com`.

Po zmianie zrestartuj front: `pm2 restart utils-client-dev` (lub `utils-client-preview`).

### Weryfikacja

- Strona ładuje się bez „Blocked request”.
- W UI działa **`GET /health`** (proxy Vite → FastAPI na `VITE_API_PROXY_TARGET`).
- Backend (`utils-api`) musi działać równolegle; `VITE_API_PROXY_TARGET` zwykle pozostaje `http://127.0.0.1:8000`.

## Produkcja (zamiast `npm run dev`)

Na serwerze publicznym **nie używaj** `npm run dev` ani PM2 `utils-client-dev` — to tryb deweloperski (HMR, brak minifikacji, dodatkowe zabezpieczenia Vite jak `allowedHosts`).

Front woła **względne** ścieżki (`/health`, `/v1/...`). W produkcji ten sam host publiczny serwuje statykę z `dist/` i przekazuje API do FastAPI — bez zmian w kodzie TypeScript.

### Porównanie trybów

| Tryb | Komenda / PM2 | Port | Produkcja? |
|------|---------------|------|------------|
| **Dev** | `npm run dev` / `utils-client-dev` | 5173 | Nie — tylko lokalnie |
| **Preview** | `npm run preview` / `utils-client-preview` | 4173 | Tylko test po `build`; Vite **nie zaleca** na stałe |
| **Statyka + reverse proxy** | `npm run build` → nginx serwuje `client/dist/` | 443/80 | **Tak — zalecane** |

```mermaid
flowchart LR
  browser[Przeglądarka]
  proxy[Reverse_proxy]
  static[client_dist]
  api[FastAPI_8000]

  browser --> proxy
  proxy -->|"/"| static
  proxy -->|"/v1 /health"| api
```

### Kroki na serwerze (zalecany wariant)

#### 1. Zbuduj front

Po każdej zmianie UI (oraz przy pierwszym wdrożeniu):

```powershell
cd client
npm install
npm run build
```

Wynik: katalog [`client/dist/`](../dist/) — zminifikowany HTML, JS, CSS. Po `build` **Node.js nie jest potrzebny** do serwowania frontu (wystarczy nginx + Python/API).

#### 2. Zatrzymaj tryb dev

Jeśli wcześniej działał Vite dev:

```powershell
pm2 stop utils-client-dev
pm2 delete utils-client-dev   # opcjonalnie
```

Nie potrzebujesz już procesu Vite ani konfiguracji `allowedHosts` z sekcji [Dostęp przez reverse proxy](#dostęp-przez-reverse-proxy-publiczna-domena).

#### 3. Backend — PM2 `utils-api`

Konfiguracja w [`ecosystem.config.cjs`](../../ecosystem.config.cjs) jest już produkcyjna (brak `--reload`):

```powershell
pm2 start ecosystem.config.cjs --only utils-api
# skrót: npm run pm2:api
```

Sprawdzenie: `pm2 status`, `curl http://127.0.0.1:8000/health`.

#### 4. Reverse proxy (nginx)

**Zasada:** jedna domena publiczna — `/` z plików w `dist/`, `/v1` i `/health` → FastAPI na `127.0.0.1:8000`.

Przykład (dostosuj ścieżki i certyfikat SSL):

```nginx
server {
    listen 443 ssl;
    server_name example.allowedhosts.dev;

    root /ścieżka/do/utils-service/client/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        client_max_body_size 20m;   # zgodnie z UTILS_MAX_UPLOAD_BYTES
    }

    location = /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Po zmianie: `nginx -t && nginx -s reload`.

**Cloudflare** (lub inny CDN) — zwykle tylko DNS i SSL; routing `/` vs `/v1` konfigurujesz na nginx/Caddy/Traefik **za** CDN.

**HTTPS:** wymagany m.in. dla przycisku „Kopiuj” w UI (`navigator.clipboard`).

Alternatywa przy **osobnych domenach** frontu i API: CORS na backendzie — wtedy front musiałby wołać pełny URL API (obecny kod tego nie robi).

#### 5. Weryfikacja

- `https://twoja-domena` — UI bez Vite i bez „Blocked request”
- `https://twoja-domena/health` → `{"status":"ok"}`
- W UI: status API OK, konwersja pliku działa

### Wariant pośredni: `vite preview`

Do szybkiego testu po `build` (lokalnie lub na serwerze), zanim skonfigurujesz nginx:

```powershell
cd client
npm run build
npm run preview          # port 4173
# lub PM2:
pm2 start ecosystem.config.cjs --only utils-client-preview
```

Proxy do API nadal z [`vite.config.ts`](../vite.config.ts) — mniej zmian w nginx, ale dodatkowy proces Node i [ograniczenia Vite preview](https://vite.dev/guide/cli#vite-preview). Za reverse proxy z publiczną domeną nadal może być potrzebne `allowedHosts` (patrz sekcja wyżej).

### Aktualizacja po zmianach w kodzie

| Co się zmieniło | Co zrobić |
|-----------------|-----------|
| Tylko front (UI) | `cd client && npm run build` — nginx od razu serwuje nowy `dist/` |
| Tylko backend | `pm2 restart utils-api` |
| Front i backend | `npm run build` + `pm2 restart utils-api` |

## Build i podgląd produkcyjny lokalnie

Skrót do testu buildu na maszynie deweloperskiej (szczegóły produkcyjne: sekcja [Produkcja](#produkcja-zamiast-npm-run-dev) powyżej):

```powershell
cd client
npm run build
npm run preview
```

`preview` używa tego samego proxy co `dev` (patrz `vite.config.ts`).

## Funkcje interfejsu

- Przycisk / automatyczne sprawdzenie **`GET /health`**
- Formularz **PDF → tekst** (`POST /v1/pdf-to-text`, query `ocr`), **plik → Markdown** (`POST /v1/to-markdown`) oraz **DOCX → Markdown** (`POST /v1/docx-to-markdown`, query `comments`, `extract_media`)
- **Wybór pliku:** standardowy przycisk systemowy oraz **strefa przeciągnij-i-upuść** (PDF tylko pliki `.pdf` / typ `application/pdf`)
- **Kopiuj:** zapis treści pola wyniku do schowka (`navigator.clipboard`) — wymaga zwykle **HTTPS** lub **`localhost`**; przy braku uprawnień pojawi się podpowiedź (można skopiować ręcznie z pola)
- **Zwiń / pokaż odpowiedź:** zwijanie bloku z polem tekstowym wyniku (treść pozostaje w polu; „Kopiuj” nadal kopiuje aktualną zawartość)

## Typowe problemy

| Objaw | Co sprawdzić |
|--------|----------------|
| „API nieosiągalne” / błąd `/health` | Czy uvicorn działa na `VITE_API_PROXY_TARGET`; czy `.env` w `client/` jest poprawny (wymaga restartu `npm run dev`). |
| 502 / „connection refused” w konsoli sieci | Backend wyłączony lub zły port w `VITE_API_PROXY_TARGET`. |
| Po `build` brak działania na zwykłym hostingu plików | Brak reverse proxy — patrz [Produkcja (zamiast npm run dev)](#produkcja-zamiast-npm-run-dev). |
| Schowek / „Kopiuj” nie działa | Czy strona jest na `localhost` lub HTTPS; w niektórych przeglądarkach trzeba zezwolić na dostęp do schowka. |
| „Blocked request. This host … is not allowed” | Domena spoza `localhost` — patrz sekcja [Dostęp przez reverse proxy](#dostęp-przez-reverse-proxy-publiczna-domena): `allowedHosts` w `vite.config.ts` **lub** `__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS` w `client/.env`. |
