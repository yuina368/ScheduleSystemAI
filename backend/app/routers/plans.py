from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dates import app_today
from app.db.session import get_db
from app.deps import get_current_user
from app.models import StudyPlan, User
from app.schemas import PlanSummary, StudyPlanRead
from app.services.planner import get_plan_summary, regenerate_plans

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/generate", response_model=list[StudyPlanRead])
def generate_plans(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[StudyPlan]:
    plans = regenerate_plans(db, current_user.id)
    plan_ids = [plan.id for plan in plans]
    db.commit()
    if not plan_ids:
        return []
    return list(
        db.scalars(
            select(StudyPlan)
            .options(joinedload(StudyPlan.subject))
            .where(StudyPlan.id.in_(plan_ids))
            .order_by(StudyPlan.plan_date.asc(), StudyPlan.id.asc())
        ).all()
    )


@router.get("", response_model=list[StudyPlanRead])
def list_plans(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StudyPlan]:
    start = from_date or app_today()
    end = to_date or (start + timedelta(days=30))
    return list(
        db.scalars(
            select(StudyPlan)
            .options(joinedload(StudyPlan.subject))
            .where(
                StudyPlan.user_id == current_user.id,
                StudyPlan.plan_date >= start,
                StudyPlan.plan_date <= end,
            )
            .order_by(StudyPlan.plan_date.asc(), StudyPlan.id.asc())
        ).all()
    )


@router.get("/today", response_model=PlanSummary)
def today_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return get_plan_summary(db, current_user.id, app_today())
