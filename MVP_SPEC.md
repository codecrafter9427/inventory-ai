# Inventory AI — MVP Specification

## Purpose

Stock and warehouse operations for small retailers, distributors, and small warehouses. Portfolio MVP; local demo without paid APIs.

## Roles

| Role | Code | Capabilities |
|------|------|----------------|
| Owner / Admin | `owner` | Settings, users, all reports; catalog + receive |
| Inventory Manager | `inventory_manager` | Catalog, suppliers, purchasing, stock; receive |
| Staff | `staff` | Receiving, counts, transfers, dispatch; limited settings (no catalog create) |

Milestone 2: mutating endpoints enforce organization match and role gates (`forbidden_role` / org-scoped 404).

## Entities (schema implemented)

Organization, User, Role, Product, Category, Unit, Location, Supplier, PurchaseOrder, PurchaseOrderLine, StockBalance, StockMovement, StockCount, StockCountLine, StockTransfer, StockTransferLine, AuditEvent.

UUID primary keys, UTC timestamps, decimal monetary values, organization scoping on every business record.

## API groups (`/api/v1`)

| Group | Status |
|-------|--------|
| `/auth/demo-login` | Implemented (DB-backed demo JWT) |
| `/me` | Implemented |
| `/organizations/current`, `/organizations/{id}` | Implemented (tenant-scoped) |
| `/products` | Implemented (CRUD + search by SKU/name/barcode) |
| `/categories`, `/units` | List read implemented; write Coming Soon |
| `/locations` | List read implemented; write Coming Soon |
| `/purchase-orders` | List + detail read implemented; write Coming Soon |
| `/receipts` | `POST` receive implemented (atomic balance + ledger) |
| `/stock/balances`, `/stock/movements` | Read implemented |
| `/suppliers`, `/stock/counts`, `/stock/transfers`, `/reports/inventory` | Coming Soon (501; auth required) |
| `/ai/reorder-recommendations` | Demo stub (auth required) |
| `/ai/inventory-question` | Demo stub (auth required) |
| `/ai/stockout-radar` | Demo stub (differentiator; auth required) |

Error shape: `{ "error": { "code", "message", "details" } }`.

## Differentiator — Stockout Radar

Transparent risk score from stock on hand, average daily movement, supplier lead time, and safety stock. Show formula, inputs, reason, and assumptions. Avoid certainty claims. Scaffold endpoint: `POST /api/v1/ai/stockout-radar`.

## Acceptance criteria

### Milestone 1 (met)

- [x] Backend starts; `/health` OK
- [x] Alembic initial migration applies cleanly
- [x] Seed: ≥30 products, 3 locations, 5 suppliers, 8 POs, movement history
- [x] Demo login for Owner, Inventory Manager, Staff (+ second org user)
- [x] Org scoping: wrong-org access denied (403)
- [x] Smoke tests for health, auth, tenant basics
- [x] `AIProvider` + `DemoAIProvider` + Ollama adapter stub retained
- [x] README: setup, env, migrations, seed, credentials, limitations, backlog

### Milestone 2 (met)

- [x] Products CRUD API + web create/list/search (SKU/name/barcode)
- [x] Purchase order receive updates `StockBalance` + immutable `StockMovement` atomically
- [x] Stock balances + recent movements readable on web
- [x] Org-scoped authorization on mutating endpoints (+ role gates)
- [x] API tests for CRUD, tenant isolation, receive transaction
- [x] README demo steps for the workflow; other features marked Coming Soon

### Full MVP (later milestones)

1. Create product on web and search it on mobile.
2. Receive PO atomically updates balance and immutable ledger. *(web path done in M2)*
3. Barcode scan opens the correct product (ML Kit; manual search fallback).
4. Count variance requires approval and reason.
5. Transfer preserves total quantity across locations.
6. AI uses seeded records and only creates a draft PO after user confirmation.
7. Stockout Radar shows formula + assumptions; never claims certainty.
8. Local setup works with Docker Postgres, demo login, Ollama optional / DemoAI fallback.

## Backlog

### Milestone 3

- Real Ollama prompt wiring and schema validation
- Reorder assistant + draft PO confirmation flow
- Stockout Radar UI with formula/assumptions
- Reports + CSV export (partial)

### Milestone 4

- ML Kit barcode scanning
- Offline queue for count/receiving drafts + conflict UI
- Settings (org, roles, units, reorder defaults)
- Broader unit/API/E2E coverage and demo recording
- Stock transfers + count sessions (full workflows)
- Mobile product search vertical slice

## Non-goals (MVP)

- Paid OCR, maps, SMS, analytics, or LLM APIs
- Production SSO / hosted auth as a requirement
- Certified accounting or guarantee of stockout predictions
