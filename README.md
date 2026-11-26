# Inventory AI

Stock and warehouse operations for small retailers, distributors, and small warehouses. Local-first portfolio MVP — no paid APIs required.

## Purpose

Help owners and inventory staff track catalog, locations, purchasing, receiving, counts, transfers, and stock movements. Differentiator: **Stockout Radar** — a transparent risk score from on-hand stock, average daily movement, supplier lead time, and safety stock (formula shown; no certainty claims).

**Milestone 2 (current):** products CRUD + search, purchase-order receiving (atomic `StockBalance` + immutable `StockMovement`), stock balances/movements on web, org-scoped auth on mutations, API tests. AI / barcode / offline / reports remain Coming Soon (M3–M4).

## Tech stack

| Layer | Stack |
|-------|--------|
| Web | Next.js + TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic, REST JSON under `/api/v1` |
| Database | PostgreSQL (UUID PKs, UTC timestamps, decimal money) via Docker Compose |
| AI | `AIProvider` + deterministic `DemoAIProvider`; optional Ollama adapter stub |
| Mobile | Kotlin + Jetpack Compose (native Android — not WebView); optional for M2 |
| Auth | Local demo login → JWT (organization + role claims) |

## Project layout

```
products/inventory-ai/
  README.md
  MVP_SPEC.md
  .env.example
  docker-compose.yml      # PostgreSQL only (host port 5435)
  backend/                # FastAPI + models + Alembic + seed + tests
  web/                    # Next.js — products / PO receive / stock
  mobile/                 # Android Compose shell (optional)
```

## Setup

### Prerequisites

- Docker (PostgreSQL)
- Python 3.12+
- Node.js 20+ (web)
- Android Studio / JDK 17+ (mobile — optional for M2)

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
- Products: `GET/POST /api/v1/products` (search `?q=`)
- Purchase orders: `GET /api/v1/purchase-orders`
- Receive: `POST /api/v1/receipts`
- Stock: `GET /api/v1/stock/balances`, `GET /api/v1/stock/movements`

### 4. Tests

```bash
cd backend
pytest tests -q
```

### 5. Web

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`. Sign in with demo credentials, then use **Products**, **Purchase orders**, and **Stock**.

### 6. Mobile (Android) — optional for M2

Open `mobile/` in Android Studio when ready. Shell only for now; device run can wait.

## Demo credentials

Password for all seeded users: `demo-password`

| Email | Role |
|-------|------|
| `admin@demo.inventory.local` | Owner / Admin |
| `manager@demo.inventory.local` | Inventory Manager |
| `staff@demo.inventory.local` | Staff (can receive; cannot create products) |
| `other@demo.inventory.local` | Owner of a second org (tenant isolation demos) |

Seed minimums (primary org `demo-retail`): **30 products**, **3 locations**, **5 suppliers**, **8 purchase orders**, opening/receive/dispatch **movement history**.

## Demo steps (Milestone 2 vertical slice)

1. Start Postgres, migrate, seed, and run the API (`uvicorn` on `:8000`).
2. Start the web app (`npm run dev` → `http://localhost:3000`).
3. Sign in as `admin@demo.inventory.local` / `demo-password`.
4. **Products** — click **New product**, enter SKU/name/barcode/unit/prices, save. Search by SKU, name, or barcode and confirm the new row appears.
5. **Purchase orders** — open an order with status `ordered` or `partially received` (e.g. seeded `PO-2026-004`). Enter receive quantities (optionally add discrepancy notes) and click **Receive stock**.
6. **Stock** — confirm the product balance increased at the PO location and a `receive` movement appears in recent movements.
7. (Optional) Sign in as `other@demo.inventory.local` and confirm primary-org products/POs are not visible (tenant isolation).

## AI (Ollama + demo fallback)

- Default: `AI_PROVIDER=demo` — deterministic JSON; works offline.
- Optional: `AI_PROVIDER=ollama` + local [Ollama](https://ollama.com) model; adapter is still a stub until Milestone 3.
- AI never changes stock or owns authoritative balances.

## Milestone backlog

1. **Done (M1)** — env, Docker Postgres, models, migrations, demo login + roles, org scoping, seed, health, smoke tests.
2. **Done (M2)** — products CRUD/search; PO receive → atomic balance + immutable ledger; stock balances/movements; role-gated mutations; web vertical slice; API tests.
3. **M3** — Ollama wiring, reorder assistant, draft PO confirmation, Stockout Radar UI with formula/assumptions, reports + CSV (partial).
4. **M4** — offline queue, ML Kit barcode, settings polish, broader E2E/demo recording.

## Known limitations (M2)

- Transfers, stock counts, supplier/location write APIs, and reports remain **Coming Soon** (501 stubs).
- PO create/edit is not wired; receiving uses seeded receivable POs (or API-created test POs).
- Mobile product search / barcode path deferred; web covers the primary slice.
- Auth is demo JWT only (local secret; not production SSO).
- Ollama not fully prompt-wired beyond availability ping + demo fallback.
- Prototype security: env placeholders, limited rate limiting, no production hardening.

See `MVP_SPEC.md` for entities, API groups, and acceptance criteria.
