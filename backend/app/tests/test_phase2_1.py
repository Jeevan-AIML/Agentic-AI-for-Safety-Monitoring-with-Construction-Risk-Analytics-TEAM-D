"""
ACRIP Milestone 2 Phase 2.1 Safety Agent Integration & Hardening Test Suite
==========================================================================
Tests the specialized Safety Agent:
1.  SafetyAgent initialization, health check, orchestrator status
2.  BaseSafetyAnalyzer & RuleBasedSafetyAnalyzer deterministic execution
3.  Worker retrieval & real database context aggregation
4.  Rule 1: PPE violation detection (HIGH during construction, MEDIUM routine)
5.  Rule 2: Expired training detection & actionable recommendation
6.  Rule 3: Missing training for specialized activity (welder/electrician/excavation)
7.  Rule 4: Unsafe equipment operation (CRITICAL severity, unauthorized operator)
8.  Rule 5: High-risk activity without controls (HIGH / CRITICAL severity)
9.  Rule 6: High-risk zone exposure (Worker in HIGH/CRITICAL site with deficient PPE/training)
10. Deterministic severity calculation (LOW, MEDIUM, HIGH, CRITICAL)
11. Safety recommendation generation for HIGH and CRITICAL findings
12. SafetyFinding & SafetyAnalysis database persistence
13. API Authentication & valid JWT token verification
14. RBAC enforcement (Safety Officer, Site Manager, PM, Super Admin allowed; Viewer blocked with 403)
15. All 5 deterministic demo scenarios (Compliant, PPE Violation, Expired Training, Unsafe Equipment, High-Risk Activity)
16. Safety Notifications generation for HIGH/CRITICAL & deduplication
17. Finding lifecycle transitions (OPEN -> ACKNOWLEDGED -> MITIGATED -> CLOSED)
"""

import uuid
import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, Worker, Equipment, Activity, Hazard, RiskScore,
    Notification, UserRole, ProjectStatus, SiteStatus,
    RiskCategory, WorkerRole, SafetyTrainingStatus, PPEStatus, EquipmentStatus,
    ActivityType, HazardType, NotificationCategory,
    SafetyFinding, SafetyAnalysis, SafetyFindingStatus, SafetyFindingType
)
from app.core.security import hash_password, create_access_token
from app.agents.safety_agent import (
    SafetyAgent, RuleBasedSafetyAnalyzer, safety_agent, SAFETY_DEMO_SCENARIOS
)
from app.agents.base_agents import orchestrator
from app.seed import seed_database
from app.main import app


class TestPhase21SafetyAgent(unittest.TestCase):
    """Test suite for Milestone 2 Phase 2.1 Safety Agent."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        db = SessionLocal()

        # Ensure seed data exists
        try:
            seed_database()
        except Exception:
            pass

        # Query users for RBAC testing
        cls.admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        cls.pm = db.query(User).filter(User.role == UserRole.PROJECT_MANAGER).first()
        cls.sm = db.query(User).filter(User.role == UserRole.SITE_MANAGER).first()
        cls.safety_officer = db.query(User).filter(User.role == UserRole.SAFETY_OFFICER).first()
        cls.viewer = db.query(User).filter(User.role == UserRole.VIEWER).first()

        cls.site = db.query(Site).first()
        cls.site_id = str(cls.site.id)

        # Worker for individual testing
        cls.test_worker = db.query(Worker).filter(Worker.site_id == cls.site.id).first()
        cls.worker_id = str(cls.test_worker.id)

        # Generate auth tokens
        cls.tokens = {
            "admin": create_access_token({"sub": cls.admin.id, "role": cls.admin.role.value}),
            "pm": create_access_token({"sub": cls.pm.id, "role": cls.pm.role.value}),
            "sm": create_access_token({"sub": cls.sm.id, "role": cls.sm.role.value}),
            "safety": create_access_token({"sub": cls.safety_officer.id, "role": cls.safety_officer.role.value}),
            "viewer": create_access_token({"sub": cls.viewer.id, "role": cls.viewer.role.value}),
        }
        cls.headers = {role: {"Authorization": f"Bearer {token}"} for role, token in cls.tokens.items()}
        db.close()

    # ── 1. SafetyAgent Initialization & Health Check ────────────────────────

    def test_01_safety_agent_initialization(self):
        """Verify SafetyAgent is active, has correct version, and analyzer is RuleBasedSafetyAnalyzer."""
        agent = SafetyAgent()
        self.assertEqual(agent.agent_id, "safety_agent_v1")
        self.assertEqual(agent.name, "Safety Agent")
        self.assertTrue(agent.is_active)
        self.assertEqual(agent.analyzer.__class__.__name__, "RuleBasedSafetyAnalyzer")
        status = agent.get_status()
        self.assertEqual(status["detection_source"], "RULE_ENGINE")
        self.assertEqual(status["rules_count"], 6)

    def test_02_orchestrator_safety_agent_active(self):
        """Verify orchestrator registers safety agent as active in Phase 2.1."""
        all_statuses = orchestrator.get_all_statuses()
        self.assertIn("safety", all_statuses)
        self.assertTrue(all_statuses["safety"]["is_active"])
        self.assertEqual(all_statuses["safety"]["status"], "active")

    # ── 2. Rule-Based Safety Rules (Rules 1 - 6) ────────────────────────────

    def test_03_rule_1_ppe_violation(self):
        """Rule 1: Incomplete/non-compliant PPE generates HIGH finding during active construction."""
        analyzer = RuleBasedSafetyAnalyzer()
        context = {
            "site_id": "test-site",
            "site_name": "Test Tower",
            "workers": [{
                "id": "w1",
                "worker_id": "WRK-001",
                "name": "Arun Kumar",
                "role": "mason",
                "safety_training": "certified",
                "ppe_status": "non_compliant",
            }],
            "activities": [{"activity_type": "concrete_work"}],
            "equipment": [],
            "site_risk_score": 50.0,
            "site_risk_category": "medium",
        }
        res = analyzer.analyze(context)
        self.assertEqual(res["violation_count"], 1)
        finding = res["findings"][0]
        self.assertEqual(finding["finding_type"], SafetyFindingType.PPE_VIOLATION)
        self.assertEqual(finding["severity"], RiskCategory.HIGH)
        self.assertIn("PPE status 'NON_COMPLIANT'", finding["evidence"])
        self.assertIn("Stop worker entry", finding["recommendation"])
        self.assertEqual(finding["detection_source"], "RULE_ENGINE")

    def test_04_rule_2_expired_training(self):
        """Rule 2: Expired safety training generates finding with renewal recommendation."""
        analyzer = RuleBasedSafetyAnalyzer()
        context = {
            "site_id": "test-site",
            "site_name": "Test Tower",
            "workers": [{
                "id": "w2",
                "worker_id": "WRK-002",
                "name": "Suresh Babu",
                "role": "electrician",
                "safety_training": "expired",
                "ppe_status": "compliant",
            }],
            "activities": [{"activity_type": "electrical_work"}],
            "equipment": [],
            "site_risk_score": 40.0,
            "site_risk_category": "medium",
        }
        res = analyzer.analyze(context)
        self.assertEqual(res["violation_count"], 1)
        finding = res["findings"][0]
        self.assertEqual(finding["finding_type"], SafetyFindingType.EXPIRED_TRAINING)
        self.assertEqual(finding["severity"], RiskCategory.HIGH)  # Specialized role -> HIGH
        self.assertIn("EXPIRED", finding["evidence"])
        self.assertIn("Restrict assignment", finding["recommendation"])

    def test_05_rule_3_missing_training(self):
        """Rule 3: Missing/not started training for specialized role triggers HIGH finding."""
        analyzer = RuleBasedSafetyAnalyzer()
        context = {
            "site_id": "test-site",
            "site_name": "Test Tower",
            "workers": [{
                "id": "w3",
                "worker_id": "WRK-003",
                "name": "Ravi Welder",
                "role": "welder",
                "safety_training": "not_started",
                "ppe_status": "compliant",
            }],
            "activities": [{"activity_type": "welding"}],
            "equipment": [],
            "site_risk_score": 30.0,
            "site_risk_category": "low",
        }
        res = analyzer.analyze(context)
        self.assertEqual(res["violation_count"], 1)
        finding = res["findings"][0]
        self.assertEqual(finding["finding_type"], SafetyFindingType.MISSING_TRAINING)
        self.assertEqual(finding["severity"], RiskCategory.HIGH)
        self.assertIn("NOT_STARTED", finding["evidence"])
        self.assertIn("Reassign worker away", finding["recommendation"])

    def test_06_rule_4_unsafe_equipment_operation(self):
        """Rule 4: Worker operating equipment with invalid training triggers CRITICAL finding."""
        analyzer = RuleBasedSafetyAnalyzer()
        context = {
            "site_id": "test-site",
            "site_name": "Test Tower",
            "workers": [{
                "id": "w4",
                "worker_id": "WRK-004",
                "name": "Kiran Operator",
                "role": "operator",
                "safety_training": "expired",
                "ppe_status": "compliant",
            }],
            "activities": [{"activity_type": "material_handling"}],
            "equipment": [{
                "name": "Excavator EX-01",
                "equipment_type": "Excavator",
                "operator_name": "Kiran Operator",
                "status": "operational",
            }],
            "site_risk_score": 50.0,
            "site_risk_category": "medium",
        }
        res = analyzer.analyze(context)
        # Expected: Expired Training (Rule 2) + Unsafe Equipment Operation (Rule 4)
        crit_findings = [f for f in res["findings"] if f["finding_type"] == SafetyFindingType.UNSAFE_EQUIPMENT_OPERATION]
        self.assertEqual(len(crit_findings), 1)
        eq_finding = crit_findings[0]
        self.assertEqual(eq_finding["severity"], RiskCategory.CRITICAL)
        self.assertIn("Excavator EX-01", eq_finding["evidence"])
        self.assertIn("Stop equipment operation", eq_finding["recommendation"])

    def test_07_rule_5_high_risk_activity(self):
        """Rule 5: High risk activity (welding/excavation) without compliant controls triggers finding."""
        analyzer = RuleBasedSafetyAnalyzer()
        context = {
            "site_id": "test-site",
            "site_name": "Test Tower",
            "workers": [{
                "id": "w5",
                "worker_id": "WRK-005",
                "name": "Mohan Lal",
                "role": "welder",
                "safety_training": "in_progress",
                "ppe_status": "non_compliant",
            }],
            "activities": [{"activity_type": "welding"}],
            "equipment": [],
            "site_risk_score": 60.0,
            "site_risk_category": "medium",
        }
        res = analyzer.analyze(context)
        hr_findings = [f for f in res["findings"] if f["finding_type"] == SafetyFindingType.HIGH_RISK_ACTIVITY]
        self.assertEqual(len(hr_findings), 1)
        self.assertEqual(hr_findings[0]["severity"], RiskCategory.CRITICAL)  # both PPE and training deficient

    def test_08_rule_6_high_risk_zone_exposure(self):
        """Rule 6: Worker on high risk site with deficient safeguards triggers zone exposure finding."""
        analyzer = RuleBasedSafetyAnalyzer()
        context = {
            "site_id": "test-site",
            "site_name": "Deep Foundation Section",
            "workers": [{
                "id": "w6",
                "worker_id": "WRK-006",
                "name": "Bhaskar Rao",
                "role": "general_worker",
                "safety_training": "expired",
                "ppe_status": "compliant",
            }],
            "activities": [{"activity_type": "general_construction"}],
            "equipment": [],
            "site_risk_score": 82.0,  # CRITICAL site risk score
            "site_risk_category": "critical",
        }
        res = analyzer.analyze(context)
        zone_findings = [f for f in res["findings"] if f["finding_type"] == SafetyFindingType.HIGH_RISK_ZONE_EXPOSURE]
        self.assertEqual(len(zone_findings), 1)
        self.assertEqual(zone_findings[0]["severity"], RiskCategory.CRITICAL)
        self.assertIn("Restrict access", zone_findings[0]["recommendation"])

    # ── 3. All 5 Deterministic Demo Scenarios ────────────────────────────────

    def test_09_all_5_demo_scenarios_deterministic(self):
        """Verify all 5 demo scenarios produce expected deterministic severity and findings."""
        analyzer = RuleBasedSafetyAnalyzer()

        for s_id, s_data in SAFETY_DEMO_SCENARIOS.items():
            context = dict(s_data["input"])
            context["site_id"] = f"scenario-{s_id}"
            context["site_name"] = f"Scenario {s_id} Site"
            res = analyzer.analyze(context)

            self.assertEqual(
                res["safety_level"], s_data["expected_level"],
                f"Scenario {s_id} failed level: expected {s_data['expected_level']}, got {res['safety_level']}"
            )
            self.assertEqual(
                res["violation_count"], s_data["expected_violations"],
                f"Scenario {s_id} failed count: expected {s_data['expected_violations']}, got {res['violation_count']}"
            )

    # ── 4. Database Persistence and Notifications ───────────────────────────

    def test_10_analyze_and_persist_workflow(self):
        """Verify SafetyAgent.analyze_and_persist saves SafetyAnalysis and SafetyFinding entities."""
        db = SessionLocal()
        initial_analyses = db.query(SafetyAnalysis).count()
        initial_findings = db.query(SafetyFinding).count()

        result = safety_agent.analyze_and_persist(
            db=db,
            site_id=self.site_id,
            source_label="unit_test_run"
        )

        self.assertIn("overall_safety_score", result)
        self.assertIn("analysis_id", result)
        self.assertEqual(result["detection_source"], "RULE_ENGINE")

        new_analyses = db.query(SafetyAnalysis).count()
        self.assertEqual(new_analyses, initial_analyses + 1)

        saved_analysis = db.query(SafetyAnalysis).filter(SafetyAnalysis.id == result["id"]).first()
        self.assertIsNotNone(saved_analysis)
        self.assertEqual(saved_analysis.site_id, self.site_id)
        db.close()

    def test_11_high_critical_notifications_generated_and_deduplicated(self):
        """Verify HIGH/CRITICAL findings generate Notifications and prevent duplicates."""
        db = SessionLocal()
        # Custom input with a critical finding
        custom_input = {
            "workers": [{
                "id": self.worker_id,
                "worker_id": "WRK-CRIT",
                "name": "Operator Alert Test",
                "role": "operator",
                "safety_training": "expired",
                "ppe_status": "non_compliant",
            }],
            "equipment": [{
                "name": "Critical Test Crane",
                "equipment_type": "Crane",
                "operator_name": "Operator Alert Test",
                "status": "operational",
            }],
            "activities": [{"activity_type": "material_handling"}],
        }

        # Run 1: Should create notifications
        res1 = safety_agent.analyze_and_persist(db=db, site_id=self.site_id, custom_input=custom_input)
        notifs_count_1 = db.query(Notification).filter(Notification.category == NotificationCategory.SAFETY).count()
        self.assertGreater(notifs_count_1, 0)

        # Run 2 with same context: Deduplication should prevent duplicate unread alerts
        res2 = safety_agent.analyze_and_persist(db=db, site_id=self.site_id, custom_input=custom_input)
        notifs_count_2 = db.query(Notification).filter(Notification.category == NotificationCategory.SAFETY).count()
        self.assertEqual(notifs_count_1, notifs_count_2)
        db.close()

    # ── 5. API Endpoints & RBAC Verification ─────────────────────────────────

    def test_12_api_analyze_site_success_for_safety_officer(self):
        """Verify Safety Officer can trigger site safety analysis via API."""
        res = self.client.post(
            f"/api/v1/safety/analyze/site/{self.site_id}",
            headers=self.headers["safety"]
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("overall_safety_score", data)
        self.assertIn("findings", data)
        self.assertEqual(data["detection_source"], "RULE_ENGINE")

    def test_13_api_analyze_site_forbidden_for_viewer(self):
        """Verify Viewer role is blocked (403 Forbidden) from executing safety analysis."""
        res = self.client.post(
            f"/api/v1/safety/analyze/site/{self.site_id}",
            headers=self.headers["viewer"]
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access denied", res.json()["detail"])

    def test_14_api_get_site_summary_accessible_to_viewer(self):
        """Verify Viewer can READ safety summaries without restriction."""
        res = self.client.get(
            f"/api/v1/safety/site/{self.site_id}",
            headers=self.headers["viewer"]
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["site_id"], self.site_id)
        self.assertIn("open_findings_count", data)

    def test_15_api_get_findings_filters(self):
        """Verify GET /safety/site/{id}/findings returns findings with status filtering."""
        res = self.client.get(
            f"/api/v1/safety/site/{self.site_id}/findings?status=open",
            headers=self.headers["pm"]
        )
        self.assertEqual(res.status_code, 200)
        findings = res.json()
        self.assertIsInstance(findings, list)
        for f in findings:
            self.assertEqual(f["status"], "open")

    def test_16_api_demo_scenarios_list_and_run(self):
        """Verify listing and executing demo scenario via API."""
        # List demo scenarios
        list_res = self.client.get("/api/v1/safety/demo-scenarios", headers=self.headers["viewer"])
        self.assertEqual(list_res.status_code, 200)
        scenarios = list_res.json()
        self.assertEqual(len(scenarios), 5)

        # Run Scenario 4 (Unsafe Equipment Operation)
        run_res = self.client.post(
            "/api/v1/safety/demo-scenario",
            headers=self.headers["safety"],
            json={"site_id": self.site_id, "scenario_id": 4}
        )
        self.assertEqual(run_res.status_code, 200)
        result = run_res.json()
        self.assertEqual(result["safety_level"], "critical")
        self.assertGreaterEqual(result["critical_count"], 1)

    def test_17_api_finding_lifecycle_transitions(self):
        """Verify finding lifecycle: OPEN -> ACKNOWLEDGED -> MITIGATED -> CLOSED."""
        db = SessionLocal()
        # Find or create an open finding
        finding = db.query(SafetyFinding).filter(SafetyFinding.status == SafetyFindingStatus.OPEN).first()
        if not finding:
            finding = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id="SAF-TEST-01",
                site_id=self.site_id,
                finding_type=SafetyFindingType.PPE_VIOLATION,
                description="Test finding for lifecycle",
                severity=RiskCategory.MEDIUM,
                status=SafetyFindingStatus.OPEN,
                detection_source="RULE_ENGINE",
            )
            db.add(finding)
            db.commit()
        finding_id = finding.id
        db.close()

        # Step 1: Acknowledge
        res_ack = self.client.patch(
            f"/api/v1/safety/findings/{finding_id}",
            headers=self.headers["safety"],
            json={"status": "acknowledged"}
        )
        self.assertEqual(res_ack.status_code, 200)
        self.assertEqual(res_ack.json()["status"], "acknowledged")
        self.assertIsNotNone(res_ack.json()["acknowledged_at"])

        # Step 2: Mitigate with notes
        res_mit = self.client.patch(
            f"/api/v1/safety/findings/{finding_id}",
            headers=self.headers["sm"],
            json={"status": "mitigated", "mitigation_notes": "Supervisor verified replacement PPE"}
        )
        self.assertEqual(res_mit.status_code, 200)
        self.assertEqual(res_mit.json()["status"], "mitigated")
        self.assertEqual(res_mit.json()["mitigation_notes"], "Supervisor verified replacement PPE")

        # Step 3: Close
        res_close = self.client.patch(
            f"/api/v1/safety/findings/{finding_id}",
            headers=self.headers["admin"],
            json={"status": "closed"}
        )
        self.assertEqual(res_close.status_code, 200)
        self.assertEqual(res_close.json()["status"], "closed")

        # Step 4: Verify invalid transition from CLOSED
        res_invalid = self.client.patch(
            f"/api/v1/safety/findings/{finding_id}",
            headers=self.headers["safety"],
            json={"status": "open"}
        )
        self.assertEqual(res_invalid.status_code, 400)
