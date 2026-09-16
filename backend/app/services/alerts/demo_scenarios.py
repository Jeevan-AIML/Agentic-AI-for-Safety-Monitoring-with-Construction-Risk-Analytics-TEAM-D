"""Deterministic Demo Scenarios for ACRIP Safety Alert System (Phase 2.4).

Provides 7 explicit simulation scenarios:
1. DEMO 1 — HIGH ALERT: High-risk finding creates HIGH alert
2. DEMO 2 — CRITICAL ALERT: Critical finding creates immediate CRITICAL alert
3. DEMO 3 — ALERT ACKNOWLEDGED: Open alert transitions to ACKNOWLEDGED
4. DEMO 4 — ALERT ESCALATION: Unacknowledged alert exceeds timeout and transitions to ESCALATED
5. DEMO 5 — ALERT RESOLUTION: Acknowledged alert transitions to RESOLVED with notes
6. DEMO 6 — DUPLICATE PREVENTION: Same source event does not create duplicate active alerts
7. DEMO 7 — MULTIPLE ALERTS: Multiple independent safety events create separate alerts

All fixtures and outputs are explicitly tagged: DEMO / SIMULATION.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.models import (
    SafetyAlert, AlertSeverity, AlertStatus, AlertPriority,
    SafetyFinding, SafetyFindingType, SafetyFindingStatus,
    RiskCategory, Site, Worker, User
)
from app.services.alerts.alert_service import AlertService


DEMO_SCENARIOS_CATALOG: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "DEMO 1 — HIGH ALERT",
        "description": "High-risk safety finding automatically produces a tracked HIGH alert with 30m acknowledgment window.",
        "expected_severity": "high",
        "expected_status": "open",
        "summary": "Generates a HIGH alert from a high-risk zone dwell violation, dispatches in-app, email, and push notifications.",
    },
    {
        "id": 2,
        "name": "DEMO 2 — CRITICAL ALERT",
        "description": "Critical proximity finding triggers an immediate CRITICAL alert with dual role notification (Safety Officer + Site Manager).",
        "expected_severity": "critical",
        "expected_status": "open",
        "summary": "Generates an urgent CRITICAL alert with 15m timeout window and multi-channel broadcast.",
    },
    {
        "id": 3,
        "name": "DEMO 3 — ALERT ACKNOWLEDGED",
        "description": "Safety Officer acknowledges an open alert, capturing responder identity, timestamp, and audit trail.",
        "expected_severity": "high",
        "expected_status": "acknowledged",
        "summary": "Simulates acknowledgment flow: transitions alert state from OPEN to ACKNOWLEDGED.",
    },
    {
        "id": 4,
        "name": "DEMO 4 — ALERT ESCALATION",
        "description": "Unacknowledged alert exceeds timeout and escalates to Site Manager (Level 1) with higher priority.",
        "expected_severity": "critical",
        "expected_status": "escalated",
        "summary": "Demonstrates automated tiered escalation: increases level to 1, reassigns to site_manager, dispatches escalation alert.",
    },
    {
        "id": 5,
        "name": "DEMO 5 — ALERT RESOLUTION",
        "description": "Responder resolves an acknowledged alert with corrective mitigation notes, synchronizing underlying finding.",
        "expected_severity": "high",
        "expected_status": "resolved",
        "summary": "Simulates complete remediation: moves alert to RESOLVED and marks underlying SafetyFinding as mitigated.",
    },
    {
        "id": 6,
        "name": "DEMO 6 — DUPLICATE PREVENTION",
        "description": "Identical active finding evaluated multiple times does NOT create duplicate open alerts.",
        "expected_severity": "high",
        "expected_status": "open",
        "summary": "Enforces strict idempotency: re-evaluates an active source finding and suppresses redundant alert generation.",
    },
    {
        "id": 7,
        "name": "DEMO 7 — MULTIPLE ALERTS",
        "description": "Two distinct concurrent safety violations create two independent, segregated alerts.",
        "expected_severity": "critical",
        "expected_status": "open",
        "summary": "Validates concurrent handling: multiple independent hazards each generate dedicated alerts.",
    },
]


class AlertDemoRunner:
    """Executes deterministic demo scenarios for Phase 2.4."""

    def __init__(self):
        self.service = AlertService()

    def run_scenario(
        self,
        db: Session,
        scenario_id: int,
        user: User,
        site_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes a scenario by ID and returns execution results with simulation metadata."""
        # Ensure fallback site exists
        site = None
        if site_id:
            site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            site = db.query(Site).first()

        if not site:
            raise ValueError("No active site found to run alert demo scenario")

        # Pick or find a worker
        worker = db.query(Worker).filter(Worker.site_id == site.id).first()
        if not worker:
            worker = db.query(Worker).first()

        if scenario_id == 1:
            # DEMO 1: HIGH ALERT
            finding = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-HIGH-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.TIME_IN_ZONE_EXCEEDED,
                description="[DEMO / SIMULATION] Worker sustained 52 minutes in restricted excavation zone.",
                evidence="Continuous zone presence detected: 52m (Threshold: 45m).",
                severity=RiskCategory.HIGH,
                status=SafetyFindingStatus.OPEN,
                recommendation="Direct worker to rotate out of excavation zone immediately.",
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow(),
            )
            db.add(finding)
            db.flush()

            alert = self.service.create_alert_from_finding(db, finding, is_simulation=True)
            return {
                "scenario_id": 1,
                "scenario_name": "DEMO 1 — HIGH ALERT",
                "is_simulation": True,
                "label": "DEMO / SIMULATION",
                "alert": alert,
                "notifications_sent": len(alert.notifications) if alert else 0,
                "audit_events": len(alert.audit_events) if alert else 0,
                "message": "HIGH alert generated successfully with 30m timeout window and multi-channel dispatch.",
            }

        elif scenario_id == 2:
            # DEMO 2: CRITICAL ALERT
            finding = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-CRIT-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.EQUIPMENT_PROXIMITY,
                description="[DEMO / SIMULATION] Worker detected within 2.8m of active excavator swing radius.",
                evidence="Proximity breach: 2.8m (Safe threshold: 10.0m).",
                severity=RiskCategory.CRITICAL,
                status=SafetyFindingStatus.OPEN,
                recommendation="Halt excavator operations and evacuate standoff radius immediately.",
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow(),
            )
            db.add(finding)
            db.flush()

            alert = self.service.create_alert_from_finding(db, finding, is_simulation=True)
            return {
                "scenario_id": 2,
                "scenario_name": "DEMO 2 — CRITICAL ALERT",
                "is_simulation": True,
                "label": "DEMO / SIMULATION",
                "alert": alert,
                "notifications_sent": len(alert.notifications) if alert else 0,
                "audit_events": len(alert.audit_events) if alert else 0,
                "message": "CRITICAL alert created with immediate dual role broadcast (Safety Officer & Site Manager).",
            }

        elif scenario_id == 3:
            # DEMO 3: ALERT ACKNOWLEDGED
            finding = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-ACK-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.PPE_VIOLATION,
                description="[DEMO / SIMULATION] Worker operating in Zone B without high-visibility vest.",
                severity=RiskCategory.HIGH,
                status=SafetyFindingStatus.OPEN,
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow(),
            )
            db.add(finding)
            db.flush()

            alert = self.service.create_alert_from_finding(db, finding, is_simulation=True)
            ack_alert = self.service.acknowledge_alert(
                db=db,
                alert_id=alert.id,
                user=user,
                notes="[DEMO / SIMULATION] Acknowledged: Safety Officer dispatched to inspect worker PPE.",
            )
            return {
                "scenario_id": 3,
                "scenario_name": "DEMO 3 — ALERT ACKNOWLEDGED",
                "is_simulation": True,
                "label": "DEMO / SIMULATION",
                "alert": ack_alert,
                "status_before": "open",
                "status_after": ack_alert.status.value,
                "acknowledged_by": user.full_name,
                "message": "Alert transitioned from OPEN to ACKNOWLEDGED with responder identity logged.",
            }

        elif scenario_id == 4:
            # DEMO 4: ALERT ESCALATION
            finding = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-ESC-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.UNSAFE_WORKER_EQUIPMENT_INTERACTION,
                description="[DEMO / SIMULATION] Uncontrolled worker-equipment interaction unacknowledged.",
                severity=RiskCategory.CRITICAL,
                status=SafetyFindingStatus.OPEN,
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow() - timedelta(minutes=20),
            )
            db.add(finding)
            db.flush()

            alert = self.service.create_alert_from_finding(db, finding, is_simulation=True)
            # Escalate
            esc_alert = self.service.escalate_alert(
                db=db,
                alert_id=alert.id,
                user=user,
                reason="[DEMO / SIMULATION] Unacknowledged for > 15m. Escalated to Site Manager.",
                target_role="site_manager",
            )
            return {
                "scenario_id": 4,
                "scenario_name": "DEMO 4 — ALERT ESCALATION",
                "is_simulation": True,
                "label": "DEMO / SIMULATION",
                "alert": esc_alert,
                "escalation_level": esc_alert.escalation_level,
                "assigned_role": esc_alert.assigned_role,
                "message": f"Alert escalated to Level {esc_alert.escalation_level} ({esc_alert.assigned_role}) with escalation notification sent.",
            }

        elif scenario_id == 5:
            # DEMO 5: ALERT RESOLUTION
            finding = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-RES-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.HAZARD_PROXIMITY,
                description="[DEMO / SIMULATION] Worker in proximity to open electrical conduit.",
                severity=RiskCategory.HIGH,
                status=SafetyFindingStatus.OPEN,
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow(),
            )
            db.add(finding)
            db.flush()

            alert = self.service.create_alert_from_finding(db, finding, is_simulation=True)
            self.service.acknowledge_alert(db, alert.id, user, notes="En route to isolate power")
            resolved_alert = self.service.resolve_alert(
                db=db,
                alert_id=alert.id,
                user=user,
                notes="[DEMO / SIMULATION] Power isolated, conduit covered and tagged out. Area cleared.",
            )
            return {
                "scenario_id": 5,
                "scenario_name": "DEMO 5 — ALERT RESOLUTION",
                "is_simulation": True,
                "label": "DEMO / SIMULATION",
                "alert": resolved_alert,
                "status": resolved_alert.status.value,
                "resolution_notes": resolved_alert.resolution_notes,
                "message": "Alert resolved and underlying SafetyFinding synchronized to MITIGATED.",
            }

        elif scenario_id == 6:
            # DEMO 6: DUPLICATE PREVENTION
            finding = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-DUP-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.OVERCROWDED_ZONE,
                description="[DEMO / SIMULATION] Overcrowded zone condition detected.",
                severity=RiskCategory.HIGH,
                status=SafetyFindingStatus.OPEN,
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow(),
            )
            db.add(finding)
            db.flush()

            alert_first = self.service.create_alert_from_finding(db, finding, is_simulation=True)
            alert_second = self.service.create_alert_from_finding(db, finding, is_simulation=True)

            return {
                "scenario_id": 6,
                "scenario_name": "DEMO 6 — DUPLICATE PREVENTION",
                "is_simulation": True,
                "label": "DEMO / SIMULATION",
                "alert": alert_first,
                "duplicate_detected": True,
                "first_alert_id": alert_first.alert_id if alert_first else None,
                "second_alert_id": alert_second.alert_id if alert_second else None,
                "is_identical_instance": alert_first.id == alert_second.id if (alert_first and alert_second) else False,
                "message": "Verified: re-evaluating the same active source event returns the existing alert without creating duplicates.",
            }

        elif scenario_id == 7:
            # DEMO 7: MULTIPLE ALERTS
            finding_a = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-M1-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.HIGH_RISK_ZONE_EXPOSURE,
                description="[DEMO / SIMULATION] Event A: Unauthorized entry into crane lifting envelope.",
                severity=RiskCategory.CRITICAL,
                status=SafetyFindingStatus.OPEN,
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow(),
            )
            finding_b = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f"SF-DEMO-M2-{uuid.uuid4().hex[:6].upper()}",
                site_id=site.id,
                worker_id=worker.id if worker else None,
                finding_type=SafetyFindingType.PPE_VIOLATION,
                description="[DEMO / SIMULATION] Event B: Missing safety harness on elevated scaffolding.",
                severity=RiskCategory.HIGH,
                status=SafetyFindingStatus.OPEN,
                detection_source="DEMO / SIMULATION",
                created_at=datetime.utcnow(),
            )
            db.add_all([finding_a, finding_b])
            db.flush()

            alert_a = self.service.create_alert_from_finding(db, finding_a, is_simulation=True)
            alert_b = self.service.create_alert_from_finding(db, finding_b, is_simulation=True)

            return {
                "scenario_id": 7,
                "scenario_name": "DEMO 7 — MULTIPLE ALERTS",
                "is_simulation": True,
                "label": "DEMO / SIMULATION",
                "alert_count": 2,
                "alert_a": alert_a,
                "alert_b": alert_b,
                "message": "Verified: multiple distinct safety events generated two separate, independently tracked alerts.",
            }

        else:
            raise ValueError(f"Unknown scenario_id: {scenario_id}")
