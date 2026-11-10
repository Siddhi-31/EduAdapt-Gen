"""EduAdapt Database Module.

Provides SQLAlchemy 2.0 ORM models, session lifecycle, security utilities,
and database connection management for PostgreSQL.
"""

from eduadapt.db.base import Base, CompatibleJSON, TimestampMixin
from eduadapt.db.models import (
    User,
    Student,
    CurriculumTopic,
    CurriculumSubtopic,
    Question,
    DiagnosticAttempt,
    DiagnosticResponse,
    StudentSubtopicMastery,
    LearningRecommendation,
    AITutorConversation,
    AITutorMessage,
)
from eduadapt.db.security import (
    hash_password,
    verify_password,
    normalize_email,
    needs_rehash,
)
from eduadapt.db.session import (
    get_async_engine,
    get_sync_engine,
    get_async_session_factory,
    get_sync_session_factory,
    get_db_session,
    get_sync_db_session,
    check_database_connection,
    check_database_connection_sync,
    close_database_connections,
    normalize_database_url,
)

__all__ = [
    # Base
    "Base",
    "CompatibleJSON",
    "TimestampMixin",
    # Models
    "User",
    "Student",
    "CurriculumTopic",
    "CurriculumSubtopic",
    "Question",
    "DiagnosticAttempt",
    "DiagnosticResponse",
    "StudentSubtopicMastery",
    "LearningRecommendation",
    "AITutorConversation",
    "AITutorMessage",
    # Security
    "hash_password",
    "verify_password",
    "normalize_email",
    "needs_rehash",
    # Session & Lifecycle
    "get_async_engine",
    "get_sync_engine",
    "get_async_session_factory",
    "get_sync_session_factory",
    "get_db_session",
    "get_sync_db_session",
    "check_database_connection",
    "check_database_connection_sync",
    "close_database_connections",
    "normalize_database_url",
]
