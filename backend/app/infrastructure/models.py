from sqlalchemy import CheckConstraint, Index, String, Text
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
