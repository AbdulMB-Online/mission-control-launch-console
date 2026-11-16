from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.application.reports import ReportService
from app.domain.reports import ReportInput


CREATED_AT = datetime(2026, 11, 15, 23, 58, tzinfo=UTC)


class MemoryReports:
    async def save(self, report):
        self.report = report

    async def get(self, report_id):
        return self.report if self.report.id == report_id else None

    async def update_priority(self, report):
        self.report = report


async def filed_report(payload):
    store = MemoryReports()
    service = ReportService(store, clock=lambda: CREATED_AT)
    report = await service.file(ReportInput(**{
        **payload,
        **{field: Decimal(payload[field]) for field in ("wind_knots", "temp_c", "fuel_pct")},
    }))
    return service, store, report


async def test_before_classification_priority_is_provisional_high(report_payload):
    _, store, report = await filed_report(report_payload)
    assert getattr(report, "effective_severity", None) == "high"
    assert report.classified_severity is None
    assert report.severity_provisional is True
    assert report.deadline_minutes == 5
    assert report.brief_by_at == CREATED_AT + timedelta(minutes=5)
    assert store.report is report


@pytest.mark.parametrize("severity, minutes", [("high", 5), ("medium", 15), ("low", 30)])
async def test_severity_mapping_is_anchored_to_submission_not_classification_time(report_payload, severity, minutes):
    service, store, original = await filed_report(report_payload)
    service.clock = lambda: CREATED_AT + timedelta(days=2)
    # Internal application operation, never an engineer-facing API endpoint.
    resolved = await service.resolve_priority(original.id, severity)
    assert resolved.effective_severity == severity
    assert resolved.classified_severity == severity
    assert resolved.deadline_minutes == minutes
    assert resolved.brief_by_at == CREATED_AT + timedelta(minutes=minutes)
    assert resolved.brief_by_at.utcoffset() == timedelta(0)
    assert resolved.severity_provisional is False
    assert store.report is resolved
    for field in ("id", "created_at", "wind_knots", "temp_c", "fuel_pct", "note", "verdict", "violations", "rule_version"):
        assert getattr(resolved, field) == getattr(original, field)


@pytest.mark.parametrize("severity", ["high", "medium", "low"])
@pytest.mark.parametrize("field, value", [
    ("wind_knots", "25.001"), ("temp_c", "3.999"), ("fuel_pct", "97.999"), ("fuel_pct", "100.001"),
])
async def test_each_violation_overrides_every_classification_to_high(report_payload, severity, field, value):
    service, store, original = await filed_report({**report_payload, field: value})
    resolved = await service.resolve_priority(original.id, severity)
    assert resolved.classified_severity == severity
    assert resolved.effective_severity == "high"
    assert resolved.deadline_minutes == 5
    assert resolved.brief_by_at == CREATED_AT + timedelta(minutes=5)
    assert resolved.verdict == "no_go"
    assert resolved.violations == original.violations
    assert store.report is resolved


@pytest.mark.parametrize("invalid", [None, "critical", "LOW", True, {"severity": "low"}])
async def test_invalid_severity_falls_back_to_high_without_changing_safety_facts(report_payload, invalid):
    service, _, original = await filed_report(report_payload)
    resolved = await service.resolve_priority(original.id, invalid)
    assert resolved.effective_severity == "high"
    assert resolved.deadline_minutes == 5
    assert resolved.brief_by_at == CREATED_AT + timedelta(minutes=5)
    assert resolved.severity_provisional is False
    for field, value in asdict(original).items():
        if field in ("id", "created_at", "wind_knots", "temp_c", "fuel_pct", "verdict", "rule_version"):
            assert getattr(resolved, field) == value
