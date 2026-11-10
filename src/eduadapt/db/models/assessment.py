"""Assessment models storing student diagnostic attempts and responses."""

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UUID,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eduadapt.db.base import Base, CompatibleJSON, TimestampMixin

if TYPE_CHECKING:
    from eduadapt.db.models.student import Student
    from eduadapt.db.models.question import Question


class DiagnosticAttempt(Base, TimestampMixin):
    """Student diagnostic or periodic assessment attempt session."""

    __tablename__ = "diagnostic_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assessment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="in_progress",
        nullable=False,
    )
    total_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    maximum_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    assigned_skill_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    result_summary: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    question_ids: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    current_question_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    flagged_question_ids: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    category_scores: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="diagnostic_attempts",
    )
    responses: Mapped[List["DiagnosticResponse"]] = relationship(
        "DiagnosticResponse",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'abandoned')",
            name="ck_diagnostic_attempts_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<DiagnosticAttempt id={self.id} student_id={self.student_id} status={self.status}>"


class DiagnosticResponse(Base, TimestampMixin):
    """Individual question response recorded within an assessment attempt."""

    __tablename__ = "diagnostic_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagnostic_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selected_answer: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    is_correct: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    marks_obtained: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    attempt: Mapped["DiagnosticAttempt"] = relationship(
        "DiagnosticAttempt",
        back_populates="responses",
    )
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="responses",
    )

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_question_response",
        ),
    )

    def __repr__(self) -> str:
        return f"<DiagnosticResponse id={self.id} attempt_id={self.attempt_id} question_id={self.question_id} is_correct={self.is_correct}>"
