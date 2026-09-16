"""Safety Alert System API Routes — Milestone 2 Phase 2.4
======================================================
Endpoints for:
- Querying and filtering alerts
- Inspecting alert details with audit events and dispatched notifications
- Acknowledging alerts
- Resolving alerts with mitigation feedback
- Tiered alert escalation
- Running deterministic demo scenarios
- Checking and triggering escalation timeouts
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.models.models import User, UserRole, Site, Worker
from app.schemas.schemas import (
    SafetyAlertOut,
    SafetyAlertDetailOut,
    AlertAcknowledgeIn,
    AlertResolveIn,
    AlertEscalateIn,
    AlertCreateIn,
    AlertDemoScenarioOut,
    AlertDemoScenarioRequest,
)
from app.services.alerts.alert_service import AlertService
from app.services.alerts.demo_scenarios import AlertDemoRunner, DEMO_SCENARIOS_CATALOG


router = APIRouter(prefix="/safety/alerts", tags=["safety-alerts"])
alert_service = AlertService()
demo_runner = AlertDemoRunner()


@router.get("", response_model=List[SafetyAlertOut])
def get_alerts(
    site_id: Optional[str] = Query(None, description="Filter by Site ID"),
    worker_id: Optional[str] = Query(None, description="Filter by Worker ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (open, acknowledged, escalated, resolved, dismissed)"),
    severity_filter: Optional[str] = Query(None, alias="severity", description="Filter by severity (high, critical)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List safety alerts with optional filtering.
    Available to all authenticated roles (Super Admin, Safety Officer, Site Manager, Project Manager, Viewer).
    """
    alerts = alert_service.list_alerts(
        db=db,
        site_id=site_id,
        worker_id=worker_id,
        status=status_filter,
        severity=severity_filter,
        limit=limit,
    )
    # Populate site_name and worker_name
    result = []
    for a in alerts:
        out = SafetyAlertOut.model_validate(a)
        if a.site:
            out.site_name = a.site.name
        if a.worker:
            out.worker_name = a.worker.name
        result.append(out)
    return result


@router.get("/demo-scenarios", response_model=List[AlertDemoScenarioOut])
def get_demo_scenarios(
    current_user: User = Depends(get_current_user),
):
    """
    List the 7 deterministic demo scenarios for the safety alert system.
    Available to all authenticated users.
    """
    return [
        AlertDemoScenarioOut(
            id=s["id"],
            name=s["name"],
            description=s["description"],
            expected_severity=s["expected_severity"],
            expected_status=s["expected_status"],
            summary=s["summary"],
        )
        for s in DEMO_SCENARIOS_CATALOG
    ]


@router.post("/demo-scenario", response_model=Dict[str, Any])
def run_demo_scenario(
    request: AlertDemoScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.SAFETY_OFFICER,
            UserRole.SITE_MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
):
    """
    Execute a deterministic alert demo scenario.
    Permissions: Safety Officer, Site Manager, Project Manager, Super Admin.
    """
    try:
        res = demo_runner.run_scenario(
            db=db,
            scenario_id=request.scenario_id,
            user=current_user,
            site_id=request.site_id,
        )
        # Convert any ORM SafetyAlert in res to dict
        if "alert" in res and res["alert"]:
            res["alert"] = SafetyAlertOut.model_validate(res["alert"]).model_dump()
        if "alert_a" in res and res["alert_a"]:
            res["alert_a"] = SafetyAlertOut.model_validate(res["alert_a"]).model_dump()
        if "alert_b" in res and res["alert_b"]:
            res["alert_b"] = SafetyAlertOut.model_validate(res["alert_b"]).model_dump()
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scenario execution failed: {str(e)}")


@router.get("/site/{site_id}", response_model=List[SafetyAlertOut])
def get_site_alerts(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all safety alerts for a specific construction site.
    Available to all authenticated roles.
    """
    alerts = alert_service.list_alerts(db=db, site_id=site_id)
    result = []
    for a in alerts:
        out = SafetyAlertOut.model_validate(a)
        if a.site:
            out.site_name = a.site.name
        if a.worker:
            out.worker_name = a.worker.name
        result.append(out)
    return result


@router.get("/worker/{worker_id}", response_model=List[SafetyAlertOut])
def get_worker_alerts(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all safety alerts concerning a specific worker.
    Available to all authenticated roles.
    """
    alerts = alert_service.list_alerts(db=db, worker_id=worker_id)
    result = []
    for a in alerts:
        out = SafetyAlertOut.model_validate(a)
        if a.site:
            out.site_name = a.site.name
        if a.worker:
            out.worker_name = a.worker.name
        result.append(out)
    return result


@router.post("/check-timeouts", response_model=List[SafetyAlertOut])
def trigger_escalation_timeouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.SAFETY_OFFICER,
        )
    ),
):
    """
    Evaluates acknowledgment timeouts on all open alerts and triggers automated escalation.
    Permissions: Safety Officer, Super Admin.
    """
    escalated = alert_service.check_escalation_timeouts(db)
    return [SafetyAlertOut.model_validate(a) for a in escalated]


@router.get("/{alert_id}", response_model=SafetyAlertDetailOut)
def get_alert_detail(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve detailed alert data including full audit trail and dispatched notifications.
    Available to all authenticated roles.
    """
    alert = alert_service.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety Alert '{alert_id}' not found",
        )
    out = SafetyAlertDetailOut.model_validate(alert)
    if alert.site:
        out.site_name = alert.site.name
    if alert.worker:
        out.worker_name = alert.worker.name
    return out


@router.post("/{alert_id}/acknowledge", response_model=SafetyAlertOut)
def acknowledge_alert(
    alert_id: str,
    body: AlertAcknowledgeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.SAFETY_OFFICER,
            UserRole.SITE_MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
):
    """
    Acknowledge an open or escalated alert.
    Permissions: Safety Officer, Site Manager, Project Manager, Super Admin. (Viewer forbidden).
    """
    try:
        updated = alert_service.acknowledge_alert(
            db=db,
            alert_id=alert_id,
            user=current_user,
            notes=body.notes,
        )
        out = SafetyAlertOut.model_validate(updated)
        if updated.site:
            out.site_name = updated.site.name
        if updated.worker:
            out.worker_name = updated.worker.name
        return out
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Acknowledgment failed: {str(e)}")


@router.post("/{alert_id}/resolve", response_model=SafetyAlertOut)
def resolve_alert(
    alert_id: str,
    body: AlertResolveIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.SAFETY_OFFICER,
            UserRole.SITE_MANAGER,
        )
    ),
):
    """
    Resolve an alert with required corrective action / mitigation notes.
    Permissions: Safety Officer, Site Manager, Super Admin. (Project Manager, Viewer forbidden).
    """
    try:
        updated = alert_service.resolve_alert(
            db=db,
            alert_id=alert_id,
            user=current_user,
            notes=body.notes,
        )
        out = SafetyAlertOut.model_validate(updated)
        if updated.site:
            out.site_name = updated.site.name
        if updated.worker:
            out.worker_name = updated.worker.name
        return out
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Resolution failed: {str(e)}")


@router.post("/{alert_id}/escalate", response_model=SafetyAlertOut)
def escalate_alert(
    alert_id: str,
    body: AlertEscalateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.SAFETY_OFFICER,
        )
    ),
):
    """
    Manually escalate an alert to a higher supervisory role.
    Permissions: Safety Officer, Super Admin. (Site Manager, Project Manager, Viewer forbidden).
    """
    try:
        updated = alert_service.escalate_alert(
            db=db,
            alert_id=alert_id,
            user=current_user,
            reason=body.reason,
            target_role=body.target_role,
        )
        out = SafetyAlertOut.model_validate(updated)
        if updated.site:
            out.site_name = updated.site.name
        if updated.worker:
            out.worker_name = updated.worker.name
        return out
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Escalation failed: {str(e)}")
