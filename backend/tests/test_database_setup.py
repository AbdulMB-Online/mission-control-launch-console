from sqlalchemy import text

from app.infrastructure.db import Database


async def test_migrations_and_sqlite_connection_protections(settings):
    database = Database(settings.database_url)
    try:
        await database.migrate()
        async with database.engine.connect() as connection:
            assert (await connection.execute(text("PRAGMA foreign_keys"))).scalar() == 1
            assert (await connection.execute(text("PRAGMA journal_mode"))).scalar() == "wal"
            assert (await connection.execute(text("PRAGMA busy_timeout"))).scalar() >= 5000
            assert (await connection.execute(text("SELECT version_num FROM alembic_version"))).scalar() == "0001"
        assert await database.ready()
    finally:
        await database.close()


async def test_restart_migration_preserves_existing_data(settings):
    first = Database(settings.database_url)
    try:
        await first.migrate()
        async with first.engine.begin() as connection:
            await connection.execute(text("CREATE TABLE restart_probe (value TEXT NOT NULL)"))
            await connection.execute(text("INSERT INTO restart_probe VALUES ('preserved')"))
    finally:
        await first.close()

    restarted = Database(settings.database_url)
    try:
        await restarted.migrate()
        async with restarted.engine.connect() as connection:
            assert (await connection.execute(text("SELECT value FROM restart_probe"))).scalar() == "preserved"
    finally:
        await restarted.close()
