from datetime import date, timedelta
from math import exp

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dates import app_today
from app.models import StudyLog, StudyPlan, Subject
from app.services.planner import future_available_capacity, get_study_setting


def achievement_rate(actual_hours: float, planned_hours: float) -> float:
    if planned_hours <= 0:
        return 100.0 if actual_hours > 0 else 0.0
    return round(max(0.0, (actual_hours / planned_hours) * 100), 1)


def clamp_rate(value: float, upper: float = 200.0) -> float:
    return round(min(upper, max(0.0, value)), 1)


def get_daily_study_summaries(
    db: Session,
    user_id: int,
    target_date: date | None = None,
    days: int = 14,
) -> list[dict]:
    today = target_date or app_today()
    start_date = today - timedelta(days=days - 1)

    planned_by_date: dict[date, float] = {}
    actual_by_date: dict[date, float] = {}
    logged_planned_by_date: dict[date, float] = {}

    for plan_date, planned_hours in db.execute(
        select(StudyPlan.plan_date, func.coalesce(func.sum(StudyPlan.planned_hours), 0))
        .where(
            StudyPlan.user_id == user_id,
            StudyPlan.plan_date >= start_date,
            StudyPlan.plan_date <= today,
        )
        .group_by(StudyPlan.plan_date)
    ):
        planned_by_date[plan_date] = float(planned_hours or 0)

    for log_date, planned_hours, actual_hours in db.execute(
        select(
            StudyLog.log_date,
            func.coalesce(func.sum(StudyLog.planned_hours), 0),
            func.coalesce(func.sum(StudyLog.actual_hours), 0),
        )
        .where(
            StudyLog.user_id == user_id,
            StudyLog.log_date >= start_date,
            StudyLog.log_date <= today,
        )
        .group_by(StudyLog.log_date)
    ):
        logged_planned_by_date[log_date] = float(planned_hours or 0)
        actual_by_date[log_date] = float(actual_hours or 0)

    dates = sorted(set(planned_by_date) | set(actual_by_date) | {today})
    summaries = []
    for log_date in dates:
        planned_hours = planned_by_date.get(log_date, 0.0) or logged_planned_by_date.get(log_date, 0.0)
        actual_hours = actual_by_date.get(log_date, 0.0)
        summaries.append(
            {
                "log_date": log_date,
                "planned_hours": round(planned_hours, 4),
                "actual_hours": round(actual_hours, 4),
                "achievement_rate": achievement_rate(actual_hours, planned_hours),
            }
        )
    return summaries


def get_study_streak_days(db: Session, user_id: int, target_date: date) -> int:
    studied_dates = set(
        db.scalars(
            select(StudyLog.log_date)
            .where(
                StudyLog.user_id == user_id,
                StudyLog.log_date <= target_date,
                StudyLog.did_study.is_(True),
                StudyLog.actual_hours > 0,
            )
            .distinct()
        ).all()
    )
    if not studied_dates:
        return 0

    cursor = target_date if target_date in studied_dates else target_date - timedelta(days=1)
    streak_days = 0
    while cursor in studied_dates:
        streak_days += 1
        cursor -= timedelta(days=1)
    return streak_days


def get_recent_execution_profile(summaries: list[dict], today: date) -> dict:
    samples = [
        summary
        for summary in summaries
        if summary["log_date"] < today and (summary["planned_hours"] > 0 or summary["actual_hours"] > 0)
    ]
    if not samples:
        samples = [
            summary
            for summary in summaries
            if summary["actual_hours"] > 0 or summary["planned_hours"] > 0
        ]

    planned_total = sum(summary["planned_hours"] for summary in samples)
    actual_total = sum(summary["actual_hours"] for summary in samples)
    if planned_total > 0:
        execution_rate = min(1.25, max(0.0, actual_total / planned_total))
    elif actual_total > 0:
        execution_rate = 0.8
    else:
        execution_rate = 0.65

    confidence = min(95.0, 25.0 + len(samples) * 10.0)
    return {
        "samples": samples,
        "sample_size": len(samples),
        "execution_rate": execution_rate,
        "confidence": confidence,
    }


def probability_from_coverage(coverage_ratio: float, confidence: float) -> float:
    raw_probability = 100 / (1 + exp(-5 * (coverage_ratio - 0.85)))
    confidence_factor = 0.65 + 0.35 * (confidence / 100)
    return clamp_rate(raw_probability * confidence_factor, upper=100.0)


def final_label(probability: float) -> str:
    if probability >= 68:
        return "継続圏"
    if probability >= 34:
        return "調整圏"
    return "要再計画"


def get_subject_completion_forecasts(
    db: Session,
    user_id: int,
    target_date: date,
    execution_rate: float,
    confidence: float,
) -> list[dict]:
    setting = get_study_setting(db, user_id)
    subjects = list(
        db.scalars(
            select(Subject)
            .where(
                Subject.user_id == user_id,
                Subject.status == "active",
                Subject.required_hours > Subject.completed_hours,
            )
            .order_by(Subject.deadline_date.asc(), Subject.created_at.asc())
        ).all()
    )

    forecasts = []
    committed_required_hours = 0.0
    for subject in subjects:
        remaining_hours = max(subject.required_hours - subject.completed_hours, 0.0)
        days_left = max((subject.deadline_date - target_date).days + 1, 0)
        projected_capacity = future_available_capacity(setting, target_date, subject.deadline_date) * execution_rate
        available_after_earlier_deadlines = max(projected_capacity - committed_required_hours, 0.0)
        projected_hours = min(remaining_hours, available_after_earlier_deadlines)
        coverage_ratio = available_after_earlier_deadlines / remaining_hours if remaining_hours > 0 else 1.0
        probability = 100.0 if remaining_hours <= 0 else probability_from_coverage(coverage_ratio, confidence)
        if subject.deadline_date < target_date and remaining_hours > 0:
            probability = 0.0
        forecasts.append(
            {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "deadline_date": subject.deadline_date,
                "remaining_hours": round(remaining_hours, 4),
                "days_left": days_left,
                "required_daily_hours": round(remaining_hours / days_left, 4) if days_left > 0 else remaining_hours,
                "projected_study_hours": round(projected_hours, 4),
                "coverage_ratio": round(coverage_ratio, 4),
                "final_completion_probability": probability,
                "risk_label": final_label(probability),
            }
        )
        committed_required_hours += remaining_hours
    return forecasts


def get_study_regression(
    db: Session,
    user_id: int,
    target_date: date | None = None,
    days: int = 14,
) -> dict:
    today = target_date or app_today()
    summaries = get_daily_study_summaries(db, user_id, today, days)
    samples = [summary for summary in summaries if summary["planned_hours"] > 0 or summary["actual_hours"] > 0]
    study_streak_days = get_study_streak_days(db, user_id, today)
    execution_profile = get_recent_execution_profile(summaries, today)
    subject_forecasts = get_subject_completion_forecasts(
        db,
        user_id,
        today,
        execution_profile["execution_rate"],
        execution_profile["confidence"],
    )

    today_summary = next(
        (summary for summary in summaries if summary["log_date"] == today),
        {"actual_hours": 0.0, "achievement_rate": 0.0},
    )

    total_remaining_hours = sum(forecast["remaining_hours"] for forecast in subject_forecasts)
    projected_study_hours = sum(forecast["projected_study_hours"] for forecast in subject_forecasts)
    final_completion_probability = (
        min(forecast["final_completion_probability"] for forecast in subject_forecasts)
        if total_remaining_hours > 0 and subject_forecasts
        else 100.0
    )

    projected_completion_rate = (
        clamp_rate((projected_study_hours / total_remaining_hours) * 100, upper=100.0)
        if total_remaining_hours > 0
        else 100.0
    )
    final_status_label = final_label(final_completion_probability)

    if not samples:
        return {
            "generated_for": today,
            "sample_size": 0,
            "today_actual_hours": 0.0,
            "today_achievement_rate": 0.0,
            "predicted_achievement_rate": final_completion_probability,
            "predicted_next_achievement_rate": final_completion_probability,
            "slope_per_day": 0.0,
            "intercept": 0.0,
            "confidence": execution_profile["confidence"],
            "trend_label": final_status_label,
            "final_completion_probability": final_completion_probability,
            "projected_completion_rate": projected_completion_rate,
            "recent_execution_rate": round(execution_profile["execution_rate"] * 100, 1),
            "total_remaining_hours": round(total_remaining_hours, 4),
            "projected_study_hours": round(projected_study_hours, 4),
            "final_status_label": final_status_label,
            "study_streak_days": study_streak_days,
            "subject_forecasts": subject_forecasts,
            "daily_summaries": summaries,
        }

    first_date = samples[0]["log_date"]
    x_values = [(summary["log_date"] - first_date).days for summary in samples]
    y_values = [summary["achievement_rate"] for summary in samples]

    if len(samples) == 1:
        slope = 0.0
        intercept = y_values[0]
        confidence = 0.0
    else:
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        x_variance = sum((value - x_mean) ** 2 for value in x_values)
        if x_variance == 0:
            slope = 0.0
        else:
            slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / x_variance
        intercept = y_mean - slope * x_mean

        residual_sum = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(x_values, y_values))
        total_sum = sum((y - y_mean) ** 2 for y in y_values)
        confidence = 0.0 if total_sum == 0 else max(0.0, min(1.0, 1 - residual_sum / total_sum)) * 100

    return {
        "generated_for": today,
        "sample_size": len(samples),
        "today_actual_hours": today_summary["actual_hours"],
        "today_achievement_rate": today_summary["achievement_rate"],
        "predicted_achievement_rate": final_completion_probability,
        "predicted_next_achievement_rate": final_completion_probability,
        "slope_per_day": round(slope, 2),
        "intercept": round(intercept, 2),
        "confidence": round(max(confidence, execution_profile["confidence"]), 1),
        "trend_label": final_status_label,
        "final_completion_probability": final_completion_probability,
        "projected_completion_rate": projected_completion_rate,
        "recent_execution_rate": round(execution_profile["execution_rate"] * 100, 1),
        "total_remaining_hours": round(total_remaining_hours, 4),
        "projected_study_hours": round(projected_study_hours, 4),
        "final_status_label": final_status_label,
        "study_streak_days": study_streak_days,
        "subject_forecasts": subject_forecasts,
        "daily_summaries": summaries,
    }
