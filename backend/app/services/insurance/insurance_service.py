"""Insurance Service for ACRIP Milestone 3.

Orchestrates insurance exposure assessments, incident claim risk evaluations,
and claim documentation package dossier compilation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from app.models.models import (
    Site, Worker, Equipment, Hazard, SafetyFinding, SafetyAlert,
    ComplianceAssessment, InsuranceRiskAssessment, InsuranceClaimAssessment,
    ClaimDocumentationPackage, RiskCategory
)
from app.services.insurance.engine import InsuranceAgent
from app.services.insurance.demo_scenarios import INSURANCE_DEMO_SCENARIOS


class InsuranceService:
    """Service encapsulating construction insurance underwriting and claims intelligence."""

    def __init__(self):
        self.agent = InsuranceAgent()

    def get_latest_assessment(self, db: Session, site_id: str) -> Optional[InsuranceRiskAssessment]:
        """Returns the most recent insurance risk assessment for a site."""
        return (
            db.query(InsuranceRiskAssessment)
            .filter(InsuranceRiskAssessment.site_id == site_id)
            .order_by(InsuranceRiskAssessment.created_at.desc())
            .first()
        )

    def list_claims(self, db: Session, site_id: str) -> List[InsuranceClaimAssessment]:
        """Lists all claim assessments for a site."""
        return (
            db.query(InsuranceClaimAssessment)
            .filter(InsuranceClaimAssessment.site_id == site_id)
            .order_by(InsuranceClaimAssessment.created_at.desc())
            .all()
        )

    def assess_site_insurance(
        self,
        db: Session,
        site_id: str,
        is_simulation: bool = False,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> InsuranceRiskAssessment:
        """
        Calculates deterministic insurance risk exposure score (0-100),
        liability brackets, category breakdowns, and underwriting guidance.
        Persists InsuranceRiskAssessment in DB.
        """
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site {site_id} not found")

        if custom_context:
            context = custom_context
            context["site_id"] = site_id
            context["is_simulation"] = is_simulation
        else:
            hazards = db.query(Hazard).filter(Hazard.site_id == site_id).all()
            safety_findings = db.query(SafetyFinding).filter(SafetyFinding.site_id == site_id).all()
            safety_alerts = db.query(SafetyAlert).filter(SafetyAlert.site_id == site_id).all()
            workers = db.query(Worker).filter(Worker.site_id == site_id).all()
            latest_cmp = (
                db.query(ComplianceAssessment)
                .filter(ComplianceAssessment.site_id == site_id)
                .order_by(ComplianceAssessment.created_at.desc())
                .first()
            )
            compliance_score = latest_cmp.compliance_score if latest_cmp else 85.0

            context = {
                "site_id": site_id,
                "is_simulation": is_simulation,
                "compliance_score": compliance_score,
                "hazards": [
                    {
                        "id": h.id,
                        "title": h.title,
                        "severity": h.severity.value if hasattr(h.severity, "value") else str(h.severity),
                    }
                    for h in hazards
                ],
                "safety_findings": [
                    {
                        "id": sf.id,
                        "status": sf.status.value if hasattr(sf.status, "value") else str(sf.status),
                        "severity": sf.severity.value if hasattr(sf.severity, "value") else str(sf.severity),
                        "description": sf.description,
                    }
                    for sf in safety_findings
                ],
                "safety_alerts": [
                    {
                        "id": sa.id,
                        "severity": sa.severity.value if hasattr(sa.severity, "value") else str(sa.severity),
                        "title": sa.title,
                    }
                    for sa in safety_alerts
                ],
                "workers": [
                    {
                        "id": w.id,
                        "role": w.role.value if hasattr(w.role, "value") else str(w.role),
                        "safety_training_status": w.safety_training_status.value if hasattr(w.safety_training_status, "value") else str(w.safety_training_status),
                    }
                    for w in workers
                ]
            }

        eval_result = self.agent.assess_risk(context)

        assessment = InsuranceRiskAssessment(
            id=str(uuid.uuid4()),
            assessment_id=f"INS-ASM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            site_id=site_id,
            insurance_risk_score=eval_result["insurance_risk_score"],
            insurance_risk_level=eval_result["insurance_risk_level"],
            exposure_index=eval_result["exposure_index"],
            estimated_liability_exposure=eval_result["estimated_liability_exposure"],
            contributing_factors=eval_result["contributing_factors"],
            category_exposures=eval_result["category_exposures"],
            unresolved_findings_count=eval_result["unresolved_findings_count"],
            active_critical_alerts_count=eval_result["active_critical_alerts_count"],
            compliance_deficit_penalty=eval_result["compliance_deficit_penalty"],
            underwriting_recommendations=eval_result["underwriting_recommendations"],
            is_simulation=is_simulation,
            created_at=datetime.utcnow(),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    def create_claim_assessment_and_dossier(
        self,
        db: Session,
        site_id: str,
        incident_data: Dict[str, Any],
        is_simulation: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluates an incident for insurance claim risk, computes missing proof,
        and generates a structured ClaimDocumentationPackage dossier.
        """
        claim_analysis = self.agent.analyzer.analyze_claim_risk(incident_data)
        dossier_data = self.agent.analyzer.generate_claim_documentation_package(claim_analysis, incident_data)

        # Persist claim assessment
        claim_obj = InsuranceClaimAssessment(
            id=str(uuid.uuid4()),
            claim_assessment_id=f"CLM-{uuid.uuid4().hex[:6].upper()}",
            site_id=site_id,
            incident_ref=incident_data.get("incident_ref", f"INC-{uuid.uuid4().hex[:4].upper()}"),
            incident_title=incident_data.get("title", "Reported Site Incident"),
            incident_date=datetime.utcnow(),
            involved_worker_id=incident_data.get("worker_id"),
            involved_equipment_id=incident_data.get("equipment_id"),
            incident_severity=claim_analysis["incident_severity"],
            claim_risk_level=claim_analysis["claim_risk_level"],
            claim_probability_pct=claim_analysis["claim_probability_pct"],
            documentation_completeness_pct=claim_analysis["documentation_completeness_pct"],
            potential_claim_indicators=claim_analysis["potential_claim_indicators"],
            contributing_safety_factors=claim_analysis["contributing_safety_factors"],
            contributing_compliance_factors=claim_analysis["contributing_compliance_factors"],
            missing_documentation=claim_analysis["missing_documentation"],
            status="UNDER_REVIEW",
            is_simulation=is_simulation,
            created_at=datetime.utcnow(),
        )
        db.add(claim_obj)
        db.flush()

        # Persist documentation package
        package_obj = ClaimDocumentationPackage(
            id=str(uuid.uuid4()),
            package_id=f"PKG-{uuid.uuid4().hex[:6].upper()}",
            claim_assessment_id=claim_obj.id,
            site_id=site_id,
            title=dossier_data["title"],
            incident_summary=dossier_data["incident_summary"],
            worker_dossier=dossier_data["worker_dossier"],
            equipment_dossier=dossier_data["equipment_dossier"],
            safety_findings_dossier=dossier_data["safety_findings_dossier"],
            compliance_findings_dossier=dossier_data["compliance_findings_dossier"],
            sensor_evidence_dossier=dossier_data["sensor_evidence_dossier"],
            missing_required_documents=dossier_data["missing_required_documents"],
            recommended_actions=dossier_data["recommended_actions"],
            is_complete=dossier_data["is_complete"],
            is_simulation=is_simulation,
            created_at=datetime.utcnow(),
        )
        db.add(package_obj)
        db.commit()
        db.refresh(claim_obj)
        db.refresh(package_obj)

        return {
            "claim_assessment": claim_obj,
            "documentation_package": package_obj,
        }

    def run_demo_scenario(self, db: Session, scenario_id: int, site_id: Optional[str] = None) -> Any:
        """Executes a pre-configured deterministic insurance demo scenario."""
        scenario = next((s for s in INSURANCE_DEMO_SCENARIOS if s["id"] == scenario_id), None)
        if not scenario:
            raise ValueError(f"Demo scenario {scenario_id} not found")

        if not site_id:
            site = db.query(Site).first()
            if not site:
                raise ValueError("No site available to execute demo scenario")
            site_id = site.id

        if scenario_id == 7:
            # Claim documentation scenario
            incident = scenario["context"]["incident"]
            incident["site_id"] = site_id
            return self.create_claim_assessment_and_dossier(
                db=db,
                site_id=site_id,
                incident_data=incident,
                is_simulation=True,
            )
        else:
            return self.assess_site_insurance(
                db=db,
                site_id=site_id,
                is_simulation=True,
                custom_context=scenario["context"]
            )
