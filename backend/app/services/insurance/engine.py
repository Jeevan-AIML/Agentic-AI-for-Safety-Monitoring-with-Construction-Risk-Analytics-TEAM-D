"""Insurance Risk Analyzer & Insurance Agent.

Deterministic, explainable construction insurance exposure scoring,
claim risk analysis, and structured claim documentation package builder.

Synthesizes data across:
1. Active physical hazards and incident severity
2. Unresolved safety findings and safety alerts
3. Regulatory compliance deficits and inspection track records
4. High-risk worker density and machinery exposure
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.models.models import (
    InsuranceRiskLevel, ClaimRiskLevel,
    RiskCategory, SafetyFindingStatus
)


class BaseInsuranceAgent(ABC):
    """Abstract base class for construction insurance agents."""

    def __init__(self, agent_id: str, name: str, version: str = "1.0.0"):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.last_run: Optional[datetime] = None

    @abstractmethod
    def assess_risk(self, site_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall insurance risk exposure for a construction site."""
        pass


class InsuranceRiskAnalyzer:
    """
    Deterministic insurance exposure evaluation engine.
    Calculates explainable 0–100 risk score and claim assessments.
    """

    def calculate_insurance_score(self, site_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes deterministic insurance risk score (0-100) based on:
        - Base Hazard Exposure (up to 40 pts)
        - Compliance Deficit Penalty (up to 30 pts)
        - Safety Findings & Alert Deficit (up to 20 pts)
        - Worker High-Risk Exposure (up to 10 pts)
        """
        hazards: List[Dict[str, Any]] = site_context.get("hazards", [])
        compliance_score: float = float(site_context.get("compliance_score", 100.0))
        safety_findings: List[Dict[str, Any]] = site_context.get("safety_findings", [])
        safety_alerts: List[Dict[str, Any]] = site_context.get("safety_alerts", [])
        workers: List[Dict[str, Any]] = site_context.get("workers", [])
        is_simulation: bool = site_context.get("is_simulation", False)

        # 1. Base Hazard Exposure (0 - 40 pts)
        critical_hazards = [h for h in hazards if str(h.get("severity", "")).upper() in ["CRITICAL", "5"]]
        high_hazards = [h for h in hazards if str(h.get("severity", "")).upper() in ["HIGH", "4"]]
        hazard_pts = min(40.0, (len(critical_hazards) * 15.0) + (len(high_hazards) * 8.0))

        # 2. Compliance Deficit Penalty (0 - 30 pts)
        compliance_deficit = max(0.0, 100.0 - compliance_score)
        compliance_pts = min(30.0, compliance_deficit * 0.35)

        # 3. Safety Findings & Active Alerts Deficit (0 - 20 pts)
        open_findings = [f for f in safety_findings if str(f.get("status", "")).upper() in ["OPEN", "ACKNOWLEDGED"]]
        critical_alerts = [a for a in safety_alerts if str(a.get("severity", "")).upper() in ["CRITICAL", "HIGH"]]
        findings_pts = min(20.0, (len(open_findings) * 3.0) + (len(critical_alerts) * 4.0))

        # 4. Worker Exposure Factor (0 - 10 pts)
        high_risk_workers = [
            w for w in workers
            if any(role in str(w.get("role", "")).lower() for role in ["scaffolder", "ironworker", "crane", "excavator", "blaster", "welder"])
        ]
        worker_pts = min(10.0, len(high_risk_workers) * 2.5)

        # Total Deterministic Insurance Score
        total_score = round(min(100.0, max(0.0, hazard_pts + compliance_pts + findings_pts + worker_pts)), 1)

        # Risk Level & Financial Exposure Bracket
        if total_score >= 80.0:
            risk_level = InsuranceRiskLevel.CRITICAL
            exposure_bracket = "$750,000 — $1,500,000+"
            exposure_index = 0.92
        elif total_score >= 60.0:
            risk_level = InsuranceRiskLevel.HIGH
            exposure_bracket = "$350,000 — $750,000"
            exposure_index = 0.72
        elif total_score >= 30.0:
            risk_level = InsuranceRiskLevel.MEDIUM
            exposure_bracket = "$100,000 — $350,000"
            exposure_index = 0.45
        else:
            risk_level = InsuranceRiskLevel.LOW
            exposure_bracket = "$25,000 — $100,000"
            exposure_index = 0.18

        # Breakdown by insurance line
        category_exposures = {
            "workers_compensation": round(min(100.0, worker_pts * 4.0 + findings_pts * 2.0), 1),
            "general_liability": round(min(100.0, hazard_pts * 1.5 + compliance_pts * 1.2), 1),
            "commercial_property": round(min(100.0, hazard_pts * 1.2 + 10.0), 1),
        }

        # Underwriting recommendations
        underwriting_recommendations: List[str] = []
        if critical_hazards:
            underwriting_recommendations.append(
                f"Remediate {len(critical_hazards)} critical site hazard(s) immediately to avoid deductible escalation."
            )
        if compliance_score < 80.0:
            underwriting_recommendations.append(
                f"Elevate statutory compliance score from {compliance_score:.1f}% to > 85.0% to unlock standard underwriting rates."
            )
        if open_findings:
            underwriting_recommendations.append(
                f"Close {len(open_findings)} unresolved safety finding(s) with verified engineering mitigation records."
            )
        if not underwriting_recommendations:
            underwriting_recommendations = [
                "Maintain baseline risk controls to retain preferred tier insurance underwriting status.",
                "Verify periodic third-party crane and pressure vessel certification renewals."
            ]

        return {
            "insurance_risk_score": total_score,
            "insurance_risk_level": risk_level,
            "exposure_index": exposure_index,
            "estimated_liability_exposure": exposure_bracket,
            "contributing_factors": {
                "hazard_exposure_points": round(hazard_pts, 1),
                "compliance_deficit_points": round(compliance_pts, 1),
                "safety_findings_points": round(findings_pts, 1),
                "worker_exposure_points": round(worker_pts, 1),
            },
            "category_exposures": category_exposures,
            "unresolved_findings_count": len(open_findings),
            "active_critical_alerts_count": len(critical_alerts),
            "compliance_deficit_penalty": round(compliance_pts, 1),
            "underwriting_recommendations": underwriting_recommendations,
            "is_simulation": is_simulation,
        }

    def analyze_claim_risk(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes an incident or near-miss for potential insurance claim exposure.
        Determines claim probability, documentation completeness, and missing proof.
        """
        severity_str = str(incident_data.get("severity", "MEDIUM")).upper()
        severity_map = {
            "CRITICAL": (RiskCategory.CRITICAL, ClaimRiskLevel.SEVERE, 85.0),
            "HIGH": (RiskCategory.HIGH, ClaimRiskLevel.HIGH, 65.0),
            "MEDIUM": (RiskCategory.MEDIUM, ClaimRiskLevel.MODERATE, 40.0),
            "LOW": (RiskCategory.LOW, ClaimRiskLevel.LOW, 15.0),
        }
        severity, claim_risk_level, default_prob = severity_map.get(
            severity_str, (RiskCategory.MEDIUM, ClaimRiskLevel.MODERATE, 40.0)
        )

        has_worker = bool(incident_data.get("worker_id"))
        has_equipment = bool(incident_data.get("equipment_id"))
        has_witness = bool(incident_data.get("witness_statement"))
        has_supervisor_signoff = bool(incident_data.get("supervisor_signoff"))
        has_sensor_evidence = bool(incident_data.get("sensor_evidence") or incident_data.get("video_ref"))

        # Calculate documentation completeness
        doc_checklist = [has_worker or has_equipment, has_witness, has_supervisor_signoff, has_sensor_evidence]
        doc_score = (sum(1 for item in doc_checklist if item) / len(doc_checklist)) * 100.0

        missing_docs = []
        if not has_supervisor_signoff:
            missing_docs.append("Formal Safety Supervisor Incident Sign-off & Root Cause Form")
        if not has_witness:
            missing_docs.append("Witness Worker Sworn Statement & Contact Dossier")
        if not has_sensor_evidence:
            missing_docs.append("CCTV Camera / Drone Aerial Inspection Video Time-stamp Archive")

        indicators = [
            f"Incident severity classified as {severity.value.upper()}",
            f"Estimated Claim Probability: {default_prob:.1f}%",
        ]
        if has_worker:
            indicators.append("Direct personnel bodily injury risk identified (Workers' Comp exposure)")
        if has_equipment:
            indicators.append("Heavy machinery property damage / structural impact risk")

        return {
            "incident_severity": severity,
            "claim_risk_level": claim_risk_level,
            "claim_probability_pct": default_prob,
            "documentation_completeness_pct": round(doc_score, 1),
            "potential_claim_indicators": indicators,
            "contributing_safety_factors": [
                incident_data.get("title", "Safety Incident"),
                f"Zone: {incident_data.get('zone', 'Site Active Zone')}",
            ],
            "contributing_compliance_factors": incident_data.get("compliance_factors", ["OSHA 1926 Safety Guidelines"]),
            "missing_documentation": missing_docs,
        }

    def generate_claim_documentation_package(
        self,
        claim_assessment: Dict[str, Any],
        incident_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compiles a structured, auditable claim documentation package
        preserving sensor evidence, worker training, and safety findings.
        """
        site_id = incident_context.get("site_id", "")
        worker_id = incident_context.get("worker_id")
        equipment_id = incident_context.get("equipment_id")

        return {
            "title": f"CLAIM-DOSSIER: {incident_context.get('title', 'Site Incident')}",
            "incident_summary": incident_context.get("summary", "Construction incident documented for insurance assessment."),
            "worker_dossier": {
                "worker_id": worker_id,
                "name": incident_context.get("worker_name", "Assigned Personnel"),
                "role": incident_context.get("worker_role", "Construction Tradesperson"),
                "ppe_status": incident_context.get("worker_ppe", "VERIFIED"),
                "certification_status": incident_context.get("worker_cert", "CURRENT"),
            } if worker_id else None,
            "equipment_dossier": {
                "equipment_id": equipment_id,
                "name": incident_context.get("equipment_name", "Construction Equipment"),
                "last_maintenance": incident_context.get("equipment_maint", "Active"),
            } if equipment_id else None,
            "safety_findings_dossier": incident_context.get("safety_findings", []),
            "compliance_findings_dossier": incident_context.get("compliance_findings", []),
            "sensor_evidence_dossier": {
                "video_event_id": incident_context.get("video_event_id"),
                "drone_photo_ref": incident_context.get("drone_photo_ref"),
                "telemetry_coordinates": incident_context.get("coordinates", {"lat": 17.385, "lng": 78.486}),
                "timestamp": datetime.utcnow().isoformat(),
            },
            "missing_required_documents": claim_assessment.get("missing_documentation", []),
            "recommended_actions": [
                "File preliminary carrier first notice of loss within statutory 24-hour window.",
                "Seal and preserve physical incident zone pending safety committee inspection.",
                "Attach medical evaluation and supervisor statement to claim file once completed."
            ],
            "is_complete": len(claim_assessment.get("missing_documentation", [])) == 0,
        }


class InsuranceAgent(BaseInsuranceAgent):
    """
    ACRIP Insurance Agent — Milestone 3
    ===================================
    Assesses insurance exposure, evaluates incident severity,
    analyzes claim risks, generates insurance risk scores,
    and builds structured claim documentation dossiers.
    """

    def __init__(self):
        super().__init__(
            agent_id="insurance_agent_v1",
            name="Insurance Agent",
            version="1.0.0-milestone3",
        )
        self.analyzer = InsuranceRiskAnalyzer()

    def assess_risk(self, site_context: Dict[str, Any]) -> Dict[str, Any]:
        self.last_run = datetime.utcnow()
        return self.analyzer.calculate_insurance_score(site_context)

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.assess_risk(context)

    async def health_check(self) -> bool:
        return True
