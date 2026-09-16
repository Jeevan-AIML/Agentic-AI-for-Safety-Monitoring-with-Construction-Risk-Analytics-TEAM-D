"""
Safety Agent — Milestone 2 Phase 2.1
====================================
Specialized Worker Safety Compliance and Behavioral Safety Intelligence Engine.

Architecture:
    SafetyAgent (BaseAgent)
         ↓
    BaseSafetyAnalyzer (Interface)
         ↓
    RuleBasedSafetyAnalyzer (Phase 2.1 Deterministic Engine)
      [Future: CVSafetyAnalyzer, MultimodalSafetyAnalyzer, LLMSafetyAnalyzer, IoTSafetyAnalyzer]

Detection Source: RULE_ENGINE (Deterministic, auditable, explainable)
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid

from app.models.models import (
    Worker, Site, Activity, Equipment, Hazard, RiskScore, Notification,
    SafetyFinding, SafetyAnalysis,
    WorkerRole, SafetyTrainingStatus, PPEStatus, EquipmentStatus,
    ActivityType, RiskCategory, NotificationCategory,
    SafetyFindingStatus, SafetyFindingType
)


# ── PPE Foundation ──────────────────────────────────────────────────────────

STANDARD_PPE_ITEMS = [
    "Helmet",
    "Safety Vest",
    "Gloves",
    "Safety Shoes",
    "Eye Protection",
    "Hearing Protection",
    "Safety Harness",
    "Respiratory Protection",
]

# Mapping of high-risk activities to mandatory PPE requirements
ACTIVITY_REQUIRED_PPE: Dict[str, List[str]] = {
    "welding": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Eye Protection", "Respiratory Protection"],
    "electrical_work": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Eye Protection"],
    "excavation": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
    "scaffolding": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Safety Harness"],
    "demolition": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Eye Protection", "Hearing Protection", "Respiratory Protection"],
    "concrete_work": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes", "Eye Protection"],
    "material_handling": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
    "general_construction": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
}


# ── Abstract Base Safety Analyzer ───────────────────────────────────────────

class BaseSafetyAnalyzer(ABC):
    """
    Abstract base interface for safety analyzers.
    Ensures extensibility for future Computer Vision, Multimodal AI,
    or LLM reasoning analyzers without altering agent orchestrator or UI layers.
    """

    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze worker and site safety context.
        Returns safety score, safety level, findings, and metrics.
        """
        pass


# ── Rule-Based Safety Analyzer ──────────────────────────────────────────────

class RuleBasedSafetyAnalyzer(BaseSafetyAnalyzer):
    """
    Deterministic rule-based worker safety compliance and hazard detection engine.
    Executes rules 1 through 6 against real site and worker operational data.
    """

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        site_id = context.get("site_id", "")
        site_name = context.get("site_name", "Construction Site")
        site_risk_score = float(context.get("site_risk_score", 0.0))
        site_risk_category = context.get("site_risk_category", RiskCategory.LOW)
        if isinstance(site_risk_category, str):
            try:
                site_risk_category = RiskCategory(site_risk_category.lower())
            except ValueError:
                site_risk_category = RiskCategory.LOW

        workers_data: List[Dict[str, Any]] = context.get("workers", [])
        activities_data: List[Dict[str, Any]] = context.get("activities", [])
        equipment_data: List[Dict[str, Any]] = context.get("equipment", [])
        hazards_data: List[Dict[str, Any]] = context.get("hazards", [])

        # Identify active hazardous activities on site
        active_activity_types = [
            (a.get("activity_type") if isinstance(a, dict) else getattr(a, "activity_type", None))
            for a in activities_data
        ]
        active_activity_names = [
            (t.value if hasattr(t, "value") else str(t)).lower()
            for t in active_activity_types if t
        ]

        # Equipment operator assignments
        equipment_operators = {}
        for eq in equipment_data:
            op_name = eq.get("operator_name") if isinstance(eq, dict) else getattr(eq, "operator_name", None)
            if op_name:
                equipment_operators[op_name.strip().lower()] = eq

        # Critical site conditions
        has_critical_hazards = any(
            (h.get("risk_category") in [RiskCategory.CRITICAL, "critical"] if isinstance(h, dict)
             else getattr(h, "risk_category", None) == RiskCategory.CRITICAL)
            for h in hazards_data
        )
        is_high_risk_site = site_risk_score >= 75.0 or site_risk_category in [RiskCategory.CRITICAL, "critical"] or has_critical_hazards

        detected_findings: List[Dict[str, Any]] = []
        rule_hits: Dict[str, int] = {
            "RULE_1_PPE_VIOLATION": 0,
            "RULE_2_EXPIRED_TRAINING": 0,
            "RULE_3_MISSING_TRAINING": 0,
            "RULE_4_UNSAFE_EQUIPMENT_OPERATION": 0,
            "RULE_5_HIGH_RISK_ACTIVITY": 0,
            "RULE_6_HIGH_RISK_ZONE_EXPOSURE": 0,
        }

        for w in workers_data:
            w_id = w.get("id", "")
            w_code = w.get("worker_id", "WRK")
            w_name = w.get("name", "Worker")
            w_role = w.get("role")
            w_role_val = w_role.value if hasattr(w_role, "value") else str(w_role or "").lower()

            training_status = w.get("safety_training")
            training_val = training_status.value if hasattr(training_status, "value") else str(training_status or "").lower()

            ppe_status = w.get("ppe_status")
            ppe_val = ppe_status.value if hasattr(ppe_status, "value") else str(ppe_status or "").lower()

            # Optional detailed PPE breakdown support
            worker_ppe_items = w.get("ppe_items")  # List of items worn if available

            # ── RULE 1: PPE VIOLATION ───────────────────────────────────────
            # If worker PPE is incomplete/non-compliant
            is_ppe_deficient = ppe_val in [PPEStatus.NON_COMPLIANT.value, PPEStatus.PARTIAL.value, "non_compliant", "partial"]
            if is_ppe_deficient:
                rule_hits["RULE_1_PPE_VIOLATION"] += 1
                # Severity is HIGH if active construction/hazardous work is present, else MEDIUM
                sev = RiskCategory.HIGH if (active_activity_names or is_high_risk_site) else RiskCategory.MEDIUM
                evidence = (
                    f"Worker {w_name} ({w_code}, {w_role_val}) recorded with PPE status '{ppe_val.upper()}' "
                    f"while deployed at active construction site '{site_name}'."
                )
                if worker_ppe_items is not None:
                    missing_ppe = [item for item in STANDARD_PPE_ITEMS[:4] if item not in worker_ppe_items]
                    if missing_ppe:
                        evidence += f" Missing critical items: {', '.join(missing_ppe)}."

                detected_findings.append({
                    "worker_id": w_id,
                    "worker_name": w_name,
                    "worker_code": w_code,
                    "finding_type": SafetyFindingType.PPE_VIOLATION,
                    "description": f"PPE compliance violation for {w_name} ({w_role_val})",
                    "evidence": evidence,
                    "severity": sev,
                    "status": SafetyFindingStatus.OPEN,
                    "recommendation": "Stop worker entry into the active work zone until the required PPE (hard hat, high-vis vest, safety boots, and task-specific gear) is correctly worn and verified by a supervisor.",
                    "detection_source": "RULE_ENGINE",
                })

            # ── RULE 2: EXPIRED TRAINING ────────────────────────────────────
            # If worker training is expired
            if training_val in [SafetyTrainingStatus.EXPIRED.value, "expired"]:
                rule_hits["RULE_2_EXPIRED_TRAINING"] += 1
                # High severity if specialized operator/technician or hazardous active site
                is_specialized = w_role_val in ["operator", "welder", "electrician", "technician"]
                sev = RiskCategory.HIGH if (is_specialized or is_high_risk_site) else RiskCategory.MEDIUM
                detected_findings.append({
                    "worker_id": w_id,
                    "worker_name": w_name,
                    "worker_code": w_code,
                    "finding_type": SafetyFindingType.EXPIRED_TRAINING,
                    "description": f"Safety training certification expired for {w_name}",
                    "evidence": (
                        f"Worker {w_name} ({w_code}, role: {w_role_val}) holds EXPIRED safety training. "
                        f"Worker is not certified to perform hazardous site operations."
                    ),
                    "severity": sev,
                    "status": SafetyFindingStatus.OPEN,
                    "recommendation": "Restrict assignment to the relevant activity until the required safety training is renewed and re-certified.",
                    "detection_source": "RULE_ENGINE",
                })

            # ── RULE 3: MISSING TRAINING FOR SPECIALIZED ACTIVITY ───────────
            # If worker lacks required training for assigned activity
            is_training_missing = training_val in [
                SafetyTrainingStatus.NOT_STARTED.value,
                SafetyTrainingStatus.IN_PROGRESS.value,
                "not_started",
                "in_progress"
            ]
            has_specialized_hazards = any(act in active_activity_names for act in ["welding", "electrical_work", "excavation", "scaffolding", "demolition"])
            if is_training_missing and (has_specialized_hazards or w_role_val in ["welder", "electrician", "operator"]):
                rule_hits["RULE_3_MISSING_TRAINING"] += 1
                detected_findings.append({
                    "worker_id": w_id,
                    "worker_name": w_name,
                    "worker_code": w_code,
                    "finding_type": SafetyFindingType.MISSING_TRAINING,
                    "description": f"Missing mandatory safety training for specialized role ({w_name})",
                    "evidence": (
                        f"Worker {w_name} ({w_code}) is deployed in specialized role '{w_role_val}' "
                        f"with unverified safety training (status: '{training_val.upper()}')."
                    ),
                    "severity": RiskCategory.HIGH,
                    "status": SafetyFindingStatus.OPEN,
                    "recommendation": "Reassign worker away from high-risk tasks until mandatory role-specific safety training is fully completed and certified.",
                    "detection_source": "RULE_ENGINE",
                })

            # ── RULE 4: UNSAFE EQUIPMENT OPERATION ──────────────────────────
            # If worker is assigned to equipment without valid authorization/training
            assigned_eq = equipment_operators.get(w_name.strip().lower())
            if assigned_eq or w_role_val == "operator":
                eq_name = assigned_eq.get("name", "Heavy Equipment") if assigned_eq else "Heavy Machinery"
                eq_status = assigned_eq.get("status", "operational") if assigned_eq else "operational"
                eq_status_val = eq_status.value if hasattr(eq_status, "value") else str(eq_status).lower()

                training_invalid = training_val in [
                    SafetyTrainingStatus.EXPIRED.value,
                    SafetyTrainingStatus.NOT_STARTED.value,
                    SafetyTrainingStatus.IN_PROGRESS.value,
                    "expired", "not_started", "in_progress"
                ]

                # If operator training is invalid or machine inspection is due
                if training_invalid or eq_status_val in ["inspection_due", "out_of_service"]:
                    rule_hits["RULE_4_UNSAFE_EQUIPMENT_OPERATION"] += 1
                    evidence_parts = []
                    if training_invalid:
                        evidence_parts.append(f"Operator training is invalid ({training_val.upper()})")
                    if eq_status_val in ["inspection_due", "out_of_service"]:
                        evidence_parts.append(f"Equipment status is {eq_status_val.upper()}")

                    detected_findings.append({
                        "worker_id": w_id,
                        "worker_name": w_name,
                        "worker_code": w_code,
                        "finding_type": SafetyFindingType.UNSAFE_EQUIPMENT_OPERATION,
                        "description": f"Untrained or uninspected equipment operation: {eq_name}",
                        "evidence": f"Worker {w_name} ({w_code}) assigned to operate {eq_name}. {', '.join(evidence_parts)}.",
                        "severity": RiskCategory.CRITICAL,
                        "status": SafetyFindingStatus.OPEN,
                        "recommendation": "Stop equipment operation and assign an authorized trained operator. Lock out uninspected machinery until inspection is cleared.",
                        "detection_source": "RULE_ENGINE",
                    })

            # ── RULE 5: HIGH-RISK ACTIVITY WITHOUT REQUIRED CONTROLS ────────
            # If worker is assigned to high-risk activity without required safety controls
            high_risk_activities = ["excavation", "welding", "scaffolding", "electrical_work", "demolition"]
            active_high_risks = [a for a in active_activity_names if any(hr in a for hr in high_risk_activities)]
            if active_high_risks and is_ppe_deficient:
                rule_hits["RULE_5_HIGH_RISK_ACTIVITY"] += 1
                # If both PPE is non-compliant and training is missing, this is CRITICAL
                is_crit = is_ppe_deficient and is_training_missing
                sev = RiskCategory.CRITICAL if is_crit else RiskCategory.HIGH
                detected_findings.append({
                    "worker_id": w_id,
                    "worker_name": w_name,
                    "worker_code": w_code,
                    "finding_type": SafetyFindingType.HIGH_RISK_ACTIVITY,
                    "description": f"High-risk activity violation during {active_high_risks[0].upper()}",
                    "evidence": (
                        f"Worker {w_name} is active in high-risk activity zone ({active_high_risks[0]}) "
                        f"with inadequate safety controls (PPE: {ppe_val.upper()}, Training: {training_val.upper()})."
                    ),
                    "severity": sev,
                    "status": SafetyFindingStatus.OPEN,
                    "recommendation": "Suspend worker participation in high-risk operations immediately. Verify JHA, install physical barriers, and ensure compliant PPE and certified training.",
                    "detection_source": "RULE_ENGINE",
                })

            # ── RULE 6: HIGH-RISK ZONE EXPOSURE ─────────────────────────────
            # If worker is assigned to a high-risk site/zone while safety requirements are incomplete
            if is_high_risk_site and (is_ppe_deficient or training_val in [SafetyTrainingStatus.EXPIRED.value, "expired"]):
                rule_hits["RULE_6_HIGH_RISK_ZONE_EXPOSURE"] += 1
                sev = RiskCategory.CRITICAL if (site_risk_category == RiskCategory.CRITICAL or site_risk_score >= 80) else RiskCategory.HIGH
                detected_findings.append({
                    "worker_id": w_id,
                    "worker_name": w_name,
                    "worker_code": w_code,
                    "finding_type": SafetyFindingType.HIGH_RISK_ZONE_EXPOSURE,
                    "description": f"Worker exposure to elevated risk site conditions ({site_name})",
                    "evidence": (
                        f"Worker {w_name} ({w_code}) is present in elevated risk environment "
                        f"('{site_name}', Risk Score: {site_risk_score}/100, Level: {site_risk_category.value.upper()}) "
                        f"with deficient safety safeguards (PPE: {ppe_val}, Training: {training_val})."
                    ),
                    "severity": sev,
                    "status": SafetyFindingStatus.OPEN,
                    "recommendation": "Restrict access until required safety controls are verified. Evacuate non-compliant personnel from elevated danger zones.",
                    "detection_source": "RULE_ENGINE",
                })

        # Calculate overall safety score (100 is best, deductions for violations)
        crit_count = sum(1 for f in detected_findings if f["severity"] == RiskCategory.CRITICAL)
        high_count = sum(1 for f in detected_findings if f["severity"] == RiskCategory.HIGH)
        med_count = sum(1 for f in detected_findings if f["severity"] == RiskCategory.MEDIUM)
        low_count = sum(1 for f in detected_findings if f["severity"] == RiskCategory.LOW)

        deductions = (crit_count * 25.0) + (high_count * 15.0) + (med_count * 8.0) + (low_count * 3.0)
        overall_safety_score = max(0.0, min(100.0, round(100.0 - deductions, 1)))

        # Categorize overall safety level
        if crit_count > 0 or overall_safety_score < 40.0:
            safety_level = RiskCategory.CRITICAL
        elif high_count > 0 or overall_safety_score < 60.0:
            safety_level = RiskCategory.HIGH
        elif med_count > 0 or overall_safety_score < 80.0:
            safety_level = RiskCategory.MEDIUM
        else:
            safety_level = RiskCategory.LOW

        summary_data = {
            "site_id": site_id,
            "site_name": site_name,
            "workers_analyzed": len(workers_data),
            "violation_count": len(detected_findings),
            "critical_count": crit_count,
            "high_count": high_count,
            "medium_count": med_count,
            "low_count": low_count,
            "overall_safety_score": overall_safety_score,
            "safety_level": safety_level,
            "rule_hits": rule_hits,
            "detection_source": "RULE_ENGINE",
        }

        return {
            "overall_safety_score": overall_safety_score,
            "safety_level": safety_level,
            "workers_analyzed": len(workers_data),
            "violation_count": len(detected_findings),
            "critical_count": crit_count,
            "high_count": high_count,
            "medium_count": med_count,
            "low_count": low_count,
            "findings": detected_findings,
            "summary": summary_data,
            "rule_hits": rule_hits,
            "detection_source": "RULE_ENGINE",
        }


# ── 5 Deterministic Demo Scenarios ──────────────────────────────────────────

SAFETY_DEMO_SCENARIOS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Scenario 1 — Compliant Worker",
        "description": "Worker with valid safety training certification and full PPE compliance assigned to routine general construction. No high-risk exposure.",
        "input": {
            "workers": [{
                "id": "demo-wrk-1",
                "worker_id": "WRK-DEMO-01",
                "name": "Kavita Sharma",
                "role": WorkerRole.GENERAL_WORKER,
                "safety_training": SafetyTrainingStatus.CERTIFIED,
                "ppe_status": PPEStatus.COMPLIANT,
                "ppe_items": ["Helmet", "Safety Vest", "Gloves", "Safety Shoes"],
            }],
            "activities": [{"activity_type": ActivityType.GENERAL_CONSTRUCTION}],
            "equipment": [],
            "site_risk_score": 25.0,
            "site_risk_category": RiskCategory.LOW,
        },
        "expected_level": RiskCategory.LOW,
        "expected_violations": 0,
    },
    2: {
        "name": "Scenario 2 — PPE Violation",
        "description": "Worker on active construction site with incomplete/non-compliant PPE. Triggers Rule 1 (PPE Violation).",
        "input": {
            "workers": [{
                "id": "demo-wrk-2",
                "worker_id": "WRK-DEMO-02",
                "name": "Ravi Kumar",
                "role": WorkerRole.MASON,
                "safety_training": SafetyTrainingStatus.CERTIFIED,
                "ppe_status": PPEStatus.NON_COMPLIANT,
            }],
            "activities": [{"activity_type": ActivityType.CONCRETE_WORK}],
            "equipment": [],
            "site_risk_score": 45.0,
            "site_risk_category": RiskCategory.MEDIUM,
        },
        "expected_level": RiskCategory.HIGH,
        "expected_violations": 1,
    },
    3: {
        "name": "Scenario 3 — Expired Training",
        "description": "Worker with expired safety training assigned to operational activity. Triggers Rule 2 (Expired Training).",
        "input": {
            "workers": [{
                "id": "demo-wrk-3",
                "worker_id": "WRK-DEMO-03",
                "name": "Deepak Verma",
                "role": WorkerRole.ELECTRICIAN,
                "safety_training": SafetyTrainingStatus.EXPIRED,
                "ppe_status": PPEStatus.COMPLIANT,
            }],
            "activities": [{"activity_type": ActivityType.ELECTRICAL_WORK}],
            "equipment": [],
            "site_risk_score": 40.0,
            "site_risk_category": RiskCategory.MEDIUM,
        },
        "expected_level": RiskCategory.HIGH,
        "expected_violations": 1,
    },
    4: {
        "name": "Scenario 4 — Unsafe Equipment Operation",
        "description": "Worker operating heavy crane or excavator without valid operator training credentials. Triggers Rule 4 (CRITICAL Unsafe Equipment Operation).",
        "input": {
            "workers": [{
                "id": "demo-wrk-4",
                "worker_id": "WRK-DEMO-04",
                "name": "Sunil Patil",
                "role": WorkerRole.OPERATOR,
                "safety_training": SafetyTrainingStatus.EXPIRED,
                "ppe_status": PPEStatus.COMPLIANT,
            }],
            "activities": [{"activity_type": ActivityType.MATERIAL_HANDLING}],
            "equipment": [{
                "name": "Tower Crane TC-01",
                "equipment_type": "Tower Crane",
                "operator_name": "Sunil Patil",
                "status": "operational",
            }],
            "site_risk_score": 60.0,
            "site_risk_category": RiskCategory.MEDIUM,
        },
        "expected_level": RiskCategory.CRITICAL,
        "expected_violations": 2,  # Expired Training + Unsafe Equipment Operation
    },
    5: {
        "name": "Scenario 5 — High-Risk Activity + PPE Violation",
        "description": "Worker engaged in high-risk welding or excavation with non-compliant PPE. Triggers Rule 1 and Rule 5 (High-Risk Activity).",
        "input": {
            "workers": [{
                "id": "demo-wrk-5",
                "worker_id": "WRK-DEMO-05",
                "name": "Arun Patel",
                "role": WorkerRole.WELDER,
                "safety_training": SafetyTrainingStatus.IN_PROGRESS,
                "ppe_status": PPEStatus.NON_COMPLIANT,
            }],
            "activities": [{"activity_type": ActivityType.WELDING}],
            "equipment": [],
            "site_risk_score": 65.0,
            "site_risk_category": RiskCategory.HIGH,
        },
        "expected_level": RiskCategory.CRITICAL,
        "expected_violations": 3,  # PPE Violation + Missing Training + High-Risk Activity Violation
    },
}


# ── Safety Agent Implementation ─────────────────────────────────────────────

class SafetyAgent:
    """
    Safety Agent (Phase 2.1)
    Coordinates worker safety compliance monitoring, PPE checking,
    unsafe behavior detection, persistence of SafetyFinding and SafetyAnalysis records,
    and automated dispatch of HIGH/CRITICAL safety notifications.
    """

    def __init__(self, analyzer: Optional[BaseSafetyAnalyzer] = None):
        self.agent_id = "safety_agent_v1"
        self.name = "Safety Agent"
        self.version = "1.0.0-phase2.1"
        self.is_active = True
        self.last_run: Optional[datetime] = None
        self.analyzer: BaseSafetyAnalyzer = analyzer or RuleBasedSafetyAnalyzer()

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis on provided safety context."""
        self.last_run = datetime.now(timezone.utc).replace(tzinfo=None)
        return self.analyzer.analyze(context)

    async def health_check(self) -> bool:
        return self.is_active

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "is_active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "status": "active" if self.is_active else "inactive",
            "analyzer": self.analyzer.__class__.__name__,
            "detection_source": "RULE_ENGINE",
            "rules_count": 6,
        }

    def analyze_and_persist(
        self,
        db,
        site_id: str,
        worker_id: Optional[str] = None,
        custom_input: Optional[Dict[str, Any]] = None,
        source_label: str = "safety_agent"
    ) -> Dict[str, Any]:
        """
        Execute safety analysis for a site (or single worker), persist SafetyAnalysis,
        save new SafetyFinding entities, and broadcast Notifications for HIGH and CRITICAL findings.
        """
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site '{site_id}' not found")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.last_run = now

        # Compile real database context
        context: Dict[str, Any] = {
            "site_id": site.id,
            "site_name": site.name,
            "site_risk_score": site.current_risk_score or 0.0,
            "site_risk_category": site.risk_category or RiskCategory.LOW,
        }

        if custom_input:
            context.update(custom_input)
            context["site_id"] = site.id
            context["site_name"] = site.name
        else:
            # Aggregate real database records
            worker_query = db.query(Worker).filter(Worker.site_id == site.id, Worker.is_active == True)
            if worker_id:
                worker_query = worker_query.filter(Worker.id == worker_id)
            workers = worker_query.all()

            activities = db.query(Activity).filter(Activity.site_id == site.id).order_by(Activity.date.desc()).limit(10).all()
            equipment = db.query(Equipment).filter(Equipment.site_id == site.id).all()
            hazards = db.query(Hazard).filter(
                Hazard.site_id == site.id,
                Hazard.status.in_([SafetyFindingStatus.OPEN, "open", "under_review"])
            ).all()

            context["workers"] = [
                {
                    "id": w.id,
                    "worker_id": w.worker_id,
                    "name": w.name,
                    "role": w.role,
                    "department": w.department,
                    "safety_training": w.safety_training,
                    "ppe_status": w.ppe_status,
                }
                for w in workers
            ]
            context["activities"] = [
                {
                    "id": a.id,
                    "activity_type": a.activity_type,
                    "description": a.description,
                    "workers_involved": a.workers_involved,
                }
                for a in activities
            ]
            context["equipment"] = [
                {
                    "id": e.id,
                    "name": e.name,
                    "equipment_type": e.equipment_type,
                    "operator_name": e.operator_name,
                    "status": e.status,
                }
                for e in equipment
            ]
            context["hazards"] = [
                {
                    "id": h.id,
                    "hazard_type": h.hazard_type,
                    "severity": h.severity,
                    "risk_category": h.risk_category,
                    "status": h.status,
                }
                for h in hazards
            ]

        # Execute analysis
        analysis_output = self.analyzer.analyze(context)

        # Count total existing analyses for human-readable code
        analysis_count = db.query(SafetyAnalysis).count()
        analysis_code = f"SAF-ANL-{analysis_count + 1:04d}"

        # Persist SafetyAnalysis record
        analysis_entity = SafetyAnalysis(
            id=str(uuid.uuid4()),
            analysis_id=analysis_code,
            site_id=site.id,
            worker_id=worker_id,
            overall_safety_score=analysis_output["overall_safety_score"],
            safety_level=analysis_output["safety_level"],
            workers_analyzed=analysis_output["workers_analyzed"],
            violation_count=analysis_output["violation_count"],
            high_count=analysis_output["high_count"],
            critical_count=analysis_output["critical_count"],
            detection_source="RULE_ENGINE",
            summary=analysis_output["summary"],
            created_at=now,
        )
        db.add(analysis_entity)

        # Persist SafetyFinding records
        base_finding_count = db.query(SafetyFinding).count()
        created_findings: List[SafetyFinding] = []

        for idx, f_data in enumerate(analysis_output["findings"]):
            finding_code = f"SAF-FND-{base_finding_count + idx + 1:04d}"
            finding_entity = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=finding_code,
                site_id=site.id,
                worker_id=f_data.get("worker_id"),
                analysis_id=analysis_entity.id,
                finding_type=f_data["finding_type"],
                description=f_data["description"],
                evidence=f_data.get("evidence"),
                severity=f_data["severity"],
                status=SafetyFindingStatus.OPEN,
                recommendation=f_data.get("recommendation"),
                detection_source="RULE_ENGINE",
                created_at=now,
                updated_at=now,
            )
            db.add(finding_entity)
            created_findings.append(finding_entity)

            # Generate automated Notification for High or Critical safety findings with deduplication
            if f_data["severity"] in [RiskCategory.HIGH, RiskCategory.CRITICAL]:
                sev_level = "critical" if f_data["severity"] == RiskCategory.CRITICAL else "warning"
                notif_title = f"{'CRITICAL' if sev_level == 'critical' else 'HIGH'} Safety Alert: {f_data['description'][:50]}"

                existing_notif = db.query(Notification).filter(
                    Notification.category == NotificationCategory.SAFETY,
                    Notification.title == notif_title,
                    Notification.link == f"/sites/{site.id}",
                    Notification.is_read == False
                ).first()

                if not existing_notif:
                    notif = Notification(
                        id=str(uuid.uuid4()),
                        user_id=None,  # Broadcast to safety officers and site managers
                        category=NotificationCategory.SAFETY,
                        title=notif_title,
                        message=(
                            f"Safety Agent detected {f_data['severity'].value.upper()} violation at {site.name}: "
                            f"{f_data['description']}. Recommendation: {f_data['recommendation']}"
                        ),
                        severity=sev_level,
                        is_read=False,
                        link=f"/sites/{site.id}",
                        created_at=now,
                    )
                    db.add(notif)

        db.commit()
        db.refresh(analysis_entity)

        # Attach generated IDs to returned results
        for idx, f in enumerate(analysis_output["findings"]):
            if idx < len(created_findings):
                f["id"] = created_findings[idx].id
                f["finding_id"] = created_findings[idx].finding_id
                f["analysis_id"] = analysis_entity.id
                f["site_id"] = site.id
                f["created_at"] = created_findings[idx].created_at
                f["updated_at"] = created_findings[idx].updated_at

        analysis_output["id"] = analysis_entity.id
        analysis_output["analysis_id"] = analysis_entity.analysis_id
        analysis_output["site_id"] = site.id
        analysis_output["site_name"] = site.name
        analysis_output["timestamp"] = now.isoformat()

        return analysis_output


# Global singleton instance
safety_agent = SafetyAgent()
