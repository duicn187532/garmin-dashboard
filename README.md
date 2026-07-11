# Garmin Insight

Garmin Insight is a monorepo MVP for personal Garmin data search, health trend review, training load metrics, and grounded AI analysis.

The app treats Garmin Connect as the device sync source, then stores normalized data in your own database. The short-term connector can use unofficial Garmin libraries or deterministic demo data. The service boundary keeps room for a future official Garmin Connect Developer Program API connector.

## Structure

```text
backend/  FastAPI, SQLAlchemy, SQLite/PostgreSQL-ready schema, sync, metrics, AI
web/      React + Vite + Tailwind mobile-first PWA
mobile/   Expo React Native iOS app
shared/   API contract and shared TypeScript types
```

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Load demo data and create a grounded AI report:

```bash
python -m app.jobs.sync_garmin
python -m app.jobs.run_ai_analysis
```

Web:

```bash
cd web
npm install
npm run dev
```

Mobile:

```bash
cd mobile
npm install
npm run ios
```

For Expo Go on a physical iPhone, set the mobile Settings API Base URL to your computer LAN address, for example `http://192.168.1.10:8000`.

## Environment

Create `backend/.env` from `backend/.env.example`.

- `DATABASE_URL`: defaults to `sqlite:///./garmin_insight.db`; use PostgreSQL in production.
- `DEMO_MODE`: `true` loads deterministic local demo data; set `false` for real Garmin sync.
- `GARMIN_EMAIL`, `GARMIN_PASSWORD`, `GARMIN_MFA_CODE`: used only by the unofficial connector.
- `SYNC_TOKEN`: protects scheduled sync calls in production.
- `AI_PROVIDER`: defaults to `gemini`; set `local` to avoid external LLM calls.
- `GEMINI_API_KEY`: Gemini API key from Google AI Studio. Without it, AI falls back to the local grounded rule-based provider.
- `GEMINI_MODEL`: defaults to `gemini-2.5-flash-lite` to target Gemini's low-cost/free-tier-friendly model path.

Do not commit `.env`, tokens, SQLite DB files, raw Garmin files, or personal exports.

## Key API Workflows

- Sync: `POST /api/sync/garmin` with `{ "days": 30 }`. For first-time Garmin MFA initialization, include `{ "days": 30, "mfa_code": "123456" }`.
- Today dashboard: `GET /api/dashboard/today`
- Activity search: `GET /api/activities?...filters`
- Health trend: `GET /api/health/trends?metric=hrv&range=30d`
- AI analysis: `POST /api/ai/analyze`
- Natural language query: `POST /api/ai/query`

AI reports are grounded by database evidence and store `evidence_json` with dates, activities, and metrics used for the answer.

## Cloud Deployment

Recommended path:

- Backend: Google Cloud Run with `backend/Dockerfile`.
- Database: MongoDB Atlas; set `DATABASE_BACKEND=mongodb`, `MONGODB_URI`, and `MONGODB_DATABASE`.
- Web: GitHub Pages via `.github/workflows/deploy-web-pages.yml`.
- Sync job: GitHub Actions schedule or platform cron calling `/api/sync/garmin`, then `/api/ai/analyze`.
- iOS: Expo/EAS Build requires an Expo account and Apple Developer account before App Store distribution.

Deployment notes are in `deploy/README.md`.

GitHub Actions sync example is in `.github/workflows/scheduled-sync.yml`. Add repository secrets:

- `API_URL`
- `SYNC_TOKEN`

In MongoDB production mode, successful Garmin login tokens are stored in MongoDB so Cloud Run restarts do not require a new MFA flow unless Garmin invalidates the session.

For GitHub Pages, add repository variables:

- `VITE_API_BASE_URL`: your Cloud Run backend URL.
- `VITE_BASE_PATH`: `/REPOSITORY_NAME/` for project pages or `/` for user/org pages.

## Tests and Checks

Backend:

```bash
cd backend
pytest
```

Web:

```bash
cd web
npm run build
```

Mobile:

```bash
cd mobile
npm install
npm run ios
```

The real Garmin path requires valid Garmin credentials, MFA/token handling, and the unofficial library installed. The official Garmin API connector is represented by an interface stub for later replacement.
