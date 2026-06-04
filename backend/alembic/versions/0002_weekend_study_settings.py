"""add weekend study settings

Revision ID: 0002_weekend_study_settings
Revises: 0001_initial
Create Date: 2026-06-04 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_weekend_study_settings"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("study_settings", sa.Column("weekday_available_hours", sa.Float(), nullable=True))
    op.add_column("study_settings", sa.Column("weekend_available_hours", sa.Float(), nullable=True))
    op.execute(
        """
        UPDATE study_settings
        SET weekday_available_hours = daily_available_hours
        WHERE weekday_available_hours IS NULL
        """
    )
    op.execute(
        """
        UPDATE study_settings
        SET weekend_available_hours = daily_available_hours
        WHERE weekend_available_hours IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("study_settings", "weekend_available_hours")
    op.drop_column("study_settings", "weekday_available_hours")
