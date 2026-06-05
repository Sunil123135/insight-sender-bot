"""
Module: alembic/env.py
Purpose: Alembic migration environment for ScrapeSignal
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.config.py (DATABASE_URL)
    - src.db.models.py (metadata)

Used by:
    - alembic upgrade head
"""

# Standard library
from logging.config import fileConfig

# Third-party
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Local
from src.config import settings
from src.db.models import Base
from src.db.url import normalize_database_url

config = context.config
config.set_main_option("sqlalchemy.url", normalize_database_url(settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    """Run Alembic migrations with a sync connection.

    Args:
        connection: SQLAlchemy connection.
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations through async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_async_migrations())
