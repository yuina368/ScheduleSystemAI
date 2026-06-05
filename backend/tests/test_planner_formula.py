from datetime import date, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import StudyLog, StudyPlan, StudySetting, Subject, User
from app.services.analytics import get_study_regression
from app.services.planner import regenerate_plans


def test_formula_expected_daily_hours() -> None:
    required_hours = 10
    completed_hours = 4
    today = date(2026, 6, 1)
    deadline = today + timedelta(days=2)

    remaining_hours = required_hours - completed_hours
    remaining_days = (deadline - today).days + 1

    assert remaining_hours / remaining_days == 2


def test_regenerate_plans_weights_weekday_and_weekend_hours() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        user = User(email="test@example.com", hashed_password="hashed")
        db.add(user)
        db.flush()
        db.add(
            StudySetting(
                user_id=user.id,
                daily_available_hours=2,
                weekday_available_hours=2,
                weekend_available_hours=4,
            )
        )
        db.add(
            Subject(
                user_id=user.id,
                name="Exam",
                deadline_date=date(2026, 6, 7),
                required_hours=8,
                completed_hours=0,
                status="active",
            )
        )
        db.flush()

        regenerate_plans(db, user.id, start_date=date(2026, 6, 5))
        plans = list(db.scalars(select(StudyPlan).order_by(StudyPlan.plan_date.asc())).all())

    assert [plan.plan_date for plan in plans] == [
        date(2026, 6, 5),
        date(2026, 6, 6),
        date(2026, 6, 7),
    ]
    assert [plan.planned_hours for plan in plans] == [1.6, 3.2, 3.2]


def test_regenerate_plans_limits_daily_subjects_by_priority() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    today = date(2026, 6, 5)
    with Session(engine) as db:
        user = User(email="priority@example.com", hashed_password="hashed")
        db.add(user)
        db.flush()
        db.add(
            StudySetting(
                user_id=user.id,
                daily_available_hours=4,
                weekday_available_hours=4,
                weekend_available_hours=4,
                max_daily_subjects=2,
            )
        )
        subjects = [
            Subject(
                user_id=user.id,
                name="Urgent Exam",
                deadline_date=today + timedelta(days=1),
                required_hours=8,
                completed_hours=0,
                status="active",
            ),
            Subject(
                user_id=user.id,
                name="Medium Exam",
                deadline_date=today + timedelta(days=3),
                required_hours=4,
                completed_hours=0,
                status="active",
            ),
            Subject(
                user_id=user.id,
                name="Far Exam",
                deadline_date=today + timedelta(days=30),
                required_hours=10,
                completed_hours=0,
                status="active",
            ),
        ]
        db.add_all(subjects)
        db.flush()

        regenerate_plans(db, user.id, start_date=today)
        today_plans = list(
            db.scalars(select(StudyPlan).where(StudyPlan.plan_date == today).order_by(StudyPlan.priority_score.desc()))
        )

    assert len(today_plans) == 2
    assert today_plans[0].subject_id == subjects[0].id
    assert all(plan.priority_score is not None for plan in today_plans)
    assert all(plan.priority_reasons for plan in today_plans)


def test_study_regression_uses_daily_actual_totals() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        user = User(email="analytics@example.com", hashed_password="hashed")
        db.add(user)
        db.flush()
        subject = Subject(
            user_id=user.id,
            name="Exam",
            deadline_date=date(2026, 6, 10),
            required_hours=10,
            completed_hours=0,
            status="active",
        )
        db.add(subject)
        db.flush()

        for offset, actual_hours in enumerate([1.0, 1.5, 2.0]):
            log_date = date(2026, 6, 1) + timedelta(days=offset)
            db.add(
                StudyPlan(
                    user_id=user.id,
                    subject_id=subject.id,
                    plan_date=log_date,
                    planned_hours=2.0,
                    status="planned",
                )
            )
            db.add(
                StudyLog(
                    user_id=user.id,
                    subject_id=subject.id,
                    log_date=log_date,
                    planned_hours=2.0,
                    actual_hours=actual_hours,
                    did_study=True,
                )
            )
        db.flush()

        analysis = get_study_regression(db, user.id, target_date=date(2026, 6, 3), days=3)

    assert analysis["sample_size"] == 3
    assert analysis["today_actual_hours"] == 2.0
    assert analysis["today_achievement_rate"] == 100.0
    assert analysis["slope_per_day"] > 0
    assert analysis["trend_label"] == "上昇傾向"
