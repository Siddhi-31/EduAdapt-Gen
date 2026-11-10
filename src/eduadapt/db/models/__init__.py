"""Database model registry exporting all declarative tables."""

from eduadapt.db.base import Base, CompatibleJSON, TimestampMixin
from eduadapt.db.models.user import User
from eduadapt.db.models.student import Student
from eduadapt.db.models.curriculum import CurriculumTopic, CurriculumSubtopic
from eduadapt.db.models.question import Question
from eduadapt.db.models.assessment import DiagnosticAttempt, DiagnosticResponse
from eduadapt.db.models.progress import StudentSubtopicMastery, LearningRecommendation
from eduadapt.db.models.tutor import AITutorConversation, AITutorMessage

__all__ = [
    "Base",
    "CompatibleJSON",
    "TimestampMixin",
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
]
