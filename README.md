# Inventory AI

Stock and warehouse operations for small retailers, distributors, and small warehouses. Portfolio MVP skeleton — local-first, free-only tooling.

## Purpose

Help owners and inventory staff track catalog, locations, purchasing, receiving, counts, transfers, and stock movements. Differentiator: **Stockout Radar** — a transparent risk score from on-hand stock, average daily movement, supplier lead time, and safety stock (formula shown; no certainty claims).

This repository milestone is a **scaffold only**: runnable shells for backend, web, and Android with Coming Soon routes. Full CRUD, ledger, barcode scanning, and seed scale are backlog.

## Tech stack

| Layer | Stack |
|-------|--------|
| Web | Next.js + TypeScript |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic, REST JSON under `/api/v1` |
| Database | PostgreSQL (UUID PKs planned) via Docker Compose |
| AI | `AIProvider` interface + deterministic `DemoAIProvider`; optional Ollama adapter stub |
| Mobile | Kotlin + Jetpack Compose (native Android — not WebView) |
| Auth | Demo login placeholder only |

No paid APIs, paid models, or paid SaaS are required.

## Project layout

```
products/inventory-ai/
  README.md
  MVP_SPEC.md
  .env.example
  docker-compose.yml      # PostgreSQL only
  backend/                # FastAPI + AI stubs + Alembic
  web/                    # Next.js app shell
  mobile/                 # Android Compose shell
```

## Setup

### Prerequisites

- Docker (PostgreSQL)
- Python 3.12+
- Node.js 20+
- Android Studio / JDK 17+ (for mobile)

### 1. Environment

```bash
cp .env.example .env
# Optional: copy relevant vars into backend/.env and web/.env.local
```

### 2. Database

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- OpenAPI: `http://localhost:8000/docs`
- Demo login: `POST /api/v1/auth/demo-login`
- AI stubs: `POST /api/v1/ai/reorder-recommendations`, `/ai/inventory-question`, `/ai/stockout-radar`
- Business routes return **501 Coming Soon**

Alembic is configured; no initial migration revision is generated yet. Seed script is a placeholder:

```bash
python seed.py
```

### 4. Web

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`. Use demo login shell; major inventory pages are marked Coming Soon / disabled.

Demo credentials (from `.env.example`):

- Email: `admin@demo.inventory.local`
- Password: `demo-password`

### 5. Mobile (Android)

Open `mobile/` in Android Studio, sync Gradle, run on an emulator or device. Demo login + home shortcut stubs only (barcode/receiving/counts are Coming Soon).

## AI (Ollama + demo fallback)

- Default: `DemoAIProvider` — deterministic JSON with explanations; works offline with no model installed.
- Optional: set `AI_PROVIDER=ollama`, `OLLAMA_BASE_URL`, and `OLLAMA_MODEL` after installing [Ollama](https://ollama.com) and pulling a local open model.
- The Ollama adapter is a **stub**: it pings the local server and still returns demo-shaped payloads until real prompt wiring lands.
- AI never changes stock or computes authoritative balances; Stockout Radar formula is transparent and labeled as a risk signal.

## Milestones

1. **Scaffold (current)** — repo/env/db compose/health/demo login shells/Coming Soon routes/AI stubs.
2. **Core vertical slice** — migrations, seed, product CRUD, receive PO → balance + ledger, web + mobile search.
3. **AI + Stockout Radar** — Ollama wiring, reorder assistant, draft PO confirmation, radar UI.
4. **Polish** — counts/transfers offline queue, barcode (ML Kit), tests, demo recording.

## Known limitations

- No real stock ledger, balances, or PO receiving yet.
- No Alembic revision or scaled seed data.
- Auth is demo-only (placeholder bearer token).
- Barcode scanning, offline sync, and CSV export are unimplemented.
- Ollama is not fully wired beyond availability ping + fallback.
- Tests are placeholders only.
- Prototype security: env placeholders, no production hardening.

See `MVP_SPEC.md` for roles, entities, API groups, acceptance criteria, and backlog.
