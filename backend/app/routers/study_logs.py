from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dates import app_today
from app.db.session import get_db
from app.deps import get_current_user
from app.models import StudyLog, Subject, User
from app.schemas import StudyLogCreate, StudyLogRead
from app.services.planner import planned_hours_for_subject, refresh_subject_status, regenerate_plans

router = APIRouter(prefix="/study-logs", tags=["study-logs"])


@router.get("", response_model=list[StudyLogRead])
def list_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[StudyLog]:
    return list(
        db.scalars(
            select(StudyLog)
            .where(StudyLog.user_id == current_user.id)
            .order_by(StudyLog.log_date.desc(), StudyLog.id.desc())
        ).all()
    )


@router.post("", response_model=StudyLogRead, status_code=status.HTTP_201_CREATED)
def upsert_log(
    payload: StudyLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudyLog:
    subject = db.get(Subject, payload.subject_id)
    if not subject or subject.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    log_date = payload.log_date or app_today()
    planned_hours = planned_hours_for_subject(db, current_user.id, subject.id, log_date)
    actual_hours = payload.actual_hours if payload.did_study else 0.0

    existing = db.scalar(
        select(StudyLog).where(
            StudyLog.user_id == current_user.id,
            StudyLog.subject_id == subject.id,
            StudyLog.log_date == log_date,
        )
    )

    if existing:
        subject.completed_hours = max(subject.completed_hours - existing.actual_hours + actual_hours, 0)
        existing.planned_hours = planned_hours
        existing.actual_hours = actual_hours
        existing.did_study = payload.did_study
        existing.note = payload.note
        log = existing
    else:
        subject.completed_hours = max(subject.completed_hours + actual_hours, 0)
        log = StudyLog(
            user_id=current_user.id,
            subject_id=subject.id,
            log_date=log_date,
            planned_hours=planned_hours,
            actual_hours=actual_hours,
            did_study=payload.did_study,
            note=payload.note,
        )
        db.add(log)

    refresh_subject_status(subject)
    regenerate_plans(db, current_user.id)
    db.commit()
    db.refresh(log)
    return log
