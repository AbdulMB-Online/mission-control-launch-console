from dataclasses import FrozenInstanceError, asdict
from decimal import Decimal

import pytest

from app.application.reports import ReportService
from app.domain.reports import ReportInput


class RecordingStore:
    """Capture the report at the persistence boundary, without a DB or model."""

    async def save(self, report, traces=()):
        self.saved = report


def submission(payload):
    return ReportInput(**{
        **payload,
        **{field: Decimal(payload[field]) for field in ("wind_knots", "temp_c", "fuel_pct")},
    })


async def test_python_decides_each_boundary_before_persistence(launch_case):
    store = RecordingStore()
    original = submission(launch_case["payload"])
    report = await ReportService(store).file(original)

    assert getattr(report, "verdict", None) == launch_case["verdict"], "Python must decide at submission time"
    assert report.rule_version == "v1"
    assert store.saved is report
    assert len(report.violations) == len(launch_case["violations"])
    for actual, expected in zip(report.violations, launch_case["violations"], strict=True):
        assert actual.field == expected["field"]
        assert actual.observed == Decimal(expected["observed"])
        assert actual.operator == expected["operator"]
        assert actual.limit == Decimal(expected["limit"])
        assert actual.message.strip()
    for field, value in asdict(original).items():
        assert getattr(report, field) == value


@pytest.mark.parametrize("fuel, operator, limit", [("97.999", ">=", "98"), ("100.001", "<=", "100")])
async def test_all_violations_are_returned_in_wind_temperature_fuel_order(report_payload, fuel, operator, limit):
    store = RecordingStore()
    report = await ReportService(store).file(submission({
        **report_payload, "wind_knots": "25.001", "temp_c": "3.999", "fuel_pct": fuel,
    }))

    assert getattr(report, "verdict", None) == "no_go"
    assert [item.field for item in report.violations] == ["wind_knots", "temp_c", "fuel_pct"]
    assert [(item.operator, item.limit) for item in report.violations] == [
        ("<=", Decimal("25")), (">=", Decimal("4")), (operator, Decimal(limit)),
    ]
    assert all(item.message.strip() for item in report.violations)


async def test_python_decision_and_violations_are_immutable(report_payload):
    report = await ReportService(RecordingStore()).file(submission({**report_payload, "wind_knots": "25.001"}))
    assert getattr(report, "verdict", None) == "no_go"
    assert isinstance(report.violations, tuple)
    with pytest.raises(FrozenInstanceError):
        report.verdict = "go"
    with pytest.raises(FrozenInstanceError):
        report.violations[0].observed = Decimal("0")
