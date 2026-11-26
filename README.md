# Inventory AI

Stock and warehouse operations for small retailers, distributors, and small warehouses. Local-first portfolio MVP — no paid APIs required.

## Purpose

Help owners and inventory staff track catalog, locations, purchasing, receiving, counts, transfers, and stock movements. Differentiator: **Stockout Radar** — a transparent risk score from on-hand stock, average daily movement, supplier lead time, and safety stock (formula shown; no certainty claims).

**Milestone 1 (current):** database schema, Alembic migrations, demo auth with roles, org-scoped protection, fictional seed data, `/health`, and smoke tests. Business CRUD/workflows remain Coming Soon (Milestone 2+).

## Tech stack

| Layer | Stack |
|-------|--------|
| Web | Next.js + TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic, REST JSON under `/api/v1` |
| Database | PostgreSQL (UUID PKs, UTC timestamps, decimal money) via Docker Compose |
| AI | `AIProvider` + deterministic `DemoAIProvider`; optional Ollama adapter stub |
| Mobile | Kotlin + Jetpack Compose (native Android — not WebView) |
| Auth | Local demo login → JWT (organization + role claims) |

## Project layout

```
products/inventory-ai/
  README.md
  MVP_SPEC.md
  .env.example
  docker-compose.yml      # PostgreSQL only (host port 5435)
  backend/                # FastAPI + models + Alembic + seed + tests
  web/                    # Next.js app shell (Coming Soon pages)
  mobile/                 # Android Compose shell
```

## Setup

### Prerequisites

- Docker (PostgreSQL)
- Python 3.12+
- Node.js 20+ (web)
- Android Studio / JDK 17+ (mobile — optional for M1)

### 1. Environment

```bash
cp .env.example .env
cp .env.example backend/.env
# Optional web:
cp web/.env.example web/.env.local
```

Default DB URL uses host port **5435** so it does not clash with other local Postgres containers.

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
- Demo login: `POST /api/v1/auth/demo-login`
- Current user: `GET /api/v1/me` (Bearer token)
- Org (tenant-scoped): `GET /api/v1/organizations/{id}` — wrong org → **403**
- AI stubs (auth required): `POST /api/v1/ai/...`
- Business routes return **501 Coming Soon** (auth required)

### 4. Tests

```bash
cd backend
pytest tests -q
```

### 5. Web (optional for M1)

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`. Demo login calls the backend; inventory pages remain Coming Soon.

### 6. Mobile (Android) — deferred for M1 run/setup

Open `mobile/` in Android Studio when ready. Shell only (login + home stubs).

## Demo credentials

Password for all seeded users: `demo-password`

| Email | Role |
|-------|------|
| `admin@demo.inventory.local` | Owner / Admin |
| `manager@demo.inventory.local` | Inventory Manager |
| `staff@demo.inventory.local` | Staff |
| `other@demo.inventory.local` | Owner of a second org (tenant isolation demos) |

Seed minimums (primary org `demo-retail`): **30 products**, **3 locations**, **5 suppliers**, **8 purchase orders**, opening/receive/dispatch **movement history**.

## AI (Ollama + demo fallback)

- Default: `AI_PROVIDER=demo` — deterministic JSON; works offline.
- Optional: `AI_PROVIDER=ollama` + local [Ollama](https://ollama.com) model; adapter is still a stub until Milestone 3.
- AI never changes stock or owns authoritative balances.

## Milestone backlog

1. **Done (M1)** — env, Docker Postgres, models, migrations, demo login + roles, org scoping, seed, health, smoke tests, README.
2. **M2** — catalog/supplier/location CRUD; PO receiving → atomic balance + immutable ledger; web + mobile product search; barcode path; transfers/counts vertical slice.
3. **M3** — Ollama wiring, reorder assistant, draft PO confirmation, Stockout Radar UI with formula/assumptions.
4. **M4** — offline queue, ML Kit barcode, reports/CSV, polish, E2E/demo recording.

## Known limitations (M1)

- No product/PO/stock CRUD workflows yet (501 Coming Soon).
- Role codes are returned and stored; fine-grained permission matrix on mutations is M2.
- Auth is demo JWT only (local secret; not production SSO).
- Ollama not fully prompt-wired beyond availability ping + demo fallback.
- Web/mobile UI mostly Coming Soon; mobile setup not required for M1.
- Prototype security: env placeholders, no rate limiting beyond stubs, no production hardening.

See `MVP_SPEC.md` for entities, API groups, and acceptance criteria.
