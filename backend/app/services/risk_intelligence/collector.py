"""
Risk Intelligence Data Collector — Milestone 4 Phase 4.2
========================================================
Collects and unifies operational findings across Site Risk, Safety,
Compliance, and Insurance agents for risk intelligence analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dataclasses import dataclass, asdict

from app.models.models import (
    Site, Project, Worker, Equipment, Activity,
    Hazard, RiskScore, SafetyFinding, SafetyAnalysis, SafetyAlert,
    ComplianceFinding, ComplianceAssessment, InspectionRequirement,
    InsuranceRiskAssessment, InsuranceClaimAssessment, PPEAnalysis
)
from app.services.reporting.normalizer import (
    NormalizedFinding,
    normalize_site_risk_hazard,
    normalize_safety_finding,
    normalize_safety_alert,
    normalize_compliance_finding,
    normalize_insurance_claim,
)


@dataclass
class RiskIntelligenceFinding:
    """Normalized finding representation for cross-agent risk intelligence."""
    source_agent: str          # 'site_risk' | 'safety' | 'compliance' | 'insurance'
    finding_id: str
    category: str              # 'HAZARD' | 'SAFETY_VIOLATION' | 'REGULATORY_BREACH' | 'INSURANCE_CLAIM'
    risk_level: str = "LOW"    # 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    risk_score: float = 0.0    # 0.0 to 100.0
    severity: str = "LOW"
    probability: Optional[float] = None
    status: str = "OPEN"
    timestamp: Any = ""
    description: str = ""
    project_id: Optional[str] = None
    site_id: Optional[str] = None
    evidence: Optional[str] = None
    finding_type: Optional[str] = None
    score: Optional[float] = None
    location: Optional[str] = None
    is_resolved: bool = False
    source_table: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.score is not None and self.risk_score == 0.0:
            self.risk_score = float(self.score)
        if isinstance(self.timestamp, datetime):
            self.timestamp = self.timestamp.isoformat()
        if not self.finding_type and self.metadata:
            self.finding_type = self.metadata.get("hazard_type") or self.metadata.get("violation_type")
        if not self.location and self.metadata:
            self.location = self.metadata.get("location")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RiskDataCollector:
    """Collects actual data from all ACRIP agent data stores."""

    def collect_site_findings(
        self,
        db: Session,
        site_id: str,
        window_days: int = 30,
    ) -> List[RiskIntelligenceFinding]:
        """Convenience method returning raw normalized findings list."""
        data = self.collect(db=db, site_id=site_id, time_window_days=window_days)
        return data.get("findings", [])

    def collect(
        self,
        db: Optional[Session] = None,
        site_id: Optional[str] = None,
        time_window_days: int = 30,
        custom_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Gathers raw findings, assessments, and metrics from all 4 agent pillars.
        Gracefully handles missing or partial datasets.
        """
        if custom_context:
            return self._collect_from_context(custom_context, site_id, time_window_days)

        if not db or not site_id:
            raise ValueError("Either custom_context or (db, site_id) must be provided.")

        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site with id {site_id} not found.")

        project = (
            db.query(Project).filter(Project.id == site.project_id).first()
            if site.project_id
            else None
        )

        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)

        # ── 1. Site Risk Agent ──────────────────────────────────────────────
        hazards = (
            db.query(Hazard)
            .filter(Hazard.site_id == site_id, Hazard.detected_at >= cutoff_date)
            .order_by(Hazard.detected_at.desc())
            .all()
        )
        latest_risk_score = (
            db.query(RiskScore)
            .filter(RiskScore.site_id == site_id)
            .order_by(RiskScore.recorded_at.desc())
            .first()
        )
        site_risk_available = (len(hazards) > 0) or (latest_risk_score is not None)

        # ── 2. Safety Agent ─────────────────────────────────────────────────
        safety_findings = (
            db.query(SafetyFinding)
            .filter(SafetyFinding.site_id == site_id, SafetyFinding.created_at >= cutoff_date)
            .order_by(SafetyFinding.created_at.desc())
            .all()
        )
        safety_alerts = (
            db.query(SafetyAlert)
            .filter(SafetyAlert.site_id == site_id, SafetyAlert.created_at >= cutoff_date)
            .order_by(SafetyAlert.created_at.desc())
            .all()
        )
        latest_safety_analysis = (
            db.query(SafetyAnalysis)
            .filter(SafetyAnalysis.site_id == site_id)
            .order_by(SafetyAnalysis.created_at.desc())
            .first()
        )
        ppe_records = (
            db.query(PPEAnalysis)
            .filter(PPEAnalysis.site_id == site_id, PPEAnalysis.created_at >= cutoff_date)
            .order_by(PPEAnalysis.created_at.desc())
            .limit(50)
            .all()
        )
        safety_available = (len(safety_findings) > 0) or (len(safety_alerts) > 0) or (latest_safety_analysis is not None)

        # ── 3. Compliance Agent ─────────────────────────────────────────────
        compliance_findings = (
            db.query(ComplianceFinding)
            .filter(ComplianceFinding.site_id == site_id, ComplianceFinding.created_at >= cutoff_date)
            .order_by(ComplianceFinding.created_at.desc())
            .all()
        )
        latest_compliance = (
            db.query(ComplianceAssessment)
            .filter(ComplianceAssessment.site_id == site_id)
            .order_by(ComplianceAssessment.created_at.desc())
            .first()
        )
        inspections = db.query(InspectionRequirement).filter(InspectionRequirement.site_id == site_id).all()
        compliance_available = (len(compliance_findings) > 0) or (latest_compliance is not None)

        # ── 4. Insurance Agent ──────────────────────────────────────────────
        insurance_claims = (
            db.query(InsuranceClaimAssessment)
            .filter(InsuranceClaimAssessment.site_id == site_id, InsuranceClaimAssessment.created_at >= cutoff_date)
            .order_by(InsuranceClaimAssessment.created_at.desc())
            .all()
        )
        latest_insurance = (
            db.query(InsuranceRiskAssessment)
            .filter(InsuranceRiskAssessment.site_id == site_id)
            .order_by(InsuranceRiskAssessment.created_at.desc())
            .first()
        )
        insurance_available = (len(insurance_claims) > 0) or (latest_insurance is not None)

        # ── 5. Normalize Findings into RiskIntelligenceFinding ──────────────
        norm_findings: List[RiskIntelligenceFinding] = []

        for h in hazards:
            sev_str = h.risk_category.value.upper() if hasattr(h.risk_category, "value") else str(h.risk_category).upper()
            score_val = float(h.risk_score or 50.0)
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="site_risk",
                finding_id=h.hazard_id or h.id,
                category="HAZARD",
                risk_level=sev_str,
                risk_score=score_val,
                severity=sev_str,
                probability=float(h.probability) if h.probability else 3.0,
                status=h.status.value.upper() if hasattr(h.status, "value") else str(h.status).upper(),
                timestamp=h.detected_at.isoformat() if h.detected_at else datetime.utcnow().isoformat(),
                description=h.description or "Site hazard detected",
                project_id=site.project_id,
                site_id=site.id,
                evidence=h.evidence,
                metadata={
                    "hazard_type": h.hazard_type.value if hasattr(h.hazard_type, "value") else str(h.hazard_type),
                    "recommended_action": h.recommended_action,
                }
            ))

        for sf in safety_findings:
            sev_str = sf.severity.value.upper() if hasattr(sf.severity, "value") else str(sf.severity).upper()
            score_val = 80.0 if sev_str == "CRITICAL" else (60.0 if sev_str == "HIGH" else (35.0 if sev_str == "MEDIUM" else 15.0))
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="safety",
                finding_id=sf.finding_id or sf.id,
                category="SAFETY_VIOLATION",
                risk_level=sev_str,
                risk_score=score_val,
                severity=sev_str,
                probability=4.0 if sev_str in ["HIGH", "CRITICAL"] else 2.0,
                status=sf.status.value.upper() if hasattr(sf.status, "value") else str(sf.status).upper(),
                timestamp=sf.created_at.isoformat() if sf.created_at else datetime.utcnow().isoformat(),
                description=sf.description or "Safety violation",
                project_id=site.project_id,
                site_id=site.id,
                evidence=sf.evidence,
                metadata={
                    "finding_type": sf.finding_type.value if hasattr(sf.finding_type, "value") else str(sf.finding_type),
                    "worker_id": sf.worker_id,
                    "recommendation": sf.recommendation,
                }
            ))

        for sa in safety_alerts:
            sev_str = sa.severity.value.upper() if hasattr(sa.severity, "value") else str(sa.severity).upper()
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="safety",
                finding_id=sa.alert_id or sa.id,
                category="SAFETY_ALERT",
                risk_level=sev_str,
                risk_score=85.0 if sev_str == "CRITICAL" else 65.0,
                severity=sev_str,
                probability=4.0,
                status=sa.status.value.upper() if hasattr(sa.status, "value") else str(sa.status).upper(),
                timestamp=sa.created_at.isoformat() if sa.created_at else datetime.utcnow().isoformat(),
                description=f"{sa.title}: {sa.description}" if sa.description else sa.title,
                project_id=site.project_id,
                site_id=site.id,
                evidence=sa.evidence,
                metadata={
                    "escalation_level": sa.escalation_level,
                    "assigned_role": sa.assigned_role,
                }
            ))

        for cf in compliance_findings:
            sev_str = cf.severity.value.upper() if hasattr(cf.severity, "value") else str(cf.severity).upper()
            score_val = 80.0 if sev_str == "CRITICAL" else (60.0 if sev_str == "HIGH" else 30.0)
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="compliance",
                finding_id=cf.finding_id or cf.id,
                category="REGULATORY_BREACH",
                risk_level=sev_str,
                risk_score=score_val,
                severity=sev_str,
                probability=3.5,
                status=cf.status.value.upper() if hasattr(cf.status, "value") else str(cf.status).upper(),
                timestamp=cf.created_at.isoformat() if cf.created_at else datetime.utcnow().isoformat(),
                description=cf.description or "Regulatory violation",
                project_id=site.project_id,
                site_id=site.id,
                evidence=cf.evidence,
                metadata={
                    "standard_ref": cf.standard_ref,
                    "violation_type": cf.violation_type,
                    "recommendation": cf.recommendation,
                }
            ))

        for cl in insurance_claims:
            c_risk = cl.claim_risk_level.value.upper() if hasattr(cl.claim_risk_level, "value") else str(cl.claim_risk_level).upper()
            sev_map = {"SEVERE": "CRITICAL", "HIGH": "HIGH", "MODERATE": "MEDIUM", "LOW": "LOW"}
            sev_str = sev_map.get(c_risk, "MEDIUM")
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="insurance",
                finding_id=cl.claim_assessment_id or cl.id,
                category="INSURANCE_CLAIM",
                risk_level=sev_str,
                risk_score=float(cl.claim_probability_pct or 50.0),
                severity=sev_str,
                probability=float(cl.claim_probability_pct or 50.0) / 20.0,
                status=(cl.status or "UNDER_REVIEW").upper(),
                timestamp=cl.created_at.isoformat() if cl.created_at else datetime.utcnow().isoformat(),
                description=f"{cl.incident_title} (Ref: {cl.incident_ref})",
                project_id=site.project_id,
                site_id=site.id,
                evidence=f"Documentation completeness: {cl.documentation_completeness_pct}%",
                metadata={
                    "incident_ref": cl.incident_ref,
                    "claim_probability_pct": cl.claim_probability_pct,
                    "documentation_completeness_pct": cl.documentation_completeness_pct,
                }
            ))

        return {
            "site": {
                "id": site.id,
                "site_id": site.site_id,
                "name": site.name,
                "site_type": site.site_type,
                "project_id": site.project_id,
                "project_name": project.name if project else "General Construction Project",
                "client": project.client if project else "N/A",
                "city": site.city,
                "state": site.state,
                "worker_count": site.worker_count,
                "equipment_count": site.equipment_count,
                "current_risk_score": site.current_risk_score,
                "current_risk_category": site.risk_category.value if hasattr(site.risk_category, "value") else str(site.risk_category),
            },
            "data_quality": {
                "site_risk": "available" if site_risk_available else "unavailable",
                "safety": "available" if safety_available else "unavailable",
                "compliance": "available" if compliance_available else "unavailable",
                "insurance": "available" if insurance_available else "unavailable",
            },
            "findings": norm_findings,
            "raw": {
                "latest_risk_score": latest_risk_score,
                "latest_safety_analysis": latest_safety_analysis,
                "latest_compliance": latest_compliance,
                "latest_insurance": latest_insurance,
                "inspections": inspections,
                "ppe_records": ppe_records,
                "hazards_count": len(hazards),
                "safety_findings_count": len(safety_findings),
                "compliance_findings_count": len(compliance_findings),
                "insurance_claims_count": len(insurance_claims),
            }
        }

    def _collect_from_context(
        self,
        context: Dict[str, Any],
        site_id: Optional[str] = None,
        time_window_days: int = 30,
    ) -> Dict[str, Any]:
        """Collect directly from a custom context dictionary (for testing or simulations)."""
        site_info = {
            "id": context.get("site_id") or site_id or "SITE-CTX-001",
            "site_id": context.get("site_code") or context.get("site_id") or "SITE-CTX-001",
            "name": context.get("site_name", "Risk Intelligence Context Site"),
            "site_type": context.get("site_type", "Commercial"),
            "project_id": context.get("project_id", "PROJ-001"),
            "project_name": context.get("project_name", "Enterprise Project"),
            "client": context.get("client", "Client Corp"),
            "city": context.get("city", "Austin"),
            "state": context.get("state", "TX"),
            "worker_count": context.get("worker_count", 30),
            "equipment_count": context.get("equipment_count", 8),
            "current_risk_score": context.get("current_risk_score", 45.0),
            "current_risk_category": context.get("current_risk_category", "MEDIUM"),
        }

        norm_findings: List[RiskIntelligenceFinding] = []

        # Hazards
        raw_hazards = context.get("hazards", [])
        for h in raw_hazards:
            norm_h = normalize_site_risk_hazard(h)
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="site_risk",
                finding_id=norm_h.finding_id,
                category="HAZARD",
                risk_level=norm_h.risk_level,
                risk_score=float(h.get("risk_score") or (70.0 if norm_h.risk_level == "HIGH" else 40.0)),
                severity=norm_h.severity,
                probability=float(h.get("probability") or 3.0),
                status=norm_h.status,
                timestamp=norm_h.timestamp,
                description=norm_h.description,
                project_id=site_info["project_id"],
                site_id=site_info["id"],
                evidence=norm_h.metadata.get("evidence") if norm_h.metadata else None,
                metadata=norm_h.metadata,
            ))

        # Safety
        raw_safety = context.get("safety_findings", [])
        for sf in raw_safety:
            norm_sf = normalize_safety_finding(sf)
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="safety",
                finding_id=norm_sf.finding_id,
                category="SAFETY_VIOLATION",
                risk_level=norm_sf.risk_level,
                risk_score=75.0 if norm_sf.risk_level == "HIGH" else 35.0,
                severity=norm_sf.severity,
                probability=3.0,
                status=norm_sf.status,
                timestamp=norm_sf.timestamp,
                description=norm_sf.description,
                project_id=site_info["project_id"],
                site_id=site_info["id"],
                evidence=norm_sf.metadata.get("evidence") if norm_sf.metadata else None,
                metadata=norm_sf.metadata,
            ))

        # Compliance
        raw_compliance = context.get("compliance_findings", [])
        for cf in raw_compliance:
            norm_cf = normalize_compliance_finding(cf)
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="compliance",
                finding_id=norm_cf.finding_id,
                category="REGULATORY_BREACH",
                risk_level=norm_cf.risk_level,
                risk_score=80.0 if norm_cf.risk_level == "CRITICAL" else 55.0,
                severity=norm_cf.severity,
                probability=3.5,
                status=norm_cf.status,
                timestamp=norm_cf.timestamp,
                description=norm_cf.description,
                project_id=site_info["project_id"],
                site_id=site_info["id"],
                evidence=norm_cf.metadata.get("evidence") if norm_cf.metadata else None,
                metadata=norm_cf.metadata,
            ))

        # Insurance
        raw_claims = context.get("insurance_claims", [])
        for cl in raw_claims:
            norm_cl = normalize_insurance_claim(cl)
            norm_findings.append(RiskIntelligenceFinding(
                source_agent="insurance",
                finding_id=norm_cl.finding_id,
                category="INSURANCE_CLAIM",
                risk_level=norm_cl.risk_level,
                risk_score=float(cl.get("claim_probability_pct", 50.0)),
                severity=norm_cl.severity,
                probability=float(cl.get("claim_probability_pct", 50.0)) / 20.0,
                status=norm_cl.status,
                timestamp=norm_cl.timestamp,
                description=norm_cl.description,
                project_id=site_info["project_id"],
                site_id=site_info["id"],
                evidence=str(cl.get("potential_claim_indicators", [])),
                metadata=norm_cl.metadata,
            ))

        return {
            "site": site_info,
            "data_quality": {
                "site_risk": "available" if len(raw_hazards) > 0 or "site_risk" in context else "unavailable",
                "safety": "available" if len(raw_safety) > 0 or "safety" in context else "unavailable",
                "compliance": "available" if len(raw_compliance) > 0 or "compliance" in context else "unavailable",
                "insurance": "available" if len(raw_claims) > 0 or "insurance" in context else "unavailable",
            },
            "findings": norm_findings,
            "raw": {
                "latest_risk_score": context.get("latest_risk_score"),
                "latest_safety_analysis": context.get("latest_safety_analysis"),
                "latest_compliance": context.get("latest_compliance"),
                "latest_insurance": context.get("latest_insurance"),
                "inspections": context.get("inspections", []),
                "ppe_records": context.get("ppe_records", []),
                "hazards_count": len(raw_hazards),
                "safety_findings_count": len(raw_safety),
                "compliance_findings_count": len(raw_compliance),
                "insurance_claims_count": len(raw_claims),
            }
        }
