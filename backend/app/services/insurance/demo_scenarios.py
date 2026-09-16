"""Deterministic Insurance Demo Scenarios for Milestone 3.

Pre-configured, reproducible scenarios demonstrating:
1. Low Insurance Exposure (Clean audit, high compliance, low score)
2. High Insurance Exposure (Multiple critical hazards, compliance penalty, critical score)
3. Claim Documentation Support (Structured claim dossier, missing proof identification)

All synthetic data explicitly labeled 'DEMO / SIMULATION' with is_simulation=True.
"""

from typing import List, Dict, Any

INSURANCE_DEMO_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": 5,
        "name": "DEMO 5 — LOW INSURANCE EXPOSURE",
        "description": "Exemplary construction site with 95% compliance score, 0 critical hazards, full PPE adherence, and current equipment certifications. Qualifies for preferred underwriting insurance rates.",
        "expected_risk_level": "LOW",
        "expected_score_range": "10.0 — 25.0",
        "narrative": "Comprehensive underwriting evaluation confirms minimal loss exposure. Low probability of workers' compensation or third-party general liability claims.",
        "context": {
            "is_simulation": True,
            "compliance_score": 96.0,
            "hazards": [],
            "safety_findings": [],
            "safety_alerts": [],
            "workers": [
                {"role": "laborer", "safety_training_status": "certified"},
                {"role": "surveyor", "safety_training_status": "certified"}
            ]
        }
    },
    {
        "id": 6,
        "name": "DEMO 6 — HIGH INSURANCE EXPOSURE",
        "description": "High-risk construction site with active excavation trench cave-in risk, uncertified tower crane operator, 4 open critical safety findings, and active high-severity alerts.",
        "expected_risk_level": "CRITICAL",
        "expected_score_range": "80.0 — 95.0",
        "narrative": "Underwriting risk escalates to CRITICAL (Score > 85.0). High probability of major workers' comp loss, catastrophic property damage, and regulatory stop-work fines. Surcharge mandated.",
        "context": {
            "is_simulation": True,
            "compliance_score": 38.0,
            "hazards": [
                {"title": "Unshored Deep Trench Collapse Risk", "severity": "CRITICAL"},
                {"title": "Tower Crane Out-of-Tolerance Clearance", "severity": "CRITICAL"},
                {"title": "Temporary Electrical Water Immersion", "severity": "HIGH"},
            ],
            "safety_findings": [
                {"status": "OPEN", "severity": "CRITICAL", "description": "Trench wall sloughing without protective trench box"},
                {"status": "OPEN", "severity": "CRITICAL", "description": "Crane operator license expired 45 days"},
                {"status": "OPEN", "severity": "HIGH", "description": "Scaffolding guardrail missing on 4th level"},
                {"status": "OPEN", "severity": "HIGH", "description": "PPE eye protection non-compliance during cutting"},
            ],
            "safety_alerts": [
                {"severity": "CRITICAL", "title": "Immediate Trench Cave-in Evacuation Alert"},
                {"severity": "HIGH", "title": "Overdue High-Voltage Grounding Alarm"},
            ],
            "workers": [
                {"role": "crane_operator", "safety_training_status": "EXPIRED"},
                {"role": "excavator_operator", "safety_training_status": "EXPIRED"},
                {"role": "scaffolder", "safety_training_status": "certified"},
                {"role": "ironworker", "safety_training_status": "certified"},
            ]
        }
    },
    {
        "id": 7,
        "name": "DEMO 7 — CLAIM DOCUMENTATION SUPPORT",
        "description": "Simulated scaffolding near-miss incident where an ironworker slipped on an unplanked scaffold ledger. Full claim dossier is generated, identifying missing supervisor sign-off and witness statements.",
        "expected_risk_level": "HIGH",
        "expected_score_range": "65.0 — 80.0",
        "narrative": "The Insurance Agent compiles a claim dossier linking worker credentials, active site telemetry, and safety findings while flagging missing supervisor witness documentation.",
        "context": {
            "is_simulation": True,
            "compliance_score": 68.0,
            "incident": {
                "title": "Ironworker Slip on 3rd-Floor Scaffold Bay — Fall Arrest Deployed",
                "summary": "At 10:45 AM, worker slipped while navigating unplanked scaffold section. Personal fall arrest harness arrested fall. Worker evacuated with minor contusions. Scaffolding tagged red.",
                "severity": "HIGH",
                "worker_id": "WRK-DEMO-701",
                "worker_name": "Marcus Vance",
                "worker_role": "Ironworker / Rigger",
                "equipment_id": "EQ-SCF-04",
                "equipment_name": "Modular Frame Scaffold Bay #4",
                "zone": "Zone B — Structural Works",
                "witness_statement": False,
                "supervisor_signoff": False,
                "sensor_evidence": True,
                "video_event_id": "VE-DEMO-882",
                "compliance_factors": ["OSHA 1926.451 Scaffolding", "OSHA 1926.501 Fall Protection"],
            }
        }
    }
]
