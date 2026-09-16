"""
Video Surveillance Demo Scenarios — Milestone 3 Phase 3.1
==========================================================
Defines the 5 deterministic demo scenarios required for Phase 3.1:
1. SAFE SITE: 2 workers detected, fully compliant PPE, safe laydown zone, 0 violations.
2. PPE VIOLATION: Worker detected without hard hat in active zone -> PPE_VIOLATION event & SafetyFinding.
3. HIGH-RISK ZONE ENTRY: Worker enters excavation/restricted zone -> HIGH finding & alert.
4. EQUIPMENT PROXIMITY: Non-operator worker enters heavy equipment operating envelope -> CRITICAL finding & alert.
5. MULTIPLE SAFETY VIOLATIONS: Worker missing PPE, inside excavation zone, near operating equipment -> Multiple findings & CRITICAL alert.

Explicitly labeled: DEMO / SIMULATION
"""

from typing import Dict, Any, List

VIDEO_DEMO_SCENARIOS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "DEMO 1 — SAFE SITE",
        "description": "Two workers detected in Safe Laydown Area wearing certified Hard Hat, High-Visibility Vest, and Goggles. Zero safety violations.",
        "expected_violations": 0,
        "expected_severity": "LOW",
        "summary": "Full PPE compliance verified, personnel located within designated safe boundaries, 0 active hazards or equipment risks.",
        "detection_source": "DEMO / SIMULATION",
        "is_simulation": True,
        "scenario_data": {
            "scenario_id": 1,
            "workers_count": 2,
            "current_zone": "Safe Laydown Area",
            "is_high_risk_zone": False,
            "nearby_hazards": [],
            "nearby_equipment": [],
            "simulated_ppe": ["HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"],
        },
    },
    2: {
        "id": 2,
        "name": "DEMO 2 — PPE VIOLATION",
        "description": "Worker Marcus Vance detected in active work sector without mandatory Hard Hat. Optical detection flags missing head protection.",
        "expected_violations": 1,
        "expected_severity": "CRITICAL",
        "summary": "Worker missing certified Hard Hat during active site operation. Generates PPE_VIOLATION event, SafetyFinding, and SafetyAlert.",
        "detection_source": "DEMO / SIMULATION",
        "is_simulation": True,
        "scenario_data": {
            "scenario_id": 2,
            "workers_count": 1,
            "current_zone": "Active Work Sector",
            "is_high_risk_zone": False,
            "nearby_hazards": [],
            "nearby_equipment": [],
            "simulated_ppe": ["SAFETY_VEST"],  # Missing HARD_HAT
        },
    },
    3: {
        "id": 3,
        "name": "DEMO 3 — HIGH-RISK ZONE ENTRY",
        "description": "Worker enters perimeter of designated Excavation Zone without spotter oversight. Generates HIGH_RISK_ZONE_ENTRY event.",
        "expected_violations": 1,
        "expected_severity": "HIGH",
        "summary": "Unauthorized entry into hazardous Excavation Sector. Generates HIGH severity SafetyFinding and automated AlertEngine dispatch.",
        "detection_source": "DEMO / SIMULATION",
        "is_simulation": True,
        "scenario_data": {
            "scenario_id": 3,
            "workers_count": 1,
            "current_zone": "Excavation Zone",
            "is_high_risk_zone": True,
            "nearby_hazards": ["Open Trench Excavation (Depth 3.5m)"],
            "nearby_equipment": [],
            "simulated_ppe": ["HARD_HAT", "SAFETY_VEST"],
        },
    },
    4: {
        "id": 4,
        "name": "DEMO 4 — EQUIPMENT PROXIMITY",
        "description": "Non-operator worker enters operating swing radius of CAT 320 Hydraulic Excavator. Generates EQUIPMENT_PROXIMITY event.",
        "expected_violations": 1,
        "expected_severity": "CRITICAL",
        "summary": "Worker breached 10-meter exclusion zone of active heavy machinery. Generates immediate CRITICAL Alert.",
        "detection_source": "DEMO / SIMULATION",
        "is_simulation": True,
        "scenario_data": {
            "scenario_id": 4,
            "workers_count": 1,
            "current_zone": "Heavy Equipment Zone",
            "is_high_risk_zone": True,
            "nearby_hazards": [],
            "nearby_equipment": ["CAT 320 Hydraulic Excavator (Operating)"],
            "simulated_ppe": ["HARD_HAT", "SAFETY_VEST"],
        },
    },
    5: {
        "id": 5,
        "name": "DEMO 5 — MULTIPLE SAFETY VIOLATIONS",
        "description": "Compound hazard event: worker missing Hard Hat and Vest, operating within Excavation Zone near operating Komatsu excavator and open trench.",
        "expected_violations": 3,
        "expected_severity": "CRITICAL",
        "summary": "Severe compound violations: Unprotected worker in high-risk zone with heavy equipment proximity. Multiple findings and immediate CRITICAL Alert.",
        "detection_source": "DEMO / SIMULATION",
        "is_simulation": True,
        "scenario_data": {
            "scenario_id": 5,
            "workers_count": 1,
            "current_zone": "Excavation Zone",
            "is_high_risk_zone": True,
            "nearby_hazards": ["Unguarded Excavation Trench (Depth 3.5m)"],
            "nearby_equipment": ["Komatsu PC210 Excavator (Operating)"],
            "simulated_ppe": [],  # Missing HARD_HAT and SAFETY_VEST
        },
    },
}
