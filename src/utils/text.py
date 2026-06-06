"""Text helpers for ScrapeSignal."""


def sanitize_postgres_text(value: str | None) -> str:
    """Remove NUL bytes that PostgreSQL text columns reject.

    Args:
        value: Raw text value.

    Returns:
        Sanitized text safe for PostgreSQL.
    """
    if not value:
        return ""
    return str(value).replace("\x00", "")
