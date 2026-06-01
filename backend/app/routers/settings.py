from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import StudySetting, User
from app.schemas import StudySettingRead, StudySettingUpsert
from app.services.planner import regenerate_plans

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/study-time", response_model=StudySettingRead)
def get_study_time(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StudySetting:
    setting = db.scalar(select(StudySetting).where(StudySetting.user_id == current_user.id))
    if not setting:
        setting = StudySetting(user_id=current_user.id, daily_available_hours=2.0)
        db.add(setting)
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
    if not setting:
        setting = StudySetting(user_id=current_user.id, daily_available_hours=payload.daily_available_hours)
        db.add(setting)
    else:
        setting.daily_available_hours = payload.daily_available_hours

    regenerate_plans(db, current_user.id)
    db.commit()
    db.refresh(setting)
    return setting
