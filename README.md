# ScrapeSignal

ScrapeSignal is a production-oriented daily intelligence pipeline for Supply Chain + AI.
It scrapes configured industry sources, scores and deduplicates articles, summarizes the
top results, and delivers the daily brief to Power Automate.

## Quick Start

```powershell
python -m poetry install
Copy-Item .env.example .env
python -m poetry run python scripts/init_db.py
python -m poetry run python scripts/seed_sources.py
python -m poetry run python -m src.main --dry-run
```

Use Python 3.11 through Poetry. The daily GitHub Actions cron is `30 1 * * *`,
which is 07:00 IST.

## Neon Database Setup

ScrapeSignal uses the Neon project **SupplyChainSignalScraper** (`wispy-cloud-93669868`).

1. Install the Neon CLI and authenticate: `npx neonctl auth`
2. Fetch the pooled connection string (recommended for GitHub Actions):

```powershell
npx neonctl connection-string production --project-id wispy-cloud-93669868 --pooled
```

3. Copy the result into `.env` and GitHub Actions secret `DATABASE_URL`, using the
   `postgresql+psycopg://` prefix if it is not already present.
4. Initialize schema and seed data:

```powershell
python -m poetry run python scripts/init_db.py
python -m poetry run python scripts/seed_sources.py
```

If port 5432 is blocked on your network, use the WebSocket bootstrap instead:

```powershell
npm install @neondatabase/serverless ws --no-save
node scripts/setup_neon_remote.mjs
```

5. Configure GitHub Actions secrets and trigger the first dry run:

```powershell
gh auth login
git remote add origin https://github.com/<owner>/<repo>.git
.\scripts\setup_github.ps1 -Repo <owner>/<repo>
```

If you are on a corporate network that blocks outbound PostgreSQL port 5432, local
Python runs may time out. GitHub Actions can still reach Neon; trigger the workflow manually
with `dry_run=true` after updating the `DATABASE_URL` secret.

## Required Production Secrets

- `DATABASE_URL` (Neon pooled URL with `sslmode=require`)
- `GROQ_API_KEY` or `GEMINI_API_KEY` (Groq primary, Gemini fallback)
- `POWER_AUTOMATE_WEBHOOK_URL`

Optional but recommended:

- `JINA_API_KEY` (fallback scraper in native -> Jina -> Apify chain)
- `APIFY_API_TOKEN` (final scraper fallback)
- `GEMINI_API_KEY` (LLM fallback when Groq is unavailable)
- `SLACK_WEBHOOK_URL`

## Scraper Chain

Sources use `scraper_type=chain` by default:

1. **Native** — built-in httpx + BeautifulSoup scraper (no API key)
2. **Jina Reader** — if native content is too thin
3. **Apify** — if Jina also fails

## LLM Summarization

1. **Groq** (`GROQ_MODEL=llama-3.3-70b-versatile`)
2. **Gemini fallbacks** (`gemini-2.5-flash`, `gemini-3-flash-preview`, `gemini-2.0-flash`)
3. **Extractive fallback** — first 240 characters of article body

## Quality Gates

```powershell
python -m poetry run black --check src tests scripts
python -m poetry run ruff check src tests scripts
python -m poetry run mypy src
python -m poetry run pytest --cov=src
```
