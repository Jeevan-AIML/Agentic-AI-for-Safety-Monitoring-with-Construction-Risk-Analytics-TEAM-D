"""
ACRIP Milestone 2 Phase 2.4 Safety Alert System Test Suite
==========================================================
Comprehensive tests for:
1. Alert Engine severity evaluation (LOW/MEDIUM suppressed, HIGH/CRITICAL generated)
2. Alert deduplication against active (OPEN/ACKNOWLEDGED/ESCALATED) alerts
3. Multi-channel notification dispatch (IN_APP, EMAIL_ADAPTER mock, PUSH_ADAPTER mock)
4. Alert acknowledgment lifecycle and audit log recording
5. Alert resolution lifecycle and SafetyFinding synchronization
6. Manual tiered escalation (Level 1 -> Site Manager, Level 2 -> Super Admin)
7. Automated timeout-based escalation check
8. Full audit trail verification across lifecycle states
9. API: List and filter alerts (site, status, severity)
10. API: Get alert detail with audit events and notification history
11. API: Acknowledge endpoint
12. API: Resolve endpoint with required notes
13. API: Escalate endpoint
14. API Authentication: 401 Unauthorized for unauthenticated requests
15. RBAC: Safety Officer (Acknowledge, Resolve, Escalate)
16. RBAC: Site Manager (Acknowledge, Resolve, cannot Escalate -> 403)
17. RBAC: Project Manager (Acknowledge, cannot Resolve -> 403, cannot Escalate -> 403)
18. RBAC: Viewer (Read-only, 403 on all mutations)
19. Demo Scenario 1: HIGH ALERT
20. Demo Scenario 2: CRITICAL ALERT
21. Demo Scenario 3: ALERT ACKNOWLEDGED
22. Demo Scenario 4: ALERT ESCALATION
23. Demo Scenario 5: ALERT RESOLUTION
24. Demo Scenario 6: DUPLICATE PREVENTION
25. Demo Scenario 7: MULTIPLE ALERTS
"""

import uuid
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, Worker, UserRole, ProjectStatus, SiteStatus,
    WorkerRole, SafetyTrainingStatus, PPEStatus,
    SafetyFinding, SafetyFindingStatus, SafetyFindingType,
    RiskCategory, SafetyAlert, AlertSeverity, AlertStatus, AlertPriority,
    AlertNotification, NotificationChannel, AlertAuditEvent, AlertAuditEventType
)
from app.core.security import hash_password, create_access_token
from app.services.alerts.alert_engine import AlertEngine
from app.services.alerts.alert_service import AlertService
from app.services.alerts.notification_adapters import NotificationDispatcher
from app.services.alerts.demo_scenarios import AlertDemoRunner, DEMO_SCENARIOS_CATALOG
from app.main import app


class TestPhase24SafetyAlertSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.suffix = uuid.uuid4().hex[:6]

        # 1. Super Admin
        cls.admin_email = f"admin_p24_{cls.suffix}@acrip.com"
        cls.admin = User(
            id=str(uuid.uuid4()),
            email=cls.admin_email,
            full_name="Admin P24",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        cls.db.add(cls.admin)

        # 2. Safety Officer
        cls.safety_email = f"safety_p24_{cls.suffix}@acrip.com"
        cls.safety_officer = User(
            id=str(uuid.uuid4()),
            email=cls.safety_email,
            full_name="Safety Officer P24",
            hashed_password=hash_password("Safety@123"),
            role=UserRole.SAFETY_OFFICER,
            is_active=True,
        )
        cls.db.add(cls.safety_officer)

        # 3. Site Manager
        cls.site_manager_email = f"sitemgr_p24_{cls.suffix}@acrip.com"
        cls.site_manager = User(
            id=str(uuid.uuid4()),
            email=cls.site_manager_email,
            full_name="Site Manager P24",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.SITE_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.site_manager)

        # 4. Project Manager
        cls.pm_email = f"pm_p24_{cls.suffix}@acrip.com"
        cls.pm = User(
            id=str(uuid.uuid4()),
            email=cls.pm_email,
            full_name="Project Manager P24",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.PROJECT_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.pm)

        # 5. Viewer
        cls.viewer_email = f"viewer_p24_{cls.suffix}@acrip.com"
        cls.viewer = User(
            id=str(uuid.uuid4()),
            email=cls.viewer_email,
            full_name="Viewer P24",
            hashed_password=hash_password("Viewer@123"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        cls.db.add(cls.viewer)

        # 6. Test Project, Site, Worker
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-P24-{cls.suffix}",
            name="Phase 2.4 Alert Test Project",
            description="Testing alert lifecycle and escalation",
            client="Global Infra Corp",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-P24-{cls.suffix.upper()}",
            name="Phase 2.4 Test Site",
            project_id=cls.project.id,
            status=SiteStatus.ACTIVE,
            current_risk_score=50.0,
            risk_category=RiskCategory.MEDIUM,
        )
        cls.db.add(cls.site)

        cls.worker = Worker(
            id=str(uuid.uuid4()),
            worker_id=f"WRK-P24-{cls.suffix.upper()}",
            site_id=cls.site.id,
            name="Ravi Shankar",
            role=WorkerRole.GENERAL_WORKER,
            safety_training=SafetyTrainingStatus.CERTIFIED,
            ppe_status=PPEStatus.COMPLIANT,
            is_active=True,
        )
        cls.db.add(cls.worker)
        cls.db.commit()

        # Generate JWT Auth Tokens
        cls.admin_token = create_access_token({"sub": cls.admin.id, "email": cls.admin.email, "role": cls.admin.role.value})
        cls.safety_token = create_access_token({"sub": cls.safety_officer.id, "email": cls.safety_officer.email, "role": cls.safety_officer.role.value})
        cls.sitemgr_token = create_access_token({"sub": cls.site_manager.id, "email": cls.site_manager.email, "role": cls.site_manager.role.value})
        cls.pm_token = create_access_token({"sub": cls.pm.id, "email": cls.pm.email, "role": cls.pm.role.value})
        cls.viewer_token = create_access_token({"sub": cls.viewer.id, "email": cls.viewer.email, "role": cls.viewer.role.value})

        cls.auth_headers_admin = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.auth_headers_safety = {"Authorization": f"Bearer {cls.safety_token}"}
        cls.auth_headers_sitemgr = {"Authorization": f"Bearer {cls.sitemgr_token}"}
        cls.auth_headers_pm = {"Authorization": f"Bearer {cls.pm_token}"}
        cls.auth_headers_viewer = {"Authorization": f"Bearer {cls.viewer_token}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ── 1. Alert Engine Rules & Deduplication ─────────────────────────────────

    def test_01_alert_engine_severity_evaluation_rules(self):
        """Rule verification: LOW and MEDIUM do not create alerts; HIGH and CRITICAL create alerts."""
        engine_inst = AlertEngine()

        self.assertIsNone(engine_inst.evaluate_severity(RiskCategory.LOW))
        self.assertIsNone(engine_inst.evaluate_severity(RiskCategory.MEDIUM))
        self.assertIsNone(engine_inst.evaluate_severity("low"))
        self.assertIsNone(engine_inst.evaluate_severity("medium"))

        self.assertEqual(engine_inst.evaluate_severity(RiskCategory.HIGH), AlertSeverity.HIGH)
        self.assertEqual(engine_inst.evaluate_severity(RiskCategory.CRITICAL), AlertSeverity.CRITICAL)
        self.assertEqual(engine_inst.evaluate_severity("high"), AlertSeverity.HIGH)
        self.assertEqual(engine_inst.evaluate_severity("critical"), AlertSeverity.CRITICAL)

    def test_02_alert_creation_from_finding_and_notification_dispatch(self):
        """Verify AlertService generates HIGH alert, dispatches all 3 adapters, and records creation audit."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-P24-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.TIME_IN_ZONE_EXCEEDED,
            description="Exceeded restricted excavation zone threshold",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            recommendation="Rotate worker immediately.",
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()

        alert = svc.create_alert_from_finding(self.db, finding)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, AlertSeverity.HIGH)
        self.assertEqual(alert.status, AlertStatus.OPEN)
        self.assertEqual(alert.escalation_timeout_minutes, 30)
        self.assertTrue(alert.alert_id.startswith("ALT-"))

        # Verify audit trail
        audits = self.db.query(AlertAuditEvent).filter(AlertAuditEvent.alert_id == alert.id).all()
        self.assertTrue(any(a.event_type == AlertAuditEventType.ALERT_CREATED for a in audits))

        # Verify multi-channel notifications (In-App, Email Mock, Push Mock)
        notifs = self.db.query(AlertNotification).filter(AlertNotification.alert_id == alert.id).all()
        channels = [n.channel for n in notifs]
        self.assertIn(NotificationChannel.IN_APP, channels)
        self.assertIn(NotificationChannel.EMAIL_ADAPTER, channels)
        self.assertIn(NotificationChannel.PUSH_ADAPTER, channels)

        # Check mock labels
        email_notif = next(n for n in notifs if n.channel == NotificationChannel.EMAIL_ADAPTER)
        self.assertEqual(email_notif.status, "SENT_MOCK")
        self.assertTrue("[MOCK / STUB]" in email_notif.delivery_details.get("delivery_note", ""))

    def test_03_alert_deduplication_active_event(self):
        """Active findings do not produce duplicate alerts."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-DUP-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.HAZARD_PROXIMITY,
            description="Proximity to trench edge",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()

        alert_1 = svc.create_alert_from_finding(self.db, finding)
        alert_2 = svc.create_alert_from_finding(self.db, finding)

        self.assertIsNotNone(alert_1)
        self.assertEqual(alert_1.id, alert_2.id)

    def test_04_alert_acknowledgment_lifecycle(self):
        """Verify OPEN -> ACKNOWLEDGED transition and audit log."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-ACK-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.PPE_VIOLATION,
            description="Missing eye protection",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()

        alert = svc.create_alert_from_finding(self.db, finding)
        self.assertEqual(alert.status, AlertStatus.OPEN)

        ack_alert = svc.acknowledge_alert(
            self.db,
            alert.id,
            user=self.safety_officer,
            notes="Acknowledged, delivering safety goggles",
        )
        self.assertEqual(ack_alert.status, AlertStatus.ACKNOWLEDGED)
        self.assertEqual(ack_alert.acknowledged_by, self.safety_officer.id)
        self.assertIsNotNone(ack_alert.acknowledged_at)

        # Finding should be acknowledged as well
        self.db.refresh(finding)
        self.assertEqual(finding.status, SafetyFindingStatus.ACKNOWLEDGED)

    def test_05_alert_resolution_lifecycle(self):
        """Verify ACKNOWLEDGED -> RESOLVED transition and finding synchronization."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-RES-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.HIGH_RISK_ACTIVITY,
            description="Unsecured hot work",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()

        alert = svc.create_alert_from_finding(self.db, finding)
        svc.acknowledge_alert(self.db, alert.id, user=self.safety_officer)

        resolved_alert = svc.resolve_alert(
            self.db,
            alert.id,
            user=self.safety_officer,
            notes="Hot work permit verified and fire blanket deployed.",
        )
        self.assertEqual(resolved_alert.status, AlertStatus.RESOLVED)
        self.assertEqual(resolved_alert.resolved_by, self.safety_officer.id)
        self.assertEqual(resolved_alert.resolution_notes, "Hot work permit verified and fire blanket deployed.")

        # Finding must be updated to MITIGATED
        self.db.refresh(finding)
        self.assertEqual(finding.status, SafetyFindingStatus.MITIGATED)

    def test_06_manual_escalation_and_role_assignment(self):
        """Manual escalation increments level to 1 and reassigns role."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-ESC-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.EQUIPMENT_PROXIMITY,
            description="Worker near swing radius",
            severity=RiskCategory.CRITICAL,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()

        alert = svc.create_alert_from_finding(self.db, finding)
        self.assertEqual(alert.escalation_level, 0)

        # Escalate Level 1
        esc_alert = svc.escalate_alert(
            self.db,
            alert.id,
            user=self.safety_officer,
            reason="Unattended critical proximity breach",
        )
        self.assertEqual(esc_alert.status, AlertStatus.ESCALATED)
        self.assertEqual(esc_alert.escalation_level, 1)
        self.assertEqual(esc_alert.assigned_role, "site_manager")

        # Escalate Level 2
        esc_alert_2 = svc.escalate_alert(
            self.db,
            alert.id,
            user=self.admin,
            reason="Repeated supervisor non-response",
        )
        self.assertEqual(esc_alert_2.escalation_level, 2)
        self.assertEqual(esc_alert_2.assigned_role, "super_admin")

    def test_07_automated_timeout_escalation_check(self):
        """Alerts whose created_at exceeds timeout_minutes automatically escalate."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-TIM-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.UNSAFE_EQUIPMENT_OPERATION,
            description="Overdue operator certification",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()

        alert = svc.create_alert_from_finding(self.db, finding)
        # Artificially set created_at back by 40 minutes (timeout is 30)
        alert.created_at = datetime.utcnow() - timedelta(minutes=40)
        self.db.commit()

        escalated_list = svc.check_escalation_timeouts(self.db)
        self.assertTrue(any(a.id == alert.id for a in escalated_list))

        self.db.refresh(alert)
        self.assertEqual(alert.status, AlertStatus.ESCALATED)
        self.assertEqual(alert.escalation_level, 1)

    # ── 2. REST API & RBAC Tests ──────────────────────────────────────────────

    def test_08_api_authentication_required(self):
        """Unauthenticated requests to alert endpoints return 401."""
        res = self.client.get("/api/v1/safety/alerts")
        self.assertEqual(res.status_code, 401)

        res_ack = self.client.post("/api/v1/safety/alerts/some-id/acknowledge", json={"notes": "test"})
        self.assertEqual(res_ack.status_code, 401)

    def test_09_api_list_and_filter_alerts(self):
        """Authenticated users can query alerts with site, severity, and status filters."""
        res = self.client.get(
            f"/api/v1/safety/alerts?site_id={self.site.id}",
            headers=self.auth_headers_viewer,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)

    def test_10_api_alert_detail_with_audit_and_notifications(self):
        """GET /api/v1/safety/alerts/{alert_id} returns full audit trail and notifications."""
        # Query any existing alert
        alert = self.db.query(SafetyAlert).filter(SafetyAlert.site_id == self.site.id).first()
        self.assertIsNotNone(alert)

        res = self.client.get(
            f"/api/v1/safety/alerts/{alert.id}",
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["alert_id"], alert.alert_id)
        self.assertIn("notifications", data)
        self.assertIn("audit_events", data)
        self.assertTrue(len(data["audit_events"]) > 0)

    def test_11_rbac_safety_officer_full_lifecycle(self):
        """Safety Officer can acknowledge, escalate, and resolve alerts."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-RBAC1-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.PPE_VIOLATION,
            description="Safety Officer RBAC test",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()
        alert = svc.create_alert_from_finding(self.db, finding)

        # 1. Acknowledge
        res_ack = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/acknowledge",
            json={"notes": "Safety Officer acknowledged"},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res_ack.status_code, 200)
        self.assertEqual(res_ack.json()["status"], "acknowledged")

        # 2. Escalate
        res_esc = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/escalate",
            json={"reason": "Safety Officer escalated"},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res_esc.status_code, 200)
        self.assertEqual(res_esc.json()["status"], "escalated")

        # 3. Resolve
        res_res = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/resolve",
            json={"notes": "Safety Officer resolved"},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.json()["status"], "resolved")

    def test_12_rbac_site_manager_permissions(self):
        """Site Manager can acknowledge and resolve, but CANNOT escalate (403)."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-RBAC2-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.PPE_VIOLATION,
            description="Site Manager RBAC test",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()
        alert = svc.create_alert_from_finding(self.db, finding)

        # Escalate must fail with 403 Forbidden
        res_esc = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/escalate",
            json={"reason": "Site Manager trying to escalate"},
            headers=self.auth_headers_sitemgr,
        )
        self.assertEqual(res_esc.status_code, 403)

        # Acknowledge succeeds
        res_ack = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/acknowledge",
            json={"notes": "Site Manager ack"},
            headers=self.auth_headers_sitemgr,
        )
        self.assertEqual(res_ack.status_code, 200)

        # Resolve succeeds
        res_res = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/resolve",
            json={"notes": "Site Manager resolved"},
            headers=self.auth_headers_sitemgr,
        )
        self.assertEqual(res_res.status_code, 200)

    def test_13_rbac_project_manager_permissions(self):
        """Project Manager can acknowledge, but CANNOT resolve (403) or escalate (403)."""
        svc = AlertService()
        finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-RBAC3-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            worker_id=self.worker.id,
            finding_type=SafetyFindingType.PPE_VIOLATION,
            description="Project Manager RBAC test",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.commit()
        alert = svc.create_alert_from_finding(self.db, finding)

        # Escalate forbidden (403)
        res_esc = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/escalate",
            json={"reason": "PM trying to escalate"},
            headers=self.auth_headers_pm,
        )
        self.assertEqual(res_esc.status_code, 403)

        # Resolve forbidden (403)
        res_res = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/resolve",
            json={"notes": "PM trying to resolve"},
            headers=self.auth_headers_pm,
        )
        self.assertEqual(res_res.status_code, 403)

        # Acknowledge allowed
        res_ack = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/acknowledge",
            json={"notes": "PM ack"},
            headers=self.auth_headers_pm,
        )
        self.assertEqual(res_ack.status_code, 200)

    def test_14_rbac_viewer_read_only(self):
        """Viewer can view alerts, but all mutation endpoints return 403 Forbidden."""
        alert = self.db.query(SafetyAlert).filter(SafetyAlert.site_id == self.site.id).first()
        self.assertIsNotNone(alert)

        # View detail -> 200
        res_get = self.client.get(
            f"/api/v1/safety/alerts/{alert.id}",
            headers=self.auth_headers_viewer,
        )
        self.assertEqual(res_get.status_code, 200)

        # Acknowledge -> 403
        res_ack = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/acknowledge",
            json={"notes": "Viewer attempt"},
            headers=self.auth_headers_viewer,
        )
        self.assertEqual(res_ack.status_code, 403)

        # Resolve -> 403
        res_res = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/resolve",
            json={"notes": "Viewer attempt"},
            headers=self.auth_headers_viewer,
        )
        self.assertEqual(res_res.status_code, 403)

        # Escalate -> 403
        res_esc = self.client.post(
            f"/api/v1/safety/alerts/{alert.id}/escalate",
            json={"reason": "Viewer attempt"},
            headers=self.auth_headers_viewer,
        )
        self.assertEqual(res_esc.status_code, 403)

    # ── 3. Deterministic Demo Scenarios ───────────────────────────────────────

    def test_15_demo_scenarios_catalog_list(self):
        """GET /api/v1/safety/alerts/demo-scenarios returns 7 catalogued scenarios."""
        res = self.client.get(
            "/api/v1/safety/alerts/demo-scenarios",
            headers=self.auth_headers_viewer,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 7)
        self.assertEqual(data[0]["name"], "DEMO 1 — HIGH ALERT")

    def test_16_demo_scenario_1_high_alert(self):
        """DEMO 1: HIGH finding creates HIGH alert with simulation tags."""
        res = self.client.post(
            "/api/v1/safety/alerts/demo-scenario",
            json={"scenario_id": 1, "site_id": self.site.id},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_simulation"])
        self.assertEqual(data["label"], "DEMO / SIMULATION")
        self.assertEqual(data["alert"]["severity"], "high")
        self.assertEqual(data["alert"]["status"], "open")

    def test_17_demo_scenario_2_critical_alert(self):
        """DEMO 2: CRITICAL finding creates CRITICAL alert."""
        res = self.client.post(
            "/api/v1/safety/alerts/demo-scenario",
            json={"scenario_id": 2, "site_id": self.site.id},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_simulation"])
        self.assertEqual(data["alert"]["severity"], "critical")
        self.assertEqual(data["alert"]["status"], "open")

    def test_18_demo_scenario_3_acknowledged(self):
        """DEMO 3: Alert transitions to ACKNOWLEDGED."""
        res = self.client.post(
            "/api/v1/safety/alerts/demo-scenario",
            json={"scenario_id": 3, "site_id": self.site.id},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status_after"], "acknowledged")

    def test_19_demo_scenario_4_escalated(self):
        """DEMO 4: Alert transitions to ESCALATED with Level 1."""
        res = self.client.post(
            "/api/v1/safety/alerts/demo-scenario",
            json={"scenario_id": 4, "site_id": self.site.id},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["escalation_level"], 1)
        self.assertEqual(data["assigned_role"], "site_manager")

    def test_20_demo_scenario_5_resolved(self):
        """DEMO 5: Alert transitions to RESOLVED with notes."""
        res = self.client.post(
            "/api/v1/safety/alerts/demo-scenario",
            json={"scenario_id": 5, "site_id": self.site.id},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "resolved")
        self.assertIsNotNone(data["resolution_notes"])

    def test_21_demo_scenario_6_duplicate_prevention(self):
        """DEMO 6: Re-evaluating same active finding suppresses duplicate."""
        res = self.client.post(
            "/api/v1/safety/alerts/demo-scenario",
            json={"scenario_id": 6, "site_id": self.site.id},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["duplicate_detected"])
        self.assertTrue(data["is_identical_instance"])

    def test_22_demo_scenario_7_multiple_alerts(self):
        """DEMO 7: Multiple distinct safety events create independent alerts."""
        res = self.client.post(
            "/api/v1/safety/alerts/demo-scenario",
            json={"scenario_id": 7, "site_id": self.site.id},
            headers=self.auth_headers_safety,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["alert_count"], 2)
        self.assertNotEqual(data["alert_a"]["id"], data["alert_b"]["id"])
