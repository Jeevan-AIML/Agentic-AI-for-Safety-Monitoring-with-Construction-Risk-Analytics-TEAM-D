"""
ACRIP Milestone 3 Phase 3.1 Real-Time Video Surveillance Test Suite
===================================================================
Comprehensive tests for:
1. Video provider initialization (Base, Demo, Local, RTSP)
2. Demo stream creation
3. Stream start
4. Stream stop
5. Stream status
6. Frame validation (dimensions, payload, bounds)
7. Person detection structure (person_id, bounding_box, confidence, source)
8. PPE integration (reusing Phase 2.2 detection/compliance logic)
9. Zone detection (Safe, Excavation, Equipment, Restricted, Electrical)
10. High-risk zone event generation
11. Equipment proximity event generation
12. PPE violation event generation
13. Multiple violation event generation
14. Event persistence in database
15. AlertEngine integration (automatic CRITICAL/HIGH alert dispatch & deduplication)
16. RBAC authorization (Safety Officer & Admin full permissions)
17. Viewer restrictions (strictly read-only, 403 on mutations)
18. Demo scenario execution (DEMO 1 to DEMO 5)
19. API stream creation endpoint
20. API event retrieval endpoint
21. Invalid frame handling (malformed, negative dimensions, oversized)
22. Regression protection with Phase 2.2 (PPE detection)
23. Regression protection with Phase 2.3 (Worker monitoring)
24. Regression protection with Phase 2.4 (Alert system)
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
    RiskCategory, SafetyAlert, AlertSeverity, AlertStatus,
    CameraZone, VideoStream, VideoEvent, StreamStatus, VideoSourceType,
    VideoEventType, ZoneType
)
from app.core.security import hash_password, create_access_token
from app.services.video.providers import (
    DemoVideoProvider, LocalVideoProvider, FutureRTSPProvider
)
from app.services.video.person_detector import (
    DemoPersonDetector, CVPersonDetector
)
from app.services.video.video_pipeline import VideoAnalysisPipeline
from app.services.video.video_service import VideoSurveillanceService, video_service
from app.services.video.demo_scenarios import VIDEO_DEMO_SCENARIOS
from app.services.cv.ppe_service import PPEDetectionService
from app.services.monitoring.monitoring_service import monitoring_service
from app.services.alerts.alert_service import AlertService
from app.main import app


class TestPhase31VideoSurveillance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.suffix = uuid.uuid4().hex[:6]

        # 1. Super Admin
        cls.admin_email = f"admin_p31_{cls.suffix}@acrip.com"
        cls.admin = User(
            id=str(uuid.uuid4()),
            email=cls.admin_email,
            full_name="Admin P31",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        cls.db.add(cls.admin)

        # 2. Safety Officer
        cls.safety_email = f"safety_p31_{cls.suffix}@acrip.com"
        cls.safety_officer = User(
            id=str(uuid.uuid4()),
            email=cls.safety_email,
            full_name="Safety Officer P31",
            hashed_password=hash_password("Safety@123"),
            role=UserRole.SAFETY_OFFICER,
            is_active=True,
        )
        cls.db.add(cls.safety_officer)

        # 3. Site Manager
        cls.site_manager_email = f"sitemgr_p31_{cls.suffix}@acrip.com"
        cls.site_manager = User(
            id=str(uuid.uuid4()),
            email=cls.site_manager_email,
            full_name="Site Manager P31",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.SITE_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.site_manager)

        # 4. Project Manager
        cls.pm_email = f"pm_p31_{cls.suffix}@acrip.com"
        cls.pm = User(
            id=str(uuid.uuid4()),
            email=cls.pm_email,
            full_name="Project Manager P31",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.PROJECT_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.pm)

        # 5. Viewer (Read-only)
        cls.viewer_email = f"viewer_p31_{cls.suffix}@acrip.com"
        cls.viewer = User(
            id=str(uuid.uuid4()),
            email=cls.viewer_email,
            full_name="Viewer P31",
            hashed_password=hash_password("Viewer@123"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        cls.db.add(cls.viewer)

        # Project and Site
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-V-{cls.suffix}",
            name="Surveillance Testing Facility",
            client="Global Infra Corp",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-V-{cls.suffix}",
            name="Terminal West Platform",
            site_type="Infrastructure",
            project_id=cls.project.id,
            status=SiteStatus.ACTIVE,
            worker_count=4,
        )
        cls.db.add(cls.site)

        # Test Worker
        cls.worker = Worker(
            id=str(uuid.uuid4()),
            worker_id=f"WRK-V-{cls.suffix}",
            name="Marcus Vance",
            role=WorkerRole.OPERATOR,
            site_id=cls.site.id,
            safety_training=SafetyTrainingStatus.CERTIFIED,
            ppe_status=PPEStatus.COMPLIANT,
        )
        cls.db.add(cls.worker)

        cls.db.commit()

        # Generate JWT tokens
        cls.admin_token = create_access_token({"sub": cls.admin.id})
        cls.safety_token = create_access_token({"sub": cls.safety_officer.id})
        cls.sitemgr_token = create_access_token({"sub": cls.site_manager.id})
        cls.pm_token = create_access_token({"sub": cls.pm.id})
        cls.viewer_token = create_access_token({"sub": cls.viewer.id})

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ── Test 1: Video Provider Initialization ────────────────────────────────
    def test_01_video_provider_initialization(self):
        demo_p = DemoVideoProvider(stream_id="STRM-01", site_id="SITE-01")
        self.assertEqual(demo_p.source_type, "DEMO")
        self.assertTrue(demo_p.is_simulation)
        self.assertEqual(demo_p.label, "DEMO / SIMULATION")

        local_p = LocalVideoProvider(stream_id="STRM-02", site_id="SITE-01")
        self.assertEqual(local_p.source_type, "LOCAL")
        self.assertFalse(local_p.is_simulation)
        self.assertEqual(local_p.label, "COMPUTER_VISION")

        rtsp_p = FutureRTSPProvider(stream_id="STRM-03", site_id="SITE-01", rtsp_url="rtsp://10.0.0.1/live")
        self.assertEqual(rtsp_p.source_type, "RTSP")
        self.assertFalse(rtsp_p.is_simulation)
        self.assertEqual(rtsp_p.label, "COMPUTER_VISION")

    # ── Test 2: Demo Stream Creation ─────────────────────────────────────────
    def test_02_demo_stream_creation(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="North Gate Camera",
            source_type=VideoSourceType.DEMO,
            user_id=self.safety_officer.id,
        )
        self.assertIsNotNone(stream.id)
        self.assertTrue(stream.stream_id.startswith("STRM-"))
        self.assertEqual(stream.status, StreamStatus.ACTIVE)
        self.assertTrue(stream.is_simulation)

    # ── Test 3: Stream Start ─────────────────────────────────────────────────
    def test_03_stream_start(self):
        demo_p = DemoVideoProvider(stream_id="TEST-START", site_id="SITE-01")
        self.assertFalse(demo_p.is_active)
        started = demo_p.start()
        self.assertTrue(started)
        self.assertTrue(demo_p.is_active)
        self.assertIsNotNone(demo_p.started_at)

    # ── Test 4: Stream Stop ──────────────────────────────────────────────────
    def test_04_stream_stop(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Perimeter Camera",
            source_type=VideoSourceType.DEMO,
        )
        self.assertEqual(stream.status, StreamStatus.ACTIVE)
        stopped_stream = video_service.stop_stream(self.db, stream.stream_id)
        self.assertEqual(stopped_stream.status, StreamStatus.STOPPED)
        self.assertIsNotNone(stopped_stream.stopped_at)

    # ── Test 5: Stream Status ────────────────────────────────────────────────
    def test_05_stream_status(self):
        demo_p = DemoVideoProvider(stream_id="TEST-STATUS", site_id="SITE-01", fps=20.0)
        demo_p.start()
        status_dict = demo_p.get_status()
        self.assertEqual(status_dict["stream_id"], "TEST-STATUS")
        self.assertTrue(status_dict["is_active"])
        self.assertEqual(status_dict["fps"], 20.0)
        self.assertEqual(status_dict["label"], "DEMO / SIMULATION")

    # ── Test 6: Frame Validation ─────────────────────────────────────────────
    def test_06_frame_validation(self):
        pipeline = VideoAnalysisPipeline()

        # Valid payload
        valid_payload = {"width": 1280, "height": 720, "frame_number": 1}
        is_val, err = pipeline.validate_frame(valid_payload)
        self.assertTrue(is_val)
        self.assertIsNone(err)

        # Invalid zero dimensions
        zero_payload = {"width": 0, "height": 720}
        is_val, err = pipeline.validate_frame(zero_payload)
        self.assertFalse(is_val)
        self.assertIn("Invalid frame dimensions", err)

        # Invalid oversized dimensions (> 4K)
        huge_payload = {"width": 5000, "height": 4000}
        is_val, err = pipeline.validate_frame(huge_payload)
        self.assertFalse(is_val)
        self.assertIn("exceed maximum", err)

    # ── Test 7: Person Detection Structure ───────────────────────────────────
    def test_07_person_detection_structure(self):
        detector = DemoPersonDetector()
        frame_payload = {"timestamp": datetime.now(timezone.utc), "scenario_id": 1}
        persons = detector.detect_persons(frame_payload)

        self.assertGreater(len(persons), 0)
        p = persons[0]
        self.assertIn("person_id", p)
        self.assertIn("bounding_box", p)
        self.assertIn("confidence", p)
        self.assertIn("timestamp", p)
        self.assertEqual(p["detection_source"], "DEMO / SIMULATION")
        self.assertTrue(p["is_simulation"])
        self.assertIsInstance(p["bounding_box"], dict)
        self.assertIn("x", p["bounding_box"])

    # ── Test 8: PPE Integration ──────────────────────────────────────────────
    def test_08_ppe_integration(self):
        # Verify reuse of Phase 2.2 PPE Detection Service & compliance evaluator
        ppe_svc = PPEDetectionService()
        self.assertIsNotNone(ppe_svc.detector)
        # Test compliance evaluator
        from app.services.cv.base_detector import RawPPEDetection, BoundingBox
        det = [
            RawPPEDetection(
                detection_id="d1",
                ppe_class="HARD_HAT",
                confidence=0.92,
                bounding_box=BoundingBox(10, 10, 50, 50),
            ),
            RawPPEDetection(
                detection_id="d2",
                ppe_class="SAFETY_VEST",
                confidence=0.88,
                bounding_box=BoundingBox(10, 60, 50, 80),
            ),
        ]
        status, missing, uncertain = ppe_svc.evaluate_compliance(
            detections=det,
            required_classes=["HARD_HAT", "SAFETY_VEST"]
        )
        self.assertEqual(missing, [])
        self.assertEqual(status.value, "COMPLIANT")

    # ── Test 9: Zone Detection ───────────────────────────────────────────────
    def test_09_zone_detection(self):
        zones = video_service.ensure_default_zones(self.db, self.site.id)
        zone_names = [z.name for z in zones]
        self.assertIn("Safe Laydown Area", zone_names)
        self.assertIn("Excavation Zone", zone_names)
        self.assertIn("Heavy Equipment Zone", zone_names)
        self.assertIn("Restricted Zone", zone_names)
        self.assertIn("Electrical Work Zone", zone_names)

    # ── Test 10: High-Risk Zone Event ────────────────────────────────────────
    def test_10_high_risk_zone_event(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Excavation Cam",
            source_type=VideoSourceType.DEMO,
        )
        # Run Scenario 3 (High-Risk Zone Entry)
        res = video_service.process_frame(
            db=self.db,
            stream_id=stream.stream_id,
            scenario_id=3,
        )
        self.assertTrue(res["success"])
        zone_events = [e for e in res["events"] if e["event_type"] == "high_risk_zone_entry"]
        self.assertGreater(len(zone_events), 0)
        self.assertEqual(zone_events[0]["severity"], "high")
        self.assertEqual(zone_events[0]["zone_name"], "Excavation Zone")

    # ── Test 11: Equipment Proximity Event ───────────────────────────────────
    def test_11_equipment_proximity_event(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Heavy Machinery Cam",
            source_type=VideoSourceType.DEMO,
        )
        # Run Scenario 4 (Equipment Proximity)
        res = video_service.process_frame(
            db=self.db,
            stream_id=stream.stream_id,
            scenario_id=4,
        )
        self.assertTrue(res["success"])
        eq_events = [e for e in res["events"] if e["event_type"] == "equipment_proximity"]
        self.assertGreater(len(eq_events), 0)
        self.assertEqual(eq_events[0]["severity"], "critical")
        self.assertIn("CAT 320", eq_events[0]["evidence"])

    # ── Test 12: PPE Violation Event ─────────────────────────────────────────
    def test_12_ppe_violation_event(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Gate Cam",
            source_type=VideoSourceType.DEMO,
        )
        # Run Scenario 2 (Missing Hard Hat)
        res = video_service.process_frame(
            db=self.db,
            stream_id=stream.stream_id,
            scenario_id=2,
        )
        self.assertTrue(res["success"])
        ppe_events = [e for e in res["events"] if e["event_type"] == "ppe_violation"]
        self.assertGreater(len(ppe_events), 0)
        self.assertIn("HARD_HAT", ppe_events[0]["missing_ppe"])

    # ── Test 13: Multiple Violation Event ────────────────────────────────────
    def test_13_multiple_violation_event(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Trench Cam",
            source_type=VideoSourceType.DEMO,
        )
        # Run Scenario 5 (Compound Violations: Missing PPE + High-Risk Zone + Equipment + Hazard)
        res = video_service.process_frame(
            db=self.db,
            stream_id=stream.stream_id,
            scenario_id=5,
        )
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["violations_count"], 3)
        self.assertGreaterEqual(res["findings_created"], 3)
        self.assertGreaterEqual(res["alerts_created"], 1)

    # ── Test 14: Event Persistence ───────────────────────────────────────────
    def test_14_event_persistence(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Persistence Cam",
            source_type=VideoSourceType.DEMO,
        )
        res = video_service.process_frame(
            db=self.db,
            stream_id=stream.stream_id,
            scenario_id=3,
        )
        event_id = res["events"][0]["event_id"]
        persisted = self.db.query(VideoEvent).filter(VideoEvent.event_id == event_id).first()
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.stream_id, stream.id)
        self.assertEqual(persisted.site_id, self.site.id)

    # ── Test 15: AlertEngine Integration ─────────────────────────────────────
    def test_15_alert_engine_integration(self):
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Alert Integration Cam",
            source_type=VideoSourceType.DEMO,
        )
        # Equipment proximity triggers a CRITICAL SafetyFinding -> AlertEngine creates SafetyAlert
        res = video_service.process_frame(
            db=self.db,
            stream_id=stream.stream_id,
            scenario_id=4,
        )
        self.assertGreater(res["alerts_created"], 0)
        self.db.expire_all()
        # Check DB for created alert
        alert = (
            self.db.query(SafetyAlert)
            .filter(SafetyAlert.site_id == self.site.id, SafetyAlert.severity == AlertSeverity.CRITICAL)
            .first()
        )
        self.assertIsNotNone(alert)
        self.assertIn("Equipment Proximity", alert.title)

    # ── Test 16: RBAC Authorization ──────────────────────────────────────────
    def test_16_rbac_authorization(self):
        # Safety Officer starts a stream -> 201 Created
        resp = self.client.post(
            "/api/v1/safety/video/streams/start",
            headers={"Authorization": f"Bearer {self.safety_token}"},
            json={
                "site_id": self.site.id,
                "camera_name": "Safety Officer Camera",
                "source_type": "demo",
            },
        )
        self.assertEqual(resp.status_code, 201)
        strm_id = resp.json()["stream_id"]

        # Super Admin stops the stream -> 200 OK
        resp_stop = self.client.post(
            f"/api/v1/safety/video/streams/stop/{strm_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(resp_stop.status_code, 200)

    # ── Test 17: Viewer Restrictions ─────────────────────────────────────────
    def test_17_viewer_restrictions(self):
        # Viewer tries to start stream -> 403 Forbidden
        resp_start = self.client.post(
            "/api/v1/safety/video/streams/start",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
            json={"site_id": self.site.id, "camera_name": "Viewer Camera"},
        )
        self.assertEqual(resp_start.status_code, 403)

        # Viewer tries to process frame -> 403 Forbidden
        resp_proc = self.client.post(
            "/api/v1/safety/video/streams/STRM-DUMMY/process-frame",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
            json={},
        )
        self.assertEqual(resp_proc.status_code, 403)

        # Viewer can READ streams -> 200 OK
        resp_get = self.client.get(
            "/api/v1/safety/video/streams",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(resp_get.status_code, 200)

    # ── Test 18: Demo Scenario Execution ─────────────────────────────────────
    def test_18_demo_scenario_execution(self):
        for scen_id in range(1, 6):
            res = video_service.run_demo_scenario(
                db=self.db,
                scenario_id=scen_id,
                site_id=self.site.id,
                user_id=self.safety_officer.id,
            )
            self.assertEqual(res["scenario"]["id"], scen_id)
            self.assertTrue(res["result"]["success"])
            self.assertEqual(res["result"]["detection_source"], "DEMO / SIMULATION")
            self.assertTrue(res["result"]["is_simulation"])

    # ── Test 19: API Stream Creation ─────────────────────────────────────────
    def test_19_api_stream_creation(self):
        resp = self.client.post(
            "/api/v1/safety/video/streams/start",
            headers={"Authorization": f"Bearer {self.sitemgr_token}"},
            json={
                "site_id": self.site.id,
                "camera_name": "Site Manager Crane Cam",
                "source_type": "demo",
                "fps": 30.0,
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["camera_name"], "Site Manager Crane Cam")
        self.assertEqual(data["fps"], 30.0)
        self.assertEqual(data["status"], "active")

    # ── Test 20: API Event Retrieval ─────────────────────────────────────────
    def test_20_api_event_retrieval(self):
        # Create stream and process frame
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Retrieval Cam",
            source_type=VideoSourceType.DEMO,
        )
        video_service.process_frame(
            db=self.db,
            stream_id=stream.stream_id,
            scenario_id=1,
        )
        # Fetch events via API
        resp = self.client.get(
            f"/api/v1/safety/video/streams/{stream.stream_id}/events",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        events = resp.json()
        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)

    # ── Test 21: Invalid Frame Handling ──────────────────────────────────────
    def test_21_invalid_frame_handling(self):
        pipeline = VideoAnalysisPipeline()
        stream = video_service.start_stream(
            db=self.db,
            site_id=self.site.id,
            camera_name="Invalid Frame Cam",
            source_type=VideoSourceType.DEMO,
        )
        # Pass empty payload
        res = pipeline.process_frame(
            db=self.db,
            stream=stream,
            frame_payload={},
        )
        self.assertFalse(res["success"])
        self.assertIn("empty", res["error"])

    # ── Test 22: Regression with Phase 2.2 ────────────────────────────────────
    def test_22_regression_with_phase2_2_ppe(self):
        # Verify Phase 2.2 PPE demo scenarios remain 100% operational
        resp = self.client.get(
            "/api/v1/safety/ppe/demo-scenarios",
            headers={"Authorization": f"Bearer {self.safety_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        scenarios = resp.json()
        self.assertEqual(len(scenarios), 5)

    # ── Test 23: Regression with Phase 2.3 ────────────────────────────────────
    def test_23_regression_with_phase2_3_monitoring(self):
        # Verify Phase 2.3 worker safety monitoring engine is intact
        resp = self.client.get(
            f"/api/v1/safety/monitoring/site/{self.site.id}",
            headers={"Authorization": f"Bearer {self.safety_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("is_monitoring_active", data)

    # ── Test 24: Regression with Phase 2.4 ────────────────────────────────────
    def test_24_regression_with_phase2_4_alerts(self):
        # Verify Phase 2.4 alert listing and demo scenarios remain intact
        resp = self.client.get(
            "/api/v1/safety/alerts/demo-scenarios",
            headers={"Authorization": f"Bearer {self.safety_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        scenarios = resp.json()
        self.assertEqual(len(scenarios), 7)
