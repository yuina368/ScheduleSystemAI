import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dates import app_today
from app.db.session import get_db
from app.deps import get_current_user
from app.models import StudySetting, User
from app.schemas import StudySettingRead, StudySettingUpsert
from app.services.planner import regenerate_plans
from app.services.webhooks import build_morning_payload

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/study-time", response_model=StudySettingRead)
def get_study_time(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StudySetting:
    setting = db.scalar(select(StudySetting).where(StudySetting.user_id == current_user.id))
    if not setting:
        setting = StudySetting(
            user_id=current_user.id,
            daily_available_hours=2.0,
            weekday_available_hours=2.0,
            weekend_available_hours=2.0,
            max_daily_subjects=3,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    elif (
        setting.weekday_available_hours is None
        or setting.weekend_available_hours is None
        or setting.max_daily_subjects is None
    ):
        setting.weekday_available_hours = setting.weekday_available_hours or setting.daily_available_hours
        setting.weekend_available_hours = setting.weekend_available_hours or setting.daily_available_hours
        setting.max_daily_subjects = setting.max_daily_subjects or 3
        db.commit()
        db.refresh(setting)
    return setting


@router.post("/study-time", response_model=StudySettingRead)
def upsert_study_time(
    payload: StudySettingUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudySetting:
    setting = db.scalar(select(StudySetting).where(StudySetting.user_id == current_user.id))
    current_daily = setting.daily_available_hours if setting else 2.0
    current_weekday = setting.weekday_available_hours if setting and setting.weekday_available_hours is not None else current_daily
    current_weekend = setting.weekend_available_hours if setting and setting.weekend_available_hours is not None else current_daily
    current_webhook_url = setting.morning_webhook_url if setting else None
    current_max_daily_subjects = setting.max_daily_subjects if setting and setting.max_daily_subjects is not None else 3
    weekday_hours = (
        payload.weekday_available_hours
        if payload.weekday_available_hours is not None
        else payload.daily_available_hours
        if payload.daily_available_hours is not None
        else current_weekday
    )
    weekend_hours = (
        payload.weekend_available_hours
        if payload.weekend_available_hours is not None
        else payload.daily_available_hours
        if payload.daily_available_hours is not None
        else current_weekend
    )
    webhook_url = (
        payload.morning_webhook_url
        if "morning_webhook_url" in payload.model_fields_set
        else current_webhook_url
    )
    max_daily_subjects = payload.max_daily_subjects or current_max_daily_subjects
    if not setting:
        setting = StudySetting(
            user_id=current_user.id,
            daily_available_hours=weekday_hours,
            weekday_available_hours=weekday_hours,
            weekend_available_hours=weekend_hours,
            morning_webhook_url=webhook_url,
            max_daily_subjects=max_daily_subjects,
        )
        db.add(setting)
    else:
        setting.daily_available_hours = weekday_hours
        setting.weekday_available_hours = weekday_hours
        setting.weekend_available_hours = weekend_hours
        setting.morning_webhook_url = webhook_url
        setting.max_daily_subjects = max_daily_subjects

    regenerate_plans(db, current_user.id)
    db.commit()
    db.refresh(setting)
    return setting


@router.post("/morning-webhook/test")
def test_morning_webhook(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    setting = db.scalar(select(StudySetting).where(StudySetting.user_id == current_user.id))
    if not setting or not setting.morning_webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL is not configured",
        )

    today = app_today()
    regenerate_plans(db, current_user.id, today)
    db.commit()
    payload = build_morning_payload(db, current_user.id, today)
    try:
        response = httpx.post(setting.morning_webhook_url, json=payload, timeout=10)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Webhook request failed: {exc}",
        ) from exc

    if not response.is_success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Webhook returned HTTP {response.status_code}",
        )

    return {"ok": True, "status_code": response.status_code}
