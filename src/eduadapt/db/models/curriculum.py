"""Curriculum models representing topics and subtopics for PPS and adaptive learning."""

from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UUID, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eduadapt.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from eduadapt.db.models.question import Question
    from eduadapt.db.models.progress import StudentSubtopicMastery


class CurriculumTopic(Base, TimestampMixin):
    """High-level curriculum topics (e.g. Loops, Arrays, Pointers)."""

    __tablename__ = "curriculum_topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    subtopics: Mapped[List["CurriculumSubtopic"]] = relationship(
        "CurriculumSubtopic",
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="CurriculumSubtopic.display_order",
    )

    def __repr__(self) -> str:
        return f"<CurriculumTopic id={self.id} slug={self.slug} name={self.name}>"


class CurriculumSubtopic(Base, TimestampMixin):
    """Granular subtopics within a parent curriculum topic."""

    __tablename__ = "curriculum_subtopics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    topic: Mapped["CurriculumTopic"] = relationship(
        "CurriculumTopic",
        back_populates="subtopics",
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="subtopic",
        cascade="all, delete-orphan",
    )
    mastery_records: Mapped[List["StudentSubtopicMastery"]] = relationship(
        "StudentSubtopicMastery",
        back_populates="subtopic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "topic_id",
            "slug",
            name="uq_curriculum_subtopics_topic_slug",
        ),
    )

    def __repr__(self) -> str:
        return f"<CurriculumSubtopic id={self.id} slug={self.slug} name={self.name}>"
