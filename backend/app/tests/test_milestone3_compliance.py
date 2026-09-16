"""
ACRIP Milestone 3 Compliance Intelligence Test Suite
====================================================
Comprehensive tests for:
1. Compliance Agent initialization
2. Rule loading
3. Regulatory validation
4. Compliant site (Demo 1)
5. Violation detection
6. Severity calculation & score deductions
7. Inspection tracking
8. Overdue inspection detection
9. SafetyFinding & Alert integration
10. Compliance report generation
11. RBAC permissions
12. Viewer read-only restrictions (403 Forbidden)
"""

import uuid
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, UserRole, ProjectStatus, SiteStatus,
    ComplianceRule, ComplianceFinding, InspectionRequirement,
    ComplianceAssessment, ComplianceStatus, InspectionRequirementStatus,
    SafetyFinding, SafetyFindingStatus, SafetyFindingType,
    RiskCategory, SafetyAlert, AlertSeverity, AlertStatus
)
from app.core.security import hash_password, create_access_token
from app.services.compliance.engine import (
    BaseComplianceAgent, RegulatoryValidationEngine, ComplianceAgent
)
from app.services.compliance.rules import DEFAULT_COMPLIANCE_RULES
from app.services.compliance.demo_scenarios import COMPLIANCE_DEMO_SCENARIOS
from app.services.compliance.compliance_service import ComplianceService
from app.services.alerts.alert_service import AlertService
from app.main import app


class TestMilestone3Compliance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        from app.database.session import migrate_db_columns
        migrate_db_columns(engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.suffix = uuid.uuid4().hex[:6]

        # 1. Super Admin
        cls.admin_email = f"admin_cmp_{cls.suffix}@acrip.com"
        cls.admin = User(
            id=str(uuid.uuid4()),
            email=cls.admin_email,
            full_name="Admin Compliance",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        cls.db.add(cls.admin)

        # 2. Safety Officer
        cls.safety_email = f"safety_cmp_{cls.suffix}@acrip.com"
        cls.safety_officer = User(
            id=str(uuid.uuid4()),
            email=cls.safety_email,
            full_name="Safety Officer Compliance",
            hashed_password=hash_password("Safety@123"),
            role=UserRole.SAFETY_OFFICER,
            is_active=True,
        )
        cls.db.add(cls.safety_officer)

        # 3. Site Manager
        cls.site_manager_email = f"sitemgr_cmp_{cls.suffix}@acrip.com"
        cls.site_manager = User(
            id=str(uuid.uuid4()),
            email=cls.site_manager_email,
            full_name="Site Manager Compliance",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.SITE_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.site_manager)

        # 4. Project Manager
        cls.proj_manager_email = f"projmgr_cmp_{cls.suffix}@acrip.com"
        cls.proj_manager = User(
            id=str(uuid.uuid4()),
            email=cls.proj_manager_email,
            full_name="Project Manager Compliance",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.PROJECT_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.proj_manager)

        # 5. Viewer
        cls.viewer_email = f"viewer_cmp_{cls.suffix}@acrip.com"
        cls.viewer = User(
            id=str(uuid.uuid4()),
            email=cls.viewer_email,
            full_name="Viewer Compliance",
            hashed_password=hash_password("Viewer@123"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        cls.db.add(cls.viewer)

        # Project and Site
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-CMP-{cls.suffix}",
            name="Compliance Gateway Center",
            client="Global Build Corp",
            description="Compliance testing site",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-CMP-{cls.suffix}",
            name="Compliance Site Alpha",
            address="Industrial Corridor, Sector 4",
            project_id=cls.project.id,
            manager_id=cls.site_manager.id,
            status=SiteStatus.ACTIVE,
        )
        cls.db.add(cls.site)
        cls.db.commit()

        # Auth Headers
        cls.admin_token = create_access_token({"sub": cls.admin.id, "email": cls.admin_email, "role": "super_admin"})
        cls.safety_token = create_access_token({"sub": cls.safety_officer.id, "email": cls.safety_email, "role": "safety_officer"})
        cls.site_manager_token = create_access_token({"sub": cls.site_manager.id, "email": cls.site_manager_email, "role": "site_manager"})
        cls.proj_manager_token = create_access_token({"sub": cls.proj_manager.id, "email": cls.proj_manager_email, "role": "project_manager"})
        cls.viewer_token = create_access_token({"sub": cls.viewer.id, "email": cls.viewer_email, "role": "viewer"})

        cls.headers_admin = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.headers_safety = {"Authorization": f"Bearer {cls.safety_token}"}
        cls.headers_site_mgr = {"Authorization": f"Bearer {cls.site_manager_token}"}
        cls.headers_proj_mgr = {"Authorization": f"Bearer {cls.proj_manager_token}"}
        cls.headers_viewer = {"Authorization": f"Bearer {cls.viewer_token}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ── Test 1: Compliance Agent Initialization ──────────────────────────────
    def test_01_compliance_agent_initialization(self):
        agent = ComplianceAgent()
        self.assertEqual(agent.agent_id, "compliance_agent_v1")
        self.assertEqual(agent.name, "Compliance Agent")
        self.assertTrue(isinstance(agent, BaseComplianceAgent))

    # ── Test 2: Rule Loading ──────────────────────────────────────────────────
    def test_02_rule_loading(self):
        engine_inst = RegulatoryValidationEngine()
        self.assertGreaterEqual(len(engine_inst.rules), 8)
        rule_ids = [r["rule_id"] for r in engine_inst.rules]
        self.assertIn("R-OSHA-1926.95", rule_ids)
        self.assertIn("R-OSHA-1926.451", rule_ids)
        self.assertIn("R-OSHA-1926.651", rule_ids)
        self.assertIn("R-ISO-45001-7.2", rule_ids)

    # ── Test 3: Regulatory Validation Logic ───────────────────────────────────
    def test_03_regulatory_validation(self):
        engine_inst = RegulatoryValidationEngine()
        context = {
            "site_id": self.site.id,
            "workers": [],
            "equipment": [],
            "hazards": [],
            "inspections": [],
            "ppe_events": [],
        }
        res = engine_inst.evaluate(context)
        self.assertEqual(res["compliance_score"], 100.0)
        self.assertEqual(res["compliance_status"], ComplianceStatus.COMPLIANT)
        self.assertEqual(res["critical_violations"], 0)

    # ── Test 4: Compliant Site (Demo 1) ───────────────────────────────────────
    def test_04_compliant_site(self):
        service = ComplianceService()
        assessment = service.run_demo_scenario(self.db, scenario_id=1, site_id=self.site.id)
        self.assertIsNotNone(assessment)
        self.assertGreaterEqual(assessment.compliance_score, 90.0)
        self.assertEqual(assessment.compliance_status, ComplianceStatus.COMPLIANT)
        self.assertEqual(assessment.critical_violations, 0)
        self.assertTrue(assessment.is_simulation)

    # ── Test 5: Violation Detection ───────────────────────────────────────────
    def test_05_violation_detection(self):
        service = ComplianceService()
        assessment = service.run_demo_scenario(self.db, scenario_id=2, site_id=self.site.id)
        self.assertIsNotNone(assessment)
        self.assertGreaterEqual(assessment.rules_violated, 1)
        # Verify findings list in DB
        findings = service.list_findings(self.db, self.site.id)
        ppe_findings = [f for f in findings if "PPE" in f.violation_type]
        self.assertTrue(len(ppe_findings) > 0)
        self.assertEqual(ppe_findings[0].standard_ref, "OSHA 1926.95")

    # ── Test 6: Severity Calculation & Score Deductions ───────────────────────
    def test_06_severity_calculation(self):
        engine_inst = RegulatoryValidationEngine()
        context = {
            "site_id": self.site.id,
            "workers": [
                {"role": "crane_operator", "safety_training_status": "EXPIRED"}  # Critical: -20
            ],
            "hazards": [
                {"title": "Unshored trench wall", "hazard_type": "excavation", "severity": "CRITICAL"} # Critical: -20
            ],
            "inspections": [],
            "ppe_events": [],
        }
        res = engine_inst.evaluate(context)
        # 100 - 20 - 20 = 60.0
        self.assertEqual(res["critical_violations"], 2)
        self.assertEqual(res["compliance_score"], 60.0)
        self.assertEqual(res["compliance_status"], ComplianceStatus.PARTIALLY_COMPLIANT)

    # ── Test 7: Inspection Tracking ───────────────────────────────────────────
    def test_07_inspection_tracking(self):
        service = ComplianceService()
        insp_data = {
            "title": "Quarterly Tower Crane Rigging Certification",
            "inspection_type": "Quarterly Third-Party",
            "regulatory_reference": "ISO 45001:2018 Cl. 7.2",
            "responsible_role": "safety_officer",
            "due_date": datetime.utcnow() + timedelta(days=30),
            "status": InspectionRequirementStatus.SCHEDULED,
            "notes": "Third-party crane surveyor booked",
        }
        created = service.create_inspection_requirement(self.db, self.site.id, insp_data)
        self.assertIsNotNone(created.id)
        self.assertTrue(created.requirement_id.startswith("INSP-"))
        self.assertEqual(created.status, InspectionRequirementStatus.SCHEDULED)

        listed = service.list_inspections(self.db, self.site.id)
        self.assertTrue(any(i.requirement_id == created.requirement_id for i in listed))

    # ── Test 8: Overdue Inspection Detection ─────────────────────────────────
    def test_08_overdue_inspection_detection(self):
        service = ComplianceService()
        # Add an overdue inspection
        overdue_insp = InspectionRequirement(
            id=str(uuid.uuid4()),
            requirement_id=f"INSP-OVD-{uuid.uuid4().hex[:4].upper()}",
            site_id=self.site.id,
            title="Expired Scaffolding Tag Inspection",
            inspection_type="Weekly Statutory",
            regulatory_reference="IS 3696:1987",
            responsible_role="safety_officer",
            due_date=datetime.utcnow() - timedelta(days=5),
            status=InspectionRequirementStatus.OVERDUE,
            is_overdue=True,
            created_at=datetime.utcnow(),
        )
        self.db.add(overdue_insp)
        self.db.commit()

        assessment = service.analyze_site_compliance(self.db, self.site.id, is_simulation=False)
        self.assertGreaterEqual(assessment.overdue_inspections, 1)

    # ── Test 9: SafetyFinding & AlertService Integration ──────────────────────
    def test_09_safety_finding_and_alert_integration(self):
        service = ComplianceService()
        # Run Demo 4 (Multiple critical violations)
        assessment = service.run_demo_scenario(self.db, scenario_id=4, site_id=self.site.id)
        self.assertLessEqual(assessment.compliance_score, 60.0)

        # Check that SafetyFindings were generated with compliance_finding_id
        sf_records = (
            self.db.query(SafetyFinding)
            .filter(
                SafetyFinding.site_id == self.site.id,
                SafetyFinding.compliance_finding_id.isnot(None),
            )
            .all()
        )
        self.assertGreaterEqual(len(sf_records), 1)
        self.assertTrue(sf_records[0].detection_source == "COMPLIANCE_AGENT")

        # Check that high/critical alerts exist for the site
        alerts = self.db.query(SafetyAlert).filter(SafetyAlert.site_id == self.site.id).all()
        self.assertGreaterEqual(len(alerts), 1)

    # ── Test 10: Compliance Report Generation ─────────────────────────────────
    def test_10_compliance_report_generation(self):
        resp = self.client.get(
            f"/api/v1/compliance/reports/{self.site.id}",
            headers=self.headers_safety,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("compliance_score", data)
        self.assertIn("compliance_status", data)
        self.assertIn("category_scores", data)
        self.assertIn("recommendations", data)
        self.assertIn("disclaimer", data)

    # ── Test 11: RBAC Operational Roles ───────────────────────────────────────
    def test_11_rbac_operational_roles(self):
        # Super Admin
        resp_admin = self.client.post(
            f"/api/v1/compliance/analyze/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_admin,
        )
        self.assertEqual(resp_admin.status_code, 200)

        # Safety Officer
        resp_safety = self.client.post(
            f"/api/v1/compliance/analyze/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_safety,
        )
        self.assertEqual(resp_safety.status_code, 200)

        # Site Manager
        resp_sitemgr = self.client.post(
            f"/api/v1/compliance/analyze/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_site_mgr,
        )
        self.assertEqual(resp_sitemgr.status_code, 200)

    # ── Test 12: Viewer Read-Only Enforcement (403 Forbidden) ─────────────────
    def test_12_viewer_read_only(self):
        # Mutation: analyze
        resp_mut = self.client.post(
            f"/api/v1/compliance/analyze/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_mut.status_code, 403)

        # Mutation: create inspection
        resp_insp = self.client.post(
            f"/api/v1/compliance/inspections/{self.site.id}",
            json={
                "title": "Unauthorized Inspection",
                "inspection_type": "Test",
                "due_date": datetime.utcnow().isoformat(),
            },
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_insp.status_code, 403)

        # Mutation: run demo
        resp_demo = self.client.post(
            "/api/v1/compliance/demo-scenarios/run",
            json={"scenario_id": 1, "site_id": self.site.id},
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_demo.status_code, 403)

        # Read: allowed for Viewer
        resp_read = self.client.get(
            f"/api/v1/compliance/site/{self.site.id}",
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_read.status_code, 200)
