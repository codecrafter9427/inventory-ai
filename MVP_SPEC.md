# Inventory AI — MVP Specification

## Purpose

Stock and warehouse operations for small retailers, distributors, and small warehouses. Portfolio MVP; local demo without paid APIs.

## Roles

| Role | Code | Capabilities |
|------|------|----------------|
| Owner / Admin | `owner` | Settings (org + reorder defaults), users, all reports; catalog + receive; confirm AI draft PO; approve counts |
| Inventory Manager | `inventory_manager` | Catalog, suppliers, locations, units, purchasing (PO write), stock; receive; confirm AI draft PO; approve counts |
| Staff | `staff` | Receiving, counts (submit), transfers, dispatch; no catalog/supplier/location/PO create; no AI draft PO / no count approve |

Milestone 2+: mutating endpoints enforce organization match and role gates (`forbidden_role` / org-scoped 404).

## Entities (schema implemented)

Organization (incl. reorder defaults), User, Role, Product, Category, Unit, Location, Supplier, PurchaseOrder, PurchaseOrderLine, StockBalance, StockMovement, StockCount, StockCountLine, StockTransfer, StockTransferLine, AuditEvent.

UUID primary keys, UTC timestamps, decimal monetary values, organization scoping on every business record.

## API groups (`/api/v1`)

| Group | Status |
|-------|--------|
| `/auth/demo-login` | Implemented (rate-limited; DB-backed demo JWT) |
| `/me` | Implemented |
| `/organizations/current`, `/organizations/{id}` | Implemented (tenant-scoped) |
| `/settings/organization`, `/settings/roles`, `/settings/units` | Implemented (M6) |
| `/products` | Implemented (CRUD + search) |
| `/categories`, `/units` | List read; category write Coming Soon; units create via `/settings/units` |
| `/locations` | List + create/update/deactivate (M6) |
| `/suppliers` | List + create/update/deactivate (M6) |
| `/purchase-orders` | List/detail + create/edit/submit/cancel (M6) |
| `/receipts` | `POST` receive implemented (atomic balance + ledger + audit) |
| `/stock/balances`, `/stock/movements` | Read implemented |
| `/stock/transfers` | Thin slice |
| `/stock/counts` | Thin slice |
| `/reports/inventory` (+ CSV), `/dashboard/summary` | Implemented |
| `/connectors/insights/v1/health`, `/summary` | Implemented (service token + org header) |
| `/ai/*` | Reorder, Q&A, Stockout Radar, confirm-draft-po |

Error shape: `{ "error": { "code", "message", "details" } }`.

## Differentiator — Stockout Radar

Transparent risk score from stock on hand, average daily movement, supplier lead time, and safety stock. Show formula, inputs, reason, and assumptions. Avoid certainty claims.

Formula:

`risk = clamp(1 - coverage_days / (lead_time_days + safety_stock/avg_daily), 0, 1)` where `coverage_days = on_hand / avg_daily_movement`.

Endpoint: `POST /api/v1/ai/stockout-radar`.

## Acceptance criteria

### Milestone 1–5 (met)

See prior checklists in git history / README backlog. M1 foundation through M5 mobile barcode + receive.

### Milestone 6 (met)

- [x] Supplier + location write APIs + Settings UI (org / roles / units / reorder defaults migration)
- [x] PO create / edit / submit / cancel; keep `POST /receipts` receive
- [x] Ledger integrity helper + tests (balance vs sum movements)
- [x] Tests: receiving, permissions, org isolation on new writes
- [x] Hardening: login rate limit; password / JWT TTL notes; audit on PO submit/receive/supplier/location; BACKUP.md; CI; `.env.example` demo vs prod; Docker health unchanged
- [x] Insights connector health + summary (Bearer `INSIGHTS_CONNECTOR_TOKEN` + `X-Organization-Id`)
- [x] Docs + version `0.6.0-m6`; pytest green

### Full MVP (later)

1. Create product on web and search it on mobile.
2. Receive PO atomically updates balance and immutable ledger.
3. Barcode scan opens the correct product.
4. Count variance requires approval and reason.
5. Transfer preserves total quantity across locations.
6. AI uses seeded records and only creates a draft PO after user confirmation.
7. Stockout Radar shows formula + assumptions; never claims certainty.
8. Local setup works with Docker Postgres, demo login, Ollama optional / DemoAI fallback.

## Backlog (post-M6)

- Offline queue for count/receiving drafts + conflict UI
- Full multi-line transfer/count mobile workflows
- Broader E2E / recorded demo video
- Production auth / stronger connector identity

## Non-goals (MVP)

- Paid OCR, maps, SMS, analytics, or LLM APIs
- Production SSO / hosted auth as a requirement
- Certified accounting or guarantee of stockout predictions
