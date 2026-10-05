"""
Reporting Agent REST API Router — Milestone 4 Phase 4.1
=======================================================
Exposes endpoints for multi-agent report generation, retrieval,
listing, and report type introspection.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.models import User, UserRole, ReportType
from app.schemas.schemas import (
    ReportGenerateRequest,
    GeneratedReportOut,
    GeneratedReportSummaryOut,
    ReportTypeInfoOut,
)
from app.services.reporting.reporting_service import ReportingService

router = APIRouter(prefix="/reports", tags=["Reporting Intelligence"])
reporting_service = ReportingService()


@router.get("/types", response_model=List[ReportTypeInfoOut])
def get_report_types():
    """Retrieve metadata and descriptions for all supported ACRIP report types."""
    return reporting_service.get_available_report_types()


@router.post("/generate", response_model=GeneratedReportOut, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate and persist a new intelligence report by dynamically aggregating
    findings from Site Risk, Safety, Compliance, and Insurance agents.
    """
    try:
        report = reporting_service.generate_and_save_report(
            db=db,
            site_id=payload.site_id,
            report_type=payload.report_type,
            reporting_period_start=payload.reporting_period_start,
            reporting_period_end=payload.reporting_period_end,
            title=payload.title,
            created_by=current_user.full_name or "ReportingAgent",
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("", response_model=List[GeneratedReportSummaryOut])
def list_reports(
    site_id: Optional[str] = Query(None, description="Filter by site ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List previously generated reports with optional filtering."""
    return reporting_service.list_reports(
        db=db,
        site_id=site_id,
        project_id=project_id,
        report_type=report_type,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=GeneratedReportOut)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full content and metadata for a specific generated report."""
    report = reporting_service.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with identifier '{report_id}' not found."
        )
    return report


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a generated report."""
    # Allow Super Admin, Project Manager, or Site Manager to delete
    allowed = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER]
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete reports."
        )
    success = reporting_service.delete_report(db, report_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with identifier '{report_id}' not found."
        )
    return {"success": True, "message": f"Report '{report_id}' deleted successfully."}
