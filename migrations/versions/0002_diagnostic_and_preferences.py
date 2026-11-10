"""Add diagnostic and preference columns to students, questions, and diagnostic_attempts.

Revision ID: 0002_diagnostic_and_preferences
Revises: 0001_initial_foundation
Create Date: 2026-11-07 23:42:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_diagnostic_and_preferences"
down_revision: Union[str, None] = "0001_initial_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    # 1. students additions
    with op.batch_alter_table("students") as batch_op:
        batch_op.add_column(sa.Column("learning_pace", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("explanation_style", sa.String(length=50), server_default="step_by_step", nullable=True))
        batch_op.add_column(sa.Column("preferences", json_type, nullable=True))
        batch_op.add_column(sa.Column("accessibility", json_type, nullable=True))

    # 2. questions additions
    with op.batch_alter_table("questions") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=100), nullable=True))
        batch_op.alter_column("subtopic_id", existing_type=sa.UUID(), nullable=True)

    # 3. diagnostic_attempts additions
    with op.batch_alter_table("diagnostic_attempts") as batch_op:
        batch_op.add_column(sa.Column("question_ids", json_type, nullable=True))
        batch_op.add_column(sa.Column("current_question_index", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("flagged_question_ids", json_type, nullable=True))
        batch_op.add_column(sa.Column("category_scores", json_type, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("diagnostic_attempts") as batch_op:
        batch_op.drop_column("category_scores")
        batch_op.drop_column("flagged_question_ids")
        batch_op.drop_column("current_question_index")
        batch_op.drop_column("question_ids")

    with op.batch_alter_table("questions") as batch_op:
        batch_op.alter_column("subtopic_id", existing_type=sa.UUID(), nullable=False)
        batch_op.drop_column("category")

    with op.batch_alter_table("students") as batch_op:
        batch_op.drop_column("accessibility")
        batch_op.drop_column("preferences")
        batch_op.drop_column("explanation_style")
        batch_op.drop_column("learning_pace")
