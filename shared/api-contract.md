# Garmin Insight API Contract

Base URL defaults to `http://localhost:8000`.

## Status and Sync

- `GET /api/status`
- `POST /api/sync/garmin`
  - Body: `{ "days": 30 }`
  - Header: `X-Sync-Token: <token>` when `SYNC_TOKEN` is set.
- `GET /api/sync/status`

## Dashboard

- `GET /api/summary`
- `GET /api/dashboard/today`
- `GET /api/dashboard/trends?range=7d|30d|90d`

## Activities

- `GET /api/activities`
  - Query: `start_date`, `end_date`, `activity_type`, `min_distance`, `max_distance`, `min_avg_hr`, `max_avg_hr`, `min_training_load`, `sort`, `page`, `page_size`
- `GET /api/activities/{activity_id}`
- `GET /api/activities/{activity_id}/laps`
- `GET /api/activities/{activity_id}/trackpoints`

## Health

- `GET /api/health/daily`
- `GET /api/health/trends?metric=sleep|hrv|rhr|stress|steps|body_battery&range=7d|30d|90d`

## AI

- `POST /api/ai/analyze`
  - Body: `{ "report_type": "today" }`
- `POST /api/ai/query`
  - Body: `{ "question": "最近 14 天我的恢復狀態如何？" }`
- `GET /api/ai/latest`
- `GET /api/ai/reports`

AI responses include `evidence_json`. The backend must query the database before creating an answer and must say when data is insufficient.

