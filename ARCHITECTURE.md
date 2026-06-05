# ScrapeSignal Architecture

Pipeline:

```mermaid
flowchart LR
  A["GitHub Actions 01:30 UTC"] --> B["ScrapeSignalOrchestrator"]
  B --> C["ScraperManager"]
  C --> D["Firecrawl/Jina/Apify/arXiv"]
  C --> E["Extractor + PDFParser"]
  E --> F["Deduplicator + RelevanceScorer"]
  F --> G["Neon PostgreSQL"]
  G --> H["Top 20 Articles"]
  H --> I["Claude Summarizer"]
  I --> J["Jinja Email"]
  J --> K["SendGrid"]
  B --> L["Slack Alerts"]
```

The database layer uses SQLAlchemy 2.0 async sessions and PostgreSQL indexes for
the common relevance-score and email-sent queries. External network calls use
`httpx.AsyncClient` with explicit timeouts and retry wrappers.

The schema has six primary tables:

- `articles`
- `dedup_hashes`
- `source_configs`
- `keywords_master`
- `scrape_logs`
- `email_logs`
