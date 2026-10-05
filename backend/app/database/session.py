from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Handle SQLite connection args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db_columns(engine):
    """Ensure newly added columns and tables exist in existing database without data loss."""
    from sqlalchemy import inspect, text
    try:
        from app.models.models import Base as ModelsBase
        ModelsBase.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if "hazards" in tables:
            hazard_cols = [c["name"] for c in inspector.get_columns("hazards")]
            new_hazard_cols = [
                ("evidence", "TEXT"),
                ("detection_source", "VARCHAR(50) DEFAULT 'RULE_ENGINE'"),
                ("acknowledged_at", "DATETIME"),
                ("acknowledged_by", "VARCHAR(36)"),
                ("mitigated_at", "DATETIME"),
                ("mitigated_by", "VARCHAR(36)"),
                ("mitigation_notes", "TEXT"),
            ]
            with engine.begin() as conn:
                for col_name, col_type in new_hazard_cols:
                    if col_name not in hazard_cols:
                        conn.execute(text(f"ALTER TABLE hazards ADD COLUMN {col_name} {col_type}"))

        if "risk_scores" in tables:
            risk_cols = [c["name"] for c in inspector.get_columns("risk_scores")]
            new_risk_cols = [
                ("activity_risk", "FLOAT DEFAULT 0.0"),
                ("highest_hazard_score", "FLOAT DEFAULT 0.0"),
                ("active_hazards_count", "INTEGER DEFAULT 0"),
                ("critical_hazards_count", "INTEGER DEFAULT 0"),
                ("recommendations", "JSON"),
                ("reasoning", "JSON"),
            ]
            with engine.begin() as conn:
                for col_name, col_type in new_risk_cols:
                    if col_name not in risk_cols:
                        conn.execute(text(f"ALTER TABLE risk_scores ADD COLUMN {col_name} {col_type}"))

        if "safety_findings" in tables:
            sf_cols = [c["name"] for c in inspector.get_columns("safety_findings")]
            new_sf_cols = [
                ("compliance_finding_id", "VARCHAR(36)"),
            ]
            with engine.begin() as conn:
                for col_name, col_type in new_sf_cols:
                    if col_name not in sf_cols:
                        conn.execute(text(f"ALTER TABLE safety_findings ADD COLUMN {col_name} {col_type}"))

        if "safety_alerts" in tables:
            sa_cols = [c["name"] for c in inspector.get_columns("safety_alerts")]
            new_sa_cols = [
                ("video_event_id", "VARCHAR(36)"),
            ]
            with engine.begin() as conn:
                for col_name, col_type in new_sa_cols:
                    if col_name not in sa_cols:
                        conn.execute(text(f"ALTER TABLE safety_alerts ADD COLUMN {col_name} {col_type}"))
    except Exception as e:
        print(f"[WARN] Database column migration notice: {e}")


# Auto-run column migrations on module load so all test suites have current schema
try:
    migrate_db_columns(engine)
except Exception:
    pass
