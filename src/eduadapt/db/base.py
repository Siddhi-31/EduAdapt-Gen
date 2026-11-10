"""Declarative base and common mixins for EduAdapt database models."""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON

# Cross-dialect JSON type: uses JSONB on PostgreSQL, falls back to JSON elsewhere
CompatibleJSON = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    """Base class for all EduAdapt SQLAlchemy declarative models."""

    pass


class TimestampMixin:
    """Mixin providing created_at and updated_at timezone-aware timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
