from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ReportRow(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("length(engineer_name) BETWEEN 1 AND 100", name="report_name_length"),
        CheckConstraint("length(station) BETWEEN 1 AND 50", name="report_station_length"),
        CheckConstraint("length(note) BETWEEN 1 AND 4000", name="report_note_length"),
        CheckConstraint("verdict IN ('go', 'no_go')", name="report_verdict_value"),
        CheckConstraint("classified_severity IS NULL OR classified_severity IN ('high', 'medium', 'low')", name="report_classified_severity_value"),
        CheckConstraint(
            "(effective_severity = 'high' AND deadline_minutes = 5) OR "
            "(effective_severity = 'medium' AND deadline_minutes = 15) OR "
            "(effective_severity = 'low' AND deadline_minutes = 30)", name="report_priority_mapping",
        ),
        CheckConstraint("verdict = 'go' OR effective_severity = 'high'", name="report_no_go_priority"),
        CheckConstraint("classification_status IN ('not_run', 'completed', 'fallback')", name="report_classification_status"),
        Index("ix_reports_created_id", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engineer_name: Mapped[str] = mapped_column(String(100))
    station: Mapped[str] = mapped_column(String(50))
    wind_knots: Mapped[str] = mapped_column(Text)
    temp_c: Mapped[str] = mapped_column(Text)
    fuel_pct: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(27))
    verdict: Mapped[str] = mapped_column(String(5))
    violations_json: Mapped[str] = mapped_column(Text)
    rule_version: Mapped[str] = mapped_column(String(20))
    classified_severity: Mapped[str | None] = mapped_column(String(6))
    effective_severity: Mapped[str] = mapped_column(String(6))
    deadline_minutes: Mapped[int] = mapped_column(Integer)
    brief_by_at: Mapped[str] = mapped_column(String(27))
    severity_provisional: Mapped[bool] = mapped_column(Boolean)
    subsystem: Mapped[str] = mapped_column(String(32))
    classification_status: Mapped[str] = mapped_column(String(12))
    classification_rationale: Mapped[str] = mapped_column(String(500))
    requires_review: Mapped[bool] = mapped_column(Boolean)
    review_reasons_json: Mapped[str] = mapped_column(Text)


class StepTraceRow(Base):
    __tablename__ = "step_traces"
    __table_args__ = (
        UniqueConstraint("report_id", "step_key", name="uq_report_step"),
        CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="trace_input_tokens"),
        CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="trace_output_tokens"),
        CheckConstraint("cached_input_tokens IS NULL OR (cached_input_tokens >= 0 AND cached_input_tokens <= input_tokens)", name="trace_cached_tokens"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), index=True)
    step_key: Mapped[str] = mapped_column(String(40))
    display_order: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12))
    started_at: Mapped[str] = mapped_column(String(27))
    finished_at: Mapped[str] = mapped_column(String(27))
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(40))
    provider_response_id: Mapped[str | None] = mapped_column(String(128))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    cached_input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    usage_status: Mapped[str] = mapped_column(String(20))
    error_code: Mapped[str | None] = mapped_column(String(40))
    parallel_group: Mapped[str | None] = mapped_column(String(36))


class PipelineCheckRow(Base):
    __tablename__ = "pipeline_checks"
    __table_args__ = (
        UniqueConstraint("report_id", "kind", name="uq_report_check_kind"),
        CheckConstraint("kind IN ('injection', 'missing_information', 'tone')", name="check_kind_value"),
        CheckConstraint("status IN ('completed', 'error')", name="check_status_value"),
        CheckConstraint("(status = 'error' AND flagged IS NULL) OR (status = 'completed' AND flagged IS NOT NULL)", name="check_flag_known"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(12))
    flagged: Mapped[bool | None] = mapped_column(Boolean)
    details_json: Mapped[str] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(40))
