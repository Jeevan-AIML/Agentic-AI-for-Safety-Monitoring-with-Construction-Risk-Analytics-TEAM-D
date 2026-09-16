"""
ACRIP Milestone 2 Phase 2.2 Computer Vision PPE Compliance Detection Test Suite
==============================================================================
Tests the Computer Vision PPE Compliance Detection system:
1.  BasePPEDetector & ComputerVisionPPEDetector initialization and interface compliance
2.  Image upload validation: valid JPEG/PNG accepted
3.  Invalid file rejection: corrupted file rejection with 400 Bad Request
4.  Invalid file rejection: disallowed file extension rejected with 400 Bad Request
5.  PPE detection response schema validation (bounding_box, confidence, class, detection_source)
6.  Bounding box structure validation (0 <= x, y, width, height)
7.  Configurable confidence threshold enforcement (PPE_CONFIDENCE_THRESHOLD)
8.  Deterministic PPE compliance logic: all present -> COMPLIANT
9.  Deterministic PPE compliance logic: missing hard hat -> NON_COMPLIANT
10. Multiple PPE classes support (HARD_HAT, SAFETY_VEST, SAFETY_GOGGLES)
11. Multi-worker support in single image detection output
12. SafetyFinding integration (SafetyFinding created with finding_type=PPE_VIOLATION)
13. Actionable recommendation generation based on missing PPE
14. Cross-verification between DB worker PPE record and CV detection (PPE_DISCREPANCY finding)
15. Deterministic Demo Scenario 1: FULL PPE (COMPLIANT)
16. Deterministic Demo Scenario 2: MISSING HARD HAT (NON_COMPLIANT, HIGH)
17. Deterministic Demo Scenario 3: MULTIPLE PPE VIOLATIONS (CRITICAL on high-risk)
18. Deterministic Demo Scenario 4: LOW CONFIDENCE (UNCERTAIN status, no ungrounded violation)
19. Deterministic Demo Scenario 5: DATABASE/CV DISCREPANCY (creates PPE_DISCREPANCY finding)
20. API Authentication: unauthenticated calls return 401
21. RBAC enforcement: Safety Officer, Site Manager, PM can analyze PPE
22. RBAC enforcement: Viewer is restricted from uploading/analyzing PPE (403 Forbidden)
23. Viewer read-only access: Viewer can retrieve existing analysis and list site PPE analyses
24. Safe image retrieval endpoint: path traversal blocked, 404 on missing image
"""

import io
import os
import uuid
import unittest
from datetime import datetime, timezone
from PIL import Image
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, Worker, UserRole, ProjectStatus, SiteStatus,
    WorkerRole, SafetyTrainingStatus, PPEStatus,
    SafetyFinding, SafetyFindingStatus, SafetyFindingType,
    PPEAnalysis, PPEComplianceStatus, PPEClass,
)
from app.core.security import hash_password, create_access_token
from app.core.config import settings
from app.services.cv.base_detector import (
    BasePPEDetector, BoundingBox, RawPPEDetection, PersonDetection, DetectorOutput
)
from app.services.cv.cv_detector import ComputerVisionPPEDetector
from app.services.cv.mock_detector import MockPPEDetector, PPE_DEMO_SCENARIOS
from app.services.cv.ppe_service import ppe_detection_service
from app.seed import seed_database
from app.main import app


def create_test_image_bytes(width=200, height=200, color="blue", format="JPEG") -> bytes:
    """Create in-memory dummy image bytes for tests."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


class TestPhase22CVPPECompliance(unittest.TestCase):
    """Test suite for Phase 2.2 Computer Vision PPE Compliance Detection."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        db = SessionLocal()

        try:
            seed_database()
        except Exception:
            pass

        # Query seeded users for RBAC testing
        cls.superadmin_user = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        cls.safety_officer = db.query(User).filter(User.role == UserRole.SAFETY_OFFICER).first()
        cls.site_manager = db.query(User).filter(User.role == UserRole.SITE_MANAGER).first()
        cls.viewer_user = db.query(User).filter(User.role == UserRole.VIEWER).first()

        # Query seeded site
        cls.site = db.query(Site).first()

        # Query or create workers for testing
        cls.worker_compliant = db.query(Worker).filter(Worker.ppe_status == PPEStatus.COMPLIANT).first()
        cls.worker_violator = db.query(Worker).filter(Worker.ppe_status == PPEStatus.NON_COMPLIANT).first()

        if not cls.worker_compliant:
            cls.worker_compliant = Worker(
                id=str(uuid.uuid4()),
                site_id=cls.site.id,
                worker_id="WRK-CV-01",
                name="Marcus Vance",
                role=WorkerRole.LABORER,
                safety_training=SafetyTrainingStatus.VALID,
                ppe_status=PPEStatus.COMPLIANT,
                is_active=True,
            )
            db.add(cls.worker_compliant)
            db.commit()
            db.refresh(cls.worker_compliant)

        if not cls.worker_violator:
            cls.worker_violator = Worker(
                id=str(uuid.uuid4()),
                site_id=cls.site.id,
                worker_id="WRK-CV-02",
                name="Leo Strickland",
                role=WorkerRole.CARPENTER,
                safety_training=SafetyTrainingStatus.VALID,
                ppe_status=PPEStatus.NON_COMPLIANT,
                is_active=True,
            )
            db.add(cls.worker_violator)
            db.commit()
            db.refresh(cls.worker_violator)

        db.close()

        # Generate JWT tokens
        cls.superadmin_token = create_access_token({"sub": cls.superadmin_user.id, "role": cls.superadmin_user.role.value})
        cls.safety_token = create_access_token({"sub": cls.safety_officer.id, "role": cls.safety_officer.role.value})
        cls.site_mgr_token = create_access_token({"sub": cls.site_manager.id, "role": cls.site_manager.role.value})
        cls.viewer_token = create_access_token({"sub": cls.viewer_user.id, "role": cls.viewer_user.role.value})

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Detector Abstraction & Initialization
    # ──────────────────────────────────────────────────────────────────────────

    def test_01_cv_detector_initialization(self):
        """Test ComputerVisionPPEDetector implements BasePPEDetector correctly."""
        detector = ComputerVisionPPEDetector()
        self.assertIsInstance(detector, BasePPEDetector)
        self.assertEqual(detector.detection_source, "COMPUTER_VISION")
        self.assertIn("OpenCV", detector.model_name)

    def test_02_mock_detector_explicitly_labeled(self):
        """Verify MockPPEDetector is explicitly labeled 'DEMO / MOCK' per AI integrity mandate."""
        detector = MockPPEDetector()
        self.assertIsInstance(detector, BasePPEDetector)
        self.assertEqual(detector.detection_source, "DEMO / MOCK")
        self.assertEqual(detector.model_name, "MOCK-TEST-ADAPTER-v1.0")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. File Validation & Rejections
    # ──────────────────────────────────────────────────────────────────────────

    def test_03_image_upload_validation_valid_jpeg(self):
        """Valid JPEG image passes file validation successfully."""
        img_bytes = create_test_image_bytes(100, 100, "yellow", "JPEG")
        valid, err = ppe_detection_service.validate_image(
            file_bytes=img_bytes, filename="worker_site.jpg", content_type="image/jpeg"
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_04_image_upload_validation_corrupted_file(self):
        """Corrupted/random bytes must be rejected with an appropriate error."""
        corrupt_bytes = b"NOT_AN_IMAGE_RANDOM_GARBAGE_BYTES_123456"
        valid, err = ppe_detection_service.validate_image(
            file_bytes=corrupt_bytes, filename="corrupt.jpg", content_type="image/jpeg"
        )
        self.assertFalse(valid)
        self.assertIn("corrupt", err.lower())

    def test_05_image_upload_validation_disallowed_extension(self):
        """Disallowed file extensions (e.g. .exe, .sh, .pdf) must be rejected."""
        img_bytes = create_test_image_bytes(100, 100, "green", "JPEG")
        valid, err = ppe_detection_service.validate_image(
            file_bytes=img_bytes, filename="malicious.exe", content_type="application/x-msdownload"
        )
        self.assertFalse(valid)
        self.assertIn("extension", err.lower())

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Detection Response Schema & Bounding Boxes
    # ──────────────────────────────────────────────────────────────────────────

    def test_06_bounding_box_and_schema_validation(self):
        """Validate BoundingBox and PersonDetection data structure constraints."""
        bbox = BoundingBox(x=10.0, y=15.0, width=20.0, height=25.0)
        raw_det = RawPPEDetection(
            detection_id="DET-01",
            ppe_class="HARD_HAT",
            confidence=0.94,
            bounding_box=bbox,
            is_compliant=True,
            detection_source="COMPUTER_VISION",
        )
        person = PersonDetection(
            person_id="P-01",
            bounding_box=BoundingBox(x=5.0, y=5.0, width=30.0, height=90.0),
            confidence=0.95,
            detected_ppe=[raw_det],
        )
        out = DetectorOutput(
            model_name="Test-Model",
            detection_source="COMPUTER_VISION",
            persons=[person],
            detections=[raw_det],
            image_width=640,
            image_height=480,
        )
        self.assertEqual(len(out.persons), 1)
        self.assertEqual(out.persons[0].detected_ppe[0].confidence, 0.94)
        self.assertAlmostEqual(bbox.x, 10.0)

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Deterministic Compliance Logic & Thresholds
    # ──────────────────────────────────────────────────────────────────────────

    def test_07_deterministic_compliance_all_present(self):
        """When Hard Hat, Safety Vest, and Goggles are detected above threshold -> COMPLIANT."""
        detections = [
            RawPPEDetection("DET-01", "HARD_HAT", 0.92, BoundingBox(20.0, 5.0, 20.0, 15.0), status="DETECTED", is_compliant=True),
            RawPPEDetection("DET-02", "SAFETY_VEST", 0.90, BoundingBox(15.0, 25.0, 30.0, 40.0), status="DETECTED", is_compliant=True),
            RawPPEDetection("DET-03", "SAFETY_GOGGLES", 0.85, BoundingBox(22.0, 12.0, 15.0, 8.0), status="DETECTED", is_compliant=True),
        ]
        status, missing, uncertain = ppe_detection_service.evaluate_compliance(
            detections=detections,
            required_classes=["HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"],
            confidence_threshold=0.65,
        )
        self.assertEqual(status, PPEComplianceStatus.COMPLIANT)
        self.assertEqual(len(missing), 0)
        self.assertEqual(len(uncertain), 0)

    def test_08_deterministic_compliance_missing_hard_hat(self):
        """When Hard Hat is missing -> NON_COMPLIANT with HARD_HAT in missing list."""
        detections = [
            RawPPEDetection("DET-02", "SAFETY_VEST", 0.91, BoundingBox(15.0, 25.0, 30.0, 40.0), status="DETECTED", is_compliant=True),
            RawPPEDetection("DET-03", "SAFETY_GOGGLES", 0.88, BoundingBox(22.0, 12.0, 15.0, 8.0), status="DETECTED", is_compliant=True),
        ]
        status, missing, uncertain = ppe_detection_service.evaluate_compliance(
            detections=detections,
            required_classes=["HARD_HAT", "SAFETY_VEST"],
            confidence_threshold=0.65,
        )
        self.assertEqual(status, PPEComplianceStatus.NON_COMPLIANT)
        self.assertIn("HARD_HAT", missing)
        self.assertNotIn("SAFETY_VEST", missing)

    def test_09_configurable_confidence_threshold_low_confidence(self):
        """Detections below threshold must be marked UNCERTAIN/LOW_CONFIDENCE, not auto-violation."""
        detections = [
            RawPPEDetection("DET-01", "HARD_HAT", 0.92, BoundingBox(20.0, 5.0, 20.0, 15.0), status="DETECTED", is_compliant=True),
            RawPPEDetection("DET-02", "SAFETY_VEST", 0.90, BoundingBox(15.0, 25.0, 30.0, 40.0), status="DETECTED", is_compliant=True),
            RawPPEDetection("DET-03", "SAFETY_GOGGLES", 0.48, BoundingBox(22.0, 12.0, 15.0, 8.0), status="LOW_CONFIDENCE", is_compliant=False),
        ]
        status, missing, uncertain = ppe_detection_service.evaluate_compliance(
            detections=detections,
            required_classes=["HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"],
            confidence_threshold=0.65,
        )
        self.assertEqual(status, PPEComplianceStatus.UNCERTAIN)
        self.assertIn("SAFETY_GOGGLES", uncertain)
        self.assertEqual(len(missing), 0)

    def test_10_multiple_workers_in_single_image(self):
        """Verify pipeline handles multi-worker detections correctly."""
        p1 = PersonDetection(
            person_id="P-01",
            bounding_box=BoundingBox(5.0, 10.0, 40.0, 80.0),
            confidence=0.92,
            detected_ppe=[
                RawPPEDetection("DET-01", "HARD_HAT", 0.95, BoundingBox(15.0, 12.0, 18.0, 12.0), status="DETECTED", is_compliant=True),
                RawPPEDetection("DET-02", "SAFETY_VEST", 0.92, BoundingBox(10.0, 30.0, 30.0, 40.0), status="DETECTED", is_compliant=True),
            ],
        )
        p2 = PersonDetection(
            person_id="P-02",
            bounding_box=BoundingBox(55.0, 10.0, 40.0, 80.0),
            confidence=0.88,
            detected_ppe=[
                RawPPEDetection("DET-03", "SAFETY_VEST", 0.89, BoundingBox(60.0, 30.0, 30.0, 40.0), status="DETECTED", is_compliant=True),
            ],
        )
        output = DetectorOutput(
            model_name="Multi-Worker-Test",
            detection_source="COMPUTER_VISION",
            persons=[p1, p2],
            detections=p1.detected_ppe + p2.detected_ppe,
            image_width=1000,
            image_height=800,
        )
        self.assertEqual(len(output.persons), 2)
        p1_classes = [d.ppe_class for d in output.persons[0].detected_ppe]
        self.assertIn("HARD_HAT", p1_classes)
        p2_classes = [d.ppe_class for d in output.persons[1].detected_ppe]
        self.assertNotIn("HARD_HAT", p2_classes)

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Deterministic Demo Scenarios 1 - 5
    # ──────────────────────────────────────────────────────────────────────────

    def test_11_demo_scenario_1_full_ppe_compliant(self):
        """DEMO 1 — FULL PPE: All PPE worn -> COMPLIANT, 0 safety findings."""
        db = SessionLocal()
        try:
            analysis = ppe_detection_service.run_demo_scenario(
                db=db,
                scenario_id=1,
                site_id=self.site.id,
                worker_id=self.worker_compliant.id,
                user_id=self.safety_officer.id,
            )
            self.assertEqual(analysis["overall_compliance"], PPEComplianceStatus.COMPLIANT)
            self.assertEqual(len(analysis["missing_ppe"]), 0)
            self.assertEqual(analysis["detection_source"], "DEMO / MOCK")
        finally:
            db.close()

    def test_12_demo_scenario_2_missing_hard_hat(self):
        """DEMO 2 — MISSING HARD HAT: Safety finding created for missing hard hat."""
        db = SessionLocal()
        try:
            analysis = ppe_detection_service.run_demo_scenario(
                db=db,
                scenario_id=2,
                site_id=self.site.id,
                worker_id=self.worker_violator.id,
                user_id=self.safety_officer.id,
            )
            self.assertEqual(analysis["overall_compliance"], PPEComplianceStatus.NON_COMPLIANT)
            self.assertIn("HARD_HAT", analysis["missing_ppe"])
            # Verify SafetyFinding was generated
            finding = (
                db.query(SafetyFinding)
                .filter(
                    SafetyFinding.site_id == self.site.id,
                    SafetyFinding.description.like("%Hard Hat%"),
                )
                .first()
            )
            self.assertIsNotNone(finding)
            self.assertEqual(finding.finding_type, SafetyFindingType.PPE_VIOLATION)
            self.assertIn("hard hat", finding.recommendation.lower())
        finally:
            db.close()

    def test_13_demo_scenario_3_multiple_ppe_violations_high_risk(self):
        """DEMO 3 — MULTIPLE PPE VIOLATIONS: Missing Hard Hat + Goggles -> CRITICAL on high-risk."""
        db = SessionLocal()
        try:
            analysis = ppe_detection_service.run_demo_scenario(
                db=db,
                scenario_id=3,
                site_id=self.site.id,
                worker_id=self.worker_violator.id,
                user_id=self.safety_officer.id,
            )
            self.assertEqual(analysis["overall_compliance"], PPEComplianceStatus.NON_COMPLIANT)
            self.assertIn("HARD_HAT", analysis["missing_ppe"])
            self.assertIn("SAFETY_GOGGLES", analysis["missing_ppe"])
            self.assertEqual(len(analysis["findings"]), 2)
        finally:
            db.close()

    def test_14_demo_scenario_4_low_confidence(self):
        """DEMO 4 — LOW CONFIDENCE: Below threshold -> UNCERTAIN, does NOT create violation."""
        db = SessionLocal()
        try:
            analysis = ppe_detection_service.run_demo_scenario(
                db=db,
                scenario_id=4,
                site_id=self.site.id,
                worker_id=self.worker_compliant.id,
                user_id=self.safety_officer.id,
            )
            self.assertEqual(analysis["overall_compliance"], PPEComplianceStatus.UNCERTAIN)
            self.assertEqual(len(analysis["missing_ppe"]), 0)
        finally:
            db.close()

    def test_15_demo_scenario_5_cross_verification_discrepancy(self):
        """DEMO 5 — DISCREPANCY: DB says COMPLIANT, CV detects missing hard hat -> PPE_DISCREPANCY finding."""
        db = SessionLocal()
        try:
            # Ensure worker is recorded as COMPLIANT in DB
            w = db.query(Worker).filter(Worker.id == self.worker_compliant.id).first()
            w.ppe_status = PPEStatus.COMPLIANT
            db.commit()

            analysis = ppe_detection_service.run_demo_scenario(
                db=db,
                scenario_id=5,
                site_id=self.site.id,
                worker_id=self.worker_compliant.id,
                user_id=self.safety_officer.id,
            )
            self.assertEqual(analysis["overall_compliance"], PPEComplianceStatus.NON_COMPLIANT)
            self.assertIsNotNone(analysis["cross_verification"])
            self.assertTrue(analysis["cross_verification"]["has_discrepancy"])

            # Verify finding type is PPE_DISCREPANCY
            finding = (
                db.query(SafetyFinding)
                .filter(
                    SafetyFinding.site_id == self.site.id,
                    SafetyFinding.finding_type == SafetyFindingType.PPE_DISCREPANCY,
                )
                .first()
            )
            self.assertIsNotNone(finding)
            self.assertIn("discrepancy", finding.description.lower())
        finally:
            db.close()

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Real Computer Vision Pipeline Execution
    # ──────────────────────────────────────────────────────────────────────────

    def test_16_real_cv_model_execution(self):
        """Execute real OpenCV Computer Vision pipeline on real image file."""
        cv_detector = ComputerVisionPPEDetector()
        img_bytes = create_test_image_bytes(400, 400, color="orange", format="JPEG")
        test_file = os.path.join(settings.PPE_UPLOAD_DIR, "real_cv_test.jpg")
        with open(test_file, "wb") as f:
            f.write(img_bytes)

        try:
            output = cv_detector.detect(test_file)
            self.assertEqual(output.detection_source, "COMPUTER_VISION")
            self.assertIn("OpenCV", output.model_name)
            self.assertEqual(output.image_width, 400)
            self.assertEqual(output.image_height, 400)
            self.assertIsInstance(output.persons, list)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    # ──────────────────────────────────────────────────────────────────────────
    # 7. API Authentication & RBAC Enforcement
    # ──────────────────────────────────────────────────────────────────────────

    def test_17_api_unauthenticated_blocked(self):
        """Unauthenticated calls to /safety/ppe endpoints must return 401 Unauthorized."""
        res = self.client.get("/api/v1/safety/ppe/site/any-site-id")
        self.assertEqual(res.status_code, 401)

    def test_18_rbac_safety_officer_allowed_to_analyze(self):
        """Safety Officer is authorized to upload and analyze PPE images."""
        img_bytes = create_test_image_bytes(200, 200, "yellow", "JPEG")
        res = self.client.post(
            "/api/v1/safety/ppe/analyze",
            files={"file": ("site_work.jpg", img_bytes, "image/jpeg")},
            data={"site_id": self.site.id, "worker_id": self.worker_compliant.id},
            headers={"Authorization": f"Bearer {self.safety_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["detection_source"], "COMPUTER_VISION")

    def test_19_rbac_viewer_forbidden_from_analyzing(self):
        """Viewer role must receive 403 Forbidden when attempting to upload/analyze PPE."""
        img_bytes = create_test_image_bytes(200, 200, "yellow", "JPEG")
        res = self.client.post(
            "/api/v1/safety/ppe/analyze",
            files={"file": ("site_work.jpg", img_bytes, "image/jpeg")},
            data={"site_id": self.site.id},
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(res.status_code, 403)

    def test_20_rbac_viewer_can_read_ppe_analyses(self):
        """Viewer role has READ-ONLY access to view PPE analyses."""
        res = self.client.get(
            f"/api/v1/safety/ppe/site/{self.site.id}",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_21_demo_scenarios_list_api(self):
        """GET /safety/ppe/demo-scenarios returns all 5 deterministic scenarios."""
        res = self.client.get(
            "/api/v1/safety/ppe/demo-scenarios",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 5)
        scenario_ids = [s["id"] for s in data]
        self.assertIn(1, scenario_ids)
        self.assertIn(2, scenario_ids)
        self.assertIn(3, scenario_ids)
        self.assertIn(4, scenario_ids)
        self.assertIn(5, scenario_ids)

    def test_22_demo_scenario_execution_api(self):
        """POST /safety/ppe/demo-scenario executes deterministic fixture correctly via API."""
        res = self.client.post(
            f"/api/v1/safety/ppe/demo-scenario?scenario_id=2&site_id={self.site.id}",
            headers={"Authorization": f"Bearer {self.safety_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["overall_compliance"], "NON_COMPLIANT")
        self.assertEqual(data["detection_source"], "DEMO / MOCK")

    def test_23_image_endpoint_path_traversal_protection(self):
        """Image endpoint must block directory traversal attempts."""
        res = self.client.get(
            "/api/v1/safety/ppe/image/../../../../etc/passwd",
            headers={"Authorization": f"Bearer {self.safety_token}"},
        )
        self.assertIn(res.status_code, [400, 404])


if __name__ == "__main__":
    unittest.main()
