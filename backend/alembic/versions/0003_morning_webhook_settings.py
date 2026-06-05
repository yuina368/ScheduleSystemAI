"""add morning webhook settings

Revision ID: 0003_morning_webhook_settings
Revises: 0002_weekend_study_settings
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_morning_webhook_settings"
down_revision: Union[str, None] = "0002_weekend_study_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("study_settings", sa.Column("morning_webhook_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("study_settings", "morning_webhook_url")
