from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import Subject, User
from app.schemas import SubjectCreate, SubjectRead, SubjectUpdate
from app.services.planner import refresh_subject_status, regenerate_plans

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectRead])
def list_subjects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Subject]:
    return list(
        db.scalars(
            select(Subject)
            .where(Subject.user_id == current_user.id)
            .order_by(Subject.deadline_date.asc(), Subject.created_at.asc())
        ).all()
    )


@router.post("", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Subject:
    subject = Subject(
        user_id=current_user.id,
        name=payload.name,
        deadline_date=payload.deadline_date,
        required_hours=payload.required_hours,
        completed_hours=min(payload.completed_hours, payload.required_hours),
        status="active",
    )
    refresh_subject_status(subject)
    db.add(subject)
    db.flush()
    regenerate_plans(db, current_user.id)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/{subject_id}", response_model=SubjectRead)
def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject or subject.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


@router.patch("/{subject_id}", response_model=SubjectRead)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject or subject.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(subject, field, value)
    subject.completed_hours = min(subject.completed_hours, subject.required_hours)
    refresh_subject_status(subject)

    regenerate_plans(db, current_user.id)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    subject = db.get(Subject, subject_id)
    if not subject or subject.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    db.delete(subject)
    regenerate_plans(db, current_user.id)
    db.commit()
