"""
Report Findings Normalizer — Milestone 4 Phase 4.1
===================================================
Normalizes heterogeneous findings from SiteRiskAgent, SafetyAgent,
ComplianceAgent, and InsuranceAgent into a unified, auditable structure.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class NormalizedFinding:
    """Standardized representation of a risk or compliance finding across any agent."""
    source_agent: str          # 'site_risk' | 'safety' | 'compliance' | 'insurance'
    finding_type: str          # e.g., 'HAZARD_EXCAVATION', 'PPE_VIOLATION', 'REGULATORY_BREACH', 'CLAIM_EXPOSURE'
    finding_id: str            # Unique finding reference (e.g., 'HAZ-AI-0001', 'SAF-FND-0002')
    severity: str              # 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    risk_level: str            # Normalized risk level string
    status: str                # 'OPEN' | 'MITIGATED' | 'RESOLVED' | 'UNDER_REVIEW' | 'CLOSED'
    description: str           # Human-readable finding description
    timestamp: str             # ISO timestamp of detection
    recommendation: Optional[str] = None  # Actionable mitigation or corrective measure
    metadata: Optional[Dict[str, Any]] = None  # Agent-specific evidence, standard_refs, scores, etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_site_risk_hazard(hazard: Any) -> NormalizedFinding:
    """Normalize a Hazard database entity or hazard dictionary from SiteRiskAgent."""
    if isinstance(hazard, dict):
        h_id = str(hazard.get("hazard_id") or hazard.get("id") or "HAZ-GEN")
        h_type = str(hazard.get("hazard_type") or hazard.get("type") or "SITE_HAZARD")
        sev_val = str(hazard.get("risk_category") or hazard.get("risk_level") or "MEDIUM").upper()
        status_val = str(hazard.get("status") or "OPEN").upper()
        desc = str(hazard.get("description") or "Site risk detected")
        ts = str(hazard.get("detected_at") or hazard.get("timestamp") or datetime.utcnow().isoformat())
        rec = hazard.get("recommended_action") or hazard.get("recommendation")
        meta = {
            "evidence": hazard.get("evidence"),
            "probability": hazard.get("probability"),
            "severity_score": hazard.get("severity"),
            "risk_score": hazard.get("risk_score"),
            "detection_source": hazard.get("detection_source", "RULE_ENGINE"),
        }
    else:
        h_id = hazard.hazard_id or hazard.id
        h_type = hazard.hazard_type.value if hasattr(hazard.hazard_type, "value") else str(hazard.hazard_type)
        sev_raw = hazard.risk_category.value if hasattr(hazard.risk_category, "value") else str(hazard.risk_category)
        sev_val = sev_raw.upper() if sev_raw else "MEDIUM"
        status_raw = hazard.status.value if hasattr(hazard.status, "value") else str(hazard.status)
        status_val = status_raw.upper() if status_raw else "OPEN"
        desc = hazard.description or "Site risk hazard"
        ts = hazard.detected_at.isoformat() if hazard.detected_at else datetime.utcnow().isoformat()
        rec = hazard.recommended_action
        meta = {
            "evidence": hazard.evidence,
            "probability": hazard.probability,
            "severity_score": hazard.severity,
            "risk_score": hazard.risk_score,
            "detection_source": hazard.detection_source,
            "acknowledged_at": hazard.acknowledged_at.isoformat() if hazard.acknowledged_at else None,
            "mitigated_at": hazard.mitigated_at.isoformat() if hazard.mitigated_at else None,
        }

    return NormalizedFinding(
        source_agent="site_risk",
        finding_type=f"HAZARD_{h_type.upper()}",
        finding_id=h_id,
        severity=sev_val,
        risk_level=sev_val,
        status=status_val,
        description=desc,
        timestamp=ts,
        recommendation=rec,
        metadata=meta,
    )


def normalize_safety_finding(finding: Any) -> NormalizedFinding:
    """Normalize a SafetyFinding database entity or finding dictionary from SafetyAgent."""
    if isinstance(finding, dict):
        f_id = str(finding.get("finding_id") or finding.get("id") or "SAF-GEN")
        f_type = str(finding.get("finding_type") or "SAFETY_VIOLATION")
        sev_raw = str(finding.get("severity") or "MEDIUM").upper()
        status_val = str(finding.get("status") or "OPEN").upper()
        desc = str(finding.get("description") or "Safety violation detected")
        ts = str(finding.get("created_at") or datetime.utcnow().isoformat())
        rec = finding.get("recommendation")
        meta = {
            "evidence": finding.get("evidence"),
            "worker_id": finding.get("worker_id"),
            "detection_source": finding.get("detection_source", "RULE_ENGINE"),
        }
    else:
        f_id = finding.finding_id or finding.id
        f_type = finding.finding_type.value if hasattr(finding.finding_type, "value") else str(finding.finding_type)
        sev_raw = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        sev_raw = sev_raw.upper() if sev_raw else "MEDIUM"
        status_raw = finding.status.value if hasattr(finding.status, "value") else str(finding.status)
        status_val = status_raw.upper() if status_raw else "OPEN"
        desc = finding.description or "Worker safety violation"
        ts = finding.created_at.isoformat() if finding.created_at else datetime.utcnow().isoformat()
        rec = finding.recommendation
        meta = {
            "evidence": finding.evidence,
            "worker_id": finding.worker_id,
            "detection_source": finding.detection_source,
            "compliance_finding_id": getattr(finding, "compliance_finding_id", None),
        }

    return NormalizedFinding(
        source_agent="safety",
        finding_type=f_type.upper(),
        finding_id=f_id,
        severity=sev_raw,
        risk_level=sev_raw,
        status=status_val,
        description=desc,
        timestamp=ts,
        recommendation=rec,
        metadata=meta,
    )


def normalize_safety_alert(alert: Any) -> NormalizedFinding:
    """Normalize a SafetyAlert database entity into a normalized finding."""
    a_id = alert.alert_id or alert.id
    sev_raw = alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity)
    status_raw = alert.status.value if hasattr(alert.status, "value") else str(alert.status)
    ts = alert.created_at.isoformat() if alert.created_at else datetime.utcnow().isoformat()
    esc = alert.escalation_level.value if hasattr(alert.escalation_level, "value") else str(alert.escalation_level)

    rec = getattr(alert, "recommendation", None) or getattr(alert, "recommended_action", None)
    res_by = getattr(alert, "resolved_by", None) or getattr(alert, "mitigated_by", None)

    return NormalizedFinding(
        source_agent="safety",
        finding_type="SAFETY_ALERT",
        finding_id=a_id,
        severity=sev_raw.upper() if sev_raw else "MEDIUM",
        risk_level=sev_raw.upper() if sev_raw else "MEDIUM",
        status=status_raw.upper() if status_raw else "OPEN",
        description=f"{alert.title}: {alert.description}" if alert.description else alert.title,
        timestamp=ts,
        recommendation=rec,
        metadata={
            "escalation_level": esc,
            "acknowledged_by": alert.acknowledged_by,
            "resolved_by": res_by,
        },
    )


def normalize_compliance_finding(finding: Any) -> NormalizedFinding:
    """Normalize a ComplianceFinding database entity or dictionary from ComplianceAgent."""
    if isinstance(finding, dict):
        f_id = str(finding.get("finding_id") or finding.get("id") or "CMP-GEN")
        f_type = str(finding.get("violation_type") or "REGULATORY_NON_COMPLIANCE")
        sev_raw = str(finding.get("severity") or "MEDIUM").upper()
        status_val = str(finding.get("status") or "OPEN").upper()
        desc = str(finding.get("description") or "Regulatory compliance non-conformance")
        ts = str(finding.get("created_at") or datetime.utcnow().isoformat())
        rec = finding.get("recommendation")
        meta = {
            "standard_ref": finding.get("standard_ref"),
            "evidence": finding.get("evidence"),
            "rule_id": finding.get("rule_id"),
        }
    else:
        f_id = finding.finding_id or finding.id
        f_type = finding.violation_type or "REGULATORY_NON_COMPLIANCE"
        sev_raw = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        sev_raw = sev_raw.upper() if sev_raw else "MEDIUM"
        status_raw = finding.status.value if hasattr(finding.status, "value") else str(finding.status)
        status_val = status_raw.upper() if status_raw else "OPEN"
        desc = finding.description or "Compliance regulation standard breach"
        ts = finding.created_at.isoformat() if finding.created_at else datetime.utcnow().isoformat()
        rec = finding.recommendation
        meta = {
            "standard_ref": finding.standard_ref,
            "evidence": finding.evidence,
            "rule_id": finding.rule_id,
            "worker_id": finding.worker_id,
            "inspection_requirement_id": finding.inspection_requirement_id,
        }

    return NormalizedFinding(
        source_agent="compliance",
        finding_type=f"COMPLIANCE_{f_type.upper().replace(' ', '_')}",
        finding_id=f_id,
        severity=sev_raw,
        risk_level=sev_raw,
        status=status_val,
        description=desc,
        timestamp=ts,
        recommendation=rec,
        metadata=meta,
    )


def normalize_insurance_claim(claim: Any) -> NormalizedFinding:
    """Normalize an InsuranceClaimAssessment database entity or dictionary from InsuranceAgent."""
    if isinstance(claim, dict):
        c_id = str(claim.get("claim_assessment_id") or claim.get("id") or "CLM-GEN")
        c_risk = str(claim.get("claim_risk_level") or "MODERATE").upper()
        sev_map = {"SEVERE": "CRITICAL", "HIGH": "HIGH", "MODERATE": "MEDIUM", "LOW": "LOW"}
        sev_val = sev_map.get(c_risk, "MEDIUM")
        status_val = str(claim.get("status") or "UNDER_REVIEW").upper()
        desc = f"{claim.get('incident_title', 'Incident')} (Ref: {claim.get('incident_ref', 'N/A')})"
        ts = str(claim.get("created_at") or datetime.utcnow().isoformat())
        prob = claim.get("claim_probability_pct", 50.0)
        comp = claim.get("documentation_completeness_pct", 60.0)
        rec = f"Review missing claim evidence (completeness: {comp}%). Probability of insurer payout claim: {prob}%."
        meta = {
            "incident_ref": claim.get("incident_ref"),
            "claim_probability_pct": prob,
            "documentation_completeness_pct": comp,
            "potential_claim_indicators": claim.get("potential_claim_indicators"),
        }
    else:
        c_id = claim.claim_assessment_id or claim.id
        c_risk_raw = claim.claim_risk_level.value if hasattr(claim.claim_risk_level, "value") else str(claim.claim_risk_level)
        c_risk = c_risk_raw.upper() if c_risk_raw else "MODERATE"
        sev_map = {"SEVERE": "CRITICAL", "HIGH": "HIGH", "MODERATE": "MEDIUM", "LOW": "LOW"}
        sev_val = sev_map.get(c_risk, "MEDIUM")
        status_val = (claim.status or "UNDER_REVIEW").upper()
        desc = f"{claim.incident_title} (Ref: {claim.incident_ref})"
        ts = claim.created_at.isoformat() if claim.created_at else datetime.utcnow().isoformat()
        prob = claim.claim_probability_pct or 0.0
        comp = claim.documentation_completeness_pct or 0.0
        rec = f"Address missing claim records (dossier completeness: {comp}%). Incurred claim probability: {prob}%."
        meta = {
            "incident_ref": claim.incident_ref,
            "claim_probability_pct": prob,
            "documentation_completeness_pct": comp,
            "potential_claim_indicators": claim.potential_claim_indicators,
        }

    return NormalizedFinding(
        source_agent="insurance",
        finding_type="INSURANCE_CLAIM_EXPOSURE",
        finding_id=c_id,
        severity=sev_val,
        risk_level=c_risk,
        status=status_val,
        description=desc,
        timestamp=ts,
        recommendation=rec,
        metadata=meta,
    )
