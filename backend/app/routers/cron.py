from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.webhooks import send_morning_webhooks

router = APIRouter(prefix="/cron", tags=["cron"])


@router.get("/morning-summary")
def morning_summary(request: Request, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    if not settings.cron_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="CRON_SECRET is not configured")

    authorization = request.headers.get("authorization")
    if authorization != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return send_morning_webhooks(db)
