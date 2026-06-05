"""add daily subject limit priority

Revision ID: 0004_daily_subject_limit_priority
Revises: 0003_morning_webhook_settings
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_daily_subject_limit_priority"
down_revision: Union[str, None] = "0003_morning_webhook_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("study_settings", sa.Column("max_daily_subjects", sa.Integer(), nullable=True))
    op.execute("UPDATE study_settings SET max_daily_subjects = 3 WHERE max_daily_subjects IS NULL")
    op.add_column("study_plans", sa.Column("priority_score", sa.Float(), nullable=True))
    op.add_column("study_plans", sa.Column("priority_reasons", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("study_plans", "priority_reasons")
    op.drop_column("study_plans", "priority_score")
    op.drop_column("study_settings", "max_daily_subjects")
