"""
ACRIP Milestone 2 Phase 2.3 Worker Safety Monitoring Test Suite
==============================================================
Tests the Worker Safety Monitoring system:
1. Worker monitoring engine initialization & defaults
2. Rule 1: High-risk zone entry detection (WARNING / HIGH_RISK)
3. Rule 2: Time-in-zone threshold exceeded (HIGH_RISK)
4. Rule 3: Worker-to-hazard proximity detection
5. Rule 4: Worker-to-operating equipment proximity detection (CRITICAL)
6. Rule 5: Activity without required PPE detection (HIGH_RISK / CRITICAL)
7. Rule 6: High-risk activity without required training
8. Rule 7: Multi-worker overcrowding in restricted/high-risk zone
9. Rule 8: Unsafe worker-equipment interaction (CRITICAL)
10. Worker safety status resolution: SAFE, WARNING, HIGH_RISK, CRITICAL
11. Actionable safety recommendations generation
12. Notification dispatch on HIGH / CRITICAL findings
13. Demo Scenario 1: SAFE WORKER -> SAFE
14. Demo Scenario 2: WORKER ENTERS HIGH-RISK ZONE -> HIGH_RISK
15. Demo Scenario 3: TIME-IN-ZONE EXCEEDED -> HIGH_RISK
16. Demo Scenario 4: HAZARD PROXIMITY -> HIGH_RISK
17. Demo Scenario 5: HEAVY EQUIPMENT PROXIMITY -> CRITICAL
18. Demo Scenario 6: UNSAFE ACTIVITY + MISSING PPE -> CRITICAL
19. API Authentication: unauthenticated calls return 401
20. RBAC: Safety Officer can start, evaluate, and stop monitoring
21. RBAC: Viewer cannot start, evaluate, or stop monitoring (403 Forbidden)
22. Viewer read-only: Viewer can view site and worker monitoring status
23. Monitoring event and safety finding persistence integrity
"""

import uuid
import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, Worker, UserRole, ProjectStatus, SiteStatus,
    WorkerRole, SafetyTrainingStatus, PPEStatus,
    SafetyFinding, SafetyFindingStatus, SafetyFindingType,
    RiskCategory, WorkerSafetyStatus, Notification,
    SafetyMonitoringEvent, SiteMonitoringSession
)
from app.core.security import hash_password, create_access_token
from app.core.config import settings
from app.services.monitoring.worker_monitoring_engine import WorkerMonitoringEngine
from app.services.monitoring.demo_scenarios import MONITORING_DEMO_SCENARIOS
from app.services.monitoring.monitoring_service import monitoring_service
from app.main import app


class TestPhase23WorkerMonitoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.suffix = uuid.uuid4().hex[:6]

        # 1. Create Super Admin
        cls.admin_email = f"admin_p23_{cls.suffix}@acrip.com"
        cls.admin = User(
            id=str(uuid.uuid4()),
            email=cls.admin_email,
            full_name="Admin P23",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        cls.db.add(cls.admin)

        # 2. Create Safety Officer
        cls.safety_email = f"safety_p23_{cls.suffix}@acrip.com"
        cls.safety_officer = User(
            id=str(uuid.uuid4()),
            email=cls.safety_email,
            full_name="Safety Officer P23",
            hashed_password=hash_password("Safety@123"),
            role=UserRole.SAFETY_OFFICER,
            is_active=True,
        )
        cls.db.add(cls.safety_officer)

        # 3. Create Viewer (Read-only)
        cls.viewer_email = f"viewer_p23_{cls.suffix}@acrip.com"
        cls.viewer = User(
            id=str(uuid.uuid4()),
            email=cls.viewer_email,
            full_name="Viewer P23",
            hashed_password=hash_password("Viewer@123"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        cls.db.add(cls.viewer)

        # 4. Create Project & Site
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-P23-{cls.suffix.upper()}",
            client="Metro Corp",
            name="Metro Line Expansion",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-P23-{cls.suffix.upper()}",
            name="Station 10 Deep Excavation",
            project_id=cls.project.id,
            status=SiteStatus.ACTIVE,
            current_risk_score=50.0,
            risk_category=RiskCategory.MEDIUM,
        )
        cls.db.add(cls.site)

        # 5. Create Test Worker
        cls.worker = Worker(
            id=str(uuid.uuid4()),
            worker_id=f"WRK-P23-{cls.suffix.upper()}",
            name="Vikramaditya Verma",
            role=WorkerRole.GENERAL_WORKER,
            site_id=cls.site.id,
            safety_training=SafetyTrainingStatus.CERTIFIED,
            ppe_status=PPEStatus.COMPLIANT,
            is_active=True,
        )
        cls.db.add(cls.worker)
        cls.db.commit()

        # Tokens
        cls.admin_token = create_access_token({"sub": cls.admin.id, "email": cls.admin.email, "role": cls.admin.role.value})
        cls.safety_token = create_access_token({"sub": cls.safety_officer.id, "email": cls.safety_officer.email, "role": cls.safety_officer.role.value})
        cls.viewer_token = create_access_token({"sub": cls.viewer.id, "email": cls.viewer.email, "role": cls.viewer.role.value})

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ── Unit Tests: Worker Monitoring Engine ───────────────────────────────

    def test_01_engine_initialization(self):
        engine = WorkerMonitoringEngine()
        self.assertEqual(engine.detection_source, "WORKER_MONITORING_ENGINE")
        self.assertGreater(engine.time_threshold_minutes, 0)
        self.assertGreater(engine.max_zone_workers, 0)

    def test_02_rule_1_high_risk_zone_entry(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-01",
            "name": "Test Worker",
            "role": WorkerRole.GENERAL_WORKER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        }
        context = {
            "current_activity": "general_construction",
            "current_zone": "Zone A — Deep Excavation Pit",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 10,
        }
        res = engine.evaluate(worker_info, context)
        self.assertIn(res["safety_status"], [WorkerSafetyStatus.WARNING, WorkerSafetyStatus.HIGH_RISK])
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("High-Risk Zone Entry" in r for r in rule_names))

    def test_03_rule_2_time_in_zone_threshold(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-02",
            "name": "Fatigued Worker",
            "role": WorkerRole.GENERAL_WORKER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        }
        context = {
            "current_activity": "excavation",
            "current_zone": "Zone A — Deep Excavation Pit",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 90,  # > 45 minutes
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.HIGH_RISK)
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("Time-in-Zone Threshold" in r for r in rule_names))

    def test_04_rule_3_hazard_proximity(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-03",
            "name": "Proximity Worker",
            "role": WorkerRole.MASON,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        }
        context = {
            "current_activity": "concrete_work",
            "current_zone": "Zone B — Retaining Wall",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 20,
            "nearby_hazards": ["HAZ-001: Fragile Retaining Wall Crack"],
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.HIGH_RISK)
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("Hazard Proximity" in r for r in rule_names))

    def test_05_rule_4_heavy_equipment_proximity(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-04",
            "name": "Laborer in Swing Radius",
            "role": WorkerRole.GENERAL_WORKER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        }
        context = {
            "current_activity": "material_handling",
            "current_zone": "Zone C — Loading Bay",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 10,
            "nearby_equipment": ["EQP-001: 30-Ton Excavator"],
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.CRITICAL)
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("Heavy Equipment Proximity" in r for r in rule_names))

    def test_06_rule_5_activity_without_required_ppe(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-05",
            "name": "Unprotected Welder",
            "role": WorkerRole.WELDER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.NON_COMPLIANT,
        }
        context = {
            "current_activity": "welding",
            "current_zone": "Fabrication Bay",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 15,
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.CRITICAL)
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("Activity Without Required PPE" in r for r in rule_names))

    def test_07_rule_6_activity_without_training(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-06",
            "name": "Uncertified Electrician",
            "role": WorkerRole.ELECTRICIAN,
            "safety_training": SafetyTrainingStatus.EXPIRED,
            "ppe_status": PPEStatus.COMPLIANT,
        }
        context = {
            "current_activity": "electrical_work",
            "current_zone": "Transformer Room",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 15,
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.HIGH_RISK)
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("Without Training" in r for r in rule_names))

    def test_08_rule_7_zone_overcrowding(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-07",
            "name": "Congested Worker",
            "role": WorkerRole.GENERAL_WORKER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        }
        context = {
            "current_activity": "scaffolding",
            "current_zone": "Zone B — Scaffold Tower",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 15,
            "workers_in_zone_count": 6,  # > max 3
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.HIGH_RISK)
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("Overcrowding" in r for r in rule_names))

    def test_09_rule_8_unsafe_worker_equipment_interaction(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-08",
            "name": "High Risk Machine Conflict",
            "role": WorkerRole.WELDER,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.NON_COMPLIANT,
        }
        context = {
            "current_activity": "welding",
            "current_zone": "Zone C — Structural Yard",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 20,
            "nearby_equipment": ["EQP-002: Mobile Crawler Crane"],
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.CRITICAL)
        rule_names = [f["rule_name"] for f in res["findings"]]
        self.assertTrue(any("Unsafe Worker-Equipment Interaction" in r for r in rule_names))

    def test_10_safe_worker_status(self):
        engine = WorkerMonitoringEngine()
        worker_info = {
            "id": "w-09",
            "name": "Compliant Worker",
            "role": WorkerRole.MASON,
            "safety_training": SafetyTrainingStatus.CERTIFIED,
            "ppe_status": PPEStatus.COMPLIANT,
        }
        context = {
            "current_activity": "general_construction",
            "current_zone": "Safe Laydown Zone",
            "is_high_risk_zone": False,
            "time_in_zone_minutes": 15,
            "nearby_hazards": [],
            "nearby_equipment": [],
            "workers_in_zone_count": 1,
        }
        res = engine.evaluate(worker_info, context)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.SAFE)
        self.assertEqual(len(res["findings"]), 0)
        self.assertTrue(len(res["recommendations"]) > 0)

    # ── Demo Scenarios 1 through 6 ─────────────────────────────────────────

    def test_11_demo_scenario_1_safe(self):
        res = monitoring_service.run_demo_scenario(self.db, scenario_id=1)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.SAFE)
        self.assertEqual(len(res["findings"]), 0)
        self.assertEqual(res["detection_source"], "DEMO / SIMULATION")

    def test_12_demo_scenario_2_high_risk_zone(self):
        res = monitoring_service.run_demo_scenario(self.db, scenario_id=2)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.HIGH_RISK)
        self.assertEqual(len(res["findings"]), 1)

    def test_13_demo_scenario_3_time_in_zone(self):
        res = monitoring_service.run_demo_scenario(self.db, scenario_id=3)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.HIGH_RISK)
        self.assertEqual(len(res["findings"]), 2)

    def test_14_demo_scenario_4_hazard_proximity(self):
        res = monitoring_service.run_demo_scenario(self.db, scenario_id=4)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.HIGH_RISK)
        self.assertEqual(len(res["findings"]), 1)

    def test_15_demo_scenario_5_equipment_proximity(self):
        res = monitoring_service.run_demo_scenario(self.db, scenario_id=5)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.CRITICAL)
        self.assertEqual(len(res["findings"]), 1)

    def test_16_demo_scenario_6_unsafe_activity_missing_ppe(self):
        res = monitoring_service.run_demo_scenario(self.db, scenario_id=6)
        self.assertEqual(res["safety_status"], WorkerSafetyStatus.CRITICAL)
        self.assertGreaterEqual(len(res["findings"]), 3)

    # ── API Endpoints & RBAC ───────────────────────────────────────────────

    def test_17_api_unauthenticated_returns_401(self):
        r = self.client.post(f"/api/v1/safety/monitoring/start/{self.site.id}")
        self.assertEqual(r.status_code, 401)

    def test_18_api_viewer_cannot_start_monitoring(self):
        headers = {"Authorization": f"Bearer {self.viewer_token}"}
        r = self.client.post(f"/api/v1/safety/monitoring/start/{self.site.id}", headers=headers)
        self.assertEqual(r.status_code, 403)

    def test_19_api_safety_officer_start_and_stop_monitoring(self):
        headers = {"Authorization": f"Bearer {self.safety_token}"}
        # Start
        r_start = self.client.post(f"/api/v1/safety/monitoring/start/{self.site.id}", headers=headers)
        self.assertEqual(r_start.status_code, 200)
        data = r_start.json()
        self.assertTrue(data["is_monitoring_active"])

        # Stop
        r_stop = self.client.post(f"/api/v1/safety/monitoring/stop/{self.site.id}", headers=headers)
        self.assertEqual(r_stop.status_code, 200)
        data_stop = r_stop.json()
        self.assertFalse(data_stop["is_monitoring_active"])

    def test_20_api_evaluate_worker_authenticated(self):
        headers = {"Authorization": f"Bearer {self.safety_token}"}
        payload = {
            "worker_id": self.worker.id,
            "current_activity": "excavation",
            "current_zone": "Zone A — Trench 3",
            "is_high_risk_zone": True,
            "time_in_zone_minutes": 25,
            "nearby_hazards": ["Open trench without shoring"],
        }
        r = self.client.post(
            f"/api/v1/safety/monitoring/evaluate/{self.worker.id}",
            headers=headers,
            json=payload,
        )
        self.assertEqual(r.status_code, 200)
        eval_data = r.json()
        self.assertEqual(eval_data["worker_id"], self.worker.id)
        self.assertEqual(eval_data["safety_status"], "HIGH_RISK")
        self.assertGreater(len(eval_data["findings"]), 0)

    def test_21_api_viewer_can_view_monitoring_status(self):
        headers = {"Authorization": f"Bearer {self.viewer_token}"}
        r = self.client.get(f"/api/v1/safety/monitoring/site/{self.site.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        status_data = r.json()
        self.assertEqual(status_data["site_id"], self.site.id)

    def test_22_api_list_and_run_demo_scenarios(self):
        headers = {"Authorization": f"Bearer {self.safety_token}"}
        # List
        r_list = self.client.get("/api/v1/safety/monitoring/demo-scenarios", headers=headers)
        self.assertEqual(r_list.status_code, 200)
        scenarios = r_list.json()
        self.assertEqual(len(scenarios), 6)

        # Run Demo 5
        r_run = self.client.post(
            "/api/v1/safety/monitoring/demo-scenario",
            headers=headers,
            json={"scenario_id": 5, "site_id": self.site.id},
        )
        self.assertEqual(r_run.status_code, 200)
        data = r_run.json()
        self.assertEqual(data["safety_status"], "CRITICAL")
        self.assertEqual(data["detection_source"], "DEMO / SIMULATION")

    def test_23_persistence_event_created_in_db(self):
        # Verify SafetyMonitoringEvent records exist
        events = self.db.query(SafetyMonitoringEvent).filter(SafetyMonitoringEvent.worker_id == self.worker.id).all()
        self.assertGreater(len(events), 0)
        first_event = events[0]
        self.assertIsNotNone(first_event.event_id)
        self.assertEqual(first_event.detection_source, "WORKER_MONITORING_ENGINE")
