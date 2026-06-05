"""Export idempotent seed SQL for remote Neon initialization."""

from __future__ import annotations

import runpy
from pathlib import Path

_seed = runpy.run_path(str(Path(__file__).with_name("seed_sources.py")))
SOURCES: list[dict[str, object]] = _seed["SOURCES"]
KEYWORDS: list[dict[str, object]] = _seed["KEYWORDS"]


def _sql_str(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def main() -> None:
    """Print INSERT statements for sources and keywords."""
    for source in SOURCES:
        print(
            "INSERT INTO source_configs "
            "(source_key, name, url, scraper_type, enabled, priority, max_articles, "
            "created_at, updated_at) "
            f"VALUES ({_sql_str(source['source_key'])}, {_sql_str(source['name'])}, "
            f"{_sql_str(source['url'])}, {_sql_str(source['scraper_type'])}, TRUE, "
            f"{int(source['priority'])}, 150, NOW(), NOW()) "
            "ON CONFLICT (source_key) DO NOTHING;"
        )
    for keyword in KEYWORDS:
        print(
            "INSERT INTO keywords_master "
            "(keyword, tier, weight, category, enabled, created_at) "
            f"VALUES ({_sql_str(keyword['keyword'])}, {int(keyword['tier'])}, "
            f"{float(keyword['weight'])}, {_sql_str(keyword['category'])}, TRUE, NOW()) "
            "ON CONFLICT ON CONSTRAINT uq_keyword_tier DO NOTHING;"
        )


if __name__ == "__main__":
    main()
