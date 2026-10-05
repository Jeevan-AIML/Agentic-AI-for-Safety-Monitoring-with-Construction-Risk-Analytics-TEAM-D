"""
Agent Orchestration REST API Router
===================================
Milestone 4 Phase 4.4: Agent Orchestration Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.models import User, UserRole
from app.schemas.schemas import (
    OrchestrationRequest, OrchestrationRunResponse, OrchestrationHistoryResponse
)
from app.services.orchestration import orchestration_service

router = APIRouter(prefix="/orchestration", tags=["Agent Orchestration"])

OPERATIONAL_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.SAFETY_OFFICER,
    UserRole.SITE_MANAGER,
    UserRole.PROJECT_MANAGER,
    UserRole.VIEWER,
]


@router.post(
    "/run",
    response_model=OrchestrationRunResponse,
    summary="Trigger cross-agent orchestration workflow",
    status_code=status.HTTP_200_OK,
)
def run_orchestration(
    payload: OrchestrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a coordinated cross-agent workflow across:
    Level 1: Site Risk, Safety, Compliance, Insurance (Parallel)
    Level 2: Risk Intelligence Engine
    Level 3: Reporting Agent (optional)
    """
    if current_user.role not in OPERATIONAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to trigger cross-agent orchestration.",
        )

    try:
        return orchestration_service.execute_orchestration(
            db=db,
            request=payload,
            created_by=f"{current_user.full_name} ({current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)})",
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        if "active orchestration run" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent orchestration failed: {str(e)}",
        )


@router.get(
    "/{execution_id}",
    response_model=OrchestrationRunResponse,
    summary="Get detailed orchestration run execution record",
)
def get_orchestration_run(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full execution metadata and per-agent statuses for a specific execution ID."""
    try:
        return orchestration_service.get_execution(db=db, execution_id=execution_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{execution_id}/status",
    summary="Get execution status indicator for polling",
)
def get_orchestration_status(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve quick execution status and timestamps for polling/telemetry."""
    try:
        run = orchestration_service.get_execution(db=db, execution_id=execution_id)
        return {
            "execution_id": run.execution_id,
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "duration_ms": run.duration_ms,
            "agent_statuses": {
                name: (st.get("status") if isinstance(st, dict) else getattr(st, "status", "UNKNOWN"))
                for name, st in run.agent_statuses.items()
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/site/{site_id}/latest",
    response_model=Optional[OrchestrationRunResponse],
    summary="Get latest orchestration run for a site",
)
def get_latest_site_orchestration(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the most recent cross-agent orchestration run executed for the site."""
    return orchestration_service.get_latest_site_execution(db=db, site_id=site_id)


@router.get(
    "/site/{site_id}/history",
    response_model=OrchestrationHistoryResponse,
    summary="List historical orchestration runs for a site",
)
def list_site_orchestrations(
    site_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List historical orchestration executions for an active site."""
    runs, total = orchestration_service.list_site_executions(
        db=db, site_id=site_id, limit=limit, offset=offset
    )
    return OrchestrationHistoryResponse(runs=runs, total=total)
