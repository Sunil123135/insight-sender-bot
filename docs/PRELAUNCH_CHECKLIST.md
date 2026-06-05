# ScrapeSignal Pre-Launch Checklist

- [ ] `.env` populated with production values.
- [ ] `DATABASE_URL` points to Neon PostgreSQL with SSL enabled.
- [ ] `python -m poetry run python scripts/init_db.py` completed.
- [ ] `python -m poetry run python scripts/seed_sources.py` inserted 14 sources.
- [ ] `python -m poetry run python -m src.main --dry-run` exits with code 0.
- [ ] SendGrid sender email is verified.
- [ ] `python -m poetry run python scripts/test_email_delivery.py --recipient sunil.lalwani@quidelortho.com` succeeds.
- [ ] GitHub Actions secrets are configured.
- [ ] Manual workflow run succeeds.
- [ ] First scheduled run is monitored at 07:00 IST.
