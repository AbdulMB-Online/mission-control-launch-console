"""One tracked worker: durable claims, responsive requests and safe recovery."""

import asyncio
import logging

from app.application.ports import LLMGateway, ReportStore
from app.application.reports import ReportService


logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(self, store: ReportStore, gateway: LLMGateway, timeout_seconds: float = 270):
        self.store = store
        self.gateway = gateway
        self.timeout_seconds = timeout_seconds
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker: asyncio.Task | None = None
        self._closing = False

    async def start(self):
        for report_id in await self.store.recover_pipeline():
            self.schedule(report_id)
        self._worker = asyncio.create_task(self._work(), name="mission-control-pipeline")

    def schedule(self, report_id: str):
        if not self._closing:
            self._queue.put_nowait(report_id)

    async def wait_idle(self):
        await self._queue.join()

    async def _work(self):
        while True:
            report_id = await self._queue.get()
            try:
                await self._process(report_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Do not log provider exceptions, prompt text or SQL parameters.
                logger.error("Pipeline storage failure for report %s", report_id)
            finally:
                self._queue.task_done()

    async def _process(self, report_id):
        if not await self.store.claim_pipeline(report_id):
            return
        service = ReportService(self.store)
        try:
            async with asyncio.timeout(self.timeout_seconds):
                await service.classify(report_id, self.gateway)
                await service.run_checks(report_id, self.gateway)
                await service.generate_briefing(report_id, self.gateway)
        except asyncio.CancelledError:
            await self.store.fail_pipeline(report_id, "interrupted")
            raise
        except TimeoutError:
            await self.store.fail_pipeline(report_id, "pipeline_timeout")
        except Exception:
            await self.store.fail_pipeline(report_id, "pipeline_error")

    async def aclose(self):
        self._closing = True
        if self._worker is not None:
            self._worker.cancel()
            await asyncio.gather(self._worker, return_exceptions=True)
