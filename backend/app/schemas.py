from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class StudySettingUpsert(BaseModel):
    daily_available_hours: float | None = Field(default=None, gt=0, le=24)
    weekday_available_hours: float | None = Field(default=None, gt=0, le=24)
    weekend_available_hours: float | None = Field(default=None, gt=0, le=24)
    morning_webhook_url: str | None = Field(default=None, max_length=2048)

    @field_validator("morning_webhook_url")
    @classmethod
    def validate_webhook_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if not normalized.startswith(("https://", "http://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return normalized


class StudySettingRead(BaseModel):
    id: int
    user_id: int
    daily_available_hours: float
    weekday_available_hours: float
    weekend_available_hours: float
    morning_webhook_url: str | None

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    deadline_date: date
    required_hours: float = Field(gt=0, le=10000)
    completed_hours: float = Field(default=0, ge=0, le=10000)


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    deadline_date: date | None = None
    required_hours: float | None = Field(default=None, gt=0, le=10000)
    completed_hours: float | None = Field(default=None, ge=0, le=10000)
    status: str | None = Field(default=None, pattern="^(active|completed|archived)$")


class SubjectRead(BaseModel):
    id: int
    user_id: int
    name: str
    deadline_date: date
    required_hours: float
    completed_hours: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyPlanRead(BaseModel):
    id: int
    user_id: int
    subject_id: int
    plan_date: date
    planned_hours: float
    status: str
    subject: SubjectRead

    model_config = ConfigDict(from_attributes=True)


class PlanSummary(BaseModel):
    plan_date: date
    daily_available_hours: float
    total_planned_hours: float
    over_capacity: bool
    plans: list[StudyPlanRead]


class StudyLogCreate(BaseModel):
    subject_id: int
    log_date: date | None = None
    actual_hours: float = Field(default=0, ge=0, le=24)
    did_study: bool
    note: str | None = Field(default=None, max_length=500)


class StudyLogRead(BaseModel):
    id: int
    user_id: int
    subject_id: int
    log_date: date
    planned_hours: float
    actual_hours: float
    did_study: bool
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailyStudySummary(BaseModel):
    log_date: date
    planned_hours: float
    actual_hours: float
    achievement_rate: float


class RegressionAnalysis(BaseModel):
    generated_for: date
    sample_size: int
    today_actual_hours: float
    today_achievement_rate: float
    predicted_achievement_rate: float
    predicted_next_achievement_rate: float
    slope_per_day: float
    intercept: float
    confidence: float
    trend_label: str
    daily_summaries: list[DailyStudySummary]
