from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import Settings
from app.infrastructure.db import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.database = Database(settings.database_url)
        await app.state.database.migrate()
        try:
            yield
        finally:
            await app.state.database.close()

    app = FastAPI(title="Mission Control", lifespan=lifespan)

    @app.get("/healthz")
    async def health():
        if not await app.state.database.ready():
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return JSONResponse({
            "status": "ok",
            "service": "mission-control",
            "provider": settings.llm_provider,
        })

    return app
