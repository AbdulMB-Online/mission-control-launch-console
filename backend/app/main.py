from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.errors import register_error_handlers
from app.api.routes import router as report_router
from app.config import Settings
from app.application.runner import PipelineRunner
from app.infrastructure.db import Database
from app.infrastructure.repository import SQLAlchemyReportStore
from app.infrastructure.llm.fake_gateway import FakeGateway
from app.infrastructure.llm.openai_gateway import OpenAIGateway


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.database = Database(settings.database_url)
        app.state.llm_gateway = None
        app.state.pipeline_runner = None
        try:
            await app.state.database.migrate()
            app.state.llm_gateway = (
                FakeGateway() if settings.llm_provider == "fake" else
                OpenAIGateway(settings.openai_api_key.get_secret_value(), settings.openai_model)
            )
            if settings.pipeline_autostart:
                app.state.pipeline_runner = PipelineRunner(
                    SQLAlchemyReportStore(app.state.database.sessions), app.state.llm_gateway,
                    settings.pipeline_timeout_seconds,
                )
                await app.state.pipeline_runner.start()
            yield
        finally:
            try:
                if app.state.pipeline_runner is not None:
                    await app.state.pipeline_runner.aclose()
            finally:
                try:
                    if app.state.llm_gateway is not None:
                        await app.state.llm_gateway.aclose()
                finally:
                    await app.state.database.close()

    app = FastAPI(title="Mission Control", lifespan=lifespan)
    app.state.settings = settings
    register_error_handlers(app)
    app.include_router(report_router)

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
