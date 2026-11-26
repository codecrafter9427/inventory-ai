# Inventory AI

Stock and warehouse operations for small retailers, distributors, and small warehouses. Local-first portfolio MVP — **no paid APIs required**.

## Purpose

Help owners and inventory staff track catalog, locations, purchasing, receiving, counts, transfers, and stock movements. Differentiator: **Stockout Radar** — a transparent risk score from on-hand stock, average daily movement, supplier lead time, and safety stock (formula shown; no certainty claims).

**Milestone 4 (current):** polish (loading/error/empty/confirmations), dashboard KPI tiles, inventory reports + CSV export, thin transfers + count-approval slice, expanded tests, DEMO.md, mobile product search (code; Android Studio sync required to run).

## Architecture

```
Browser (Next.js)  ─┐
                    ├─► FastAPI /api/v1 ─► PostgreSQL (Docker :5435)
Android Compose   ─┘         │
                             ├─ DemoAIProvider (default) / optional Ollama
                             └─ Deterministic stock math (balances, reports, radar formula)
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
products/inventory-ai/
  README.md
  DEMO.md                 # Scripted demo / recording checklist
  MVP_SPEC.md
  .env.example
  docker-compose.yml      # PostgreSQL only (host port 5435)
  backend/                # FastAPI + models + Alembic + seed + tests
  web/                    # Next.js UI
  mobile/                 # Android Compose (Studio sync to run)
```

## Features (M4)

| Area | Status |
|------|--------|
| Demo login + org/role JWT | Done |
| Products CRUD / search | Done |
| PO list + atomic receive | Done |
| Stock balances + movements | Done |
| Dashboard KPI tiles | Done |
| Reports + CSV (stock-on-hand, movements) | Done |
| Transfers (create → receive; qty preserved) | Thin slice |
| Stock counts (submit → approve w/ variance reason) | Thin slice |
| Reorder AI + confirm draft PO | Done |
| Stockout Radar | Done |
| Inventory Q&A (allowlisted tools) | Done |
| Mobile login + product search + stock by SKU | Code done; device needs Studio |
| Suppliers / locations write / settings | Coming Soon |
| ML Kit barcode / offline queue | Coming Soon |

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

Default DB URL uses host port **5435**.

### 2. Database

```bash
docker compose up -d
```

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

### 4. Tests / quality

```bash
cd backend
pytest tests -q
# Optional format check if ruff/black installed locally — pytest is the gate
```

```bash
cd web
npm install
npm run lint
npx tsc --noEmit
```

### 5. Web

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

### 6. Mobile (Android)

See `mobile/README.md`. Open `mobile/` in **Android Studio**, sync Gradle, run on emulator (`10.0.2.2:8000`). Device run without Studio sync is a known limitation.

## Demo credentials

Password for all seeded users: `demo-password`

| Email | Role |
|-------|------|
| `admin@demo.inventory.local` | Owner / Admin |
| `manager@demo.inventory.local` | Inventory Manager |
| `staff@demo.inventory.local` | Staff (receive/transfers/counts; no catalog create / no AI draft PO / no count approve) |
| `other@demo.inventory.local` | Owner of a second org (tenant isolation) |

Seed minimums (primary org `demo-retail`): **30 products**, **3 locations**, **5 suppliers**, **8 purchase orders**, movement history (including low-stock rows for AI demos).

## Demo steps

Full recording checklist: **[DEMO.md](./DEMO.md)**.

1. Start Postgres, migrate, seed, API (`:8000`). `AI_PROVIDER=demo`.
2. Start web (`npm run dev`).
3. Sign in as admin → **Dashboard** KPI tiles.
4. **Products** → search/create; **Purchase orders** → confirm receive.
5. **Stock** → balances + ledger; **Transfers** → create + receive; **Counts** → approve variance with reason.
6. **Reports** → CSV stock-on-hand / movements.
7. **Reorder AI** → confirm draft PO (stock unchanged); **Stockout Radar**; **AI Q&A**.

## AI (demo + optional Ollama)

### Demo without Ollama (default)

```bash
AI_PROVIDER=demo
```

`DemoAIProvider` returns deterministic explanations over computed signals and allowlisted tools.

### Optional local Ollama

1. Install Ollama; `ollama pull llama3.2`
2. Set `AI_PROVIDER=ollama`, `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=llama3.2`
3. Restart API — invalid/down Ollama **falls back** to DemoAI

Rules: backend-only model calls; typed schemas; Q&A allowlisted read tools; AI never changes stock; draft PO only after `confirm=true`; Stockout Radar shows formula (no certainty claims).

## Prototype security notes

- Demo JWT with env `JWT_SECRET` placeholder — not production SSO.
- Env vars / `.env.example` only; never commit real secrets.
- Org scoping enforced server-side; role gates on mutations.
- AI tools org-authorized before execution; limited prototype rate limiting.
- Cleartext HTTP allowed on Android emulator for local demo only.
- Not hardened for internet exposure, multi-tenant SaaS, or compliance audits.

## Milestone backlog

1. **Done (M1)** — env, Docker Postgres, models, migrations, demo login, seed, smoke tests.
2. **Done (M2)** — products CRUD; PO receive → balance + ledger; stock reads; role gates; web slice.
3. **Done (M3)** — DemoAI + Ollama; reorder + draft PO; Q&A; Stockout Radar; AI tests.
4. **Done (M4)** — polish, KPIs, reports/CSV, thin transfers/counts, tests, DEMO.md, mobile search code.
5. **Later** — ML Kit barcode, offline queue, settings, suppliers write, full mobile ops, E2E recording.

## Known limitations

- Suppliers / locations **write** APIs and Settings remain Coming Soon.
- Transfer/count UIs are thin slices (not full multi-line offline workflows).
- General PO create/edit UI not wired (AI draft + seeded receivable POs).
- Mobile: barcode, receive, offline queue deferred; **Android Studio sync required** to run.
- Auth is demo JWT only; Ollama quality depends on local model.

See `MVP_SPEC.md` for entities, API groups, and acceptance criteria.
