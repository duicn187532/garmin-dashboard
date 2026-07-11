# Production Deployment

This project is prepared for:

- MongoDB Atlas as the production database.
- Google Cloud Run for the FastAPI backend container.
- GitHub Pages for the Vite PWA frontend.

## 1. MongoDB Atlas

Create an Atlas cluster, database user, and connection string. Set:

```env
DATABASE_BACKEND=mongodb
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>/<database>?retryWrites=true&w=majority
MONGODB_DATABASE=garmin_insight
```

The backend creates indexes at startup.

## 2. Gemini API

Create a Gemini API key in Google AI Studio and store it as `GEMINI_API_KEY`.

Production defaults:

```env
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash-lite
```

If `GEMINI_API_KEY` is not set, AI analysis still works through the local grounded rule-based provider, but it will not call Gemini.

## 3. Google Cloud Run

Create an Artifact Registry repository, then build and deploy:

```bash
gcloud artifacts repositories create garmin-insight --repository-format=docker --location=asia-east1
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=asia-east1,_ARTIFACT_REPOSITORY=garmin-insight,_CORS_ORIGINS=https://YOUR_GITHUB_USERNAME.github.io
```

Store secrets in Secret Manager before deployment:

```bash
gcloud secrets create MONGODB_URI --data-file=-
gcloud secrets create GARMIN_EMAIL --data-file=-
gcloud secrets create GARMIN_PASSWORD --data-file=-
gcloud secrets create APP_ACCESS_TOKEN --data-file=-
gcloud secrets create SYNC_TOKEN --data-file=-
```

`GEMINI_API_KEY` is optional at initial deployment. Add it later with:

```bash
gcloud secrets create GEMINI_API_KEY --data-file=-
gcloud run services update garmin-insight-backend \
  --region asia-east1 \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

## 4. GitHub Pages

In GitHub repository settings:

1. Enable Pages.
2. Set source to GitHub Actions.
3. Add repository variables:
   - `VITE_API_BASE_URL`: Cloud Run service URL.
   - `VITE_BASE_PATH`: `/REPOSITORY_NAME/` for project pages, or `/` for user/org pages.

The workflow is `.github/workflows/deploy-web-pages.yml`.

Because GitHub Pages is static, the app access token is not bundled at build time. Enter it once in the Web app Settings screen; it is stored in that browser's local storage and sent as `X-App-Token`.

## 5. Verify Production

Run from the repository root:

```powershell
.\scripts\verify-production.ps1 `
  -ApiUrl "https://YOUR-CLOUD-RUN-URL" `
  -WebUrl "https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPOSITORY/" `
  -AppToken "YOUR_APP_ACCESS_TOKEN" `
  -SyncToken "YOUR_SYNC_TOKEN"
```
