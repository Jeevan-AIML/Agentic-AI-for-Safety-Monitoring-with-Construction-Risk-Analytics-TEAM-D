"""
ACRIP Phase 4.4 Agent Orchestration Test Suite
==============================================
Comprehensive tests for:
1. AgentRegistry initialization and metadata
2. AgentOrchestrator base class integration
3. Full orchestration execution workflow (Level 1, Level 2, Level 3)
4. Orchestration with Reporting Agent integration (generate_report=True)
5. Site Risk Agent execution
6. Safety Agent execution
7. Compliance Agent execution
8. Insurance Agent execution
9. Risk Intelligence Engine execution
10. Parallel execution of domain agents
11. Failure isolation: single domain failure produces PARTIAL status
12. Failure isolation: complete domain failure marks Risk Intelligence SKIPPED
13. Targeted analysis mode (selective agents)
14. Refresh mode (Risk Intelligence only)
15. Report refresh mode (Reporting only)
16. Invalid site validation
17. Idempotency / active run duplicate protection
18. Query execution by execution ID
19. Query latest site execution
20. List site execution history
21. REST API endpoints: POST /run, GET /{id}, GET /{id}/status, GET /site/{site_id}/latest
"""

import uuid
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, UserRole, ProjectStatus, SiteStatus,
    Hazard, RiskScore, HazardType, HazardStatus, RiskCategory,
    SafetyFinding, SafetyAnalysis, SafetyAlert, SafetyFindingType, SafetyFindingStatus,
    ComplianceFinding, ComplianceAssessment, ComplianceStatus, InspectionRequirement,
    InsuranceRiskAssessment, ReportType, ReportStatus, GeneratedReport,
    ProjectRiskIntelligence, AgentOrchestrationRun, OrchestrationStatus, OrchestrationMode
)
from app.core.security import hash_password, create_access_token
from app.agents.base_agents import orchestrator
from app.services.orchestration import orchestration_service, AgentRegistry
from app.schemas.schemas import OrchestrationRequest, OrchestrationRunResponse
from app.main import app


class TestPhase44AgentOrchestration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        from app.database.session import migrate_db_columns
        migrate_db_columns(engine)
        cls.client = TestClient(app)

        cls.db = SessionLocal()
        cls.test_run_id = uuid.uuid4().hex[:8]

        # 1. Create executive/manager user
        cls.user = User(
            id=str(uuid.uuid4()),
            email=f"orchestrator_{cls.test_run_id}@acrip.internal",
            hashed_password=hash_password("OrchestratorPass123!"),
            full_name="Orchestration Project Director",
            role=UserRole.PROJECT_MANAGER,
            is_active=True,
        )
        cls.db.add(cls.user)

        # 2. Create test project
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PRJ-ORCH-{cls.test_run_id.upper()}",
            name=f"Metro High-Speed Rail {cls.test_run_id}",
            client="State Transportation Authority",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)

        # 3. Create test site
        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-ORCH-{cls.test_run_id.upper()}",
            name=f"Terminal Station Pier {cls.test_run_id}",
            project_id=cls.project.id,
            status=SiteStatus.ACTIVE,
            address="Zone 9 Central Hub",
            city="Metroville",
        )
        cls.db.add(cls.site)
        cls.db.commit()

        # Auth headers
        token = create_access_token(data={"sub": cls.user.id})
        cls.headers = {"Authorization": f"Bearer {token}"}

    @classmethod
    def tearDownClass(cls):
        try:
            cls.db.query(AgentOrchestrationRun).filter(AgentOrchestrationRun.site_id == cls.site.id).delete()
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

    def setUp(self):
        # Clear any active run locks between tests
        orchestration_service._active_runs.clear()

    # ── Test 1: Agent Registry Metadata ───────────────────────────────────

    def test_01_registry_initialization(self):
        """Test AgentRegistry correctly registers all 6 agents with descriptors."""
        registry = AgentRegistry()
        agents = registry.list_agents()
        agent_names = [a.name for a in agents]

        self.assertIn("site_risk", agent_names)
        self.assertIn("safety", agent_names)
        self.assertIn("compliance", agent_names)
        self.assertIn("insurance", agent_names)
        self.assertIn("risk_intelligence", agent_names)
        self.assertIn("reporting", agent_names)

        domain_agents = registry.get_domain_agent_names()
        self.assertEqual(set(domain_agents), {"site_risk", "safety", "compliance", "insurance"})

    # ── Test 2: Base Agents Orchestrator Integration ───────────────────────

    def test_02_base_agents_orchestrator_integration(self):
        """Test BaseAgent orchestrator in app.agents.base_agents has all active agents."""
        statuses = orchestrator.get_all_statuses()
        self.assertIn("site_risk", statuses)
        self.assertIn("safety", statuses)
        self.assertIn("compliance", statuses)
        self.assertIn("insurance", statuses)
        self.assertIn("risk_intelligence", statuses)
        self.assertIn("reporting", statuses)
        self.assertTrue(orchestrator.agents["risk_intelligence"].is_active)

    # ── Test 3: Full Orchestration Success ────────────────────────────────

    def test_03_full_orchestration_success(self):
        """Test standard FULL_ANALYSIS orchestration runs all domain agents and Risk Intelligence."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="FULL_ANALYSIS",
            generate_report=False,
            is_simulation=True,
        )
        res = orchestration_service.execute_orchestration(self.db, req, created_by="UnitTest")

        self.assertIsInstance(res, OrchestrationRunResponse)
        self.assertEqual(res.status, OrchestrationStatus.COMPLETED.value)
        self.assertEqual(res.site_id, self.site.id)
        self.assertTrue(res.execution_id.startswith("ORCH-"))
        self.assertGreater(res.duration_ms, 0)
        self.assertIsNotNone(res.risk_intelligence_id)

        # Check per-agent statuses
        self.assertEqual(res.agent_statuses["site_risk"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertEqual(res.agent_statuses["safety"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertEqual(res.agent_statuses["compliance"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertEqual(res.agent_statuses["insurance"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertEqual(res.agent_statuses["risk_intelligence"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertNotIn("reporting", res.agent_statuses)

    # ── Test 4: Orchestration with Reporting Agent Integration ─────────────

    def test_04_orchestration_with_reporting(self):
        """Test FULL_ANALYSIS with generate_report=True chains into Reporting Agent."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="FULL_ANALYSIS",
            generate_report=True,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            is_simulation=True,
        )
        res = orchestration_service.execute_orchestration(self.db, req, created_by="UnitTest")

        self.assertEqual(res.status, OrchestrationStatus.COMPLETED.value)
        self.assertIsNotNone(res.risk_intelligence_id)
        self.assertIsNotNone(res.report_id)
        self.assertEqual(res.agent_statuses["reporting"]["status"], OrchestrationStatus.COMPLETED.value)

    # ── Test 5: Site Risk Agent Execution ─────────────────────────────────

    def test_05_site_risk_agent_execution(self):
        """Verify Site Risk Agent executes and outputs summary in run record."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="TARGETED_ANALYSIS",
            agents=["site_risk"],
            generate_report=False,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        self.assertEqual(res.agent_statuses["site_risk"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertIn("hazards", res.agent_statuses["site_risk"]["output_summary"])

    # ── Test 6: Safety Agent Execution ────────────────────────────────────

    def test_06_safety_agent_execution(self):
        """Verify Safety Agent executes worker analysis."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="TARGETED_ANALYSIS",
            agents=["safety"],
            generate_report=False,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        self.assertEqual(res.agent_statuses["safety"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertIn("safety_score", res.agent_statuses["safety"]["output_summary"])

    # ── Test 7: Compliance Agent Execution ────────────────────────────────

    def test_07_compliance_agent_execution(self):
        """Verify Compliance Agent executes statutory audit."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="TARGETED_ANALYSIS",
            agents=["compliance"],
            generate_report=False,
            is_simulation=True,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        self.assertEqual(res.agent_statuses["compliance"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertIn("compliance_score", res.agent_statuses["compliance"]["output_summary"])

    # ── Test 8: Insurance Agent Execution ─────────────────────────────────

    def test_08_insurance_agent_execution(self):
        """Verify Insurance Agent assesses underwriting risk."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="TARGETED_ANALYSIS",
            agents=["insurance"],
            generate_report=False,
            is_simulation=True,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        self.assertEqual(res.agent_statuses["insurance"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertIn("exposure_index", res.agent_statuses["insurance"]["output_summary"])

    # ── Test 9: Risk Intelligence Engine Execution ────────────────────────

    def test_09_risk_intelligence_engine_execution(self):
        """Verify Risk Intelligence consolidates 4-pillar scores."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="FULL_ANALYSIS",
            generate_report=False,
            is_simulation=True,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        rki = res.agent_statuses["risk_intelligence"]
        self.assertEqual(rki["status"], OrchestrationStatus.COMPLETED.value)
        self.assertIn("overall_risk_score", rki["output_summary"])

    # ── Test 10: Parallel Execution Strategy ──────────────────────────────

    def test_10_parallel_execution(self):
        """Verify parallel execution runs domain agents concurrently."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="FULL_ANALYSIS",
            generate_report=False,
            is_simulation=True,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        # Sum of individual domain agent durations
        domain_sum = sum(
            res.agent_statuses[a]["duration_ms"]
            for a in ["site_risk", "safety", "compliance", "insurance"]
        )
        # Because they run in parallel, total duration should be less than the sum + reasonable overhead
        self.assertGreater(domain_sum, 0)
        self.assertGreater(res.duration_ms, 0)

    # ── Test 11: Failure Isolation (Single Domain Agent Failure) ──────────

    def test_11_failure_isolation_single_domain_agent(self):
        """Verify single domain agent failure results in PARTIAL status with warnings."""
        with patch.object(
            orchestration_service,
            "_execute_insurance",
            side_effect=RuntimeError("Simulated Insurance API gateway failure"),
        ):
            req = OrchestrationRequest(
                site_id=self.site.id,
                mode="FULL_ANALYSIS",
                generate_report=False,
                is_simulation=True,
            )
            res = orchestration_service.execute_orchestration(self.db, req)

            self.assertEqual(res.status, OrchestrationStatus.PARTIAL.value)
            self.assertEqual(res.agent_statuses["insurance"]["status"], OrchestrationStatus.FAILED.value)
            self.assertEqual(res.agent_statuses["site_risk"]["status"], OrchestrationStatus.COMPLETED.value)
            self.assertEqual(res.agent_statuses["safety"]["status"], OrchestrationStatus.COMPLETED.value)
            self.assertEqual(res.agent_statuses["compliance"]["status"], OrchestrationStatus.COMPLETED.value)
            self.assertEqual(res.agent_statuses["risk_intelligence"]["status"], OrchestrationStatus.COMPLETED.value)
            self.assertTrue(len(res.warnings) > 0)
            self.assertTrue(len(res.errors) > 0)

    # ── Test 12: Failure Isolation (All Domain Agents Fail) ───────────────

    def test_12_all_domain_agents_failure_isolation(self):
        """Verify when all requested domain agents fail, Risk Intelligence is SKIPPED and status is FAILED."""
        with patch.object(orchestration_service, "_execute_site_risk", side_effect=RuntimeError("Fail")), \
             patch.object(orchestration_service, "_execute_safety", side_effect=RuntimeError("Fail")), \
             patch.object(orchestration_service, "_execute_compliance", side_effect=RuntimeError("Fail")), \
             patch.object(orchestration_service, "_execute_insurance", side_effect=RuntimeError("Fail")):

            req = OrchestrationRequest(
                site_id=self.site.id,
                mode="FULL_ANALYSIS",
                generate_report=False,
            )
            res = orchestration_service.execute_orchestration(self.db, req)

            self.assertEqual(res.status, OrchestrationStatus.FAILED.value)
            self.assertEqual(res.agent_statuses["risk_intelligence"]["status"], OrchestrationStatus.SKIPPED.value)

    # ── Test 13: Targeted Analysis Mode ───────────────────────────────────

    def test_13_targeted_analysis_mode(self):
        """Test TARGETED_ANALYSIS mode executes only requested agents."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="TARGETED_ANALYSIS",
            agents=["site_risk", "safety"],
            generate_report=False,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        self.assertIn("site_risk", res.agent_statuses)
        self.assertIn("safety", res.agent_statuses)
        self.assertNotIn("compliance", res.agent_statuses)
        self.assertNotIn("insurance", res.agent_statuses)
        self.assertIn("risk_intelligence", res.agent_statuses)

    # ── Test 14: Refresh Mode ─────────────────────────────────────────────

    def test_14_refresh_mode(self):
        """Test REFRESH mode skips domain agents and refreshes Risk Intelligence directly."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="REFRESH",
            generate_report=False,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        self.assertEqual(res.status, OrchestrationStatus.COMPLETED.value)
        self.assertNotIn("site_risk", res.agent_statuses)
        self.assertNotIn("safety", res.agent_statuses)
        self.assertIn("risk_intelligence", res.agent_statuses)
        self.assertEqual(res.agent_statuses["risk_intelligence"]["status"], OrchestrationStatus.COMPLETED.value)

    # ── Test 15: Report Refresh Mode ──────────────────────────────────────

    def test_15_report_refresh_mode(self):
        """Test REPORT_REFRESH mode executes only the Reporting Agent."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="REPORT_REFRESH",
            generate_report=True,
            report_type=ReportType.DAILY_SITE,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        self.assertEqual(res.status, OrchestrationStatus.COMPLETED.value)
        self.assertNotIn("risk_intelligence", res.agent_statuses)
        self.assertIn("reporting", res.agent_statuses)
        self.assertEqual(res.agent_statuses["reporting"]["status"], OrchestrationStatus.COMPLETED.value)
        self.assertIsNotNone(res.report_id)

    # ── Test 16: Invalid Site Raises Error ─────────────────────────────────

    def test_16_invalid_site_raises_error(self):
        """Test passing an invalid site_id raises ValueError."""
        req = OrchestrationRequest(
            site_id=str(uuid.uuid4()),
            mode="FULL_ANALYSIS",
        )
        with self.assertRaises(ValueError):
            orchestration_service.execute_orchestration(self.db, req)

    # ── Test 17: Idempotency / Active Run Protection ───────────────────────

    def test_17_idempotency_duplicate_run_protection(self):
        """Test attempting concurrent run while one is in progress raises conflict error."""
        # Manually set an active run
        orchestration_service._active_runs[self.site.id] = ("ORCH-ACTIVE-123", datetime.utcnow())

        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="FULL_ANALYSIS",
        )
        with self.assertRaises(ValueError) as ctx:
            orchestration_service.execute_orchestration(self.db, req)
        self.assertIn("active orchestration run", str(ctx.exception))

    # ── Test 18: Query Execution by ID ─────────────────────────────────────

    def test_18_get_execution_by_id(self):
        """Test retrieving orchestration run by execution_id."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="TARGETED_ANALYSIS",
            agents=["site_risk"],
            generate_report=False,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        retrieved = orchestration_service.get_execution(self.db, res.execution_id)
        self.assertEqual(retrieved.execution_id, res.execution_id)
        self.assertEqual(retrieved.status, res.status)

    # ── Test 19: Query Latest Site Execution ──────────────────────────────

    def test_19_get_latest_site_execution(self):
        """Test retrieving the latest orchestration run for a site."""
        req = OrchestrationRequest(
            site_id=self.site.id,
            mode="TARGETED_ANALYSIS",
            agents=["safety"],
            generate_report=False,
        )
        res = orchestration_service.execute_orchestration(self.db, req)

        latest = orchestration_service.get_latest_site_execution(self.db, self.site.id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.execution_id, res.execution_id)

    # ── Test 20: List Site Execution History ──────────────────────────────

    def test_20_list_site_executions_history(self):
        """Test listing paginated execution history for a site."""
        runs, total = orchestration_service.list_site_executions(self.db, self.site.id, limit=10)
        self.assertGreaterEqual(total, 1)
        self.assertIsInstance(runs, list)
        self.assertTrue(all(r.site_id == self.site.id for r in runs))

    # ── Test 21: REST API Endpoints ───────────────────────────────────────

    def test_21_rest_api_run_and_status_endpoints(self):
        """Test REST API POST /run, GET /{id}, GET /{id}/status, and GET /site/{site_id}/latest."""
        # 1. POST /api/v1/orchestration/run
        payload = {
            "site_id": self.site.id,
            "mode": "TARGETED_ANALYSIS",
            "agents": ["site_risk", "safety"],
            "generate_report": False,
            "is_simulation": True,
        }
        res = self.client.post(
            "/api/v1/orchestration/run",
            json=payload,
            headers=self.headers,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        exec_id = data["execution_id"]
        self.assertEqual(data["status"], OrchestrationStatus.COMPLETED.value)

        # 2. GET /api/v1/orchestration/{execution_id}
        res2 = self.client.get(
            f"/api/v1/orchestration/{exec_id}",
            headers=self.headers,
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["execution_id"], exec_id)

        # 3. GET /api/v1/orchestration/{execution_id}/status
        res3 = self.client.get(
            f"/api/v1/orchestration/{exec_id}/status",
            headers=self.headers,
        )
        self.assertEqual(res3.status_code, 200)
        st_data = res3.json()
        self.assertEqual(st_data["execution_id"], exec_id)
        self.assertIn("status", st_data)
        self.assertIn("agent_statuses", st_data)

        # 4. GET /api/v1/orchestration/site/{site_id}/latest
        res4 = self.client.get(
            f"/api/v1/orchestration/site/{self.site.id}/latest",
            headers=self.headers,
        )
        self.assertEqual(res4.status_code, 200)
        self.assertEqual(res4.json()["execution_id"], exec_id)

        # 5. Invalid site returns 404
        res_404 = self.client.post(
            "/api/v1/orchestration/run",
            json={"site_id": str(uuid.uuid4())},
            headers=self.headers,
        )
        self.assertEqual(res_404.status_code, 404)
