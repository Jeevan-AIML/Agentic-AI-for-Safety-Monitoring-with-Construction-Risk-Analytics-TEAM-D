"""Compliance Service for ACRIP Milestone 3.

Manages the lifecycle of regulatory rules, site compliance assessments,
inspection requirements, compliance findings, and automated dispatch
to SafetyFinding and AlertService.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from app.models.models import (
    Site, Worker, Equipment, Hazard, InspectionRequirement,
    ComplianceRule, ComplianceFinding, ComplianceAssessment,
    SafetyFinding, SafetyFindingType, SafetyFindingStatus,
    RiskCategory, User, UserRole, InspectionRequirementStatus,
    PPEAnalysis, PPEComplianceStatus
)
from app.services.compliance.rules import DEFAULT_COMPLIANCE_RULES
from app.services.compliance.engine import ComplianceAgent
from app.services.compliance.demo_scenarios import COMPLIANCE_DEMO_SCENARIOS
from app.services.alerts.alert_service import AlertService


class ComplianceService:
    """Service orchestrating regulatory compliance intelligence."""

    def __init__(self):
        self.agent = ComplianceAgent()
        self.alert_service = AlertService()

    def ensure_default_rules(self, db: Session) -> List[ComplianceRule]:
        """Seeds standard regulatory rules into DB if none exist."""
        existing_count = db.query(ComplianceRule).count()
        if existing_count == 0:
            rules_to_add = []
            for r in DEFAULT_COMPLIANCE_RULES:
                rule_obj = ComplianceRule(
                    id=str(uuid.uuid4()),
                    rule_id=r["rule_id"],
                    standard_ref=r["standard_ref"],
                    title=r["title"],
                    category=r["category"],
                    requirement=r["requirement"],
                    applicable_activity=r.get("applicable_activity"),
                    applicable_zone=r.get("applicable_zone"),
                    severity=r.get("severity", RiskCategory.MEDIUM),
                    remediation_recommendation=r["remediation_recommendation"],
                    is_active=r.get("is_active", True),
                    created_at=datetime.utcnow(),
                )
                rules_to_add.append(rule_obj)
            db.add_all(rules_to_add)
            db.commit()
        return db.query(ComplianceRule).filter(ComplianceRule.is_active == True).all()

    def list_rules(self, db: Session) -> List[ComplianceRule]:
        """Returns all configured regulatory rules."""
        self.ensure_default_rules(db)
        return db.query(ComplianceRule).all()

    def list_inspections(self, db: Session, site_id: str) -> List[InspectionRequirement]:
        """Returns all inspection requirements for a site."""
        return (
            db.query(InspectionRequirement)
            .filter(InspectionRequirement.site_id == site_id)
            .order_by(InspectionRequirement.due_date.asc())
            .all()
        )

    def create_inspection_requirement(
        self, db: Session, site_id: str, data: Dict[str, Any]
    ) -> InspectionRequirement:
        """Creates a new required inspection tracking entry."""
        insp = InspectionRequirement(
            id=str(uuid.uuid4()),
            requirement_id=f"INSP-{uuid.uuid4().hex[:6].upper()}",
            site_id=site_id,
            title=data.get("title", "Site Inspection"),
            inspection_type=data.get("inspection_type", "Routine"),
            regulatory_reference=data.get("regulatory_reference", "OSHA 1926.20"),
            responsible_role=data.get("responsible_role", "safety_officer"),
            due_date=data.get("due_date", datetime.utcnow()),
            status=data.get("status", InspectionRequirementStatus.PENDING),
            notes=data.get("notes"),
            created_at=datetime.utcnow(),
        )
        db.add(insp)
        db.commit()
        db.refresh(insp)
        return insp

    def get_latest_assessment(self, db: Session, site_id: str) -> Optional[ComplianceAssessment]:
        """Gets the most recent compliance assessment for a site."""
        return (
            db.query(ComplianceAssessment)
            .filter(ComplianceAssessment.site_id == site_id)
            .order_by(ComplianceAssessment.created_at.desc())
            .first()
        )

    def list_findings(self, db: Session, site_id: str) -> List[ComplianceFinding]:
        """Lists active compliance findings for a site."""
        return (
            db.query(ComplianceFinding)
            .filter(ComplianceFinding.site_id == site_id)
            .order_by(ComplianceFinding.created_at.desc())
            .all()
        )

    def analyze_site_compliance(
        self,
        db: Session,
        site_id: str,
        is_simulation: bool = False,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> ComplianceAssessment:
        """
        Executes a deterministic compliance audit on a site.
        Persists ComplianceAssessment, records ComplianceFindings,
        and dispatches high-severity violations to SafetyFinding & AlertService.
        """
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site {site_id} not found")

        self.ensure_default_rules(db)

        # Assemble site context
        if custom_context:
            context = custom_context
            context["site_id"] = site_id
            context["is_simulation"] = is_simulation
        else:
            workers = db.query(Worker).filter(Worker.site_id == site_id).all()
            equipment = db.query(Equipment).filter(Equipment.site_id == site_id).all()
            hazards = db.query(Hazard).filter(Hazard.site_id == site_id).all()
            inspections = db.query(InspectionRequirement).filter(InspectionRequirement.site_id == site_id).all()
            ppe_records = db.query(PPEAnalysis).filter(PPEAnalysis.site_id == site_id).order_by(PPEAnalysis.created_at.desc()).limit(20).all()

            context = {
                "site_id": site_id,
                "is_simulation": is_simulation,
                "workers": [
                    {
                        "id": w.id,
                        "worker_id": w.worker_id,
                        "name": w.name,
                        "role": w.role.value if hasattr(w.role, "value") else str(w.role),
                        "ppe_status": w.ppe_status.value if hasattr(w.ppe_status, "value") else str(w.ppe_status),
                        "safety_training_status": (
                            getattr(w, "safety_training", getattr(w, "safety_training_status", None)).value
                            if hasattr(getattr(w, "safety_training", getattr(w, "safety_training_status", None)), "value")
                            else str(getattr(w, "safety_training", getattr(w, "safety_training_status", "certified")))
                        ),
                    }
                    for w in workers
                ],
                "equipment": [
                    {
                        "id": eq.id,
                        "equipment_id": eq.equipment_id,
                        "name": eq.name,
                        "status": eq.status.value if hasattr(eq.status, "value") else str(eq.status),
                    }
                    for eq in equipment
                ],
                "hazards": [
                    {
                        "id": h.id,
                        "title": h.title,
                        "hazard_type": h.hazard_type.value if hasattr(h.hazard_type, "value") else str(h.hazard_type),
                        "location": h.location,
                        "severity": h.severity,
                    }
                    for h in hazards
                ],
                "inspections": [
                    {
                        "id": insp.id,
                        "title": insp.title,
                        "inspection_type": insp.inspection_type,
                        "regulatory_reference": insp.regulatory_reference,
                        "responsible_role": insp.responsible_role,
                        "due_date": insp.due_date,
                        "status": insp.status.value if hasattr(insp.status, "value") else str(insp.status),
                        "is_overdue": insp.is_overdue,
                    }
                    for insp in inspections
                ],
                "ppe_events": [
                    {
                        "is_compliant": (getattr(p, "overall_compliance", None) == PPEComplianceStatus.COMPLIANT) if hasattr(p, "overall_compliance") else getattr(p, "is_compliant", True),
                        "person_id": getattr(p, "worker_id", None) or getattr(p, "person_id", None) or getattr(p, "analysis_id", "unknown"),
                    }
                    for p in ppe_records
                ]
            }

        # Run deterministic evaluation
        eval_result = self.agent.evaluate(context)

        # Persist ComplianceAssessment
        assessment = ComplianceAssessment(
            id=str(uuid.uuid4()),
            assessment_id=f"CMP-ASM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            site_id=site_id,
            compliance_score=eval_result["compliance_score"],
            compliance_status=eval_result["compliance_status"],
            total_rules_evaluated=eval_result["total_rules_evaluated"],
            rules_passed=eval_result["rules_passed"],
            rules_violated=eval_result["rules_violated"],
            critical_violations=eval_result["critical_violations"],
            high_violations=eval_result["high_violations"],
            medium_violations=eval_result["medium_violations"],
            total_inspections=eval_result["total_inspections"],
            overdue_inspections=eval_result["overdue_inspections"],
            findings_summary=[
                {
                    "finding_id": f["finding_id"],
                    "standard_ref": f["standard_ref"],
                    "violation_type": f["violation_type"],
                    "severity": f["severity"].value if hasattr(f["severity"], "value") else str(f["severity"]),
                    "description": f["description"],
                }
                for f in eval_result["findings"]
            ],
            category_scores=eval_result["category_scores"],
            recommendations=eval_result["recommendations"],
            detection_source="COMPLIANCE_AGENT",
            is_simulation=is_simulation,
            created_at=datetime.utcnow(),
        )
        db.add(assessment)
        db.flush()

        # Persist ComplianceFindings and integrate with SafetyFinding / Alerts
        for f in eval_result["findings"]:
            finding_obj = ComplianceFinding(
                id=str(uuid.uuid4()),
                finding_id=f["finding_id"],
                site_id=site_id,
                rule_id=f.get("rule_id"),
                worker_id=f.get("worker_id"),
                inspection_requirement_id=f.get("inspection_requirement_id"),
                standard_ref=f["standard_ref"],
                violation_type=f["violation_type"],
                description=f["description"],
                severity=f["severity"],
                evidence=f.get("evidence"),
                recommendation=f["recommendation"],
                status=SafetyFindingStatus.OPEN,
                detection_source="COMPLIANCE_AGENT",
                is_simulation=is_simulation,
                created_at=datetime.utcnow(),
            )
            db.add(finding_obj)
            db.flush()

            # Integrate CRITICAL and HIGH severity findings into SafetyFinding & AlertEngine
            if f["severity"] in [RiskCategory.CRITICAL, RiskCategory.HIGH]:
                finding_type = (
                    SafetyFindingType.INSPECTION_OVERDUE
                    if f["violation_type"] == "REQUIRED_INSPECTION_OVERDUE"
                    else SafetyFindingType.REGULATORY_VIOLATION
                )
                sf = SafetyFinding(
                    id=str(uuid.uuid4()),
                    finding_id=f"SF-CMP-{uuid.uuid4().hex[:6].upper()}",
                    site_id=site_id,
                    worker_id=f.get("worker_id"),
                    finding_type=finding_type,
                    description=f"[{f['standard_ref']}] {f['description']}",
                    evidence=str(f.get("evidence", "")),
                    severity=f["severity"],
                    status=SafetyFindingStatus.OPEN,
                    recommendation=f["recommendation"],
                    detection_source="COMPLIANCE_AGENT",
                    compliance_finding_id=finding_obj.id,
                    created_at=datetime.utcnow(),
                )
                db.add(sf)
                db.flush()

                # Dispatch to AlertService
                self.alert_service.create_alert_from_finding(
                    db=db,
                    finding=sf,
                    is_simulation=is_simulation,
                )

        db.commit()
        db.refresh(assessment)
        return assessment

    def run_demo_scenario(self, db: Session, scenario_id: int, site_id: Optional[str] = None) -> ComplianceAssessment:
        """Executes a pre-configured deterministic demo scenario."""
        scenario = next((s for s in COMPLIANCE_DEMO_SCENARIOS if s["id"] == scenario_id), None)
        if not scenario:
            raise ValueError(f"Demo scenario {scenario_id} not found")

        # Resolve or pick site
        if not site_id:
            site = db.query(Site).first()
            if not site:
                raise ValueError("No site available to execute demo scenario")
            site_id = site.id

        return self.analyze_site_compliance(
            db=db,
            site_id=site_id,
            is_simulation=True,
            custom_context=scenario["context"]
        )
