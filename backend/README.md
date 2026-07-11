# Garmin Insight Backend

FastAPI backend for Garmin personal data search, dashboard metrics, idempotent sync, and grounded AI reports.

## Local Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

The default `.env.example` uses `DEMO_MODE=true`, so `POST /api/sync/garmin` imports deterministic demo data without Garmin credentials.

## Production Database

Set MongoDB Atlas in production:

```env
DATABASE_BACKEND=mongodb
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=garmin_insight
```

SQLite remains the default for local development and tests.

## Useful Commands

```bash
python -m app.jobs.sync_garmin
python -m app.jobs.run_ai_analysis
pytest
```

## Real Garmin Sync

Install `garminconnect` or `garth`, set `DEMO_MODE=false`, then set `GARMIN_EMAIL` and `GARMIN_PASSWORD` in `.env`.

For accounts that trigger MFA, run this once from a terminal:

```bash
python -m app.jobs.setup_garmin_tokens
```

This stores Garmin session tokens in `GARMIN_TOKENSTORE` so the web Sync button can reuse them. The connector boundary is in `app/services/garmin/`; the official Garmin API can replace the unofficial connector without changing the API contract.

Never commit `.env`, SQLite databases, tokens, raw Garmin files, or personal health exports.
