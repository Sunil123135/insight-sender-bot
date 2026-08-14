# ScrapeSignal Pre-Launch Checklist

- [ ] `.env` populated with production values.
- [ ] `DATABASE_URL` points to Neon PostgreSQL with SSL enabled (`sslmode=require`).
- [ ] `python -m poetry run python scripts/init_db.py` completed.
- [ ] `python -m poetry run python scripts/seed_sources.py` inserted 14 sources.
- [ ] `python -m poetry run python -m src.main --dry-run` exits with code 0.
- [ ] `POWER_AUTOMATE_WEBHOOK_URL` is set and the flow maps subject/body correctly.
- [ ] `python -m poetry run python scripts/test_email_delivery.py` succeeds against the webhook.
- [ ] GitHub Actions secrets are configured (`DATABASE_URL`, LLM key, webhook).
- [ ] Manual workflow run succeeds with `dry_run=true`, then `dry_run=false`.
- [ ] First scheduled run is monitored at 07:00 IST.
