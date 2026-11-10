"""Question model storing assessment, diagnostic, and practice questions."""

from decimal import Decimal
from typing import Any, List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eduadapt.db.base import Base, CompatibleJSON, TimestampMixin

if TYPE_CHECKING:
    from eduadapt.db.models.curriculum import CurriculumSubtopic
    from eduadapt.db.models.assessment import DiagnosticResponse


class Question(Base, TimestampMixin):
    """Question item for diagnostic assessments and practice exercises."""

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    subtopic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_subtopics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    difficulty_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    options: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    correct_answer: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    test_cases: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("1.00"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    subtopic: Mapped["CurriculumSubtopic"] = relationship(
        "CurriculumSubtopic",
        back_populates="questions",
    )
    responses: Mapped[List["DiagnosticResponse"]] = relationship(
        "DiagnosticResponse",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('MCQ', 'coding', 'short_answer')",
            name="ck_questions_question_type",
        ),
        CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_questions_difficulty_level",
        ),
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} type={self.question_type} difficulty={self.difficulty_level}>"
