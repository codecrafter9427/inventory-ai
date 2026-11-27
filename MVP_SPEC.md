# Inventory AI — MVP Specification

## Purpose

Stock and warehouse operations for small retailers, distributors, and small warehouses. Portfolio MVP; local demo without paid APIs.

## Roles

| Role | Code | Capabilities |
|------|------|----------------|
| Owner / Admin | `owner` | Settings, users, all reports; catalog + receive; confirm AI draft PO; approve counts |
| Inventory Manager | `inventory_manager` | Catalog, suppliers, purchasing, stock; receive; confirm AI draft PO; approve counts |
| Staff | `staff` | Receiving, counts (submit), transfers, dispatch; limited settings (no catalog create / no AI draft PO / no count approve) |

Milestone 2+: mutating endpoints enforce organization match and role gates (`forbidden_role` / org-scoped 404).

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
| `/purchase-orders` | List + detail read implemented; write Coming Soon (except AI draft confirm) |
| `/receipts` | `POST` receive implemented (atomic balance + ledger) |
| `/stock/balances`, `/stock/movements` | Read implemented |
| `/stock/transfers` | Thin slice: list/create/receive (qty preserved) |
| `/stock/counts` | Thin slice: create/submit/approve (variance reason required) |
| `/reports/inventory` (+ CSV exports) | Implemented (deterministic) |
| `/dashboard/summary` | Implemented (KPI tiles) |
| `/suppliers` | Coming Soon (501; auth required) |
| `/ai/reorder-recommendations` | Implemented (signals + DemoAI/Ollama narration; auth) |
| `/ai/inventory-question` | Implemented (allowlisted read tools; auth) |
| `/ai/stockout-radar` | Implemented (deterministic formula + AI narration; auth) |
| `/ai/confirm-draft-po` | Implemented (confirm=true; catalog roles; no stock change) |

Error shape: `{ "error": { "code", "message", "details" } }`.

## Differentiator — Stockout Radar

Transparent risk score from stock on hand, average daily movement, supplier lead time, and safety stock. Show formula, inputs, reason, and assumptions. Avoid certainty claims.

Formula:

`risk = clamp(1 - coverage_days / (lead_time_days + safety_stock/avg_daily), 0, 1)` where `coverage_days = on_hand / avg_daily_movement`.

Endpoint: `POST /api/v1/ai/stockout-radar`.

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

### Milestone 3 (met)

- [x] `AIProvider` with deterministic `DemoAIProvider` + optional Ollama adapter (fallback on failure)
- [x] Reorder recommendations from movement / stock / lead time / reorder point; explain assumptions
- [x] Draft PO only after user confirmation (`/ai/confirm-draft-po`); never change stock directly
- [x] Natural-language inventory Q&A via allowlisted read tools; org auth before tools; typed schemas
- [x] Stockout Radar: transparent formula, reasons, assumptions; no certainty claims
- [x] Web UI: reorder + Stockout Radar + AI Q&A (AI content labeled; confirm for draft PO)
- [x] Tests: DemoAI paths, Stockout Radar determinism, auth on AI endpoints
- [x] README: Ollama optional setup + demo without Ollama

### Milestone 4 (met)

- [x] Polish primary web flows: loading/error/empty, confirmations, disabled Coming Soon nav
- [x] Inventory reports + CSV export (stock-on-hand / movements) — deterministic
- [x] Thin transfers + stock-count approval slice (variance reason required)
- [x] Dashboard KPI tiles from seeded data
- [x] Expanded pytest coverage; lint/typecheck commands documented
- [x] README complete + DEMO.md recording script
- [x] Mobile: demo login + product search calling same APIs (code); Android Studio sync documented

### Milestone 5 (met — mobile code; Studio sync to run)

- [x] Native Android CameraX + free ML Kit barcode scanning (`CAMERA` permission)
- [x] Manual barcode/SKU fallback when camera denied or unavailable
- [x] Scan → product resolve via `GET /products?q=` (exact barcode preferred client-side)
- [x] Mobile PO receive: receivable PO/line → confirm qty + PO location → `POST /receipts`
- [x] Post-receive UI shows balance after + recent movements
- [x] Home shortcuts: Scan + Receive enabled; count/transfer/adjust remain Coming Soon
- [x] Docs: README / DEMO / MVP_SPEC / mobile README updated; backend receive pytest regression

### Full MVP (later)

1. Create product on web and search it on mobile. *(web + mobile search code in M4)*
2. Receive PO atomically updates balance and immutable ledger. *(done)*
3. Barcode scan opens the correct product (ML Kit; manual search fallback). *(done in M5 mobile code)*
4. Count variance requires approval and reason. *(thin web/API slice in M4)*
5. Transfer preserves total quantity across locations. *(thin slice in M4)*
6. AI uses seeded records and only creates a draft PO after user confirmation. *(done)*
7. Stockout Radar shows formula + assumptions; never claims certainty. *(done)*
8. Local setup works with Docker Postgres, demo login, Ollama optional / DemoAI fallback. *(done)*

## Backlog (post-M5)

- Offline queue for count/receiving drafts + conflict UI
- Settings (org, roles, units, reorder defaults)
- Suppliers / locations write APIs
- Full multi-line transfer/count mobile workflows
- Broader E2E / recorded demo video

## Non-goals (MVP)

- Paid OCR, maps, SMS, analytics, or LLM APIs
- Production SSO / hosted auth as a requirement
- Certified accounting or guarantee of stockout predictions
