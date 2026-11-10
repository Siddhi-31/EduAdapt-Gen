"""Initial database foundation for EduAdapt.

Revision ID: 0001_initial_database_foundation
Revises: 
Create Date: 2026-11-07 21:50:00

Creates the 11 core tables for EduAdapt:
- users
- students
- curriculum_topics
- curriculum_subtopics
- questions
- diagnostic_attempts
- diagnostic_responses
- student_subtopic_mastery
- learning_recommendations
- ai_tutor_conversations
- ai_tutor_messages
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Dialect-compatible JSON/JSONB type helper
json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("role IN ('student', 'instructor', 'admin')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. students
    op.create_table(
        "students",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("student_code", sa.String(length=50), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("college", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("academic_year", sa.Integer(), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=50), nullable=True),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("has_completed_diagnostic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("current_skill_level", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_students_user_id"),
    )
    op.create_index(op.f("ix_students_user_id"), "students", ["user_id"], unique=True)
    op.create_index(op.f("ix_students_student_code"), "students", ["student_code"], unique=True)

    # 3. curriculum_topics
    op.create_table(
        "curriculum_topics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_curriculum_topics_slug"), "curriculum_topics", ["slug"], unique=True)

    # 4. curriculum_subtopics
    op.create_table(
        "curriculum_subtopics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("topic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["curriculum_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic_id", "slug", name="uq_curriculum_subtopics_topic_slug"),
    )
    op.create_index(op.f("ix_curriculum_subtopics_topic_id"), "curriculum_subtopics", ["topic_id"], unique=False)

    # 5. questions
    op.create_table(
        "questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("subtopic_id", sa.UUID(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("difficulty_level", sa.String(length=50), nullable=False),
        sa.Column("options", json_type, nullable=True),
        sa.Column("correct_answer", json_type, nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("test_cases", json_type, nullable=True),
        sa.Column("marks", sa.Numeric(precision=5, scale=2), server_default="1.00", nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("question_type IN ('MCQ', 'coding', 'short_answer')", name="ck_questions_question_type"),
        sa.CheckConstraint("difficulty_level IN ('beginner', 'intermediate', 'advanced')", name="ck_questions_difficulty_level"),
        sa.ForeignKeyConstraint(["subtopic_id"], ["curriculum_subtopics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_subtopic_id"), "questions", ["subtopic_id"], unique=False)

    # 6. diagnostic_attempts
    op.create_table(
        "diagnostic_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("assessment_type", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="in_progress", nullable=False),
        sa.Column("total_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("maximum_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("assigned_skill_level", sa.String(length=50), nullable=True),
        sa.Column("result_summary", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'abandoned')", name="ck_diagnostic_attempts_status"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnostic_attempts_student_id"), "diagnostic_attempts", ["student_id"], unique=False)

    # 7. diagnostic_responses
    op.create_table(
        "diagnostic_responses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("selected_answer", json_type, nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("marks_obtained", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["diagnostic_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_response"),
    )
    op.create_index(op.f("ix_diagnostic_responses_attempt_id"), "diagnostic_responses", ["attempt_id"], unique=False)
    op.create_index(op.f("ix_diagnostic_responses_question_id"), "diagnostic_responses", ["question_id"], unique=False)

    # 8. student_subtopic_mastery
    op.create_table(
        "student_subtopic_mastery",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("subtopic_id", sa.UUID(), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("successes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("accuracy", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("mastery_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("mastery_status", sa.String(length=50), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("attempts >= 0", name="ck_mastery_attempts_non_negative"),
        sa.CheckConstraint("successes >= 0", name="ck_mastery_successes_non_negative"),
        sa.CheckConstraint("successes <= attempts", name="ck_mastery_successes_le_attempts"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subtopic_id"], ["curriculum_subtopics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "subtopic_id", name="uq_student_subtopic_mastery"),
    )
    op.create_index(op.f("ix_student_subtopic_mastery_student_id"), "student_subtopic_mastery", ["student_id"], unique=False)
    op.create_index(op.f("ix_student_subtopic_mastery_subtopic_id"), "student_subtopic_mastery", ["subtopic_id"], unique=False)

    # 9. learning_recommendations
    op.create_table(
        "learning_recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("subtopic_id", sa.UUID(), nullable=True),
        sa.Column("recommendation_type", sa.String(length=50), nullable=False),
        sa.Column("recommendation_content", json_type, nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'completed', 'dismissed')", name="ck_recommendation_status"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subtopic_id"], ["curriculum_subtopics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_recommendations_student_id"), "learning_recommendations", ["student_id"], unique=False)
    op.create_index(op.f("ix_learning_recommendations_subtopic_id"), "learning_recommendations", ["subtopic_id"], unique=False)

    # 10. ai_tutor_conversations
    op.create_table(
        "ai_tutor_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_tutor_conversations_student_id"), "ai_tutor_conversations", ["student_id"], unique=False)

    # 11. ai_tutor_messages
    op.create_table(
        "ai_tutor_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant', 'student', 'system')", name="ck_tutor_messages_role"),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_tutor_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_tutor_messages_conversation_id"), "ai_tutor_messages", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_table("ai_tutor_messages")
    op.drop_table("ai_tutor_conversations")
    op.drop_table("learning_recommendations")
    op.drop_table("student_subtopic_mastery")
    op.drop_table("diagnostic_responses")
    op.drop_table("diagnostic_attempts")
    op.drop_table("questions")
    op.drop_table("curriculum_subtopics")
    op.drop_table("curriculum_topics")
    op.drop_table("students")
    op.drop_table("users")
