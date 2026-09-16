"""
ACRIP Milestone 3 Insurance Intelligence Test Suite
===================================================
Comprehensive tests for:
13. Insurance Agent initialization
14. Exposure assessment
15. Incident severity evaluation
16. Insurance risk scoring formula & bounds
17. Low-risk scenario (Demo 5)
18. High-risk scenario (Demo 6)
19. Claim-risk analysis
20. Claim documentation package (Demo 7)
21. Evidence preservation
22. Alert integration
23. RBAC permissions
24. Viewer restrictions (403 Forbidden)
25. Compliance + Safety integration
26. Insurance + Safety integration
27. Compliance + Insurance workflow
28. Deterministic demo execution
29. Demo labeling
30. API functionality
"""

import uuid
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, Worker, Equipment, Hazard, UserRole,
    ProjectStatus, SiteStatus, SafetyFinding, SafetyAlert,
    InsuranceRiskAssessment, InsuranceClaimAssessment, ClaimDocumentationPackage,
    InsuranceRiskLevel, ClaimRiskLevel, RiskCategory, AlertSeverity
)
from app.core.security import hash_password, create_access_token
from app.services.insurance.engine import (
    BaseInsuranceAgent, InsuranceRiskAnalyzer, InsuranceAgent
)
from app.services.insurance.demo_scenarios import INSURANCE_DEMO_SCENARIOS
from app.services.insurance.insurance_service import InsuranceService
from app.services.compliance.compliance_service import ComplianceService
from app.main import app


class TestMilestone3Insurance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        from app.database.session import migrate_db_columns
        migrate_db_columns(engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.suffix = uuid.uuid4().hex[:6]

        # 1. Super Admin
        cls.admin_email = f"admin_ins_{cls.suffix}@acrip.com"
        cls.admin = User(
            id=str(uuid.uuid4()),
            email=cls.admin_email,
            full_name="Admin Insurance",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        cls.db.add(cls.admin)

        # 2. Safety Officer
        cls.safety_email = f"safety_ins_{cls.suffix}@acrip.com"
        cls.safety_officer = User(
            id=str(uuid.uuid4()),
            email=cls.safety_email,
            full_name="Safety Officer Insurance",
            hashed_password=hash_password("Safety@123"),
            role=UserRole.SAFETY_OFFICER,
            is_active=True,
        )
        cls.db.add(cls.safety_officer)

        # 3. Site Manager
        cls.site_manager_email = f"sitemgr_ins_{cls.suffix}@acrip.com"
        cls.site_manager = User(
            id=str(uuid.uuid4()),
            email=cls.site_manager_email,
            full_name="Site Manager Insurance",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.SITE_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.site_manager)

        # 4. Project Manager
        cls.proj_manager_email = f"projmgr_ins_{cls.suffix}@acrip.com"
        cls.proj_manager = User(
            id=str(uuid.uuid4()),
            email=cls.proj_manager_email,
            full_name="Project Manager Insurance",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.PROJECT_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.proj_manager)

        # 5. Viewer
        cls.viewer_email = f"viewer_ins_{cls.suffix}@acrip.com"
        cls.viewer = User(
            id=str(uuid.uuid4()),
            email=cls.viewer_email,
            full_name="Viewer Insurance",
            hashed_password=hash_password("Viewer@123"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        cls.db.add(cls.viewer)

        # Project and Site
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-INS-{cls.suffix}",
            name="Insurance Risk Logistics Hub",
            client="Global Build Corp",
            description="Insurance testing site",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-INS-{cls.suffix}",
            name="Insurance Site Beta",
            address="Harbor Zone, Dock 12",
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

    # ── Test 13: Insurance Agent Initialization ──────────────────────────────
    def test_13_insurance_agent_initialization(self):
        agent = InsuranceAgent()
        self.assertEqual(agent.agent_id, "insurance_agent_v1")
        self.assertEqual(agent.name, "Insurance Agent")
        self.assertTrue(isinstance(agent, BaseInsuranceAgent))

    # ── Test 14: Exposure Assessment ─────────────────────────────────────────
    def test_14_exposure_assessment(self):
        analyzer = InsuranceRiskAnalyzer()
        res = analyzer.calculate_insurance_score({
            "compliance_score": 100.0,
            "hazards": [],
            "safety_findings": [],
            "safety_alerts": [],
            "workers": [],
        })
        self.assertEqual(res["insurance_risk_score"], 0.0)
        self.assertEqual(res["insurance_risk_level"], InsuranceRiskLevel.LOW)
        self.assertIn("estimated_liability_exposure", res)

    # ── Test 15: Incident Severity Evaluation ─────────────────────────────────
    def test_15_incident_severity_evaluation(self):
        analyzer = InsuranceRiskAnalyzer()
        incident = {"title": "Tower crane load slip", "severity": "CRITICAL", "worker_id": "W-1"}
        res = analyzer.analyze_claim_risk(incident)
        self.assertEqual(res["incident_severity"], RiskCategory.CRITICAL)
        self.assertEqual(res["claim_risk_level"], ClaimRiskLevel.SEVERE)
        self.assertGreaterEqual(res["claim_probability_pct"], 80.0)

    # ── Test 16: Insurance Risk Scoring Formula & Bounds ─────────────────────
    def test_16_insurance_risk_scoring_bounds(self):
        analyzer = InsuranceRiskAnalyzer()
        # Test extreme inputs to verify bounds clamping [0.0, 100.0]
        extreme_context = {
            "compliance_score": 0.0,
            "hazards": [{"severity": "CRITICAL"}] * 10,
            "safety_findings": [{"status": "OPEN"}] * 20,
            "safety_alerts": [{"severity": "CRITICAL"}] * 10,
            "workers": [{"role": "scaffolder"}] * 10,
        }
        res = analyzer.calculate_insurance_score(extreme_context)
        self.assertLessEqual(res["insurance_risk_score"], 100.0)
        self.assertGreaterEqual(res["insurance_risk_score"], 80.0)
        self.assertEqual(res["insurance_risk_level"], InsuranceRiskLevel.CRITICAL)

    # ── Test 17: Low-Risk Scenario (Demo 5) ───────────────────────────────────
    def test_17_low_risk_scenario(self):
        service = InsuranceService()
        assessment = service.run_demo_scenario(self.db, scenario_id=5, site_id=self.site.id)
        self.assertIsNotNone(assessment)
        self.assertLessEqual(assessment.insurance_risk_score, 25.0)
        self.assertEqual(assessment.insurance_risk_level, InsuranceRiskLevel.LOW)
        self.assertTrue(assessment.is_simulation)

    # ── Test 18: High-Risk Scenario (Demo 6) ──────────────────────────────────
    def test_18_high_risk_scenario(self):
        service = InsuranceService()
        assessment = service.run_demo_scenario(self.db, scenario_id=6, site_id=self.site.id)
        self.assertIsNotNone(assessment)
        self.assertGreaterEqual(assessment.insurance_risk_score, 80.0)
        self.assertEqual(assessment.insurance_risk_level, InsuranceRiskLevel.CRITICAL)
        self.assertGreater(assessment.compliance_deficit_penalty, 15.0)

    # ── Test 19: Claim-Risk Analysis ──────────────────────────────────────────
    def test_19_claim_risk_analysis(self):
        analyzer = InsuranceRiskAnalyzer()
        incident = {
            "title": "Trench wall minor collapse near excavator",
            "severity": "HIGH",
            "worker_id": "W-102",
            "equipment_id": "EQ-02",
            "witness_statement": True,
            "supervisor_signoff": False,
            "sensor_evidence": False,
        }
        res = analyzer.analyze_claim_risk(incident)
        self.assertEqual(res["claim_risk_level"], ClaimRiskLevel.HIGH)
        # Completeness: has worker/equip (1), has witness (1), no supervisor (0), no sensor (0) = 50%
        self.assertEqual(res["documentation_completeness_pct"], 50.0)
        self.assertGreaterEqual(len(res["missing_documentation"]), 2)

    # ── Test 20: Claim Documentation Package (Demo 7) ─────────────────────────
    def test_20_claim_documentation_package(self):
        service = InsuranceService()
        result = service.run_demo_scenario(self.db, scenario_id=7, site_id=self.site.id)
        self.assertIn("claim_assessment", result)
        self.assertIn("documentation_package", result)
        dossier = result["documentation_package"]
        self.assertTrue(dossier.package_id.startswith("PKG-"))
        self.assertIsNotNone(dossier.worker_dossier)
        self.assertIsNotNone(dossier.equipment_dossier)

    # ── Test 21: Evidence Preservation ────────────────────────────────────────
    def test_21_evidence_preservation(self):
        service = InsuranceService()
        result = service.run_demo_scenario(self.db, scenario_id=7, site_id=self.site.id)
        dossier = result["documentation_package"]
        sensor_data = dossier.sensor_evidence_dossier
        self.assertIsNotNone(sensor_data)
        self.assertEqual(sensor_data.get("video_event_id"), "VE-DEMO-882")
        self.assertIn("missing_required_documents", dossier.__dict__)

    # ── Test 22: Alert Integration ────────────────────────────────────────────
    def test_22_alert_integration(self):
        analyzer = InsuranceRiskAnalyzer()
        res_no_alerts = analyzer.calculate_insurance_score({
            "compliance_score": 90.0,
            "hazards": [],
            "safety_findings": [],
            "safety_alerts": [],
            "workers": [],
        })
        res_with_alerts = analyzer.calculate_insurance_score({
            "compliance_score": 90.0,
            "hazards": [],
            "safety_findings": [],
            "safety_alerts": [{"severity": "CRITICAL"}] * 3,
            "workers": [],
        })
        self.assertGreater(
            res_with_alerts["insurance_risk_score"],
            res_no_alerts["insurance_risk_score"],
        )

    # ── Test 23: RBAC Operational Roles ───────────────────────────────────────
    def test_23_rbac_permissions(self):
        # Admin
        resp_admin = self.client.post(
            f"/api/v1/insurance/assess/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_admin,
        )
        self.assertEqual(resp_admin.status_code, 200)

        # Safety Officer
        resp_safety = self.client.post(
            f"/api/v1/insurance/assess/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_safety,
        )
        self.assertEqual(resp_safety.status_code, 200)

        # Site Manager
        resp_mgr = self.client.post(
            f"/api/v1/insurance/assess/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_site_mgr,
        )
        self.assertEqual(resp_mgr.status_code, 200)

    # ── Test 24: Viewer Restrictions (403 Forbidden) ──────────────────────────
    def test_24_viewer_restrictions(self):
        # Assess
        resp_assess = self.client.post(
            f"/api/v1/insurance/assess/{self.site.id}",
            json={"is_simulation": True},
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_assess.status_code, 403)

        # Claim doc
        resp_doc = self.client.post(
            "/api/v1/insurance/claim-documentation/TEST-INC",
            json={"incident_title": "Unauthorized"},
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_doc.status_code, 403)

        # Demo
        resp_demo = self.client.post(
            "/api/v1/insurance/demo-scenarios/run",
            json={"scenario_id": 5, "site_id": self.site.id},
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_demo.status_code, 403)

        # Read allowed
        resp_read = self.client.get(
            f"/api/v1/insurance/site/{self.site.id}",
            headers=self.headers_viewer,
        )
        self.assertEqual(resp_read.status_code, 200)

    # ── Test 25: Compliance + Safety Integration ──────────────────────────────
    def test_25_compliance_plus_safety_integration(self):
        cmp_service = ComplianceService()
        # Trigger audit which populates compliance findings and links safety findings
        assessment = cmp_service.run_demo_scenario(self.db, scenario_id=4, site_id=self.site.id)
        sf_list = self.db.query(SafetyFinding).filter(SafetyFinding.site_id == self.site.id).all()
        self.assertGreaterEqual(len(sf_list), 1)

    # ── Test 26: Insurance + Safety Integration ───────────────────────────────
    def test_26_insurance_plus_safety_integration(self):
        ins_service = InsuranceService()
        assessment = ins_service.assess_site_insurance(self.db, site_id=self.site.id)
        self.assertIsNotNone(assessment)
        self.assertGreaterEqual(assessment.insurance_risk_score, 0.0)

    # ── Test 27: Compliance + Insurance Workflow ──────────────────────────────
    def test_27_compliance_plus_insurance_workflow(self):
        analyzer = InsuranceRiskAnalyzer()
        # Test correlation: poor compliance increases insurance score
        good_cmp = analyzer.calculate_insurance_score({"compliance_score": 95.0, "hazards": []})
        bad_cmp = analyzer.calculate_insurance_score({"compliance_score": 40.0, "hazards": []})
        self.assertGreater(bad_cmp["insurance_risk_score"], good_cmp["insurance_risk_score"])

    # ── Test 28: Deterministic Demo Execution ─────────────────────────────────
    def test_28_deterministic_demo_execution(self):
        service = InsuranceService()
        res1 = service.run_demo_scenario(self.db, scenario_id=5, site_id=self.site.id)
        res2 = service.run_demo_scenario(self.db, scenario_id=5, site_id=self.site.id)
        self.assertEqual(res1.insurance_risk_score, res2.insurance_risk_score)
        self.assertEqual(res1.insurance_risk_level, res2.insurance_risk_level)

    # ── Test 29: Demo Labeling ────────────────────────────────────────────────
    def test_29_demo_labeling(self):
        service = InsuranceService()
        assessment = service.run_demo_scenario(self.db, scenario_id=6, site_id=self.site.id)
        self.assertTrue(assessment.is_simulation)

    # ── Test 30: API Functionality ────────────────────────────────────────────
    def test_30_api_functionality(self):
        # 1. GET /risk
        resp_risk = self.client.get(f"/api/v1/insurance/risk/{self.site.id}", headers=self.headers_safety)
        self.assertEqual(resp_risk.status_code, 200)
        self.assertIn("exposure_index", resp_risk.json())

        # 2. GET /claims
        resp_claims = self.client.get(f"/api/v1/insurance/claims/{self.site.id}", headers=self.headers_safety)
        self.assertEqual(resp_claims.status_code, 200)

        # 3. GET /demo-scenarios
        resp_demos = self.client.get("/api/v1/insurance/demo-scenarios", headers=self.headers_safety)
        self.assertEqual(resp_demos.status_code, 200)
        self.assertEqual(len(resp_demos.json()), 3)
