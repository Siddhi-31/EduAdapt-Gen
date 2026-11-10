"""Student profile model storing academic and diagnostic profile information."""

from typing import Any, List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eduadapt.db.base import Base, CompatibleJSON, TimestampMixin

if TYPE_CHECKING:
    from eduadapt.db.models.user import User
    from eduadapt.db.models.assessment import DiagnosticAttempt
    from eduadapt.db.models.progress import StudentSubtopicMastery, LearningRecommendation
    from eduadapt.db.models.tutor import AITutorConversation


class Student(Base, TimestampMixin):
    """Student academic profile extending core user identity."""

    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    student_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    college: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    academic_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    semester: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    section: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    has_completed_diagnostic: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    current_skill_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    learning_pace: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    explanation_style: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="step_by_step",
        nullable=True,
    )
    preferences: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    accessibility: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="student_profile",
    )
    diagnostic_attempts: Mapped[List["DiagnosticAttempt"]] = relationship(
        "DiagnosticAttempt",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    subtopic_mastery_records: Mapped[List["StudentSubtopicMastery"]] = relationship(
        "StudentSubtopicMastery",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    learning_recommendations: Mapped[List["LearningRecommendation"]] = relationship(
        "LearningRecommendation",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    tutor_conversations: Mapped[List["AITutorConversation"]] = relationship(
        "AITutorConversation",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} code={self.student_code} name={self.full_name}>"
