"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "study_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("daily_available_hours", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("deadline_date", sa.Date(), nullable=False),
        sa.Column("required_hours", sa.Float(), nullable=False),
        sa.Column("completed_hours", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subjects_user_id"), "subjects", ["user_id"], unique=False)

    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("planned_hours", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "subject_id", "plan_date", name="uq_plan_user_subject_date"),
    )
    op.create_index(op.f("ix_study_plans_plan_date"), "study_plans", ["plan_date"], unique=False)
    op.create_index(op.f("ix_study_plans_user_id"), "study_plans", ["user_id"], unique=False)

    op.create_table(
        "study_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("planned_hours", sa.Float(), nullable=False),
        sa.Column("actual_hours", sa.Float(), nullable=False),
        sa.Column("did_study", sa.Boolean(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "subject_id", "log_date", name="uq_log_user_subject_date"),
    )
    op.create_index(op.f("ix_study_logs_log_date"), "study_logs", ["log_date"], unique=False)
    op.create_index(op.f("ix_study_logs_user_id"), "study_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_study_logs_user_id"), table_name="study_logs")
    op.drop_index(op.f("ix_study_logs_log_date"), table_name="study_logs")
    op.drop_table("study_logs")
    op.drop_index(op.f("ix_study_plans_user_id"), table_name="study_plans")
    op.drop_index(op.f("ix_study_plans_plan_date"), table_name="study_plans")
    op.drop_table("study_plans")
    op.drop_index(op.f("ix_subjects_user_id"), table_name="subjects")
    op.drop_table("subjects")
    op.drop_table("study_settings")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
