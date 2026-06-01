from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

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
    app.state.db_startup_error = None
    if app_settings.create_tables_on_startup:
        try:
            Base.metadata.create_all(bind=engine)
        except SQLAlchemyError as exc:
            app.state.db_startup_error = str(exc)


def database_status() -> dict[str, str]:
    startup_error = getattr(app.state, "db_startup_error", None)
    if startup_error:
        return {"status": "error", "detail": startup_error}

    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        return {"status": "ok"}
    except SQLAlchemyError as exc:
        return {"status": "error", "detail": str(exc)}


@app.get("/health")
def health() -> dict[str, object]:
    db = database_status()
    return {"status": "ok" if db["status"] == "ok" else "degraded", "database": db}


@app.get("/")
def root() -> dict[str, object]:
    db = database_status()
    return {
        "name": "ScheduleSystemAI API",
        "status": "ok" if db["status"] == "ok" else "degraded",
        "docs": "/docs",
        "health": "/health",
        "database": db,
    }
