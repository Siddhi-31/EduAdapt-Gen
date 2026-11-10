"""Progress models storing topic/subtopic mastery and learning recommendations."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
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

from eduadapt.db.base import Base, CompatibleJSON

if TYPE_CHECKING:
    from eduadapt.db.models.student import Student
    from eduadapt.db.models.curriculum import CurriculumSubtopic


class StudentSubtopicMastery(Base):
    """Student persistent mastery state for individual curriculum subtopics."""

    __tablename__ = "student_subtopic_mastery"

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
    subtopic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_subtopics.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    successes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    accuracy: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    mastery_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    mastery_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    last_attempted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="subtopic_mastery_records",
    )
    subtopic: Mapped["CurriculumSubtopic"] = relationship(
        "CurriculumSubtopic",
        back_populates="mastery_records",
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subtopic_id",
            name="uq_student_subtopic_mastery",
        ),
        CheckConstraint(
            "attempts >= 0",
            name="ck_mastery_attempts_non_negative",
        ),
        CheckConstraint(
            "successes >= 0",
            name="ck_mastery_successes_non_negative",
        ),
        CheckConstraint(
            "successes <= attempts",
            name="ck_mastery_successes_le_attempts",
        ),
    )

    def __repr__(self) -> str:
        return f"<StudentSubtopicMastery student={self.student_id} subtopic={self.subtopic_id} mastery={self.mastery_score}>"


class LearningRecommendation(Base):
    """Personalized learning recommendations emitted by adaptive logic."""

    __tablename__ = "learning_recommendations"

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
    subtopic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_subtopics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recommendation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    recommendation_content: Mapped[Any] = mapped_column(
        CompatibleJSON,
        nullable=False,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="learning_recommendations",
    )
    subtopic: Mapped[Optional["CurriculumSubtopic"]] = relationship(
        "CurriculumSubtopic",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'completed', 'dismissed')",
            name="ck_recommendation_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<LearningRecommendation id={self.id} student_id={self.student_id} type={self.recommendation_type}>"
