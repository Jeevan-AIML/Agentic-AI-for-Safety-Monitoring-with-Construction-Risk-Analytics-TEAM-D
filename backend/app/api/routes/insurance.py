"""Insurance Intelligence REST API Router."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.models import User, UserRole, InsuranceClaimAssessment
from app.schemas.schemas import (
    InsuranceRiskAssessmentOut, InsuranceAnalysisRequest,
    InsuranceClaimAssessmentOut, ClaimDocumentationPackageOut,
    ClaimDocumentationRequest, InsuranceDemoScenarioOut,
    InsuranceDemoScenarioRequest
)
from app.services.insurance.insurance_service import InsuranceService
from app.services.insurance.demo_scenarios import INSURANCE_DEMO_SCENARIOS

router = APIRouter(prefix="/insurance", tags=["Insurance Intelligence"])
insurance_service = InsuranceService()

OPERATIONAL_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER, UserRole.SAFETY_OFFICER]
DEMO_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER, UserRole.SAFETY_OFFICER]


@router.post("/assess/{site_id}", response_model=InsuranceRiskAssessmentOut)
def assess_site_insurance(
    site_id: str,
    payload: Optional[InsuranceAnalysisRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an insurance exposure and underwriting risk assessment for a site."""
    if current_user.role not in OPERATIONAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to execute insurance risk assessments.",
        )
    is_sim = payload.is_simulation if payload else False
    try:
        return insurance_service.assess_site_insurance(
            db=db, site_id=site_id, is_simulation=is_sim
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/assessments/{site_id}/latest", response_model=Optional[InsuranceRiskAssessmentOut])
@router.get("/site/{site_id}", response_model=Optional[InsuranceRiskAssessmentOut])
def get_site_insurance(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the latest insurance assessment for a site."""
    assessment = insurance_service.get_latest_assessment(db, site_id)
    if not assessment:
        assessment = insurance_service.assess_site_insurance(db, site_id, is_simulation=False)
    return assessment


@router.get("/risk/{site_id}")
def get_insurance_risk_breakdown(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed insurance risk factors and underwriting exposure metrics."""
    assessment = insurance_service.get_latest_assessment(db, site_id)
    if not assessment:
        assessment = insurance_service.assess_site_insurance(db, site_id, is_simulation=False)

    return {
        "site_id": site_id,
        "insurance_risk_score": assessment.insurance_risk_score,
        "insurance_risk_level": assessment.insurance_risk_level,
        "exposure_index": assessment.exposure_index,
        "estimated_liability_exposure": assessment.estimated_liability_exposure,
        "contributing_factors": assessment.contributing_factors,
        "category_exposures": assessment.category_exposures,
        "unresolved_findings_count": assessment.unresolved_findings_count,
        "active_critical_alerts_count": assessment.active_critical_alerts_count,
        "compliance_deficit_penalty": assessment.compliance_deficit_penalty,
        "underwriting_recommendations": assessment.underwriting_recommendations,
        "evaluated_at": assessment.created_at.isoformat(),
        "disclaimer": "This score is computed deterministically for risk intelligence and is not a formal insurance policy underwriting commitment.",
    }


@router.get("/claims/{site_id}", response_model=List[InsuranceClaimAssessmentOut])
def list_site_claims(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all evaluated insurance claims and incident dossiers for a site."""
    return insurance_service.list_claims(db, site_id)


@router.post("/claim-documentation/{incident_id}", response_model=ClaimDocumentationPackageOut)
def generate_claim_documentation(
    incident_id: str,
    payload: Optional[ClaimDocumentationRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate or retrieve a structured claim documentation package for an incident."""
    if current_user.role not in OPERATIONAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to generate insurance claim documentation packages.",
        )

    # Check if package already exists
    claim = db.query(InsuranceClaimAssessment).filter(
        (InsuranceClaimAssessment.id == incident_id) |
        (InsuranceClaimAssessment.claim_assessment_id == incident_id)
    ).first()

    if claim and claim.package:
        return claim.package

    # Otherwise construct a new dossier
    incident_data = {
        "title": payload.incident_title if payload and payload.incident_title else f"Incident {incident_id}",
        "incident_ref": payload.incident_ref if payload and payload.incident_ref else incident_id,
        "worker_id": payload.worker_id if payload else None,
        "equipment_id": payload.equipment_id if payload else None,
        "severity": "HIGH",
    }
    site_id = claim.site_id if claim else (current_user.assigned_site_id or "SITE-001")
    is_sim = payload.is_simulation if payload else False

    result = insurance_service.create_claim_assessment_and_dossier(
        db=db,
        site_id=site_id,
        incident_data=incident_data,
        is_simulation=is_sim,
    )
    return result["documentation_package"]


@router.get("/demo-scenarios", response_model=List[InsuranceDemoScenarioOut])
def get_insurance_demo_scenarios(
    current_user: User = Depends(get_current_user),
):
    """List all deterministic insurance demo scenarios."""
    return [
        InsuranceDemoScenarioOut(
            id=s["id"],
            name=s["name"],
            description=s["description"],
            expected_risk_level=s["expected_risk_level"],
            expected_score_range=s["expected_score_range"],
            narrative=s["narrative"],
        )
        for s in INSURANCE_DEMO_SCENARIOS
    ]


@router.post("/demo-scenarios/run")
def run_insurance_demo_scenario(
    payload: InsuranceDemoScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a deterministic insurance demo scenario."""
    if current_user.role not in DEMO_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewer role is restricted to read-only access.",
        )
    try:
        result = insurance_service.run_demo_scenario(
            db=db, scenario_id=payload.scenario_id, site_id=payload.site_id
        )
        if payload.scenario_id == 7:
            # Returns dict with claim_assessment and documentation_package
            return {
                "scenario_id": 7,
                "claim_assessment": InsuranceClaimAssessmentOut.model_validate(result["claim_assessment"]),
                "documentation_package": ClaimDocumentationPackageOut.model_validate(result["documentation_package"]),
            }
        else:
            return InsuranceRiskAssessmentOut.model_validate(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
