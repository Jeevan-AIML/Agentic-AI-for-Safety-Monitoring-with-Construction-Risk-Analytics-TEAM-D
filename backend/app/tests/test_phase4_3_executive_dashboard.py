"""
ACRIP Phase 4.3 Executive Project Dashboard Test Suite
=====================================================
Comprehensive tests for:
1. ExecutiveDashboardService initialization and dependency composition
2. Executive dashboard aggregation for a site with live multi-agent data
3. Four-pillar risk score integration (Site, Safety, Compliance, Insurance)
4. Consolidated project health evaluation (health status, health score, counts)
5. Prioritized critical findings feed across agents
6. Phase 4.2 recurring patterns and causal incident predictions inclusion
7. Phase 4.2 operational recommendations (3-horizon breakdown)
8. Safety, Compliance, and Insurance domain snapshots accuracy
9. Phase 4.1 Reporting Agent integration (recent generated reports)
10. Historical risk assessments trend extraction
11. Empty/sparse site graceful handling with truthful representations
12. REST API: GET /api/v1/dashboard/executive/{site_id}
13. REST API: GET /api/v1/dashboard/executive (overview)
14. REST API: Invalid site returns 404 Not Found
15. REST API: Unauthenticated access returns 401 Unauthorized
"""

import uuid
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, UserRole, ProjectStatus, SiteStatus,
    Hazard, RiskScore, HazardType, HazardStatus, RiskCategory,
    SafetyFinding, SafetyAnalysis, SafetyAlert, SafetyFindingType, SafetyFindingStatus,
    AlertSeverity, AlertPriority, AlertStatus,
    ComplianceFinding, ComplianceAssessment, ComplianceStatus, InspectionRequirement, InspectionRequirementStatus,
    InsuranceRiskAssessment, InsuranceClaimAssessment, InsuranceRiskLevel, ClaimRiskLevel,
    ReportType, ReportStatus, GeneratedReport,
    ProjectRiskIntelligence
)
from app.core.security import hash_password, create_access_token
from app.services.dashboard.executive_service import ExecutiveDashboardService
from app.schemas.schemas import ExecutiveDashboardResponse
from app.main import app


class TestPhase43ExecutiveDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        from app.database.session import migrate_db_columns
        migrate_db_columns(engine)
        cls.client = TestClient(app)

        cls.db = SessionLocal()
        cls.test_run_id = uuid.uuid4().hex[:8]

        # Create test user
        cls.user = User(
            id=str(uuid.uuid4()),
            email=f"exec_{cls.test_run_id}@acrip.internal",
            hashed_password=hash_password("ExecutivePass123!"),
            full_name="Executive Project Director",
            role=UserRole.PROJECT_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.user)
        cls.db.commit()

        cls.token = create_access_token(data={"sub": cls.user.id})
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

        # Create test project & site
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-{cls.test_run_id[:6].upper()}",
            name=f"Metro Line Phase 4-{cls.test_run_id}",
            client="Metro Transit Authority",
            description="Executive test construction project",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)
        cls.db.commit()

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-{cls.test_run_id[:6].upper()}",
            project_id=cls.project.id,
            name=f"Central Station Pier {cls.test_run_id}",
            address="Zone 4 Metro Core",
            status=SiteStatus.ACTIVE,
            current_risk_score=55.0,
        )
        cls.db.add(cls.site)
        cls.db.commit()

        # Seed Site Risk Hazard
        cls.hazard = Hazard(
            id=str(uuid.uuid4()),
            hazard_id=f"HAZ-{cls.test_run_id[:6].upper()}",
            site_id=cls.site.id,
            hazard_type=HazardType.EXCAVATION,
            description="Deep foundation trench lacking proper hydraulic shoring",
            risk_category=RiskCategory.HIGH,
            risk_score=78.0,
            probability=4,
            severity=4,
            status=HazardStatus.OPEN,
            recommended_action="Install certified trench box immediately",
            detected_at=datetime.utcnow() - timedelta(hours=3),
        )
        cls.db.add(cls.hazard)

        # Seed Safety Finding & Alert
        cls.safety_finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SF-{uuid.uuid4().hex[:6].upper()}",
            site_id=cls.site.id,
            finding_type=SafetyFindingType.PPE_VIOLATION,
            severity=RiskCategory.HIGH,
            description="Worker operating near trench without hardhat and harness",
            status=SafetyFindingStatus.OPEN,
            recommendation="Enforce mandatory harness anchor",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        cls.safety_alert = SafetyAlert(
            id=str(uuid.uuid4()),
            alert_id=f"ALT-{uuid.uuid4().hex[:6].upper()}",
            site_id=cls.site.id,
            severity=AlertSeverity.HIGH,
            priority=AlertPriority.HIGH,
            status=AlertStatus.OPEN,
            title="Perimeter Breach in High-Risk Excavation",
            description="Uncertified worker detected in hazardous zone",
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
        cls.db.add(cls.safety_finding)
        cls.db.add(cls.safety_alert)

        # Seed Compliance Finding & Assessment
        cls.compliance_finding = ComplianceFinding(
            id=str(uuid.uuid4()),
            finding_id=f"CF-{uuid.uuid4().hex[:6].upper()}",
            site_id=cls.site.id,
            standard_ref="OSHA 1926.652(a)(1)",
            violation_type="EXCAVATION_PROTECTIVE_SYSTEMS",
            description="Excavation deeper than 5 feet without cave-in protection",
            severity=RiskCategory.CRITICAL,
            recommendation="Immediate stop-work order for trench excavation",
            status=SafetyFindingStatus.OPEN,
            created_at=datetime.utcnow() - timedelta(hours=4),
        )
        cls.compliance_assessment = ComplianceAssessment(
            id=str(uuid.uuid4()),
            assessment_id=f"CA-{uuid.uuid4().hex[:6].upper()}",
            site_id=cls.site.id,
            compliance_score=82.5,
            compliance_status=ComplianceStatus.PARTIALLY_COMPLIANT,
            total_rules_evaluated=12,
            rules_passed=10,
            rules_violated=2,
            critical_violations=1,
            high_violations=1,
            medium_violations=0,
            total_inspections=4,
            overdue_inspections=1,
            created_at=datetime.utcnow() - timedelta(hours=5),
        )
        cls.inspection = InspectionRequirement(
            id=str(uuid.uuid4()),
            requirement_id=f"IR-{uuid.uuid4().hex[:6].upper()}",
            site_id=cls.site.id,
            title="Daily Trench and Excavation Competent Person Inspection",
            inspection_type="STATUTORY_DAILY_EXCAVATION",
            regulatory_reference="OSHA 1926.651(k)(1)",
            responsible_role="safety_officer",
            due_date=datetime.utcnow() - timedelta(days=1),
            status=InspectionRequirementStatus.OVERDUE,
            is_overdue=True,
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        cls.db.add(cls.compliance_finding)
        cls.db.add(cls.compliance_assessment)
        cls.db.add(cls.inspection)

        # Seed Insurance Risk Assessment
        cls.insurance_assessment = InsuranceRiskAssessment(
            id=str(uuid.uuid4()),
            assessment_id=f"IRA-{uuid.uuid4().hex[:6].upper()}",
            site_id=cls.site.id,
            insurance_risk_score=58.0,
            insurance_risk_level=InsuranceRiskLevel.HIGH,
            exposure_index=1.45,
            estimated_liability_exposure="$500,000 - $1,000,000",
            unresolved_findings_count=3,
            active_critical_alerts_count=1,
            compliance_deficit_penalty=12.5,
            underwriting_recommendations=[
                "Mandate daily documented geotechnical inspection for deep trenches",
                "Deploy continuous geofence beacon telemetry"
            ],
            created_at=datetime.utcnow() - timedelta(hours=6),
        )
        cls.db.add(cls.insurance_assessment)

        # Seed Generated Report (Phase 4.1)
        cls.report = GeneratedReport(
            id=str(uuid.uuid4()),
            report_id=f"REP-{uuid.uuid4().hex[:8].upper()}",
            site_id=cls.site.id,
            project_id=cls.project.id,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            title="Executive Risk & Safety Digest",
            status=ReportStatus.COMPLETED,
            summary="Comprehensive multi-pillar risk evaluation for executive leadership.",
            content={"overview": "Active monitoring indicates elevated trench hazard risks."},
            metrics={"overall_score": 62.0},
            created_by="ReportingAgent",
            generated_at=datetime.utcnow() - timedelta(hours=2),
        )
        cls.db.add(cls.report)

        cls.db.commit()

        # Instantiate service
        cls.service = ExecutiveDashboardService()

    @classmethod
    def tearDownClass(cls):
        try:
            # Clean up seeded records
            cls.db.query(GeneratedReport).filter(GeneratedReport.site_id == cls.site.id).delete()
            cls.db.query(ProjectRiskIntelligence).filter(ProjectRiskIntelligence.site_id == cls.site.id).delete()
            cls.db.query(InsuranceRiskAssessment).filter(InsuranceRiskAssessment.site_id == cls.site.id).delete()
            cls.db.query(InspectionRequirement).filter(InspectionRequirement.site_id == cls.site.id).delete()
            cls.db.query(ComplianceAssessment).filter(ComplianceAssessment.site_id == cls.site.id).delete()
            cls.db.query(ComplianceFinding).filter(ComplianceFinding.site_id == cls.site.id).delete()
            cls.db.query(SafetyAlert).filter(SafetyAlert.site_id == cls.site.id).delete()
            cls.db.query(SafetyFinding).filter(SafetyFinding.site_id == cls.site.id).delete()
            cls.db.query(Hazard).filter(Hazard.site_id == cls.site.id).delete()
            cls.db.query(Site).filter(Site.id == cls.site.id).delete()
            cls.db.query(Project).filter(Project.id == cls.project.id).delete()
            cls.db.query(User).filter(User.id == cls.user.id).delete()
            cls.db.commit()
        except Exception:
            pass
        finally:
            cls.db.close()

    def test_01_service_initialization(self):
        """Test ExecutiveDashboardService initializes dependencies correctly."""
        self.assertIsNotNone(self.service.risk_intelligence_service)
        self.assertIsNotNone(self.service.reporting_service)

    def test_02_get_executive_dashboard_structure(self):
        """Test that get_executive_dashboard returns a full, validated ExecutiveDashboardResponse."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)

        self.assertIsInstance(response, ExecutiveDashboardResponse)
        self.assertEqual(response.site.site_id, self.site.id)
        self.assertEqual(response.site.site_name, self.site.name)
        self.assertIsNotNone(response.assessment)
        self.assertGreater(response.assessment.overall_risk_score, 0)
        self.assertIn(response.assessment.overall_risk_level.upper(), ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_03_four_pillar_risk_scores(self):
        """Test that four-pillar risk scores are present and correctly weighted."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)

        pillar_scores = response.pillar_scores
        self.assertIn("site_risk_score", pillar_scores)
        self.assertIn("safety_risk_score", pillar_scores)
        self.assertIn("compliance_risk_score", pillar_scores)
        self.assertIn("insurance_risk_score", pillar_scores)

        # Verify weights sum up to 1.0
        weights = pillar_scores.get("weights", {})
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)

    def test_04_health_metrics_evaluation(self):
        """Test project health status and count metrics."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)
        health = response.health

        self.assertIn(health.health_status, ["HEALTHY", "MODERATE_RISK", "ELEVATED", "CRITICAL_ACTION_REQUIRED"])
        self.assertGreaterEqual(health.health_score, 0.0)
        self.assertLessEqual(health.health_score, 100.0)
        self.assertGreaterEqual(health.total_active_findings, 1)
        self.assertGreaterEqual(health.active_safety_alerts_count, 1)
        self.assertGreaterEqual(health.overdue_inspections_count, 1)

    def test_05_critical_findings_prioritization(self):
        """Test prioritized critical findings feed across agents."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)
        findings = response.critical_findings

        self.assertGreaterEqual(len(findings), 1)
        # Check sort order: higher risk score first
        if len(findings) > 1:
            self.assertGreaterEqual(findings[0].risk_score, findings[-1].risk_score)

        # Check attributes
        first = findings[0]
        self.assertIn(first.source_agent, ["site_risk", "safety", "compliance", "insurance"])
        self.assertTrue(bool(first.title))
        self.assertTrue(bool(first.description))

    def test_06_recurring_patterns_and_predictions(self):
        """Test recurring patterns and predictive incident causal chains."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)

        # Both should be lists (can be empty or populated depending on data)
        self.assertIsInstance(response.recurring_patterns, list)
        self.assertIsInstance(response.potential_incidents, list)

    def test_07_operational_recommendations(self):
        """Test operational recommendations from recommendation engine."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)
        recs = response.recommendations

        self.assertIsInstance(recs, list)
        if recs:
            first_rec = recs[0]
            self.assertTrue(bool(first_rec.title))
            self.assertTrue(bool(first_rec.expected_risk_reduction))

    def test_08_domain_snapshots_accuracy(self):
        """Test Safety, Compliance, and Insurance snapshots."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)

        # Safety snapshot
        self.assertGreaterEqual(response.safety_summary.safety_score, 0)
        self.assertGreaterEqual(response.safety_summary.active_alerts_count, 1)

        # Compliance snapshot
        self.assertGreaterEqual(response.compliance_summary.compliance_score, 0)
        self.assertEqual(response.compliance_summary.overdue_inspections_count, 1)

        # Insurance snapshot
        self.assertGreaterEqual(response.insurance_summary.exposure_index, 1.0)
        self.assertTrue(len(response.insurance_summary.underwriting_recommendations) > 0)

    def test_09_reporting_agent_integration(self):
        """Test recent reports feed contains generated reports."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)
        reports = response.recent_reports

        self.assertGreaterEqual(len(reports), 1)
        rep = reports[0]
        self.assertEqual(rep.site_id, self.site.id)
        self.assertEqual(rep.report_type, ReportType.EXECUTIVE_SUMMARY)

    def test_10_history_trend_data(self):
        """Test history assessment records for trend plotting."""
        response = self.service.get_executive_dashboard(self.db, self.site.id)
        self.assertIsInstance(response.history, list)
        self.assertGreaterEqual(len(response.history), 1)
        self.assertIn("overall_risk_score", response.history[0])

    def test_11_rest_api_site_endpoint(self):
        """Test REST API endpoint GET /api/v1/dashboard/executive/{site_id}."""
        res = self.client.get(
            f"/api/v1/dashboard/executive/{self.site.id}",
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["site"]["site_id"], self.site.id)
        self.assertIn("assessment", data)
        self.assertIn("health", data)
        self.assertIn("pillar_scores", data)
        self.assertIn("critical_findings", data)
        self.assertIn("safety_summary", data)
        self.assertIn("compliance_summary", data)
        self.assertIn("insurance_summary", data)
        self.assertIn("recent_reports", data)
        self.assertIn("history", data)

    def test_12_rest_api_overview_endpoint(self):
        """Test REST API endpoint GET /api/v1/dashboard/executive without params."""
        res = self.client.get(
            "/api/v1/dashboard/executive",
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(bool(data["site"]["site_id"]))

    def test_13_rest_api_overview_with_site_id(self):
        """Test REST API endpoint GET /api/v1/dashboard/executive?site_id=..."""
        res = self.client.get(
            f"/api/v1/dashboard/executive?site_id={self.site.id}",
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["site"]["site_id"], self.site.id)

    def test_14_rest_api_invalid_site_returns_404(self):
        """Test that a non-existent site_id returns 404 Not Found."""
        res = self.client.get(
            f"/api/v1/dashboard/executive/{uuid.uuid4()}",
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 404)

    def test_15_rest_api_unauthorized_returns_401(self):
        """Test unauthenticated request returns 401."""
        res = self.client.get(f"/api/v1/dashboard/executive/{self.site.id}")
        self.assertEqual(res.status_code, 401)

    def test_16_sparse_site_graceful_handling(self):
        """Test a clean site with 0 findings does not crash and returns valid baseline."""
        sparse_site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-SPARSE-{self.test_run_id[:4].upper()}",
            name=f"Sparse Site {self.test_run_id}",
            status=SiteStatus.ACTIVE,
            current_risk_score=10.0,
        )
        self.db.add(sparse_site)
        self.db.commit()

        try:
            res = self.service.get_executive_dashboard(self.db, sparse_site.id)
            self.assertEqual(res.site.site_id, sparse_site.id)
            self.assertEqual(res.health.health_status, "HEALTHY")
            self.assertEqual(len(res.critical_findings), 0)
        finally:
            self.db.query(Site).filter(Site.id == sparse_site.id).delete()
            self.db.commit()


if __name__ == "__main__":
    unittest.main()
