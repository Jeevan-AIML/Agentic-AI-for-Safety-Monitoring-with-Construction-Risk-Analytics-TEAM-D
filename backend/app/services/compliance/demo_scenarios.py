"""Deterministic Compliance Demo Scenarios for Milestone 3.

Pre-configured, reproducible scenarios demonstrating:
1. Fully compliant site (OSHA/IS/ISO aligned, high score)
2. PPE compliance violation (OSHA 1926.95 violation)
3. Overdue safety inspection (Weekly crane & trench inspection overdue)
4. Multiple regulatory violations (Critical trench + operator certification + fall arrest)

Every synthetic output is explicitly labeled 'DEMO / SIMULATION' with is_simulation=True.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.models.models import (
    PPEStatus, SafetyTrainingStatus, WorkerRole,
    InspectionRequirementStatus, RiskCategory
)

COMPLIANCE_DEMO_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "DEMO 1 — FULLY COMPLIANT SITE",
        "description": "Baseline compliant construction site meeting all OSHA 1926, IS 4081, and ISO 45001 standards. 100% PPE compliance, verified worker certifications, and up-to-date inspections.",
        "category": "BASELINE_AUDIT",
        "expected_status": "COMPLIANT",
        "expected_violations": 0,
        "narrative": "Comprehensive safety audit confirms full adherence. Workers possess valid training credentials, PPE is completely deployed, and all statutory inspection certificates are active.",
        "context": {
            "is_simulation": True,
            "workers": [
                {
                    "worker_id": "WRK-DEMO-101",
                    "name": "David Miller",
                    "role": "crane_operator",
                    "ppe_status": PPEStatus.COMPLIANT,
                    "safety_training_status": SafetyTrainingStatus.CERTIFIED,
                    "missing_gear": [],
                },
                {
                    "worker_id": "WRK-DEMO-102",
                    "name": "James Wilson",
                    "role": "ironworker",
                    "ppe_status": PPEStatus.COMPLIANT,
                    "safety_training_status": SafetyTrainingStatus.CERTIFIED,
                    "missing_gear": [],
                },
                {
                    "worker_id": "WRK-DEMO-103",
                    "name": "Carlos Gomez",
                    "role": "electrician",
                    "ppe_status": PPEStatus.COMPLIANT,
                    "safety_training_status": SafetyTrainingStatus.CERTIFIED,
                    "missing_gear": [],
                }
            ],
            "hazards": [],
            "inspections": [
                {
                    "id": "INSP-DEMO-01",
                    "title": "Tower Crane Weekly Structural Inspection",
                    "inspection_type": "Weekly Statutory",
                    "regulatory_reference": "ISO 45001:2018 Cl. 7.2",
                    "responsible_role": "safety_officer",
                    "due_date": datetime.utcnow() + timedelta(days=5),
                    "status": InspectionRequirementStatus.COMPLETED,
                    "is_overdue": False,
                },
                {
                    "id": "INSP-DEMO-02",
                    "title": "Excavation Pit Shoring Daily Sign-off",
                    "inspection_type": "Daily Pre-Entry",
                    "regulatory_reference": "OSHA 1926.651",
                    "responsible_role": "site_manager",
                    "due_date": datetime.utcnow() + timedelta(hours=12),
                    "status": InspectionRequirementStatus.COMPLETED,
                    "is_overdue": False,
                }
            ],
            "ppe_events": [
                {"is_compliant": True, "person_id": "P-101"},
                {"is_compliant": True, "person_id": "P-102"},
            ]
        }
    },
    {
        "id": 2,
        "name": "DEMO 2 — PPE COMPLIANCE VIOLATION",
        "description": "Personnel observed working at ground and scaffolding levels without mandatory eye protection and high-visibility safety vests, triggering an OSHA 1926.95 violation finding.",
        "category": "PPE_VIOLATION",
        "expected_status": "COMPLIANT",  # 90.0 score (100 - 10 for High = 90.0 >= 85)
        "expected_violations": 1,
        "narrative": "Automated vision and ground inspection verify worker active without required high-visibility garment and protective safety goggles adjacent to active transport lanes.",
        "context": {
            "is_simulation": True,
            "workers": [
                {
                    "worker_id": "WRK-DEMO-201",
                    "name": "Robert Taylor",
                    "role": "mason",
                    "ppe_status": PPEStatus.NON_COMPLIANT,
                    "safety_training_status": SafetyTrainingStatus.CERTIFIED,
                    "missing_gear": ["Safety Vest", "Eye Protection"],
                },
                {
                    "worker_id": "WRK-DEMO-202",
                    "name": "Sarah Jenkins",
                    "role": "laborer",
                    "ppe_status": PPEStatus.COMPLIANT,
                    "safety_training_status": SafetyTrainingStatus.CERTIFIED,
                    "missing_gear": [],
                }
            ],
            "hazards": [],
            "inspections": [
                {
                    "id": "INSP-DEMO-03",
                    "title": "Daily Site PPE & Housekeeping Audit",
                    "inspection_type": "Daily Audit",
                    "regulatory_reference": "OSHA 1926.95",
                    "responsible_role": "safety_officer",
                    "due_date": datetime.utcnow() + timedelta(days=2),
                    "status": InspectionRequirementStatus.SCHEDULED,
                    "is_overdue": False,
                }
            ],
            "ppe_events": [
                {"is_compliant": False, "person_id": "P-201", "missing_items": ["Safety Vest", "Eye Protection"]},
            ]
        }
    },
    {
        "id": 3,
        "name": "DEMO 3 — OVERDUE SAFETY INSPECTION",
        "description": "Mandatory periodic scaffolding and crane inspections have lapsed past their statutory due dates without authorized renewal, violating mandatory inspection tracking protocols.",
        "category": "INSPECTION_OVERDUE",
        "expected_status": "COMPLIANT",  # 90.0 score (100 - 10 for High = 90.0)
        "expected_violations": 1,
        "narrative": "Platform detects that the 7-day recurring Scaffolding Stability Sign-off has expired 3 days ago. Operations on uninspected framework trigger immediate compliance findings.",
        "context": {
            "is_simulation": True,
            "workers": [
                {
                    "worker_id": "WRK-DEMO-301",
                    "name": "Michael Chang",
                    "role": "scaffolder",
                    "ppe_status": PPEStatus.COMPLIANT,
                    "safety_training_status": SafetyTrainingStatus.CERTIFIED,
                    "missing_gear": [],
                }
            ],
            "hazards": [],
            "inspections": [
                {
                    "id": "INSP-DEMO-04",
                    "title": "Weekly Scaffolding Structural & Anchor Verification",
                    "inspection_type": "Weekly Statutory",
                    "regulatory_reference": "IS 3696 (Part 1): 1987 / OSHA 1926.451",
                    "responsible_role": "safety_officer",
                    "due_date": datetime.utcnow() - timedelta(days=3),
                    "status": InspectionRequirementStatus.OVERDUE,
                    "is_overdue": True,
                }
            ],
            "ppe_events": []
        }
    },
    {
        "id": 4,
        "name": "DEMO 4 — MULTIPLE REGULATORY VIOLATIONS",
        "description": "Severe site non-compliance: deep excavation pit lacks shoring (OSHA 1926.651), uncertified excavator operator active (ISO 45001 Cl 7.2), and temporary electrical board lacks GFCI (OSHA 1926.403).",
        "category": "CRITICAL_NON_COMPLIANCE",
        "expected_status": "NON_COMPLIANT",
        "expected_violations": 3,
        "narrative": "Critical multi-regulatory failure across 3 statutory domains. Combined severity escalates audit to NON_COMPLIANT status (Score 40.0) with immediate Stop-Work recommendation.",
        "context": {
            "is_simulation": True,
            "workers": [
                {
                    "worker_id": "WRK-DEMO-401",
                    "name": "Vikram Singh",
                    "role": "excavator_operator",
                    "ppe_status": PPEStatus.COMPLIANT,
                    "safety_training_status": SafetyTrainingStatus.EXPIRED,
                    "missing_gear": [],
                }
            ],
            "hazards": [
                {
                    "title": "Deep Excavation Pit Wall Slumping — Unshored Trench",
                    "hazard_type": "excavation",
                    "location": "Zone A — Deep Excavation Pit",
                    "probability": 5,
                    "severity": 5,
                },
                {
                    "title": "Temporary Distribution Panel Wet Ground Exposure",
                    "hazard_type": "electrical",
                    "location": "Zone C — Utility Hub",
                    "probability": 4,
                    "severity": 5,
                }
            ],
            "inspections": [
                {
                    "id": "INSP-DEMO-05",
                    "title": "Daily Trench Geotechnical Inspection",
                    "inspection_type": "Daily Pre-Entry",
                    "regulatory_reference": "OSHA 1926.651",
                    "responsible_role": "site_manager",
                    "due_date": datetime.utcnow() + timedelta(hours=4),
                    "status": InspectionRequirementStatus.SCHEDULED,
                    "is_overdue": False,
                }
            ],
            "ppe_events": []
        }
    }
]
