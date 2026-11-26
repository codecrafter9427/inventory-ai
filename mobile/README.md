# Inventory AI — Android (Jetpack Compose)

Native Kotlin + Compose app (not WebView). Shares the FastAPI backend with the web app.

## Android Studio sync required

This project needs a full **Android Studio Gradle sync** (and a local Android SDK / JDK 17) before it can compile or run on an emulator/device. Code-only changes land here; **device run remains a documented limitation** until Studio sync succeeds on your machine.

1. Open `products/inventory-ai/mobile` in Android Studio.
2. Trust the project and let Gradle sync (download wrapper/SDK if prompted).
3. If `gradlew` / `gradle-wrapper.jar` are missing, use Android Studio’s “Create Gradle Wrapper” or `gradle wrapper`.
4. Start the backend on the host (`uvicorn` on port **8000**).
5. Run the `app` configuration on an emulator (API base defaults to `http://10.0.2.2:8000/api/v1`).
6. On a physical device, set the API host to your PC’s LAN IP in `ApiClient` (`baseUrl`).

## What works (code)

| Screen | Behavior |
|--------|----------|
| Demo login | `POST /auth/demo-login` with seeded credentials |
| Home | Shortcuts; unimplemented actions disabled (“Coming Soon”) |
| Product search | `GET /products` + tap row → `GET /stock/balances?q=SKU` |

## Coming Soon / gaps

- ML Kit barcode scanning
- Mobile PO receive / count / transfer / adjustment UIs
- Offline draft queue + conflict UI
- Device run without Android Studio sync

## Demo credentials

Password: `demo-password`  
Email: `admin@demo.inventory.local` (or manager/staff)
