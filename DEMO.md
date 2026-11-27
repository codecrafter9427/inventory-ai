# Inventory AI — Demo recording script (Milestone 6)

Short checklist for a screen recording. No video is produced by the agent — follow these steps.

## Prep (once)

1. `docker compose up -d` in `inventory-ai`
2. Backend: `alembic upgrade head` → `python seed.py` → `uvicorn app.main:app --reload --port 8000`
3. Web: `cd web && npm run dev` → http://localhost:3000
4. Confirm `AI_PROVIDER=demo` (no Ollama required)
5. Optional: set `INSIGHTS_CONNECTOR_TOKEN=demo-connector` for connector curl
6. (Optional mobile) Open `mobile/` in Android Studio → Gradle sync → emulator

## Script (~6–8 minutes)

| # | Action | Say / show |
|---|--------|------------|
| 1 | Open login | “Local demo JWT — no paid auth.” Sign in as `admin@demo.inventory.local` / `demo-password`. |
| 2 | Dashboard | KPI tiles from seeded data. |
| 3 | Settings | Org reorder defaults + units; mention roles read-only; owner-only org save. |
| 4 | Suppliers / Locations | Create one supplier and one location. |
| 5 | Purchase orders | **New draft PO** → **Submit** → receive qty → show status. Optionally cancel another draft. |
| 6 | Stock | Updated balance + receive movement. |
| 7 | Transfers / Counts | Thin slice as before. |
| 8 | Reports | CSV stock-on-hand / movements. |
| 9 | Reorder AI / Radar / Q&A | Confirm draft PO; show formula; ask low-stock question. |
| 10 | (Optional) Staff login | Staff can receive; cannot create supplier/PO. |
| 11 | (Optional) Connector | `curl` health + summary with Bearer token + `X-Organization-Id`. |
| 12 | (Optional) Mobile | Scan/receive as in M5. |

## Close

Mention remaining gaps: offline queue, full mobile count/transfer, production auth.
