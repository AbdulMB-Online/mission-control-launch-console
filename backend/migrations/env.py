import asyncio

from alembic import context

from app.config import Settings
from app.infrastructure.db import Database


def run(connection):
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


async def run_online():
    database = Database(Settings().database_url)
    try:
        async with database.engine.connect() as connection:
            await connection.run_sync(run)
    finally:
        await database.close()


provided_connection = context.config.attributes.get("connection")
if provided_connection is not None:
    run(provided_connection)
else:
    asyncio.run(run_online())
