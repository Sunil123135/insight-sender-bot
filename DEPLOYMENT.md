# ScrapeSignal Deployment

## Vercel

This project is **not** a Vite or Next.js web app. The daily pipeline runs on
GitHub Actions. If the repo is linked to Vercel, use the repo `vercel.json`
(static `public/` output only). Do **not** set the Vercel build command to
`vite build` — there is no frontend build in this repository.

In the Vercel dashboard, confirm:

- Framework Preset: **Other**
- Build Command: empty (or use repo `vercel.json`)
- Output Directory: `public`

## GitHub Actions

The workflow is `.github/workflows/daily-scrape.yml`. It runs at:

```text
30 1 * * *
```

GitHub schedules are UTC, so this is 07:00 IST.

## Setup

1. Create a Neon PostgreSQL database.
2. Add GitHub Actions secrets listed in `README.md`.
3. Run schema creation:

```powershell
python -m poetry run python scripts/init_db.py
python -m poetry run python scripts/seed_sources.py
```

4. Trigger the workflow manually once with `dry_run=true`.
5. Trigger once with `dry_run=false` after confirming the Power Automate webhook
   accepts the HTML brief and delivers mail correctly.

## Rollback

Pause the scheduled workflow in GitHub Actions. To revert code, redeploy the last
known-good commit. Database migrations are isolated under `alembic/versions`; run
`alembic downgrade -1` only after confirming no production run is active.

## First Week Checks

- Email arrives daily at 07:00 IST.
- Exactly 20 articles are included when enough relevant content exists.
- No duplicate articles appear across days.
- Slack alerts are investigated immediately.
