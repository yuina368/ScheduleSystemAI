from datetime import date

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    settings: Mapped["StudySetting"] = relationship(back_populates="user", cascade="all, delete-orphan")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class StudySetting(Base):
    __tablename__ = "study_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    daily_available_hours: Mapped[float] = mapped_column(Float, default=2.0)
    weekday_available_hours: Mapped[float | None] = mapped_column(Float, default=2.0, nullable=True)
    weekend_available_hours: Mapped[float | None] = mapped_column(Float, default=2.0, nullable=True)
    morning_webhook_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="settings")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    deadline_date: Mapped[date] = mapped_column(Date)
    required_hours: Mapped[float] = mapped_column(Float)
    completed_hours: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(24), default="active")
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="subjects")
    plans: Mapped[list["StudyPlan"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    logs: Mapped[list["StudyLog"]] = relationship(back_populates="subject", cascade="all, delete-orphan")


class StudyPlan(Base):
    __tablename__ = "study_plans"
    __table_args__ = (UniqueConstraint("user_id", "subject_id", "plan_date", name="uq_plan_user_subject_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    planned_hours: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(24), default="planned")
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subject: Mapped[Subject] = relationship(back_populates="plans")


class StudyLog(Base):
    __tablename__ = "study_logs"
    __table_args__ = (UniqueConstraint("user_id", "subject_id", "log_date", name="uq_log_user_subject_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    log_date: Mapped[date] = mapped_column(Date, index=True)
    planned_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_hours: Mapped[float] = mapped_column(Float, default=0.0)
    did_study: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subject: Mapped[Subject] = relationship(back_populates="logs")
