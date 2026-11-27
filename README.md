# Inventory AI

Stock and warehouse operations for small retailers, distributors, and small warehouses. Local-first portfolio MVP — **no paid APIs required**.

## Purpose

Help owners and inventory staff track catalog, locations, purchasing, receiving, counts, transfers, and stock movements. Differentiator: **Stockout Radar** — a transparent risk score from on-hand stock, average daily movement, supplier lead time, and safety stock (formula shown; no certainty claims).

**Milestone 6 (current, `0.6.0-m6`):** suppliers/locations write + Settings (org/roles/units/reorder defaults); PO create/edit/submit/cancel; ledger integrity helper; Insights connector; smallest safe hardening (login rate limit, audit on key writes, CI, backup notes).

## Architecture

```
Browser (Next.js)  ─┐
                    ├─► FastAPI /api/v1 ─► PostgreSQL (Docker :5435)
Android Compose   ─┘         │
                             ├─ DemoAIProvider (default) / optional Ollama
                             ├─ Deterministic stock math (balances, reports, radar)
                             └─ Insights connector (service token, read-only)
```

| Layer | Stack |
|-------|--------|
| Web | Next.js 15 + TypeScript + Tailwind |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic, REST under `/api/v1` |
| Database | PostgreSQL (UUID PKs, UTC timestamps, decimal money) |
| AI | `AIProvider` + deterministic `DemoAIProvider`; optional local Ollama |
| Mobile | Kotlin + Jetpack Compose (native — not WebView) |
| Auth | Local demo login → JWT (organization + role claims) |

### Project layout

```
inventory-ai/
  README.md
  DEMO.md                 # Scripted demo / recording checklist
  MVP_SPEC.md
  CONNECTORS.md           # Insights connector (Agent 5)
  BACKUP.md               # Local Postgres dump/restore
  .env.example            # Demo vs prod-like placeholders
  docker-compose.yml      # PostgreSQL only (host port 5435)
  .github/workflows/ci.yml
  backend/                # FastAPI + models + Alembic + seed + tests
  web/                    # Next.js UI
  mobile/                 # Android Compose (Studio sync to run)
```

## Features (M6)

| Area | Status |
|------|--------|
| Demo login + org/role JWT | Done |
| Products CRUD / search | Done |
| Suppliers + locations write APIs + web UI | Done (M6) |
| Settings (org, roles read, units, reorder defaults) | Done (M6) |
| PO create / edit / submit / cancel + receive | Done (M6) |
| Stock balances + movements + ledger integrity helper | Done |
| Dashboard KPI tiles + reports/CSV | Done |
| Transfers / counts (thin slices) | Thin slice |
| Reorder AI + Stockout Radar + Q&A | Done |
| Insights connector health + summary | Done (M6) |
| Mobile barcode scan + PO receive | Code done (M5); Studio sync to run |
| Offline queue (count/receive drafts) | Coming Soon |

## Setup

### Prerequisites

- Docker (PostgreSQL)
- Python 3.12+
- Node.js 20+ (web)
- Android Studio / JDK 17+ (mobile — **Gradle sync required to run**)
- [Ollama](https://ollama.com) — **optional**

### 1. Environment

```bash
cp .env.example .env
cp .env.example backend/.env
# Optional web:
cp web/.env.example web/.env.local
```

Default DB URL uses host port **5435**. See `.env.example` for **demo** vs **prod-like** placeholders (`JWT_ACCESS_TOKEN_HOURS`, `INSIGHTS_CONNECTOR_TOKEN`, rate limits).

### 2. Database

```bash
docker compose up -d
```

Postgres healthcheck is already configured. Backup notes: **[BACKUP.md](./BACKUP.md)**.

### 3. Backend — migrations, seed, run

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- OpenAPI: `http://localhost:8000/docs`
- Version: `0.6.0-m6`

### 4. Tests / quality

```bash
cd backend
pytest tests -q
```

```bash
cd web
npm install
npm run lint
npx tsc --noEmit
```

CI: `.github/workflows/ci.yml` (migrate + seed + pytest against Postgres service).

### 5. Web

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

### 6. Mobile (Android)

See `mobile/README.md`. Open `mobile/` in **Android Studio**, sync Gradle, run on emulator (`10.0.2.2:8000`).

## Demo credentials

Password for all seeded users: `demo-password`

| Email | Role |
|-------|------|
| `admin@demo.inventory.local` | Owner / Admin |
| `manager@demo.inventory.local` | Inventory Manager |
| `staff@demo.inventory.local` | Staff (receive/transfers/counts; no catalog create / no AI draft PO / no count approve) |
| `other@demo.inventory.local` | Owner of a second org (tenant isolation) |

Seed minimums (primary org `demo-retail`): **30 products**, **3 locations**, **5 suppliers**, **8 purchase orders**, movement history.

## Demo steps

Full recording checklist: **[DEMO.md](./DEMO.md)**.

1. Start Postgres, migrate, seed, API (`:8000`). `AI_PROVIDER=demo`.
2. Start web (`npm run dev`).
3. Sign in as admin → **Dashboard**.
4. **Settings** → org reorder defaults / units; **Suppliers** / **Locations** create.
5. **Purchase orders** → new draft → submit → receive (or cancel before receive).
6. **Stock** / **Reports** / AI flows as before.
7. Optional: Insights connector — see **[CONNECTORS.md](./CONNECTORS.md)**.

## Insights connector

Read-only Agent 5 surface:

- `GET /api/v1/connectors/insights/v1/health`
- `GET /api/v1/connectors/insights/v1/summary`

Auth: `Authorization: Bearer $INSIGHTS_CONNECTOR_TOKEN` + `X-Organization-Id`. Details in **CONNECTORS.md**.

## AI (demo + optional Ollama)

```bash
AI_PROVIDER=demo
```

Optional Ollama: set `AI_PROVIDER=ollama` and local `OLLAMA_*` vars — falls back to DemoAI on failure. Rules unchanged: no stock mutation by AI; draft PO only after `confirm=true`.

## Prototype security notes

- Demo JWT (`JWT_SECRET`); TTL via `JWT_ACCESS_TOKEN_HOURS` (default 24h) — not production SSO.
- Password policy **notes**: `PASSWORD_MIN_LENGTH` (default 10) documented for future non-demo auth; seeded demo passwords may be shorter.
- Login rate limit: `LOGIN_RATE_LIMIT_PER_MINUTE` (default 10) on `/auth/demo-login`.
- Org scoping + role gates on mutations; audit events on supplier/location writes, PO submit/receive.
- Insights connector uses a shared service token (empty = disabled).
- Not hardened for internet exposure, multi-tenant SaaS, or compliance audits.

## Milestone backlog

1. **Done (M1–M5)** — foundation through mobile barcode receive.
2. **Done (M6)** — suppliers/locations/settings, PO write lifecycle, ledger helper, connector, hardening docs/CI.
3. **Later** — offline queue, full mobile count/transfer/adjust, E2E recording, production auth.

## Known limitations

- Transfer/count UIs remain thin slices (not full multi-line offline workflows).
- Mobile still needs **Android Studio Gradle sync** to run.
- Offline draft queue for counts/receiving is not implemented.
- Auth is demo JWT only; connector token is a shared secret (not per-client OAuth).
- In-memory login rate limit is single-process only.

See `MVP_SPEC.md` for entities, API groups, and acceptance criteria.
