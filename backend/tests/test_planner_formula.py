from datetime import date, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import StudyPlan, StudySetting, Subject, User
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
