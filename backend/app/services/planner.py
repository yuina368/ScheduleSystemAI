from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.dates import app_today
from app.models import StudyLog, StudyPlan, StudySetting, Subject


@dataclass
class PrioritySnapshot:
    subject: Subject
    remaining_hours: float
    score: float
    reasons: list[str]


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


def max_daily_subjects_from_setting(setting: StudySetting | None) -> int:
    if not setting or setting.max_daily_subjects is None:
        return 3
    return max(1, min(int(setting.max_daily_subjects), 12))


def future_available_capacity(setting: StudySetting | None, start_date: date, end_date: date) -> float:
    if end_date < start_date:
        return 0.0
    return sum(
        available_hours_from_setting(setting, start_date + timedelta(days=offset))
        for offset in range((end_date - start_date).days + 1)
    )


def get_last_studied_dates(db: Session, user_id: int) -> dict[int, date]:
    return {
        subject_id: log_date
        for subject_id, log_date in db.execute(
            select(StudyLog.subject_id, func.max(StudyLog.log_date))
            .where(StudyLog.user_id == user_id, StudyLog.did_study.is_(True), StudyLog.actual_hours > 0)
            .group_by(StudyLog.subject_id)
        )
    }


def priority_snapshot(
    subject: Subject,
    remaining_hours: float,
    plan_date: date,
    daily_available_hours: float,
    last_studied_dates: dict[int, date],
) -> PrioritySnapshot:
    days_left = max((subject.deadline_date - plan_date).days, 0)
    progress = subject.completed_hours / subject.required_hours if subject.required_hours > 0 else 0.0
    completion_gap = max(0.0, 1 - progress)
    urgency = 1 / (days_left + 1)
    daily_need = remaining_hours / (days_left + 1)
    pressure = min(1.0, daily_need / daily_available_hours) if daily_available_hours > 0 else 1.0

    last_studied_date = last_studied_dates.get(subject.id)
    stale_days = (plan_date - last_studied_date).days if last_studied_date else 7
    stale_score = min(1.0, max(stale_days, 0) / 7)

    score = round((urgency * 35) + (pressure * 30) + (completion_gap * 25) + (stale_score * 10), 2)
    reasons: list[str] = []
    if days_left == 0:
        reasons.append("締切当日")
    elif days_left <= 3:
        reasons.append("締切が近い")
    elif days_left <= 7:
        reasons.append("締切が1週間以内")

    if pressure >= 0.75:
        reasons.append("必要時間が重い")
    if completion_gap >= 0.5:
        reasons.append("達成率が低い")
    if stale_days >= 3:
        reasons.append("最近未学習")
    if not reasons:
        reasons.append("バランス調整")

    return PrioritySnapshot(
        subject=subject,
        remaining_hours=remaining_hours,
        score=score,
        reasons=reasons[:3],
    )


def refresh_subject_status(subject: Subject) -> None:
    if subject.completed_hours >= subject.required_hours:
        subject.completed_hours = min(subject.completed_hours, subject.required_hours)
        subject.status = "completed"
    elif subject.status == "completed":
        subject.status = "active"


def regenerate_plans(db: Session, user_id: int, start_date: date | None = None) -> list[StudyPlan]:
    today = start_date or app_today()
    setting = get_study_setting(db, user_id)
    max_daily_subjects = max_daily_subjects_from_setting(setting)

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
    remaining_by_subject: dict[int, float] = {}
    subjects_by_id: dict[int, Subject] = {}
    for subject in subjects:
        refresh_subject_status(subject)
        remaining_hours = max(subject.required_hours - subject.completed_hours, 0)
        if remaining_hours > 0:
            remaining_by_subject[subject.id] = remaining_hours
            subjects_by_id[subject.id] = subject

    if not remaining_by_subject:
        db.flush()
        return created

    last_studied_dates = get_last_studied_dates(db, user_id)
    latest_deadline = max(subject.deadline_date for subject in subjects_by_id.values())

    for offset in range((latest_deadline - today).days + 1):
        plan_date = today + timedelta(days=offset)
        daily_available_hours = available_hours_from_setting(setting, plan_date)
        if daily_available_hours <= 0:
            continue

        candidates = [
            priority_snapshot(
                subject,
                remaining_by_subject[subject_id],
                plan_date,
                daily_available_hours,
                last_studied_dates,
            )
            for subject_id, subject in subjects_by_id.items()
            if remaining_by_subject[subject_id] > 0 and subject.deadline_date >= plan_date
        ]
        candidates.sort(
            key=lambda item: (
                item.score,
                -((item.subject.deadline_date - plan_date).days),
                item.remaining_hours,
            ),
            reverse=True,
        )
        selected = candidates[:max_daily_subjects]
        if not selected:
            continue

        desired_allocations: list[tuple[PrioritySnapshot, float]] = []
        for snapshot in selected:
            future_capacity = future_available_capacity(setting, plan_date, snapshot.subject.deadline_date)
            if future_capacity <= 0:
                continue
            desired_hours = snapshot.remaining_hours * (daily_available_hours / future_capacity)
            desired_allocations.append((snapshot, min(snapshot.remaining_hours, desired_hours)))

        total_desired = sum(hours for _, hours in desired_allocations)
        if total_desired <= 0:
            continue

        scale = min(1.0, daily_available_hours / total_desired)
        for snapshot, desired_hours in desired_allocations:
            planned_hours = round(min(snapshot.remaining_hours, desired_hours * scale), 4)
            if planned_hours <= 0:
                continue
            plan = StudyPlan(
                user_id=user_id,
                subject_id=snapshot.subject.id,
                plan_date=plan_date,
                planned_hours=planned_hours,
                priority_score=snapshot.score,
                priority_reasons="、".join(snapshot.reasons),
                status="planned",
            )
            db.add(plan)
            created.append(plan)
            remaining_by_subject[snapshot.subject.id] = max(
                remaining_by_subject[snapshot.subject.id] - planned_hours,
                0.0,
            )

    db.flush()
    return created


def get_plan_summary(db: Session, user_id: int, plan_date: date) -> dict:
    plans = db.scalars(
        select(StudyPlan)
        .options(joinedload(StudyPlan.subject))
        .where(StudyPlan.user_id == user_id, StudyPlan.plan_date == plan_date)
        .order_by(StudyPlan.priority_score.desc(), StudyPlan.planned_hours.desc(), StudyPlan.id.asc())
    ).all()
    setting = get_study_setting(db, user_id)
    daily_available_hours = available_hours_from_setting(setting, plan_date)
    total = sum(plan.planned_hours for plan in plans)
    return {
        "plan_date": plan_date,
        "daily_available_hours": daily_available_hours,
        "max_daily_subjects": max_daily_subjects_from_setting(setting),
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
