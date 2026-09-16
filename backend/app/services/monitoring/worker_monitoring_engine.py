"""
Worker Safety Monitoring Engine — Milestone 2 Phase 2.3
=======================================================
Deterministic rule-based worker safety monitoring engine.
Evaluates worker activity, zone exposure, dwell time thresholds,
hazard proximity, equipment interaction, and PPE compliance.

Detection Source: WORKER_MONITORING_ENGINE
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.models.models import (
    Worker, Site, Activity, Equipment, Hazard,
    RiskCategory, WorkerSafetyStatus, SafetyFindingType,
    SafetyTrainingStatus, PPEStatus
)
from app.core.config import settings


HIGH_RISK_ACTIVITIES = {
    "welding", "excavation", "scaffolding", "demolition",
    "electrical_work", "material_handling"
}

ACTIVITY_MANDATORY_PPE: Dict[str, List[str]] = {
    "welding": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Eye Protection"],
    "excavation": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
    "scaffolding": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Safety Harness"],
    "demolition": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Eye Protection"],
    "electrical_work": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Eye Protection"],
    "material_handling": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
    "concrete_work": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
    "general_construction": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
}


class WorkerMonitoringFinding:
    def __init__(
        self,
        rule_name: str,
        finding_type: str,
        severity: RiskCategory,
        description: str,
        evidence: str,
        recommendation: Optional[str] = None
    ):
        self.rule_name = rule_name
        self.finding_type = finding_type
        self.severity = severity
        self.description = description
        self.evidence = evidence
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


class WorkerMonitoringEngine:
    """
    Deterministic rule-based worker safety monitoring engine.
    Applies Rules 1 through 8 to calculate real-time safety status.
    """

    def __init__(self):
        self.detection_source = "WORKER_MONITORING_ENGINE"
        self.time_threshold_minutes = settings.MONITORING_TIME_IN_ZONE_THRESHOLD_MINUTES
        self.max_zone_workers = settings.MONITORING_MAX_ZONE_WORKERS

    def evaluate(self, worker_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate worker monitoring rules.
        """
        worker_id = worker_info.get("id", "")
        worker_name = worker_info.get("name", "Unknown Worker")
        worker_role = worker_info.get("role", "worker")
        training_status = worker_info.get("safety_training", SafetyTrainingStatus.NOT_STARTED)
        ppe_status = worker_info.get("ppe_status", PPEStatus.NON_COMPLIANT)

        # Normalize string values for enums
        ppe_str = getattr(ppe_status, "value", str(ppe_status)).lower()
        training_str = getattr(training_status, "value", str(training_status)).lower()

        current_activity = str(context.get("current_activity") or "general_construction").lower()
        current_zone = str(context.get("current_zone") or "General Site Area")
        is_high_risk_zone = bool(context.get("is_high_risk_zone", False))
        time_in_zone = int(context.get("time_in_zone_minutes", 0))
        nearby_hazards = context.get("nearby_hazards", [])
        nearby_equipment = context.get("nearby_equipment", [])
        workers_in_zone_count = int(context.get("workers_in_zone_count", 1))
        ppe_items_worn = context.get("ppe_items_worn", None)
        is_simulation = bool(context.get("is_simulation", False))

        findings: List[WorkerMonitoringFinding] = []

        # ── Rule 1: Worker enters high-risk zone ───────────────────────────
        if is_high_risk_zone:
            # Check zone severity
            zone_lower = current_zone.lower()
            if any(k in zone_lower for k in ["excavation", "fall", "confined", "high voltage", "demolition"]):
                rule1_severity = RiskCategory.HIGH
            else:
                rule1_severity = RiskCategory.MEDIUM

            findings.append(WorkerMonitoringFinding(
                rule_name="Rule 1: High-Risk Zone Entry",
                finding_type=SafetyFindingType.HIGH_RISK_ZONE_EXPOSURE.value,
                severity=rule1_severity,
                description=f"Worker {worker_name} ({worker_id}) is operating within designated high-risk sector '{current_zone}'.",
                evidence=f"Zone: {current_zone} (High-Risk: True), Activity: {current_activity}, Role: {worker_role}",
                recommendation=f"Ensure worker holds verified permits for {current_zone} and maintain designated safety spotter oversight."
            ))

        # ── Rule 2: Worker remains in high-risk zone beyond threshold ─────
        if is_high_risk_zone and time_in_zone > self.time_threshold_minutes:
            findings.append(WorkerMonitoringFinding(
                rule_name="Rule 2: Time-in-Zone Threshold Exceeded",
                finding_type=SafetyFindingType.TIME_IN_ZONE_EXCEEDED.value,
                severity=RiskCategory.HIGH,
                description=f"Worker {worker_name} has exceeded maximum safe dwell time in '{current_zone}' ({time_in_zone} mins > {self.time_threshold_minutes} mins threshold).",
                evidence=f"Time in high-risk zone: {time_in_zone} minutes (Configured limit: {self.time_threshold_minutes} min). Risk of physical/environmental fatigue.",
                recommendation=f"Immediately mandate rotation of worker {worker_name} out of '{current_zone}' to prevent fatigue-induced incident."
            ))

        # ── Rule 3: Worker approaches active hazard ────────────────────────
        if nearby_hazards:
            hazard_desc = ", ".join(str(h) for h in nearby_hazards[:3])
            findings.append(WorkerMonitoringFinding(
                rule_name="Rule 3: Hazard Proximity Detection",
                finding_type=SafetyFindingType.HAZARD_PROXIMITY.value,
                severity=RiskCategory.HIGH,
                description=f"Worker {worker_name} is in hazardous proximity to {len(nearby_hazards)} active open hazard(s): {hazard_desc}.",
                evidence=f"Active nearby hazards detected: {hazard_desc}. Proximity requires active barricade or lockout.",
                recommendation=f"Establish physical exclusion perimeter around active hazards and enforce safety standoff distance."
            ))

        # ── Rule 4: Worker approaches operating equipment ──────────────────
        if nearby_equipment:
            eq_desc = ", ".join(str(e) for e in nearby_equipment[:3])
            is_operator = "operator" in str(worker_role).lower()
            if not is_operator:
                findings.append(WorkerMonitoringFinding(
                    rule_name="Rule 4: Operating Heavy Equipment Proximity",
                    finding_type=SafetyFindingType.EQUIPMENT_PROXIMITY.value,
                    severity=RiskCategory.CRITICAL,
                    description=f"Non-operator worker {worker_name} is within operating envelope of heavy machinery: {eq_desc}.",
                    evidence=f"Machinery operating nearby: {eq_desc}. Worker role: {worker_role} (Uncertified operator). High collision/crush risk.",
                    recommendation=f"Halt heavy machinery operations immediately and clear personnel to outside the 10m exclusion radius."
                ))

        # ── Rule 5: Worker performs activity without required PPE ─────────
        required_ppe = ACTIVITY_MANDATORY_PPE.get(current_activity, ["Helmet", "Safety Vest"])
        if ppe_str in ["non_compliant", "partial"]:
            is_critical = current_activity in HIGH_RISK_ACTIVITIES or ppe_str == "non_compliant"
            findings.append(WorkerMonitoringFinding(
                rule_name="Rule 5: Activity Without Required PPE",
                finding_type=SafetyFindingType.PPE_VIOLATION.value,
                severity=RiskCategory.CRITICAL if is_critical else RiskCategory.HIGH,
                description=f"Worker {worker_name} is performing '{current_activity}' with {ppe_str.upper()} PPE status.",
                evidence=f"Current activity '{current_activity}' requires: {', '.join(required_ppe)}. Recorded PPE status: {ppe_status}.",
                recommendation=f"Stop work immediately until worker {worker_name} is fully equipped with required PPE: {', '.join(required_ppe)}."
            ))

        # ── Rule 6: Worker performs activity without required training ────
        if current_activity in HIGH_RISK_ACTIVITIES and training_str not in ["certified", "compliant"]:
            findings.append(WorkerMonitoringFinding(
                rule_name="Rule 6: High-Risk Activity Without Training",
                finding_type=SafetyFindingType.MISSING_TRAINING.value,
                severity=RiskCategory.HIGH,
                description=f"Worker {worker_name} performing high-risk activity '{current_activity}' without valid safety certification ({training_str.upper()}).",
                evidence=f"High-risk activity: {current_activity}. Required: Certified training. Actual status: {training_status}.",
                recommendation=f"Reassign worker {worker_name} to non-hazardous tasks until mandatory certification for '{current_activity}' is completed."
            ))

        # ── Rule 7: Multiple workers enter restricted/high-risk area ──────
        if is_high_risk_zone and workers_in_zone_count > self.max_zone_workers:
            findings.append(WorkerMonitoringFinding(
                rule_name="Rule 7: High-Risk Zone Overcrowding",
                finding_type=SafetyFindingType.OVERCROWDED_ZONE.value,
                severity=RiskCategory.HIGH,
                description=f"Zone personnel density limit exceeded in '{current_zone}': {workers_in_zone_count} workers detected (Limit: {self.max_zone_workers}).",
                evidence=f"Workers in zone: {workers_in_zone_count} > Maximum allowable capacity: {self.max_zone_workers} in restricted area.",
                recommendation=f"Disperse non-essential personnel from '{current_zone}' to prevent crowd hazard and maintain clear egress paths."
            ))

        # ── Rule 8: Unsafe worker-equipment interaction ────────────────────
        if nearby_equipment and (
            context.get("unsafe_equipment_interaction")
            or (current_activity in HIGH_RISK_ACTIVITIES and ppe_str in ["non_compliant", "partial"])
        ):
            findings.append(WorkerMonitoringFinding(
                rule_name="Rule 8: Unsafe Worker-Equipment Interaction",
                finding_type=SafetyFindingType.UNSAFE_WORKER_EQUIPMENT_INTERACTION.value,
                severity=RiskCategory.CRITICAL,
                description=f"Critical conflict: Worker {worker_name} is engaged in '{current_activity}' with {ppe_str.upper()} PPE in direct convergence with active equipment ({', '.join(str(e) for e in nearby_equipment[:2])}).",
                evidence=f"Concurrent hazards: High-risk activity '{current_activity}' + Deficient PPE ({ppe_str}) + Active equipment proximity. Fatal hazard scenario.",
                recommendation=f"Immediate stop-work order. Separate personnel and mobile plant with physical safety barriers before resumption."
            ))

        # ── Determine Overall Worker Safety Status ────────────────────────
        has_critical = any(f.severity == RiskCategory.CRITICAL for f in findings)
        has_high = any(f.severity == RiskCategory.HIGH for f in findings)
        has_medium_or_low = any(f.severity in [RiskCategory.MEDIUM, RiskCategory.LOW] for f in findings)

        if has_critical:
            safety_status = WorkerSafetyStatus.CRITICAL
        elif has_high:
            safety_status = WorkerSafetyStatus.HIGH_RISK
        elif has_medium_or_low:
            safety_status = WorkerSafetyStatus.WARNING
        else:
            safety_status = WorkerSafetyStatus.SAFE

        # Compile recommendations
        recommendations = [f.recommendation for f in findings if f.recommendation]
        if not recommendations and safety_status == WorkerSafetyStatus.SAFE:
            recommendations.append("Worker safety parameters optimal. Continue standard PPE compliance and site monitoring.")

        return {
            "worker_id": worker_id,
            "worker_name": worker_name,
            "safety_status": safety_status,
            "current_activity": current_activity,
            "current_zone": current_zone,
            "time_in_zone_minutes": time_in_zone,
            "is_high_risk_zone": is_high_risk_zone,
            "ppe_status": str(ppe_status),
            "training_status": str(training_status),
            "workers_in_zone_count": workers_in_zone_count,
            "findings": [f.to_dict() for f in findings],
            "recommendations": recommendations,
            "detection_source": self.detection_source,
            "evaluated_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "is_simulation": is_simulation,
        }
