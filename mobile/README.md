# Inventory AI — Android (Jetpack Compose)

Native Kotlin + Compose app (not WebView). Shares the FastAPI backend with the web app.

## Android Studio sync required

This project needs a full **Android Studio Gradle sync** (and a local Android SDK / JDK 17) before it can compile or run on an emulator/device. Code-only changes land here; **device run remains a documented limitation** until Studio sync succeeds on your machine.

1. Open `products/inventory-ai/mobile` in Android Studio.
2. Trust the project and let Gradle sync (download wrapper/SDK if prompted). CameraX + ML Kit barcode deps are declared in `app/build.gradle.kts`.
3. If `gradlew` / `gradle-wrapper.jar` are missing, use Android Studio’s “Create Gradle Wrapper” or `gradle wrapper`.
4. Start the backend on the host (`uvicorn` on port **8000**).
5. Run the `app` configuration on an emulator (API base defaults to `http://10.0.2.2:8000/api/v1`).
6. On a physical device, set the API host to your PC’s LAN IP in `ApiClient` (`baseUrl`).

## What works (code) — M5

| Screen | Behavior |
|--------|----------|
| Demo login | `POST /auth/demo-login` with seeded credentials |
| Home | Product search, **Scan barcode**, **Receive PO** enabled; count/transfer/adjust Coming Soon |
| Product search | `GET /products` + tap row → `GET /stock/balances?q=SKU` |
| Barcode scan | CameraX + free ML Kit on-device barcode; `CAMERA` permission; deny → manual barcode/SKU entry |
| Receive PO | List receivable POs (`ordered` / `partially_received`) → pick line → confirm qty + PO location → `POST /receipts` → show balance after + recent movements |
| Scan → receive | Resolve barcode via products API → filter receivable PO lines for that product |

## Manual verify (emulator / device)

1. Backend + seed running; emulator API host `10.0.2.2:8000`.
2. Login as `staff@demo.inventory.local` / `demo-password` (ops role can receive).
3. **Receive (manual):** Home → Receive PO → open an ordered/partial PO → pick a line with remaining qty → confirm qty ≤ remaining → Confirm receive → see balance after + movement.
4. **Scan path:** Home → Scan barcode → allow camera (or deny for manual) → scan/type seeded barcode e.g. `890100000001` → pick matching PO line → receive qty `1` → success shows balance + movement.
5. **Negative:** qty above remaining → API error shown; non-receivable PO statuses never listed.

## Coming Soon / gaps

- Offline draft queue + conflict UI
- Mobile count / transfer / adjustment UIs
- Device run without Android Studio sync

## Demo credentials

Password: `demo-password`  
Email: `admin@demo.inventory.local` (or manager/staff)

Seeded product barcodes: `890100000001`, `890100000002`, … (see `backend/seed.py`).
