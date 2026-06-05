from datetime import date

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dates import app_today
from app.models import StudySetting
from app.services.analytics import get_study_regression
from app.services.planner import get_plan_summary, regenerate_plans


def format_hours(value: float) -> str:
    total_minutes = max(0, round(value * 60))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours == 0:
        return f"{minutes}分"
    if minutes == 0:
        return f"{hours}時間"
    return f"{hours}時間{minutes}分"


def build_morning_payload(db: Session, user_id: int, target_date: date) -> dict:
    plan_summary = get_plan_summary(db, user_id, target_date)
    analysis = get_study_regression(db, user_id, target_date)
    plan_lines = [
        f"- {plan.subject.name}: {format_hours(plan.planned_hours)}"
        for plan in plan_summary["plans"][:8]
    ]
    if not plan_lines:
        plan_lines = ["- 今日の予定はまだありません"]

    content = "\n".join(
        [
            f"ScheduleSystemAI 朝の学習ブリーフィング ({target_date.isoformat()})",
            f"今日の予定: {format_hours(plan_summary['total_planned_hours'])}",
            f"学習可能時間: {format_hours(plan_summary['daily_available_hours'])}",
            f"最終達成確率: {analysis['final_completion_probability']}%",
            f"残り必要時間: {format_hours(analysis['total_remaining_hours'])}",
            f"予測可能学習時間: {format_hours(analysis['projected_study_hours'])}",
            f"判定: {analysis['final_status_label']}",
            "今日の科目:",
            *plan_lines,
        ]
    )

    return {
        "content": content,
        "text": content,
        "summary": {
            "date": target_date.isoformat(),
            "planned_hours": plan_summary["total_planned_hours"],
            "available_hours": plan_summary["daily_available_hours"],
            "final_completion_probability": analysis["final_completion_probability"],
            "total_remaining_hours": analysis["total_remaining_hours"],
            "projected_study_hours": analysis["projected_study_hours"],
            "final_status_label": analysis["final_status_label"],
            "plans": [
                {
                    "subject": plan.subject.name,
                    "planned_hours": plan.planned_hours,
                    "deadline_date": plan.subject.deadline_date.isoformat(),
                }
                for plan in plan_summary["plans"]
            ],
        },
    }


def send_morning_webhooks(db: Session, target_date: date | None = None) -> dict:
    send_date = target_date or app_today()
    settings = list(
        db.scalars(
            select(StudySetting).where(
                StudySetting.morning_webhook_url.is_not(None),
                StudySetting.morning_webhook_url != "",
            )
        ).all()
    )

    results = []
    for setting in settings:
        regenerate_plans(db, setting.user_id, send_date)
        db.commit()
        payload = build_morning_payload(db, setting.user_id, send_date)
        try:
            response = httpx.post(setting.morning_webhook_url or "", json=payload, timeout=10)
            results.append(
                {
                    "user_id": setting.user_id,
                    "ok": response.is_success,
                    "status_code": response.status_code,
                }
            )
        except httpx.HTTPError as exc:
            results.append(
                {
                    "user_id": setting.user_id,
                    "ok": False,
                    "error": str(exc),
                }
            )

    return {
        "date": send_date,
        "targets": len(settings),
        "sent": sum(1 for result in results if result["ok"]),
        "failed": sum(1 for result in results if not result["ok"]),
        "results": results,
    }
