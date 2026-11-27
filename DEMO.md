# Inventory AI — Demo recording script (Milestone 5)

Short checklist for a screen recording. No video is produced by the agent — follow these steps.

## Prep (once)

1. `docker compose up -d` in `products/inventory-ai`
2. Backend: `alembic upgrade head` → `python seed.py` → `uvicorn app.main:app --reload --port 8000`
3. Web: `cd web && npm run dev` → http://localhost:3000
4. Confirm `AI_PROVIDER=demo` (no Ollama required)
5. (Optional mobile) Open `mobile/` in Android Studio → Gradle sync → run on emulator (API base `http://10.0.2.2:8000/api/v1`)

## Script (~5–7 minutes)

| # | Action | Say / show |
|---|--------|------------|
| 1 | Open login | “Local demo JWT — no paid auth.” Sign in as `admin@demo.inventory.local` / `demo-password`. |
| 2 | Dashboard | Point at KPI tiles: stock value, low/out of stock, pending POs, recent movements (seeded data). |
| 3 | Products | Search a SKU; optionally create a product. Show loading/empty states if useful. |
| 4 | Purchase orders (web) | Open an **ordered** PO → enter qty → confirm receive → note status change. |
| 5 | Stock | Show updated balance + receive movement in the ledger. |
| 6 | Transfers | Create transfer (source ≠ dest) → **Receive transfer** → confirm total preserved. |
| 7 | Counts | Submit counted qty with variance → approve with reason → show adjustment. |
| 8 | Reports | Open Reports → download **CSV stock-on-hand** and **CSV movements**. |
| 9 | Reorder AI | Refresh recommendations → select lines → confirm draft PO → stock unchanged. |
| 10 | Stockout Radar | Open item → show formula, inputs, reasons, assumptions — “risk signal, not a prediction.” |
| 11 | AI Q&A | Ask “Which products are low stock?” → label as AI / allowlisted tools. |
| 12 | (Optional) Staff login | Sign in as staff → show draft-PO confirm denied; receive still works. |
| 13 | **Mobile M5** | Emulator synced: login as `staff@demo.inventory.local` → **Scan barcode** (or deny camera → type `890100000001`) → product → receive qty 1 against PO → show balance after + movement. Or Home → **Receive PO** for manual PO pick. |

## Close

Mention known gaps: suppliers/locations write, settings, offline queue, mobile count/transfer/adjust.
