# Inventory AI — MVP Specification (Scaffold)

## Purpose

Stock and warehouse operations for small retailers, distributors, and small warehouses. Portfolio MVP; local demo without paid APIs.

## Roles

| Role | Capabilities |
|------|----------------|
| Owner / Admin | Settings, users, all reports |
| Inventory Manager | Catalog, suppliers, purchasing, stock |
| Staff | Receiving, counts, transfers, dispatch; limited settings |

Scaffold today: demo login returns `owner` for documented credentials; otherwise `staff`. Role enforcement on business endpoints is Coming Soon.

## Entities (planned)

Organization, User, Role, Product, Category, Unit, Location, Supplier, PurchaseOrder, PurchaseOrderLine, StockBalance, StockMovement, StockCount, StockCountLine, StockTransfer, StockTransferLine, AuditEvent.

UUID primary keys, UTC timestamps, organization scoping on every business record.

## API groups (`/api/v1`)

| Group | Scaffold status |
|-------|-----------------|
| `/auth/demo-login` | Implemented (placeholder) |
| `/products` | Coming Soon (501) |
| `/categories` | Coming Soon (501) |
| `/units` | Coming Soon (501) |
| `/locations` | Coming Soon (501) |
| `/suppliers` | Coming Soon (501) |
| `/purchase-orders` | Coming Soon (501) |
| `/receipts` | Coming Soon (501) |
| `/stock/balances` | Coming Soon (501) |
| `/stock/movements` | Coming Soon (501) |
| `/stock/counts` | Coming Soon (501) |
| `/stock/transfers` | Coming Soon (501) |
| `/reports/inventory` | Coming Soon (501) |
| `/ai/reorder-recommendations` | Demo stub |
| `/ai/inventory-question` | Demo stub |
| `/ai/stockout-radar` | Demo stub (differentiator) |

Error shape (target): `{ "error": { "code", "message", "details" } }`.

## Differentiator — Stockout Radar

Transparent risk score from:

- stock on hand
- average daily movement
- supplier lead time
- safety stock

Show formula, inputs, reason, and assumptions. Avoid certainty claims. AI may explain the signal; deterministic code owns the score. Scaffold endpoint: `POST /api/v1/ai/stockout-radar`.

## Acceptance criteria (full MVP — not met by scaffold)

1. Create product on web and search it on mobile.
2. Receive PO atomically updates balance and immutable ledger.
3. Barcode scan opens the correct product (ML Kit; manual search fallback).
4. Count variance requires approval and reason.
5. Transfer preserves total quantity across locations.
6. AI uses seeded records and only creates a draft PO after user confirmation.
7. Stockout Radar shows formula + assumptions; never claims certainty.
8. Local setup works with Docker Postgres, demo login, Ollama optional / DemoAI fallback.

## Scaffold acceptance (this milestone)

- [x] Backend starts; `/health` OK
- [x] `/api/v1` package layout with Coming Soon business routes
- [x] `AIProvider` + `DemoAIProvider` + Ollama adapter stub
- [x] Alembic + seed placeholders
- [x] Web demo login + Coming Soon pages for major routes
- [x] Android Compose shell: demo login + home shortcuts stubs
- [x] `docker-compose.yml` PostgreSQL only
- [x] README, MVP_SPEC, `.env.example`

## Backlog (unimplemented)

- Full CRUD for catalog, locations, suppliers
- Immutable stock ledger and authoritative balances
- Purchase orders + atomic receiving with discrepancy notes
- Stock transfers (initiated / in-transit / received)
- Stock count sessions, variance approval
- Reports + CSV export
- Settings (org, roles, units, reorder defaults)
- Alembic initial migration + scaled fictional seed (30 products, 3 locations, 5 suppliers, 8 POs)
- Real Ollama prompt wiring and schema validation
- Tenant authorization enforcement on every endpoint
- ML Kit barcode scanning
- Offline queue for count/receiving drafts + conflict UI
- Unit/API/E2E tests beyond placeholders
- Web dashboard live metrics

## Non-goals (MVP)

- Paid OCR, maps, SMS, analytics, or LLM APIs
- Production SSO / hosted auth as a requirement
- Certified accounting or guarantee of stockout predictions
