from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.models import (
    Notification, User, UserRole, Project, Site, Worker, Equipment,
    Hazard, RiskScore, RiskCategory
)
from app.schemas.schemas import NotificationOut, DashboardKPI, RiskBreakdown
from app.api.dependencies import get_current_user, require_roles
import uuid

# ── Notifications ──────────────────────────────────────────────────────────

notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("", response_model=List[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    )
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return [NotificationOut.model_validate(n) for n in q.order_by(Notification.created_at.desc()).limit(50).all()]


@notifications_router.patch("/{notification_id}/read")
def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@notifications_router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None)),
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ── Dashboard ──────────────────────────────────────────────────────────────

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/kpi", response_model=DashboardKPI)
def get_dashboard_kpi(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Aggregate metrics across all sites
    sites = db.query(Site).all()
    total_sites = len(sites)
    total_projects = db.query(Project).count()
    total_workers = db.query(Worker).filter(Worker.is_active == True).count()
    total_equipment = db.query(Equipment).count()

    active_hazards = db.query(Hazard).filter(Hazard.status == "open").count()
    open_incidents = db.query(Hazard).filter(
        Hazard.status.in_(["open", "under_review"]),
        Hazard.risk_score >= 75
    ).count()

    # Average risk score across sites
    if sites:
        avg_risk = sum(s.current_risk_score for s in sites) / len(sites)
    else:
        avg_risk = 0.0

    risk_cat = RiskCategory.LOW
    if avg_risk >= 75:
        risk_cat = RiskCategory.CRITICAL
    elif avg_risk >= 50:
        risk_cat = RiskCategory.HIGH
    elif avg_risk >= 25:
        risk_cat = RiskCategory.MEDIUM

    return DashboardKPI(
        overall_risk_score=round(avg_risk, 1),
        risk_category=risk_cat,
        active_hazards=active_hazards,
        safety_observations=active_hazards + 16,  # MOCK_DATA: observations from manual records
        open_incidents=open_incidents,
        compliance_status=92.0,  # MOCK_DATA: will come from Compliance Agent in Phase 2
        site_monitoring="ACTIVE" if total_sites > 0 else "INACTIVE",
        total_sites=total_sites,
        total_projects=total_projects,
        total_workers=total_workers,
        total_equipment=total_equipment,
    )


@dashboard_router.get("/risk-breakdown", response_model=RiskBreakdown)
def get_risk_breakdown(
    site_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(RiskScore)
    if site_id:
        q = q.filter(RiskScore.site_id == site_id)
    latest = q.order_by(RiskScore.recorded_at.desc()).first()

    if latest:
        env = latest.environmental_risk
        eq = latest.equipment_risk
        sc = latest.site_condition_risk
        op = latest.operational_risk
        overall = latest.overall_score
        cat = latest.category
    else:
        # MOCK_DATA: Default demo values used until Site Risk Agent provides real data
        env, eq, sc, op = 68.0, 54.0, 82.0, 61.0
        overall = round((env * 0.25 + eq * 0.30 + sc * 0.25 + op * 0.20), 1)
        cat = RiskCategory.HIGH

    return RiskBreakdown(
        environmental_risk=env,
        equipment_risk=eq,
        site_condition_risk=sc,
        operational_risk=op,
        overall_risk=overall,
        category=cat,
    )
