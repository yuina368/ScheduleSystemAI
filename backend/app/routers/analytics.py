from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import RegressionAnalysis
from app.services.analytics import get_study_regression

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/study-regression", response_model=RegressionAnalysis)
def study_regression(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return get_study_regression(db, current_user.id)
