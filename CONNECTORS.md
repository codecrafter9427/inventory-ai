# Inventory AI — Connectors

## Insights connector (v1, read-only)

Versioned HTTP surface for **Agent 5 / Insights** to pull inventory KPIs without a user JWT.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/connectors/insights/v1/health` | GET | Liveness + connector identity |
| `/api/v1/connectors/insights/v1/summary` | GET | KPI summary (reuses dashboard/report math) |

### Auth

1. `Authorization: Bearer <INSIGHTS_CONNECTOR_TOKEN>`
2. `X-Organization-Id: <uuid>` — target tenant

Token is compared with constant-time equality against env `INSIGHTS_CONNECTOR_TOKEN`. If the env var is empty, both endpoints return **401** (`connector_disabled`).

User demo JWTs are **not** accepted on these routes.

### Summary fields

| Field | Source |
|-------|--------|
| `inventory_value` | Sum of on-hand qty × product cost (same as dashboard `stock_value`) |
| `low_stock_items` | Balance rows with `0 < qty ≤ reorder_point` |
| `out_of_stock_items` | Balance rows with `qty ≤ 0` |
| `pending_purchase_orders` | POs in `draft` / `ordered` / `partially_received` |
| `recent_movement_count` | Recent ledger rows (dashboard window) |
| `product_count` / `location_count` / `balance_rows` | Active catalog / locations / balances |

### Example

```bash
curl -s \
  -H "Authorization: Bearer $INSIGHTS_CONNECTOR_TOKEN" \
  -H "X-Organization-Id: <org-uuid>" \
  http://localhost:8000/api/v1/connectors/insights/v1/summary
```

Resolve org UUID via demo login (`organization_id`) or DB seed (`demo-retail`).

### Non-goals

- No writes, no stock mutations, no AI calls
- Not a public multi-tenant SaaS API — shared secret for local/portfolio integration only
