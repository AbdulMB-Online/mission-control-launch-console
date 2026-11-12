from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class Database:
    def __init__(self, url: str):
        path = make_url(url).database
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_async_engine(url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

        @event.listens_for(self.engine.sync_engine, "connect")
        def configure_sqlite(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    def migration_config(self):
        root = Path(__file__).resolve().parents[2]
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "migrations"))
        return config

    async def migrate(self):
        def upgrade(connection):
            config = self.migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "head")

        async with self.engine.begin() as connection:
            await connection.run_sync(upgrade)

    async def ready(self):
        try:
            async with self.engine.connect() as connection:
                current = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            return current == ScriptDirectory.from_config(self.migration_config()).get_current_head()
        except SQLAlchemyError:
            return False

    async def close(self):
        await self.engine.dispose()
