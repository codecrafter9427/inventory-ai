# Inventory AI

Stock and warehouse operations for small retailers, distributors, and small warehouses. Local-first portfolio MVP — no paid APIs required.

## Purpose

Help owners and inventory staff track catalog, locations, purchasing, receiving, counts, transfers, and stock movements. Differentiator: **Stockout Radar** — a transparent risk score from on-hand stock, average daily movement, supplier lead time, and safety stock (formula shown; no certainty claims).

**Milestone 3 (current):** AI provider + DemoAI offline fallback, reorder recommendations with draft-PO confirmation, allowlisted inventory Q&A, Stockout Radar UI, API tests. Mobile / barcode / offline remain M4.

## Tech stack

| Layer | Stack |
|-------|--------|
| Web | Next.js + TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic, REST JSON under `/api/v1` |
| Database | PostgreSQL (UUID PKs, UTC timestamps, decimal money) via Docker Compose |
| AI | `AIProvider` + deterministic `DemoAIProvider`; optional local Ollama adapter |
| Mobile | Kotlin + Jetpack Compose (native Android — not WebView); optional for M3 |
| Auth | Local demo login → JWT (organization + role claims) |

## Project layout

```
products/inventory-ai/
  README.md
  MVP_SPEC.md
  .env.example
  docker-compose.yml      # PostgreSQL only (host port 5435)
  backend/                # FastAPI + models + Alembic + seed + tests
  web/                    # Next.js — catalog / receive / AI / Stockout Radar
  mobile/                 # Android Compose shell (optional)
```

## Setup

### Prerequisites

- Docker (PostgreSQL)
- Python 3.12+
- Node.js 20+ (web)
- Android Studio / JDK 17+ (mobile — optional)
- [Ollama](https://ollama.com) — **optional** (demo works without it)

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
- AI: `POST /api/v1/ai/reorder-recommendations`, `/ai/inventory-question`, `/ai/stockout-radar`, `/ai/confirm-draft-po`

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

Open `http://localhost:3000`. Sign in with demo credentials, then use **Products**, **Purchase orders**, **Stock**, **Reorder AI**, **Stockout Radar**, and **AI Q&A**.

### 6. Mobile (Android) — optional for M3

Open `mobile/` in Android Studio when ready. Shell only for now; device run can wait.

## Demo credentials

Password for all seeded users: `demo-password`

| Email | Role |
|-------|------|
| `admin@demo.inventory.local` | Owner / Admin |
| `manager@demo.inventory.local` | Inventory Manager |
| `staff@demo.inventory.local` | Staff (can receive; cannot create products or confirm AI draft POs) |
| `other@demo.inventory.local` | Owner of a second org (tenant isolation demos) |

Seed minimums (primary org `demo-retail`): **30 products**, **3 locations**, **5 suppliers**, **8 purchase orders**, opening/receive/dispatch **movement history** (including low-stock rows for AI demos).

## Demo steps (Milestone 3 AI slice)

1. Start Postgres, migrate, seed, and run the API (`uvicorn` on `:8000`). Default `AI_PROVIDER=demo` — **no Ollama required**.
2. Start the web app (`npm run dev` → `http://localhost:3000`).
3. Sign in as `admin@demo.inventory.local` / `demo-password`.
4. **Reorder AI** — review recommendations (stock, avg daily movement, lead time, reorder point + assumptions). Select lines → **Confirm draft PO** → verify a `draft` PO appears under Purchase orders. Stock balances are unchanged.
5. **Stockout Radar** — open the differentiator page; confirm formula, inputs, reasons, and assumptions. Scores are risk signals, not predictions.
6. **AI Q&A** — ask e.g. “Which products are low stock?” or “Stockout risk for SKU-009”. Answers are labeled AI content from allowlisted read tools only.
7. (Optional) Sign in as `staff@demo.inventory.local` and confirm draft-PO confirmation is role-denied.

## AI (Ollama optional + demo fallback)

### Demo without Ollama (default)

```bash
# in .env / backend/.env
AI_PROVIDER=demo
```

`DemoAIProvider` returns deterministic explanations over the same computed signals and allowlisted tools. Works fully offline.

### Optional local Ollama

1. Install [Ollama](https://ollama.com) and pull a local open model, e.g. `ollama pull llama3.2`.
2. Ensure Ollama is listening (default `http://localhost:11434`).
3. Set:

```bash
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

4. Restart the API. If Ollama is down or returns invalid JSON, the adapter **falls back** to `DemoAIProvider`.

Rules:

- Backend-only model calls; typed schemas; validated envelopes.
- Q&A uses allowlisted read tools with org auth before execution.
- AI never changes stock or owns authoritative balances.
- Draft PO is created only after explicit `confirm=true` (owner / inventory_manager).
- Label AI content in the UI; no certainty claims on Stockout Radar.

## Milestone backlog

1. **Done (M1)** — env, Docker Postgres, models, migrations, demo login + roles, org scoping, seed, health, smoke tests.
2. **Done (M2)** — products CRUD/search; PO receive → atomic balance + immutable ledger; stock balances/movements; role-gated mutations; web vertical slice; API tests.
3. **Done (M3)** — DemoAI + optional Ollama; reorder assistant + draft PO confirmation; inventory Q&A; Stockout Radar API + UI; AI auth/formula tests.
4. **M4** — offline queue, ML Kit barcode, settings polish, reports/CSV, broader E2E/demo recording, mobile product search.

## Known limitations (M3)

- Transfers, stock counts, supplier/location write APIs, and reports remain **Coming Soon** (501 stubs).
- General PO create/edit UI is not wired; AI confirm creates `draft` POs; receiving uses receivable seeded/API POs.
- Mobile product search / barcode path deferred.
- Auth is demo JWT only (local secret; not production SSO).
- Ollama quality depends on the local model; invalid output falls back to DemoAI.
- Prototype security: env placeholders, limited rate limiting, no production hardening.

See `MVP_SPEC.md` for entities, API groups, and acceptance criteria.
