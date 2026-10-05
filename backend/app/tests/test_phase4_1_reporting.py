"""
ACRIP Phase 4.1 Reporting Agent Test Suite
==========================================
Comprehensive tests for:
1. Reporting Agent initialization and active orchestrator status
2. Site Risk findings normalization and extraction
3. Safety findings normalization and extraction
4. Compliance findings normalization and extraction
5. Insurance findings normalization and extraction
6. Combined 4-agent aggregation
7. Empty agent results graceful handling
8. Daily Site Report generation
9. Executive Risk Summary generation
10. Audit-Ready Documentation generation with traceability
11. Project Health Report generation
12. Invalid input handling
13. Report persistence and database retrieval
14. REST API endpoints (/reports/types, /generate, /, /{id}, delete)
15. Orchestrator integration
"""

import uuid
import unittest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, UserRole, ProjectStatus, SiteStatus,
    Hazard, RiskScore, HazardType, HazardStatus, RiskCategory,
    SafetyFinding, SafetyAnalysis, SafetyAlert, SafetyFindingType, SafetyFindingStatus, AlertSeverity, AlertStatus,
    ComplianceFinding, ComplianceAssessment, ComplianceStatus, InspectionRequirement, InspectionRequirementStatus,
    InsuranceRiskAssessment, InsuranceClaimAssessment, InsuranceRiskLevel, ClaimRiskLevel,
    ReportType, ReportStatus, GeneratedReport
)
from app.core.security import hash_password, create_access_token
from app.agents.reporting_agent import ReportingAgent, reporting_agent
from app.agents.base_agents import orchestrator
from app.services.reporting.normalizer import (
    NormalizedFinding,
    normalize_site_risk_hazard,
    normalize_safety_finding,
    normalize_safety_alert,
    normalize_compliance_finding,
    normalize_insurance_claim,
)
from app.services.reporting.aggregator import ReportAggregationService
from app.services.reporting.generator import ReportGenerator
from app.services.reporting.reporting_service import ReportingService
from app.main import app


class TestPhase41Reporting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        from app.database.session import migrate_db_columns
        migrate_db_columns(engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.suffix = uuid.uuid4().hex[:6]

        # 1. Users
        cls.admin_email = f"admin_rpt_{cls.suffix}@acrip.com"
        cls.admin = User(
            id=str(uuid.uuid4()),
            email=cls.admin_email,
            full_name="Admin Reporting",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.admin)

        cls.viewer_email = f"viewer_rpt_{cls.suffix}@acrip.com"
        cls.viewer = User(
            id=str(uuid.uuid4()),
            email=cls.viewer_email,
            full_name="Viewer Reporting",
            hashed_password=hash_password("Viewer@123"),
            role=UserRole.VIEWER,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.viewer)

        # 2. Project and Site
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-RPT-{cls.suffix.upper()}",
            name="Reporting Intelligence Test Project",
            client="Global Construction Corp",
            status=ProjectStatus.ACTIVE,
            manager_id=cls.admin.id,
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.project)

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SIT-RPT-{cls.suffix.upper()}",
            name="Austin Metro Tower Site",
            site_type="Commercial High-Rise",
            project_id=cls.project.id,
            manager_id=cls.admin.id,
            status=SiteStatus.ACTIVE,
            current_risk_score=58.5,
            risk_category=RiskCategory.HIGH,
            city="Austin",
            state="TX",
            worker_count=45,
            equipment_count=12,
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.site)

        # Empty site for missing-data tests
        cls.empty_site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SIT-EMP-{cls.suffix.upper()}",
            name="Empty Greenfield Site",
            site_type="Residential",
            project_id=cls.project.id,
            status=SiteStatus.ACTIVE,
            current_risk_score=10.0,
            risk_category=RiskCategory.LOW,
            city="Round Rock",
            state="TX",
            worker_count=5,
            equipment_count=2,
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.empty_site)

        # 3. Agent Findings for main site:
        # A. Site Risk: Hazard
        cls.hazard = Hazard(
            id=str(uuid.uuid4()),
            hazard_id=f"HAZ-AI-{cls.suffix.upper()}-01",
            site_id=cls.site.id,
            hazard_type=HazardType.EXCAVATION,
            description="Trench wall instability with active excavation and saturated soil",
            evidence="Water accumulation detected in excavation zone",
            severity=4,
            probability=4,
            risk_score=64.0,
            risk_category=RiskCategory.HIGH,
            status=HazardStatus.OPEN,
            recommended_action="Immediately pump standing water and shore trench walls",
            detection_source="RULE_ENGINE",
            detected_at=datetime.utcnow(),
        )
        cls.db.add(cls.hazard)

        # B. Safety: SafetyFinding
        cls.safety_finding = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SAF-FND-{cls.suffix.upper()}-01",
            site_id=cls.site.id,
            finding_type=SafetyFindingType.PPE_VIOLATION,
            description="Worker observed without mandatory safety vest in active crane perimeter",
            evidence="Vision sensory bounding box confirmation",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
            recommendation="Issue immediate PPE replacement and safety briefing",
            detection_source="RULE_ENGINE",
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.safety_finding)

        # C. Compliance: ComplianceFinding
        cls.compliance_finding = ComplianceFinding(
            id=str(uuid.uuid4()),
            finding_id=f"CMP-FND-{cls.suffix.upper()}-01",
            site_id=cls.site.id,
            standard_ref="OSHA 1926.651(c)(2)",
            violation_type="MISSING_TRENCH_EGRESS",
            description="Excavation trench exceeding 4ft depth lacks safe egress stairway or ladder within 25ft",
            severity=RiskCategory.CRITICAL,
            status=SafetyFindingStatus.OPEN,
            recommendation="Place approved ladder into trench zone immediately",
            evidence="Photographic evidence logged",
            detection_source="COMPLIANCE_AGENT",
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.compliance_finding)

        # D. Insurance: Claim Assessment
        cls.insurance_claim = InsuranceClaimAssessment(
            id=str(uuid.uuid4()),
            claim_assessment_id=f"CLM-{cls.suffix.upper()}-01",
            site_id=cls.site.id,
            incident_ref=f"INC-{cls.suffix.upper()}-001",
            incident_title="Hydraulic Boom Pressure Loss on Excavator",
            incident_date=datetime.utcnow(),
            incident_severity=RiskCategory.HIGH,
            claim_risk_level=ClaimRiskLevel.MODERATE,
            claim_probability_pct=65.0,
            documentation_completeness_pct=75.0,
            status="UNDER_REVIEW",
            potential_claim_indicators=["Overdue Hydraulic Certification"],
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.insurance_claim)

        # E. Insurance Risk Assessment
        cls.insurance_assessment = InsuranceRiskAssessment(
            id=str(uuid.uuid4()),
            assessment_id=f"INS-ASM-{cls.suffix.upper()}-01",
            site_id=cls.site.id,
            insurance_risk_score=42.5,
            insurance_risk_level=InsuranceRiskLevel.MEDIUM,
            exposure_index=45.0,
            estimated_liability_exposure="MODERATE ($100k - $250k)",
            created_at=datetime.utcnow(),
        )
        cls.db.add(cls.insurance_assessment)

        cls.db.commit()

        # Auth tokens
        cls.admin_token = create_access_token({"sub": cls.admin.id, "email": cls.admin.email, "role": cls.admin.role.value})
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

        cls.viewer_token = create_access_token({"sub": cls.viewer.id, "email": cls.viewer.email, "role": cls.viewer.role.value})
        cls.viewer_headers = {"Authorization": f"Bearer {cls.viewer_token}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # ── Test 1: Agent Initialization ─────────────────────────────────────────
    def test_01_reporting_agent_initialization(self):
        agent = ReportingAgent()
        self.assertEqual(agent.agent_id, "reporting_agent_v1")
        self.assertEqual(agent.name, "Reporting Agent")
        self.assertTrue(agent.is_active)

        health = asyncio.run(agent.health_check())
        self.assertTrue(health)

        status = agent.get_status()
        self.assertEqual(status["status"], "active")

        # Check Orchestrator registration
        self.assertIn("reporting", orchestrator.agents)
        self.assertTrue(orchestrator.agents["reporting"].is_active)
        orch_health = asyncio.run(orchestrator.agents["reporting"].health_check())
        self.assertTrue(orch_health)

    # ── Test 2: Site Risk Normalization ──────────────────────────────────────
    def test_02_site_risk_normalization(self):
        norm = normalize_site_risk_hazard(self.hazard)
        self.assertIsInstance(norm, NormalizedFinding)
        self.assertEqual(norm.source_agent, "site_risk")
        self.assertEqual(norm.finding_id, self.hazard.hazard_id)
        self.assertEqual(norm.severity, "HIGH")
        self.assertEqual(norm.status, "OPEN")
        self.assertIn("Trench wall instability", norm.description)
        self.assertIsNotNone(norm.recommendation)
        self.assertEqual(norm.metadata["detection_source"], "RULE_ENGINE")

    # ── Test 3: Safety Findings Normalization ────────────────────────────────
    def test_03_safety_normalization(self):
        norm = normalize_safety_finding(self.safety_finding)
        self.assertIsInstance(norm, NormalizedFinding)
        self.assertEqual(norm.source_agent, "safety")
        self.assertEqual(norm.finding_id, self.safety_finding.finding_id)
        self.assertEqual(norm.severity, "HIGH")
        self.assertEqual(norm.status, "OPEN")
        self.assertIn("Worker observed without", norm.description)

        # Test safety alert normalization
        alert = SafetyAlert(
            id=str(uuid.uuid4()),
            alert_id=f"ALT-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            title="Critical Zone Breach",
            description="Unauthorized worker in swing radius",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.OPEN,
            recommendation="Halt crane immediately",
            created_at=datetime.utcnow(),
        )
        norm_alert = normalize_safety_alert(alert)
        self.assertEqual(norm_alert.source_agent, "safety")
        self.assertEqual(norm_alert.severity, "CRITICAL")
        self.assertEqual(norm_alert.status, "OPEN")

    # ── Test 4: Compliance Normalization ────────────────────────────────────
    def test_04_compliance_normalization(self):
        norm = normalize_compliance_finding(self.compliance_finding)
        self.assertIsInstance(norm, NormalizedFinding)
        self.assertEqual(norm.source_agent, "compliance")
        self.assertEqual(norm.finding_id, self.compliance_finding.finding_id)
        self.assertEqual(norm.severity, "CRITICAL")
        self.assertEqual(norm.metadata["standard_ref"], "OSHA 1926.651(c)(2)")

    # ── Test 5: Insurance Normalization ─────────────────────────────────────
    def test_05_insurance_normalization(self):
        norm = normalize_insurance_claim(self.insurance_claim)
        self.assertIsInstance(norm, NormalizedFinding)
        self.assertEqual(norm.source_agent, "insurance")
        self.assertEqual(norm.finding_id, self.insurance_claim.claim_assessment_id)
        self.assertEqual(norm.metadata["incident_ref"], self.insurance_claim.incident_ref)
        self.assertEqual(norm.metadata["claim_probability_pct"], 65.0)

    # ── Test 6: Combined 4-Agent Aggregation ─────────────────────────────────
    def test_06_combined_four_agent_aggregation(self):
        aggregator = ReportAggregationService()
        result = aggregator.aggregate_site_data(db=self.db, site_id=self.site.id)

        self.assertIn("site", result)
        self.assertIn("metrics", result)
        self.assertIn("findings", result)

        metrics = result["metrics"]
        self.assertGreaterEqual(metrics["total_findings"], 4)
        self.assertGreaterEqual(metrics["critical_count"], 1)
        self.assertGreaterEqual(metrics["high_count"], 2)

        # Check all 4 agents represented
        self.assertGreaterEqual(metrics["by_agent"]["site_risk"], 1)
        self.assertGreaterEqual(metrics["by_agent"]["safety"], 1)
        self.assertGreaterEqual(metrics["by_agent"]["compliance"], 1)
        self.assertGreaterEqual(metrics["by_agent"]["insurance"], 1)

    # ── Test 7: Empty Agent Results Graceful Handling ────────────────────────
    def test_07_empty_agent_results_graceful_handling(self):
        aggregator = ReportAggregationService()
        result = aggregator.aggregate_site_data(db=self.db, site_id=self.empty_site.id)

        self.assertEqual(result["metrics"]["total_findings"], 0)
        self.assertEqual(result["metrics"]["critical_count"], 0)
        self.assertEqual(result["metrics"]["by_agent"]["compliance"], 0)
        self.assertEqual(result["metrics"]["by_agent"]["insurance"], 0)

        # Generate report with empty data
        gen = ReportGenerator()
        daily = gen.generate_daily_site_report(result)
        self.assertEqual(daily["compliance_findings"]["items"], "No findings available")
        self.assertEqual(daily["insurance_findings"]["items"], "No findings available")
        self.assertEqual(daily["site_hazards"]["items"], "No findings available")
        self.assertEqual(daily["overall_condition"]["status"], "OPTIMAL")

    # ── Test 8: Daily Site Report Generation ────────────────────────────────
    def test_08_daily_site_report_generation(self):
        aggregator = ReportAggregationService()
        agg_data = aggregator.aggregate_site_data(db=self.db, site_id=self.site.id)

        gen = ReportGenerator()
        report = gen.generate_daily_site_report(agg_data)

        self.assertEqual(report["report_type"], "DAILY_SITE")
        self.assertIn("Daily Construction Site Report", report["report_title"])
        self.assertIn("reporting_date", report)
        self.assertIn("site_information", report)
        self.assertEqual(report["site_information"]["site_name"], self.site.name)
        self.assertIn("overall_condition", report)
        self.assertIn("risk_overview", report)
        self.assertIn("site_hazards", report)
        self.assertIn("safety_violations", report)
        self.assertIn("ppe_findings", report)
        self.assertIn("compliance_findings", report)
        self.assertIn("insurance_findings", report)
        self.assertIn("important_alerts", report)
        self.assertIn("recommended_actions", report)
        self.assertGreater(len(report["recommended_actions"]), 0)

    # ── Test 9: Executive Risk Summary Generation ───────────────────────────
    def test_09_executive_risk_summary_generation(self):
        aggregator = ReportAggregationService()
        agg_data = aggregator.aggregate_site_data(db=self.db, site_id=self.site.id)

        gen = ReportGenerator()
        report = gen.generate_executive_risk_summary(agg_data)

        self.assertEqual(report["report_type"], "EXECUTIVE_SUMMARY")
        self.assertIn("executive_narrative", report)
        self.assertIn("risk_scorecard", report)
        self.assertIn("site_risk", report["risk_scorecard"])
        self.assertIn("safety_performance", report["risk_scorecard"])
        self.assertIn("compliance_status", report["risk_scorecard"])
        self.assertIn("insurance_exposure", report["risk_scorecard"])
        self.assertIn("high_priority_recommendations", report)
        self.assertIn("trend_information", report)

    # ── Test 10: Audit-Ready Documentation Generation ───────────────────────
    def test_10_audit_ready_documentation_generation(self):
        aggregator = ReportAggregationService()
        agg_data = aggregator.aggregate_site_data(db=self.db, site_id=self.site.id)

        gen = ReportGenerator()
        report = gen.generate_audit_ready_report(agg_data)

        self.assertEqual(report["report_type"], "AUDIT_READY")
        self.assertIn("audit_dossier_id", report)
        self.assertTrue(report["audit_dossier_id"].startswith("AUD-ACRIP-"))
        self.assertIn("reporting_period", report)
        self.assertIn("traceable_finding_records", report)
        self.assertIsInstance(report["traceable_finding_records"], list)
        self.assertGreater(len(report["traceable_finding_records"]), 0)

        # Check traceability of first record
        first = report["traceable_finding_records"][0]
        self.assertIn("finding_id", first)
        self.assertIn("source_agent", first)
        self.assertIn("standard_reference", first)
        self.assertIn("description", first)
        self.assertIn("severity", first)
        self.assertIn("status", first)

        self.assertIn("compliance_attestation", report)

    # ── Test 11: Project Health Report Generation ───────────────────────────
    def test_11_project_health_report_generation(self):
        aggregator = ReportAggregationService()
        agg_data = aggregator.aggregate_site_data(db=self.db, site_id=self.site.id)

        gen = ReportGenerator()
        report = gen.generate_project_health_report(agg_data)

        self.assertEqual(report["report_type"], "PROJECT_HEALTH")
        self.assertIn("composite_health", report)
        self.assertIn("health_grade", report["composite_health"])
        self.assertIn("composite_index_pct", report["composite_health"])
        self.assertIn("four_pillars", report)
        self.assertIn("site_risk", report["four_pillars"])
        self.assertIn("safety", report["four_pillars"])
        self.assertIn("compliance", report["four_pillars"])
        self.assertIn("insurance", report["four_pillars"])
        self.assertIn("cross_pillar_recommendations", report)

    # ── Test 12: Invalid Input Handling ─────────────────────────────────────
    def test_12_invalid_input_handling(self):
        service = ReportingService()
        with self.assertRaises(ValueError):
            service.generate_and_save_report(
                db=self.db,
                site_id="non-existent-site-id-9999",
                report_type=ReportType.DAILY_SITE
            )

        # Invalid report ID in API returns 404
        res = self.client.get("/api/v1/reports/non-existent-report-id", headers=self.admin_headers)
        self.assertEqual(res.status_code, 404)

    # ── Test 13: Report Persistence and Database Retrieval ───────────────────
    def test_13_report_persistence_and_retrieval(self):
        service = ReportingService()
        created = service.generate_and_save_report(
            db=self.db,
            site_id=self.site.id,
            report_type=ReportType.DAILY_SITE,
            title="Automated Test Daily Report",
            created_by="UnitTester"
        )

        self.assertIsNotNone(created.id)
        self.assertTrue(created.report_id.startswith("DSR-"))
        self.assertEqual(created.status, ReportStatus.COMPLETED)
        self.assertEqual(created.title, "Automated Test Daily Report")

        # Fetch by primary key id
        fetched = service.get_report(self.db, created.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.report_id, created.report_id)

        # Fetch by human-readable report_id
        fetched_by_code = service.get_report(self.db, created.report_id)
        self.assertIsNotNone(fetched_by_code)
        self.assertEqual(fetched_by_code.id, created.id)

        # List reports
        reports = service.list_reports(self.db, site_id=self.site.id)
        self.assertGreaterEqual(len(reports), 1)

        # Delete report
        deleted = service.delete_report(self.db, created.id)
        self.assertTrue(deleted)
        self.assertIsNone(service.get_report(self.db, created.id))

    # ── Test 14: REST API Endpoints ─────────────────────────────────────────
    def test_14_api_endpoints(self):
        # 1. GET /reports/types
        res_types = self.client.get("/api/v1/reports/types", headers=self.admin_headers)
        self.assertEqual(res_types.status_code, 200)
        types_data = res_types.json()
        self.assertEqual(len(types_data), 4)
        type_keys = [t["type"] for t in types_data]
        self.assertIn("DAILY_SITE", type_keys)
        self.assertIn("EXECUTIVE_SUMMARY", type_keys)
        self.assertIn("AUDIT_READY", type_keys)
        self.assertIn("PROJECT_HEALTH", type_keys)

        # 2. POST /reports/generate
        payload = {
            "site_id": self.site.id,
            "report_type": "EXECUTIVE_SUMMARY",
            "title": "API Generated Executive Summary"
        }
        res_gen = self.client.post("/api/v1/reports/generate", json=payload, headers=self.admin_headers)
        self.assertEqual(res_gen.status_code, 201)
        gen_data = res_gen.json()
        self.assertEqual(gen_data["report_type"], "EXECUTIVE_SUMMARY")
        self.assertIn("EXS-", gen_data["report_id"])
        report_id = gen_data["id"]

        # 3. GET /reports
        res_list = self.client.get(f"/api/v1/reports?site_id={self.site.id}", headers=self.admin_headers)
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        # 4. GET /reports/{id}
        res_get = self.client.get(f"/api/v1/reports/{report_id}", headers=self.admin_headers)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], report_id)
        self.assertIn("content", res_get.json())

        # 5. DELETE /reports/{id} with viewer should be forbidden (403)
        res_del_forbidden = self.client.delete(f"/api/v1/reports/{report_id}", headers=self.viewer_headers)
        self.assertEqual(res_del_forbidden.status_code, 403)

        # 6. DELETE /reports/{id} with admin
        res_del = self.client.delete(f"/api/v1/reports/{report_id}", headers=self.admin_headers)
        self.assertEqual(res_del.status_code, 200)

    # ── Test 15: Agent Orchestrator Integration ──────────────────────────────
    def test_15_orchestrator_integration(self):
        context = {
            "site_id": self.site.id,
            "site_name": self.site.name,
            "report_type": "PROJECT_HEALTH",
            "hazards": [
                {
                    "hazard_id": "HAZ-TEST-01",
                    "hazard_type": "FALL_HAZARD",
                    "description": "Unguarded platform edge at height",
                    "risk_category": "HIGH",
                    "status": "OPEN",
                    "recommended_action": "Install safety guardrails",
                }
            ],
            "safety_findings": [
                {
                    "finding_id": "SAF-TEST-01",
                    "finding_type": "PPE_VIOLATION",
                    "description": "No hard hat",
                    "severity": "MEDIUM",
                    "status": "OPEN",
                }
            ],
            "compliance_findings": [
                {
                    "finding_id": "CMP-TEST-01",
                    "standard_ref": "OSHA 1926.501",
                    "description": "Missing guardrails",
                    "severity": "HIGH",
                    "status": "OPEN",
                }
            ],
            "insurance_claims": [
                {
                    "claim_assessment_id": "CLM-TEST-01",
                    "incident_title": "Fall near edge",
                    "incident_ref": "INC-01",
                    "claim_risk_level": "MODERATE",
                    "claim_probability_pct": 40.0,
                }
            ],
        }

        result = asyncio.run(orchestrator.run_agent("reporting", context))
        self.assertEqual(result["report_type"], "PROJECT_HEALTH")
        self.assertIn("agent_metadata", result)
        self.assertEqual(result["agent_metadata"]["agent_id"], "reporting_agent_v1")
        self.assertIn("four_pillars", result)
        self.assertEqual(result["four_pillars"]["site_risk"]["active_hazards"], 1)


if __name__ == "__main__":
    unittest.main()
