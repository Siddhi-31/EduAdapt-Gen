"""AI Tutor conversation history and message persistence models."""

from datetime import datetime
from typing import Any, List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UUID,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eduadapt.db.base import Base, CompatibleJSON, TimestampMixin

if TYPE_CHECKING:
    from eduadapt.db.models.student import Student


class AITutorConversation(Base, TimestampMixin):
    """AI Tutor conversation session for a student."""

    __tablename__ = "ai_tutor_conversations"

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
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="tutor_conversations",
    )
    messages: Mapped[List["AITutorMessage"]] = relationship(
        "AITutorMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AITutorMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<AITutorConversation id={self.id} student_id={self.student_id} title={self.title}>"


class AITutorMessage(Base):
    """Individual message within an AI Tutor conversation session."""

    __tablename__ = "ai_tutor_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_tutor_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    context: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["AITutorConversation"] = relationship(
        "AITutorConversation",
        back_populates="messages",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'student', 'system')",
            name="ck_tutor_messages_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<AITutorMessage id={self.id} conversation_id={self.conversation_id} role={self.role}>"
