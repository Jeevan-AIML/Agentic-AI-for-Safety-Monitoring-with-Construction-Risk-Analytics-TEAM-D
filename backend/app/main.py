from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database.session import engine
from app.models.models import Base
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.sites import router as sites_router
from app.api.routes.workers import router as workers_router
from app.api.routes.equipment import router as equipment_router
from app.api.routes.risk import activities_router, hazards_router, risk_router, risk_intel_router
from app.api.routes.safety import router as safety_router
from app.api.routes.ppe import router as ppe_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.video import router as video_router
from app.api.routes.compliance import router as compliance_router
from app.api.routes.insurance import router as insurance_router
from app.api.routes.misc import notifications_router, dashboard_router
from app.agents.base_agents import orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    from app.database.session import migrate_db_columns
    migrate_db_columns(engine)

    # Auto-seed on startup in development
    if settings.APP_ENV == "development":
        try:
            from app.seed import seed_database
            seed_database()
        except Exception as e:
            print(f"[WARN] Seed skipped: {e}")

    print(f"[INFO] {settings.APP_NAME} started")
    print(f"       Environment: {settings.APP_ENV}")
    print(f"       Database: {settings.DATABASE_URL.split('://')[0]}")
    print(f"       Agents: {list(orchestrator.agents.keys())} (Phase 1.3 — Site Risk Agent active)")

    yield

    print("[INFO] Application shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI-powered construction safety and risk monitoring platform",
    version="1.0.0-phase1.3",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ─────────────────────────────────────────────────────────────

PREFIX = "/api/v1"

app.include_router(auth_router, prefix=PREFIX)
app.include_router(projects_router, prefix=PREFIX)
app.include_router(sites_router, prefix=PREFIX)
app.include_router(workers_router, prefix=PREFIX)
app.include_router(equipment_router, prefix=PREFIX)
app.include_router(activities_router, prefix=PREFIX)
app.include_router(hazards_router, prefix=PREFIX)
app.include_router(risk_router, prefix=PREFIX)
app.include_router(risk_intel_router, prefix=PREFIX)
app.include_router(safety_router, prefix=PREFIX)
app.include_router(ppe_router, prefix=PREFIX)
app.include_router(monitoring_router, prefix=PREFIX)
app.include_router(alerts_router, prefix=PREFIX)
app.include_router(video_router, prefix=PREFIX)
app.include_router(compliance_router, prefix=PREFIX)
app.include_router(insurance_router, prefix=PREFIX)
app.include_router(notifications_router, prefix=PREFIX)
app.include_router(dashboard_router, prefix=PREFIX)


# ── Health Check ───────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0-phase2.1",
        "agents": orchestrator.get_all_statuses(),
    }


@app.get("/")
def root():
    return {
        "message": "ACRIP API",
        "docs": "/api/docs",
        "health": "/api/health",
    }
