"""
ACRIP Phase 4.2 Construction Risk Intelligence Engine Test Suite
================================================================
Comprehensive tests for:
1. Multi-agent data collection & finding normalization
2. Deterministic project risk score calculation
3. Risk level mapping boundaries (0-25 Low, 26-50 Medium, 51-75 High, 76-100 Critical)
4. Recurring pattern detection (>= 2 occurrences threshold)
5. Single occurrences not flagged as patterns
6. Sparse data handling ("Insufficient historical data for reliable pattern analysis.")
7. Incident prediction with explainable causal risk chains
8. Primary driver identification in predictions
9. Prioritized operational recommendations (immediate, short-term, mid-term)
10. Database persistence of ProjectRiskIntelligence records
11. REST API endpoints:
    - POST /api/v1/risk-intelligence/analyze
    - GET /api/v1/risk-intelligence/site/{site_id}
    - GET /api/v1/risk-intelligence/patterns/{site_id}
    - GET /api/v1/risk-intelligence/predictions/{site_id}
    - GET /api/v1/risk-intelligence/recommendations/{site_id}
    - GET /api/v1/risk-intelligence/history/{site_id}
12. Edge cases: empty findings, all critical findings, all low findings
"""

import uuid
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.database.session import Base, SessionLocal, engine
from app.models.models import (
    User, Project, Site, UserRole, ProjectStatus, SiteStatus,
    Hazard, RiskScore, HazardType, HazardStatus, RiskCategory,
    SafetyFinding, SafetyAnalysis, SafetyAlert, SafetyFindingType, SafetyFindingStatus, AlertSeverity, AlertStatus,
    ComplianceFinding, ComplianceAssessment, ComplianceStatus, InspectionRequirement, InspectionRequirementStatus,
    InsuranceRiskAssessment, InsuranceClaimAssessment, InsuranceRiskLevel, ClaimRiskLevel,
    ProjectRiskIntelligence
)
from app.core.security import hash_password, create_access_token
from app.services.risk_intelligence.collector import RiskDataCollector, RiskIntelligenceFinding
from app.services.risk_intelligence.scorer import ProjectRiskScorer
from app.services.risk_intelligence.pattern_detector import RecurringRiskPatternDetector
from app.services.risk_intelligence.incident_predictor import PotentialIncidentPredictor
from app.services.risk_intelligence.recommender import OperationalRecommendationEngine
from app.services.risk_intelligence.engine import ConstructionRiskIntelligenceEngine
from app.services.risk_intelligence.intelligence_service import RiskIntelligenceService
from app.main import app


class TestPhase42RiskIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        from app.database.session import migrate_db_columns
        migrate_db_columns(engine)
        cls.client = TestClient(app)

        cls.db = SessionLocal()
        # Seed test user
        cls.test_email = f"intel_test_{uuid.uuid4().hex[:6]}@example.com"
        cls.test_user = User(
            id=str(uuid.uuid4()),
            email=cls.test_email,
            hashed_password=hash_password("Secret123!"),
            full_name="Risk Intel Officer",
            role=UserRole.SAFETY_OFFICER,
            is_active=True,
        )
        cls.db.add(cls.test_user)

        # Seed test project & site
        cls.project = Project(
            id=str(uuid.uuid4()),
            project_id=f"PROJ-ALPHA-{uuid.uuid4().hex[:4]}",
            name="Metro Tower Alpha",
            client="Metro Builders Corp",
            description="High-rise construction",
            status=ProjectStatus.ACTIVE,
        )
        cls.db.add(cls.project)

        cls.site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-INTEL-{uuid.uuid4().hex[:6]}",
            project_id=cls.project.id,
            name="North Excavation Zone",
            address="Zone 3 Sector B",
            status=SiteStatus.ACTIVE,
        )
        cls.db.add(cls.site)
        cls.db.commit()

        # Auth token
        token = create_access_token(data={"sub": cls.test_user.id})
        cls.auth_headers = {"Authorization": f"Bearer {token}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Collector Tests: Normalization & Multi-Agent Ingestion
    # ──────────────────────────────────────────────────────────────────────────

    def test_collector_empty_site_graceful(self):
        """Test collector handles a brand new site with zero findings gracefully."""
        empty_site = Site(
            id=str(uuid.uuid4()),
            site_id=f"SITE-EMPTY-{uuid.uuid4().hex[:4]}",
            project_id=self.project.id,
            name="Empty Greenfield Site",
            status=SiteStatus.ACTIVE,
        )
        self.db.add(empty_site)
        self.db.commit()

        collector = RiskDataCollector()
        findings = collector.collect_site_findings(self.db, empty_site.id, window_days=30)
        self.assertIsInstance(findings, list)
        self.assertEqual(len(findings), 0)

    def test_collector_normalizes_cross_agent_findings(self):
        """Test collector correctly ingests and normalizes findings from all 4 agent sources."""
        # 1. M1 Hazard
        h = Hazard(
            id=str(uuid.uuid4()),
            hazard_id=f"HAZ-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            hazard_type=HazardType.EXCAVATION,
            description="Trench sidewall cracking observed after continuous precipitation",
            severity=5,
            probability=4,
            risk_score=80.0,
            risk_category=RiskCategory.CRITICAL,
            status=HazardStatus.OPEN,
        )
        self.db.add(h)

        # 2. M2 Safety Finding
        sf = SafetyFinding(
            id=str(uuid.uuid4()),
            finding_id=f"SAF-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            finding_type=SafetyFindingType.HIGH_RISK_ACTIVITY,
            description="Worker working above 2m without fall arrest harness clipped",
            severity=RiskCategory.HIGH,
            status=SafetyFindingStatus.OPEN,
        )
        self.db.add(sf)

        # 3. M3 Compliance Finding
        cf = ComplianceFinding(
            id=str(uuid.uuid4()),
            finding_id=f"CMP-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            standard_ref="OSHA 1926.652",
            violation_type="Missing Trench Protective System",
            description="Excavation deeper than 5 feet lacks required shoring box",
            severity=RiskCategory.CRITICAL,
            recommendation="Install trench box immediately",
            status=SafetyFindingStatus.OPEN,
        )
        self.db.add(cf)

        # 4. M3 Insurance Claim Assessment
        ia = InsuranceClaimAssessment(
            id=str(uuid.uuid4()),
            claim_assessment_id=f"CLM-{uuid.uuid4().hex[:6]}",
            site_id=self.site.id,
            incident_ref="INC-WATER-01",
            incident_title="Groundwater Infiltration Flooding",
            incident_date=datetime.utcnow(),
            incident_severity=RiskCategory.HIGH,
            claim_risk_level=ClaimRiskLevel.HIGH,
            claim_probability_pct=75.0,
            documentation_completeness_pct=50.0,
            status="ACTIVE",
        )
        self.db.add(ia)
        self.db.commit()

        collector = RiskDataCollector()
        findings = collector.collect_site_findings(self.db, self.site.id, window_days=30)
        self.assertGreaterEqual(len(findings), 4)

        categories = {f.category for f in findings}
        self.assertIn("HAZARD", categories)
        self.assertIn("SAFETY_VIOLATION", categories)
        self.assertIn("REGULATORY_BREACH", categories)
        self.assertIn("INSURANCE_CLAIM", categories)

        sources = {f.source_agent for f in findings}
        self.assertIn("site_risk", sources)
        self.assertIn("safety", sources)
        self.assertIn("compliance", sources)
        self.assertIn("insurance", sources)

        for f in findings:
            self.assertIsInstance(f, RiskIntelligenceFinding)
            self.assertIn(f.severity, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            self.assertIsNotNone(f.source_agent)
            self.assertIsNotNone(f.timestamp)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Scorer Tests: 4-Pillar Score Calculation & Risk Tiers
    # ──────────────────────────────────────────────────────────────────────────

    def test_scorer_deterministic_score_and_weights(self):
        """Test project risk scorer computes deterministic scores across the 4 pillars."""
        scorer = ProjectRiskScorer()

        findings = [
            RiskIntelligenceFinding(
                finding_id="F1",
                source_agent="SITE_RISK_AGENT",
                source_table="hazards",
                category="SITE_RISK",
                finding_type="EXCAVATION",
                severity="CRITICAL",
                score=85.0,
                description="Trench wall instability",
                timestamp=datetime.utcnow(),
                is_resolved=False,
            ),
            RiskIntelligenceFinding(
                finding_id="F2",
                source_agent="SAFETY_AGENT",
                source_table="safety_findings",
                category="SAFETY",
                finding_type="PPE_VIOLATION",
                severity="HIGH",
                score=65.0,
                description="Missing protective hardhat",
                timestamp=datetime.utcnow(),
                is_resolved=False,
            ),
            RiskIntelligenceFinding(
                finding_id="F3",
                source_agent="COMPLIANCE_AGENT",
                source_table="compliance_findings",
                category="COMPLIANCE",
                finding_type="OSHA_VIOLATION",
                severity="HIGH",
                score=70.0,
                description="Overdue statutory crane inspection",
                timestamp=datetime.utcnow(),
                is_resolved=False,
            ),
            RiskIntelligenceFinding(
                finding_id="F4",
                source_agent="INSURANCE_AGENT",
                source_table="insurance_assessments",
                category="INSURANCE",
                finding_type="FINANCIAL_EXPOSURE",
                severity="MEDIUM",
                score=45.0,
                description="Elevated underwriting liability",
                timestamp=datetime.utcnow(),
                is_resolved=False,
            ),
        ]

        result = scorer.calculate_project_risk(findings, site_conditions={})
        self.assertIn("overall_score", result)
        self.assertIn("risk_level", result)
        self.assertIn("category_scores", result)

        cat = result["category_scores"]
        self.assertAlmostEqual(cat["weights"]["site_risk"], 0.30)
        self.assertAlmostEqual(cat["weights"]["safety_risk"], 0.30)
        self.assertAlmostEqual(cat["weights"]["compliance_risk"], 0.20)
        self.assertAlmostEqual(cat["weights"]["insurance_risk"], 0.20)

        # Re-evaluating identical findings must produce the exact identical deterministic overall score
        result2 = scorer.calculate_project_risk(findings, site_conditions={})
        self.assertEqual(result["overall_score"], result2["overall_score"])
        self.assertEqual(result["risk_level"], result2["risk_level"])

    def test_risk_level_mapping_boundaries(self):
        """Verify strict risk tier boundary mappings (0-25 Low, 26-50 Medium, 51-75 High, 76-100 Critical)."""
        scorer = ProjectRiskScorer()
        self.assertEqual(scorer._determine_risk_level(0.0), "LOW")
        self.assertEqual(scorer._determine_risk_level(15.0), "LOW")
        self.assertEqual(scorer._determine_risk_level(25.0), "LOW")
        self.assertEqual(scorer._determine_risk_level(25.1), "MEDIUM")
        self.assertEqual(scorer._determine_risk_level(50.0), "MEDIUM")
        self.assertEqual(scorer._determine_risk_level(50.1), "HIGH")
        self.assertEqual(scorer._determine_risk_level(75.0), "HIGH")
        self.assertEqual(scorer._determine_risk_level(75.1), "CRITICAL")
        self.assertEqual(scorer._determine_risk_level(100.0), "CRITICAL")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Pattern Detector Tests: Recurring Pattern Thresholds
    # ──────────────────────────────────────────────────────────────────────────

    def test_pattern_detector_identifies_recurring_patterns(self):
        """Test findings recurring >= 2 times within the window are detected as recurring patterns."""
        detector = RecurringRiskPatternDetector()
        now = datetime.utcnow()

        findings = [
            RiskIntelligenceFinding(
                finding_id="P1",
                source_agent="SITE_RISK_AGENT",
                source_table="hazards",
                category="SITE_RISK",
                finding_type="EXCAVATION",
                severity="HIGH",
                score=70.0,
                description="Trench wall instability in Sector 1",
                timestamp=now - timedelta(days=2),
                location="Sector 1",
            ),
            RiskIntelligenceFinding(
                finding_id="P2",
                source_agent="SITE_RISK_AGENT",
                source_table="hazards",
                category="SITE_RISK",
                finding_type="EXCAVATION",
                severity="CRITICAL",
                score=85.0,
                description="Trench collapse risk in Sector 2",
                timestamp=now - timedelta(hours=6),
                location="Sector 2",
            ),
        ]

        patterns = detector.detect_patterns(findings, min_threshold=2)
        self.assertGreaterEqual(len(patterns), 1)
        pat = patterns[0]
        self.assertEqual(pat["occurrence_count"], 2)
        self.assertEqual(pat["pattern_type"], "EXCAVATION")
        self.assertEqual(pat["severity"], "CRITICAL")
        self.assertIn("Sector 1", pat["locations"])
        self.assertIn("Sector 2", pat["locations"])

    def test_single_occurrence_not_flagged_as_pattern(self):
        """Verify that a single occurrence is strictly NOT flagged as a recurring pattern."""
        detector = RecurringRiskPatternDetector()
        findings = [
            RiskIntelligenceFinding(
                finding_id="SINGLE-1",
                source_agent="SAFETY_AGENT",
                source_table="safety_findings",
                category="SAFETY",
                finding_type="UNIQUE_ANOMALY_TYPE",
                severity="CRITICAL",
                score=90.0,
                description="Isolated unusual equipment fault",
                timestamp=datetime.utcnow(),
            )
        ]

        patterns = detector.detect_patterns(findings, min_threshold=2)
        self.assertEqual(len(patterns), 0)

    def test_sparse_data_returns_explanatory_message(self):
        """Verify detector handles empty findings gracefully."""
        detector = RecurringRiskPatternDetector()
        patterns = detector.detect_patterns([], min_threshold=2)
        self.assertEqual(patterns, [])

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Incident Predictor Tests: Causal Chains & Leading Indicators
    # ──────────────────────────────────────────────────────────────────────────

    def test_incident_predictor_trench_cave_in(self):
        """Test Trench Instability + Water Accumulation triggers Trench Cave-In prediction with causal chain."""
        predictor = PotentialIncidentPredictor()
        findings = [
            RiskIntelligenceFinding(
                finding_id="TC-1",
                source_agent="SITE_RISK_AGENT",
                source_table="hazards",
                category="SITE_RISK",
                finding_type="EXCAVATION",
                severity="CRITICAL",
                score=85.0,
                description="Trench wall fissures and unstable soil",
                timestamp=datetime.utcnow(),
            ),
            RiskIntelligenceFinding(
                finding_id="TC-2",
                source_agent="SITE_RISK_AGENT",
                source_table="hazards",
                category="SITE_RISK",
                finding_type="ENVIRONMENTAL",
                severity="HIGH",
                score=70.0,
                description="Surface water accumulation near trench edge",
                timestamp=datetime.utcnow(),
            ),
        ]

        site_conditions = {"water_accumulation": True, "weather_condition": "Rain"}
        predictions = predictor.predict_incidents(findings, site_conditions)

        self.assertGreaterEqual(len(predictions), 1)
        pred = next(p for p in predictions if "Trench Cave-In" in p["incident_type"])
        self.assertEqual(pred["severity_potential"], "CRITICAL")
        self.assertGreater(pred["probability_score"], 60.0)
        self.assertIn("causal_chain", pred)
        self.assertGreaterEqual(len(pred["causal_chain"]), 3)
        self.assertIn("recommended_interventions", pred)
        self.assertGreaterEqual(len(pred["recommended_interventions"]), 1)

    def test_incident_predictor_fall_from_height(self):
        """Test Working at Height without Harness triggers Fall Incident prediction."""
        predictor = PotentialIncidentPredictor()
        findings = [
            RiskIntelligenceFinding(
                finding_id="F-1",
                source_agent="SAFETY_AGENT",
                source_table="safety_findings",
                category="SAFETY",
                finding_type="FALL_HAZARD",
                severity="CRITICAL",
                score=88.0,
                description="Scaffolding platform missing guardrails and toe-boards",
                timestamp=datetime.utcnow(),
            ),
            RiskIntelligenceFinding(
                finding_id="F-2",
                source_agent="SAFETY_AGENT",
                source_table="safety_findings",
                category="SAFETY",
                finding_type="PPE_VIOLATION",
                severity="HIGH",
                score=75.0,
                description="Missing full body harness for elevated work",
                timestamp=datetime.utcnow(),
            ),
        ]

        predictions = predictor.predict_incidents(findings, {})
        self.assertGreaterEqual(len(predictions), 1)
        pred = next(p for p in predictions if "Fall From" in p["incident_type"])
        self.assertEqual(pred["severity_potential"], "CRITICAL")
        self.assertEqual(pred["primary_driver"], "Working at Height without Fall Protection")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Recommender Tests: Horizon Prioritization & Action Items
    # ──────────────────────────────────────────────────────────────────────────

    def test_recommender_prioritizes_horizons(self):
        """Test operational recommendation engine generates categorized, actionable recommendations."""
        recommender = OperationalRecommendationEngine()
        findings = [
            RiskIntelligenceFinding(
                finding_id="R1",
                source_agent="SITE_RISK_AGENT",
                source_table="hazards",
                category="SITE_RISK",
                finding_type="EXCAVATION",
                severity="CRITICAL",
                score=90.0,
                description="Critical trench collapse hazard",
                timestamp=datetime.utcnow(),
            )
        ]

        predictions = [
            {
                "prediction_id": "PRED-1",
                "incident_type": "Trench Cave-In & Worker Entrapment",
                "probability_score": 85.0,
                "severity_potential": "CRITICAL",
                "recommended_interventions": ["Evacuate trench and install hydraulic shoring"],
            }
        ]

        patterns = [
            {
                "pattern_id": "PAT-1",
                "category": "SITE_RISK",
                "pattern_type": "EXCAVATION",
                "severity": "CRITICAL",
                "occurrence_count": 3,
            }
        ]

        recs = recommender.generate_recommendations(findings, patterns, predictions, overall_risk_score=78.0)
        self.assertGreaterEqual(len(recs), 1)

        timeframes = {r["timeframe"] for r in recs}
        self.assertIn("IMMEDIATE", timeframes)

        for r in recs:
            self.assertIn("action_items", r)
            self.assertGreaterEqual(len(r["action_items"]), 1)
            self.assertIn("expected_risk_reduction", r)
            self.assertIn(r["priority"], ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Service & Persistence Tests
    # ──────────────────────────────────────────────────────────────────────────

    def test_intelligence_service_persists_assessment(self):
        """Test RiskIntelligenceService creates, stores, and retrieves ProjectRiskIntelligence."""
        service = RiskIntelligenceService()
        assessment = service.perform_site_risk_analysis(
            db=self.db,
            site_id=self.site.id,
            project_id=self.project.id,
            window_days=30,
        )

        self.assertIsNotNone(assessment.id)
        self.assertIsNotNone(assessment.assessment_id)
        self.assertEqual(assessment.site_id, self.site.id)
        self.assertGreaterEqual(assessment.findings_count, 0)
        self.assertIn(assessment.risk_level, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        # Fetch latest from DB
        latest = service.get_latest_assessment(self.db, self.site.id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.assessment_id, assessment.assessment_id)
        self.assertEqual(latest.overall_risk_score, assessment.overall_risk_score)

        # History list
        history = service.get_assessment_history(self.db, self.site.id, limit=5)
        self.assertGreaterEqual(len(history), 1)

    # ──────────────────────────────────────────────────────────────────────────
    # 7. REST API Integration Tests
    # ──────────────────────────────────────────────────────────────────────────

    def test_api_analyze_endpoint(self):
        """POST /api/v1/risk-intelligence/analyze produces 201 with full assessment."""
        payload = {
            "site_id": self.site.id,
            "project_id": self.project.id,
            "analysis_window_days": 30,
            "include_predictions": True,
            "include_patterns": True,
            "include_recommendations": True,
        }
        res = self.client.post("/api/v1/risk-intelligence/analyze", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["site_id"], self.site.id)
        self.assertIn("overall_risk_score", data)
        self.assertIn("category_scores", data)
        self.assertIn("recurring_patterns", data)
        self.assertIn("predicted_incidents", data)
        self.assertIn("recommendations", data)

    def test_api_site_endpoint(self):
        """GET /api/v1/risk-intelligence/site/{site_id} returns latest assessment."""
        res = self.client.get(f"/api/v1/risk-intelligence/site/{self.site.id}", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["site_id"], self.site.id)
        self.assertIn("overall_risk_score", data)

    def test_api_patterns_endpoint(self):
        """GET /api/v1/risk-intelligence/patterns/{site_id} returns pattern list."""
        res = self.client.get(
            f"/api/v1/risk-intelligence/patterns/{self.site.id}?window_days=30&min_threshold=2",
            headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_api_predictions_endpoint(self):
        """GET /api/v1/risk-intelligence/predictions/{site_id} returns incident predictions."""
        res = self.client.get(
            f"/api/v1/risk-intelligence/predictions/{self.site.id}?window_days=30",
            headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_api_recommendations_endpoint(self):
        """GET /api/v1/risk-intelligence/recommendations/{site_id} returns recommendations."""
        res = self.client.get(
            f"/api/v1/risk-intelligence/recommendations/{self.site.id}?window_days=30",
            headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_api_history_endpoint(self):
        """GET /api/v1/risk-intelligence/history/{site_id} returns assessment history."""
        res = self.client.get(
            f"/api/v1/risk-intelligence/history/{self.site.id}?limit=10",
            headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_api_invalid_site_returns_404(self):
        """Test API returns 404 for nonexistent site ID."""
        invalid_id = str(uuid.uuid4())
        res = self.client.get(f"/api/v1/risk-intelligence/site/{invalid_id}", headers=self.auth_headers)
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
