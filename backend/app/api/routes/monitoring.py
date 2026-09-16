"""
Worker Safety Monitoring API Routes — Milestone 2 Phase 2.3
============================================================
Endpoints for starting/stopping monitoring, evaluating worker safety conditions,
querying site and worker telemetry history, and executing demo scenarios.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.models.models import User, UserRole
from app.schemas.schemas import (
    WorkerMonitoringInput,
    WorkerMonitoringEvaluationOut,
    SiteMonitoringStatusOut,
    SafetyMonitoringEventOut,
    MonitoringDemoScenarioOut,
)
from app.services.monitoring.monitoring_service import monitoring_service


router = APIRouter(prefix="/safety/monitoring", tags=["safety-monitoring"])


@router.post("/start/{site_id}", response_model=SiteMonitoringStatusOut)
def start_site_monitoring(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.SAFETY_OFFICER,
        )
    ),
):
    """
    Start live worker safety monitoring on a site.
    Permission: Safety Officer, Super Admin.
    """
    try:
        monitoring_service.start_monitoring(db, site_id, user_id=current_user.id)
        return monitoring_service.get_site_monitoring_status(db, site_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/stop/{site_id}", response_model=SiteMonitoringStatusOut)
def stop_site_monitoring(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.SAFETY_OFFICER,
        )
    ),
):
    """
    Stop live worker safety monitoring on a site.
    Permission: Safety Officer, Super Admin.
    """
    try:
        monitoring_service.stop_monitoring(db, site_id, user_id=current_user.id)
        return monitoring_service.get_site_monitoring_status(db, site_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to stop monitoring: {str(e)}")


@router.post("/evaluate/{worker_id}", response_model=WorkerMonitoringEvaluationOut)
def evaluate_worker_safety(
    worker_id: str,
    payload: Optional[WorkerMonitoringInput] = None,
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
    Evaluate real-time safety conditions for a specific worker against the 8 monitoring rules.
    Permission: Safety Officer, Site Manager, Super Admin.
    """
    input_dict = payload.model_dump() if payload else {}
    try:
        return monitoring_service.evaluate_worker(db, worker_id, input_dict, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Evaluation failed: {str(e)}")


@router.get("/site/{site_id}", response_model=SiteMonitoringStatusOut)
def get_site_monitoring(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get live monitoring status and telemetry counts for a site.
    Permission: All authenticated users (including Viewer).
    """
    try:
        return monitoring_service.get_site_monitoring_status(db, site_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/worker/{worker_id}", response_model=List[SafetyMonitoringEventOut])
def get_worker_monitoring_history(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent safety monitoring events for a worker.
    Permission: All authenticated users (including Viewer).
    """
    return monitoring_service.get_worker_monitoring_history(db, worker_id)


@router.get("/demo-scenarios", response_model=List[MonitoringDemoScenarioOut])
def list_demo_scenarios(
    current_user: User = Depends(get_current_user),
):
    """
    List deterministic Phase 2.3 worker safety monitoring demo scenarios.
    Permission: All authenticated users.
    """
    return monitoring_service.list_demo_scenarios()


@router.post("/demo-scenario", response_model=WorkerMonitoringEvaluationOut)
def run_demo_scenario(
    scenario_id: int = Body(..., embed=True),
    site_id: Optional[str] = Body(None, embed=True),
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
    Execute a deterministic worker monitoring demo scenario.
    Output is explicitly labeled DEMO / SIMULATION.
    Permission: Safety Officer, Site Manager, Project Manager, Super Admin (Viewer receives 403).
    """
    try:
        return monitoring_service.run_demo_scenario(db, scenario_id, site_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Demo execution failed: {str(e)}")
