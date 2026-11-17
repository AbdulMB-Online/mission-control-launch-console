from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.application.reports import ReportNotFound
from app.api.auth import DirectorAuthenticationError
from app.domain.approvals import ApprovalRejected


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DirectorAuthenticationError)
    async def unauthorized(_request: Request, _exception: DirectorAuthenticationError):
        return JSONResponse(
            {"error": {"code": "unauthorized", "message": "Director credentials are invalid."}},
            status_code=401, headers={"WWW-Authenticate": "Basic"},
        )

    @app.exception_handler(ApprovalRejected)
    async def approval_rejected(_request: Request, exception: ApprovalRejected):
        return JSONResponse({"error": {"code": exception.code, "message": exception.message}}, status_code=exception.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exception: RequestValidationError):
        fields = []
        labels = {"engineer_name": "Engineer name", "station": "Station", "note": "Anomaly note"}
        for error in exception.errors():
            location = [str(part) for part in error["loc"] if part not in ("body", "query", "path")]
            field = ".".join(location) or "body"
            label = labels.get(field, field.replace("_", " ").capitalize())
            if error["type"] in ("missing", "string_too_short"):
                message = f"{label} is required."
            elif error["type"] == "string_too_long":
                message = f"{label} must contain at most {error['ctx']['max_length']} characters."
            elif error["type"] == "extra_forbidden":
                message = f"{field} is not accepted."
            else:
                message = error["msg"].removeprefix("Value error, ")
            fields.append({"field": field, "message": message})
        return JSONResponse(
            {"error": {"code": "validation_error", "message": "Check the highlighted fields.", "fields": fields}},
            status_code=422,
        )

    @app.exception_handler(ReportNotFound)
    async def report_not_found(_request: Request, _exception: ReportNotFound):
        return JSONResponse({"error": {"code": "report_not_found", "message": "Report not found."}}, status_code=404)

    @app.exception_handler(SQLAlchemyError)
    async def storage_unavailable(_request: Request, _exception: SQLAlchemyError):
        return JSONResponse(
            {"error": {"code": "storage_unavailable", "message": "Report storage is unavailable. Try again."}},
            status_code=503,
        )
