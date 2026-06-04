from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def app_today() -> date:
    return datetime.now(ZoneInfo(get_settings().app_timezone)).date()
