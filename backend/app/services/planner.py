from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.dates import app_today
from app.models import StudyPlan, StudySetting, Subject


def get_study_setting(db: Session, user_id: int) -> StudySetting | None:
    return db.scalar(select(StudySetting).where(StudySetting.user_id == user_id))


def is_weekend(target_date: date) -> bool:
    return target_date.weekday() >= 5


def available_hours_from_setting(setting: StudySetting | None, target_date: date) -> float:
    if not setting:
        return 2.0

    if is_weekend(target_date):
        return float(setting.weekend_available_hours or setting.daily_available_hours or 2.0)
    return float(setting.weekday_available_hours or setting.daily_available_hours or 2.0)


def get_daily_available_hours(db: Session, user_id: int, target_date: date) -> float:
    return available_hours_from_setting(get_study_setting(db, user_id), target_date)


def refresh_subject_status(subject: Subject) -> None:
    if subject.completed_hours >= subject.required_hours:
        subject.completed_hours = min(subject.completed_hours, subject.required_hours)
        subject.status = "completed"
    elif subject.status == "completed":
        subject.status = "active"


def regenerate_plans(db: Session, user_id: int, start_date: date | None = None) -> list[StudyPlan]:
    today = start_date or app_today()
    setting = get_study_setting(db, user_id)

    db.execute(
        delete(StudyPlan).where(
            StudyPlan.user_id == user_id,
            StudyPlan.plan_date >= today,
        )
    )

    subjects = db.scalars(
        select(Subject)
        .where(
            Subject.user_id == user_id,
            Subject.status == "active",
            Subject.deadline_date >= today,
        )
        .order_by(Subject.deadline_date.asc(), Subject.created_at.asc())
    ).all()

    created: list[StudyPlan] = []
    for subject in subjects:
        refresh_subject_status(subject)
        remaining_hours = max(subject.required_hours - subject.completed_hours, 0)
        if remaining_hours <= 0:
            continue

        planning_dates = [today + timedelta(days=offset) for offset in range((subject.deadline_date - today).days + 1)]
        day_weights = [(plan_date, available_hours_from_setting(setting, plan_date)) for plan_date in planning_dates]
        total_weight = sum(weight for _, weight in day_weights)
        if total_weight <= 0:
            continue

        for plan_date, weight in day_weights:
            plan = StudyPlan(
                user_id=user_id,
                subject_id=subject.id,
                plan_date=plan_date,
                planned_hours=round(remaining_hours * (weight / total_weight), 4),
                status="planned",
            )
            db.add(plan)
            created.append(plan)

    db.flush()
    return created


def get_plan_summary(db: Session, user_id: int, plan_date: date) -> dict:
    plans = db.scalars(
        select(StudyPlan)
        .options(joinedload(StudyPlan.subject))
        .where(StudyPlan.user_id == user_id, StudyPlan.plan_date == plan_date)
        .order_by(StudyPlan.planned_hours.desc(), StudyPlan.id.asc())
    ).all()
    daily_available_hours = get_daily_available_hours(db, user_id, plan_date)
    total = sum(plan.planned_hours for plan in plans)
    return {
        "plan_date": plan_date,
        "daily_available_hours": daily_available_hours,
        "total_planned_hours": total,
        "over_capacity": total > daily_available_hours,
        "plans": plans,
    }


def planned_hours_for_subject(db: Session, user_id: int, subject_id: int, log_date: date) -> float:
    value = db.scalar(
        select(func.coalesce(StudyPlan.planned_hours, 0))
        .where(
            StudyPlan.user_id == user_id,
            StudyPlan.subject_id == subject_id,
            StudyPlan.plan_date == log_date,
        )
        .limit(1)
    )
    return float(value or 0)
