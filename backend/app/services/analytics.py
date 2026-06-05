from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dates import app_today
from app.models import StudyLog, StudyPlan


def achievement_rate(actual_hours: float, planned_hours: float) -> float:
    if planned_hours <= 0:
        return 100.0 if actual_hours > 0 else 0.0
    return round(max(0.0, (actual_hours / planned_hours) * 100), 1)


def clamp_rate(value: float) -> float:
    return round(min(200.0, max(0.0, value)), 1)


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


def get_study_regression(
    db: Session,
    user_id: int,
    target_date: date | None = None,
    days: int = 14,
) -> dict:
    today = target_date or app_today()
    summaries = get_daily_study_summaries(db, user_id, today, days)
    samples = [summary for summary in summaries if summary["planned_hours"] > 0 or summary["actual_hours"] > 0]

    today_summary = next(
        (summary for summary in summaries if summary["log_date"] == today),
        {"actual_hours": 0.0, "achievement_rate": 0.0},
    )

    if not samples:
        return {
            "generated_for": today,
            "sample_size": 0,
            "today_actual_hours": 0.0,
            "today_achievement_rate": 0.0,
            "predicted_achievement_rate": 0.0,
            "predicted_next_achievement_rate": 0.0,
            "slope_per_day": 0.0,
            "intercept": 0.0,
            "confidence": 0.0,
            "trend_label": "データ不足",
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

    today_index = (today - first_date).days
    predicted_today = clamp_rate(intercept + slope * today_index)
    predicted_next = clamp_rate(intercept + slope * (today_index + 1))
    trend_label = "上昇傾向" if slope > 1 else "下降傾向" if slope < -1 else "横ばい"

    return {
        "generated_for": today,
        "sample_size": len(samples),
        "today_actual_hours": today_summary["actual_hours"],
        "today_achievement_rate": today_summary["achievement_rate"],
        "predicted_achievement_rate": predicted_today,
        "predicted_next_achievement_rate": predicted_next,
        "slope_per_day": round(slope, 2),
        "intercept": round(intercept, 2),
        "confidence": round(confidence, 1),
        "trend_label": trend_label,
        "daily_summaries": summaries,
    }
