"""
Executive Project Dashboard REST API Router — Milestone 4 Phase 4.3
===================================================================
Exposes consolidated executive intelligence endpoints aggregating
multi-agent risk scores, 4-pillar breakdowns, project health indicators,
critical cross-agent issues, recurring patterns, predictive causal chains,
operational recommendations, domain snapshots, recent reports, and risk trends.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.models import User, Site
from app.schemas.schemas import ExecutiveDashboardResponse
from app.services.dashboard.executive_service import ExecutiveDashboardService

router = APIRouter(prefix="/dashboard/executive", tags=["Executive Dashboard"])
executive_service = ExecutiveDashboardService()


@router.get(
    "",
    response_model=ExecutiveDashboardResponse,
    summary="Get consolidated executive dashboard overview",
)
def get_executive_dashboard_overview(
    site_id: Optional[str] = Query(None, description="Optional site identifier to focus dashboard"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve consolidated executive intelligence. If no site_id is specified,
    automatically resolves to the primary active site.
    """
    target_site_id = site_id
    if not target_site_id:
        first_site = db.query(Site).first()
        if not first_site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sites registered in the platform yet.",
            )
        target_site_id = first_site.id

    try:
        return executive_service.get_executive_dashboard(db=db, site_id=target_site_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Executive dashboard aggregation failed: {str(e)}",
        )


@router.get(
    "/{site_id}",
    response_model=ExecutiveDashboardResponse,
    summary="Get consolidated executive dashboard for a specific site",
)
def get_site_executive_dashboard(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the consolidated executive project dashboard for a designated site.
    Synthesizes Site Risk, Safety, Compliance, Insurance, Risk Intelligence,
    and Reporting data into a unified executive view.
    """
    try:
        return executive_service.get_executive_dashboard(db=db, site_id=site_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Executive dashboard aggregation failed: {str(e)}",
        )
