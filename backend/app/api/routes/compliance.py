"""Compliance Intelligence REST API Router."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.models import User, UserRole
from app.schemas.schemas import (
    ComplianceRuleOut, InspectionRequirementOut, InspectionRequirementCreate,
    ComplianceFindingOut, ComplianceAssessmentOut, ComplianceAnalysisRequest,
    ComplianceDemoScenarioOut, ComplianceDemoScenarioRequest
)
from app.services.compliance.compliance_service import ComplianceService
from app.services.compliance.demo_scenarios import COMPLIANCE_DEMO_SCENARIOS

router = APIRouter(prefix="/compliance", tags=["Compliance Intelligence"])
compliance_service = ComplianceService()

# Operational write roles
OPERATIONAL_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER, UserRole.SAFETY_OFFICER]
DEMO_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER, UserRole.SAFETY_OFFICER]


@router.post("/analyze/{site_id}", response_model=ComplianceAssessmentOut)
def analyze_site_compliance(
    site_id: str,
    payload: Optional[ComplianceAnalysisRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a regulatory compliance audit for a site."""
    if current_user.role not in OPERATIONAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to execute compliance audits.",
        )
    is_sim = payload.is_simulation if payload else False
    try:
        return compliance_service.analyze_site_compliance(
            db=db, site_id=site_id, is_simulation=is_sim
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/assessments/{site_id}/latest", response_model=Optional[ComplianceAssessmentOut])
@router.get("/site/{site_id}", response_model=Optional[ComplianceAssessmentOut])
def get_site_compliance(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the latest compliance assessment for a site."""
    assessment = compliance_service.get_latest_assessment(db, site_id)
    if not assessment:
        # Fallback: run initial baseline evaluation
        assessment = compliance_service.analyze_site_compliance(db, site_id, is_simulation=False)
    return assessment


@router.get("/findings/{site_id}", response_model=List[ComplianceFindingOut])
def list_compliance_findings(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List regulatory compliance findings for a site."""
    return compliance_service.list_findings(db, site_id)


@router.get("/rules", response_model=List[ComplianceRuleOut])
def list_regulatory_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active regulatory construction rules (OSHA / IS / ISO)."""
    return compliance_service.list_rules(db)


@router.get("/inspections/{site_id}", response_model=List[InspectionRequirementOut])
def list_inspection_requirements(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List required inspection tracking records for a site."""
    return compliance_service.list_inspections(db, site_id)


@router.post("/inspections/{site_id}", response_model=InspectionRequirementOut)
def create_inspection_requirement(
    site_id: str,
    payload: InspectionRequirementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new required statutory inspection for a site."""
    if current_user.role not in OPERATIONAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to schedule statutory inspections.",
        )
    return compliance_service.create_inspection_requirement(
        db, site_id, payload.model_dump()
    )


@router.get("/reports/{site_id}")
def get_compliance_report(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate structured compliance executive report."""
    assessment = compliance_service.get_latest_assessment(db, site_id)
    if not assessment:
        assessment = compliance_service.analyze_site_compliance(db, site_id, is_simulation=False)

    findings = compliance_service.list_findings(db, site_id)
    inspections = compliance_service.list_inspections(db, site_id)

    return {
        "site_id": site_id,
        "assessment_id": assessment.assessment_id,
        "compliance_score": assessment.compliance_score,
        "compliance_status": assessment.compliance_status.value if hasattr(assessment.compliance_status, "value") else str(assessment.compliance_status),
        "critical_violations_count": assessment.critical_violations,
        "high_violations_count": assessment.high_violations,
        "total_rules_evaluated": assessment.total_rules_evaluated,
        "rules_passed": assessment.rules_passed,
        "overdue_inspections_count": assessment.overdue_inspections,
        "category_scores": assessment.category_scores,
        "recommendations": assessment.recommendations,
        "findings": [
            {
                "finding_id": f.finding_id,
                "standard_ref": f.standard_ref,
                "violation_type": f.violation_type,
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "description": f.description,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
        "inspections": [
            {
                "requirement_id": i.requirement_id,
                "title": i.title,
                "inspection_type": i.inspection_type,
                "due_date": i.due_date.isoformat() if i.due_date else None,
                "status": i.status.value if hasattr(i.status, "value") else str(i.status),
                "is_overdue": i.is_overdue,
            }
            for i in inspections
        ],
        "generated_at": datetime.utcnow().isoformat(),
        "disclaimer": "This report is generated by the ACRIP Compliance Agent for internal risk intelligence and does not constitute formal legal counsel.",
    }


@router.get("/demo-scenarios", response_model=List[ComplianceDemoScenarioOut])
def get_compliance_demo_scenarios(
    current_user: User = Depends(get_current_user),
):
    """List all deterministic compliance demo scenarios."""
    return [
        ComplianceDemoScenarioOut(
            id=s["id"],
            name=s["name"],
            description=s["description"],
            category=s["category"],
            expected_status=s["expected_status"],
            expected_violations=s["expected_violations"],
            narrative=s["narrative"],
        )
        for s in COMPLIANCE_DEMO_SCENARIOS
    ]


@router.post("/demo-scenarios/run", response_model=ComplianceAssessmentOut)
def run_compliance_demo_scenario(
    payload: ComplianceDemoScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a deterministic compliance demo scenario."""
    if current_user.role not in DEMO_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewer role is restricted to read-only access.",
        )
    try:
        return compliance_service.run_demo_scenario(
            db=db, scenario_id=payload.scenario_id, site_id=payload.site_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
