"""
Deterministic Worker Safety Monitoring Demo Scenarios — Milestone 2 Phase 2.3
=============================================================================
Provides 6 deterministic simulation fixtures for demonstrating worker safety monitoring.
All scenarios are explicitly labeled: DEMO / SIMULATION.
"""

from typing import Dict, Any, List
from app.models.models import WorkerSafetyStatus, RiskCategory, SafetyTrainingStatus, PPEStatus, WorkerRole


MONITORING_DEMO_SCENARIOS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "DEMO 1 — SAFE WORKER",
        "description": "Worker with certified safety training and compliant PPE engaged in standard activity in a safe site area.",
        "worker_info": {
            "id": "demo-worker-1",
            "name": "Rajesh Sharma",
            "role": WorkerRole.MASON,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        },
        "context": {
            "current_activity": "general_construction",
            "current_zone": "Zone D — Laydown Area",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 15,
            "nearby_hazards": [],
            "nearby_equipment": [],
            "workers_in_zone_count": 2,
            "is_simulation": True,
        },
        "expected_status": WorkerSafetyStatus.SAFE,
        "expected_findings_count": 0,
    },
    2: {
        "id": 2,
        "name": "DEMO 2 — WORKER ENTERS HIGH-RISK ZONE",
        "description": "Worker enters a designated high-risk excavation perimeter. Triggers Rule 1 (High-Risk Zone Entry).",
        "worker_info": {
            "id": "demo-worker-2",
            "name": "Amit Kumar",
            "role": WorkerRole.GENERAL_WORKER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        },
        "context": {
            "current_activity": "general_construction",
            "current_zone": "Zone A — Deep Excavation Pit",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 10,
            "nearby_hazards": [],
            "nearby_equipment": [],
            "workers_in_zone_count": 2,
            "is_simulation": True,
        },
        "expected_status": WorkerSafetyStatus.HIGH_RISK,
        "expected_findings_count": 1,
    },
    3: {
        "id": 3,
        "name": "DEMO 3 — WORKER STAYS TOO LONG IN HIGH-RISK ZONE",
        "description": "Worker remains in high-risk zone for 75 minutes, exceeding the 45-minute dwell limit. Triggers Rule 1 and Rule 2.",
        "worker_info": {
            "id": "demo-worker-3",
            "name": "Deepak Verma",
            "role": WorkerRole.GENERAL_WORKER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        },
        "context": {
            "current_activity": "excavation",
            "current_zone": "Zone A — Deep Excavation Pit",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 75,
            "nearby_hazards": [],
            "nearby_equipment": [],
            "workers_in_zone_count": 2,
            "is_simulation": True,
        },
        "expected_status": WorkerSafetyStatus.HIGH_RISK,
        "expected_findings_count": 2,
    },
    4: {
        "id": 4,
        "name": "DEMO 4 — WORKER NEAR ACTIVE HAZARD",
        "description": "Worker operates in proximity to an active, unmitigated trench wall collapse hazard. Triggers Rule 3 (Hazard Proximity).",
        "worker_info": {
            "id": "demo-worker-4",
            "name": "Suresh Nair",
            "role": WorkerRole.ELECTRICIAN,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        },
        "context": {
            "current_activity": "electrical_work",
            "current_zone": "Zone B — Utility Corridor",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 25,
            "nearby_hazards": ["HAZ-002: Unshored Trench Wall Collapse Risk (High Severity)"],
            "nearby_equipment": [],
            "workers_in_zone_count": 1,
            "is_simulation": True,
        },
        "expected_status": WorkerSafetyStatus.HIGH_RISK,
        "expected_findings_count": 1,
    },
    5: {
        "id": 5,
        "name": "DEMO 5 — WORKER NEAR OPERATING HEAVY EQUIPMENT",
        "description": "Non-operator laborer detected inside the active 10-meter swing radius of a 30-ton excavator. Triggers Rule 4 (Equipment Proximity).",
        "worker_info": {
            "id": "demo-worker-5",
            "name": "Vikram Singh",
            "role": WorkerRole.GENERAL_WORKER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        },
        "context": {
            "current_activity": "material_handling",
            "current_zone": "Zone C — Earthmoving Sector",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 15,
            "nearby_hazards": [],
            "nearby_equipment": ["EQP-001: 30-Ton CAT Excavator (Engine Running, Swing Active)"],
            "workers_in_zone_count": 1,
            "is_simulation": True,
        },
        "expected_status": WorkerSafetyStatus.CRITICAL,
        "expected_findings_count": 1,
    },
    6: {
        "id": 6,
        "name": "DEMO 6 — UNSAFE ACTIVITY + MISSING PPE",
        "description": "Worker performing high-risk welding with non-compliant PPE in proximity to active plant machinery. Triggers Rules 4, 5, 6, and 8.",
        "worker_info": {
            "id": "demo-worker-6",
            "name": "Arun Patel",
            "role": WorkerRole.WELDER,
            "safety_training": SafetyTrainingStatus.NOT_STARTED,
            "ppe_status": PPEStatus.NON_COMPLIANT,
        },
        "context": {
            "current_activity": "welding",
            "current_zone": "Zone C — Structural Steel Bay",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 30,
            "nearby_hazards": [],
            "nearby_equipment": ["EQP-004: Mobile Diesel Crane (Operational)"],
            "workers_in_zone_count": 2,
            "is_simulation": True,
        },
        "expected_status": WorkerSafetyStatus.CRITICAL,
        "expected_findings_count": 5,
    },
}
