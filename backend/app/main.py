from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.core.config import get_settings
from app.db.session import Base, engine
from app.routers import auth, plans, settings as settings_router, study_logs, subjects

app_settings = get_settings()

app = FastAPI(
    title="ScheduleSystemAI API",
    version="0.1.0",
    description="MVP API for formula-based AI study planning.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(settings_router.router)
app.include_router(subjects.router)
app.include_router(plans.router)
app.include_router(study_logs.router)


@app.on_event("startup")
def on_startup() -> None:
    if app_settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
