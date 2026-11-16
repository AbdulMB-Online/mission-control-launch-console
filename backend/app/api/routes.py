from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.schemas import ReportCreate, ReportPage, ReportRead
from app.application.reports import ReportService
from app.infrastructure.repository import SQLAlchemyReportStore


router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


async def get_reports(request: Request) -> ReportService:
    return ReportService(SQLAlchemyReportStore(request.app.state.database.sessions))


Reports = Annotated[ReportService, Depends(get_reports)]


@router.post("", status_code=201, response_model=ReportRead)
async def file_report(submission: ReportCreate, response: Response, reports: Reports, request: Request):
    report = await reports.file(submission.to_submission())
    if request.app.state.pipeline_runner is not None:
        request.app.state.pipeline_runner.schedule(report.id)
    response.headers["Location"] = f"/api/v1/reports/{report.id}"
    return ReportRead.from_report(report)


@router.get("", response_model=ReportPage)
async def list_reports(
    reports: Reports,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = await reports.list(limit, offset)
    return ReportPage(items=[ReportRead.from_report(item) for item in items], total=total, limit=limit, offset=offset)


@router.get("/{report_id}", response_model=ReportRead)
async def read_report(report_id: UUID, reports: Reports):
    return ReportRead.from_report(await reports.get(str(report_id)))
