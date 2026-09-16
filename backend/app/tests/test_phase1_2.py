"""
ACRIP Milestone 1 Phase 1.2 Automated Test Suite
=================================================
Tests Site Risk Intelligence, Rule-Based Hazard Detection,
Risk Calculations, Multi-Category Scoring, Demo Scenarios,
Database Persistence, and Hazard Lifecycle Actions.
"""

import unittest
import os
import uuid
from datetime import datetime

# Set environment
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_acrip.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import (
    Base, User, Project, Site, Worker, Equipment, Activity,
    Hazard, RiskScore, Notification, UserRole, RiskCategory, HazardStatus, HazardType
)
from app.services.risk_scoring import calculate_risk_score, get_risk_category, calculate_overall_site_risk
from app.agents.site_risk_agent import RuleBasedRiskAnalyzer, SiteRiskAgent, DEMO_SCENARIOS


class TestRiskScoring(unittest.TestCase):
    """Test fundamental risk score formula and threshold mappings."""

    def test_step_22_required_formula_multiplications(self):
        """Verify: 1x1 -> LOW, 2x3 -> MEDIUM (or boundary), 4x4 -> HIGH, 5x5 -> CRITICAL."""
        # 1 x 1 = 1 -> (1 / 25) * 100 = 4.0 -> LOW
        score_1x1 = calculate_risk_score(1, 1)
        self.assertEqual(score_1x1, 4.0)
        self.assertEqual(get_risk_category(score_1x1), RiskCategory.LOW)

        # 2 x 3 = 6 -> (6 / 25) * 100 = 24.0 -> LOW (Threshold: 0-24 LOW, 25-49 MEDIUM)
        score_2x3 = calculate_risk_score(2, 3)
        self.assertEqual(score_2x3, 24.0)
        self.assertEqual(get_risk_category(score_2x3), RiskCategory.LOW)

        # 3 x 3 = 9 -> (9 / 25) * 100 = 36.0 -> MEDIUM
        score_3x3 = calculate_risk_score(3, 3)
        self.assertEqual(score_3x3, 36.0)
        self.assertEqual(get_risk_category(score_3x3), RiskCategory.MEDIUM)

        # 4 x 4 = 16 -> (16 / 25) * 100 = 64.0 -> HIGH
        score_4x4 = calculate_risk_score(4, 4)
        self.assertEqual(score_4x4, 64.0)
        self.assertEqual(get_risk_category(score_4x4), RiskCategory.HIGH)

        # 5 x 5 = 25 -> (25 / 25) * 100 = 100.0 -> CRITICAL
        score_5x5 = calculate_risk_score(5, 5)
        self.assertEqual(score_5x5, 100.0)
        self.assertEqual(get_risk_category(score_5x5), RiskCategory.CRITICAL)

    def test_risk_threshold_boundaries(self):
        """Verify 0-24 LOW, 25-49 MEDIUM, 50-74 HIGH, 75-100 CRITICAL."""
        self.assertEqual(get_risk_category(0.0), RiskCategory.LOW)
        self.assertEqual(get_risk_category(24.0), RiskCategory.LOW)
        self.assertEqual(get_risk_category(24.9), RiskCategory.LOW)
        self.assertEqual(get_risk_category(25.0), RiskCategory.MEDIUM)
        self.assertEqual(get_risk_category(49.0), RiskCategory.MEDIUM)
        self.assertEqual(get_risk_category(50.0), RiskCategory.HIGH)
        self.assertEqual(get_risk_category(74.0), RiskCategory.HIGH)
        self.assertEqual(get_risk_category(75.0), RiskCategory.CRITICAL)
        self.assertEqual(get_risk_category(100.0), RiskCategory.CRITICAL)


class TestHazardDetectionRules(unittest.TestCase):
    """Test deterministic hazard rules defined in Step 5."""

    def setUp(self):
        self.analyzer = RuleBasedRiskAnalyzer()

    def test_rule_1_excavation_plus_heavy_rain(self):
        """Rule 1: Heavy rain + excavation -> Excavation flooding/collapse hazard."""
        result = self.analyzer.analyze({
            "site_id": "TEST-01",
            "weather_condition": "Heavy Rain",
            "water_accumulation": True,
            "activities": ["Excavation"],
        })
        types = [h["hazard_type"] for h in result["hazards"]]
        self.assertIn(HazardType.EXCAVATION, types)
        exc_hazard = next(h for h in result["hazards"] if h["hazard_type"] == HazardType.EXCAVATION)
        self.assertEqual(exc_hazard["detection_source"], "RULE_ENGINE")
        self.assertGreaterEqual(exc_hazard["risk_score"], 75.0)
        self.assertEqual(exc_hazard["risk_level"], RiskCategory.CRITICAL)
        self.assertTrue(len(exc_hazard["evidence"]) > 10)
        self.assertTrue(len(exc_hazard["recommended_action"]) > 10)

    def test_rule_2_water_accumulation_plus_electrical_activity(self):
        """Rule 2: Water accumulation + electrical activity -> Electrical shock hazard."""
        result = self.analyzer.analyze({
            "site_id": "TEST-02",
            "weather_condition": "Clear",
            "water_accumulation": True,
            "activities": ["Electrical Work"],
        })
        types = [h["hazard_type"] for h in result["hazards"]]
        self.assertIn(HazardType.ELECTRICAL, types)
        elec_hazard = next(h for h in result["hazards"] if h["hazard_type"] == HazardType.ELECTRICAL)
        self.assertEqual(elec_hazard["detection_source"], "RULE_ENGINE")
        self.assertGreaterEqual(elec_hazard["risk_score"], 75.0)
        self.assertEqual(elec_hazard["risk_level"], RiskCategory.CRITICAL)
        self.assertIn("electrocution", elec_hazard["description"].lower())

    def test_rule_3_welding_plus_inadequate_fire_protection(self):
        """Rule 3: Welding + inadequate fire protection -> Fire/ignition hazard."""
        result = self.analyzer.analyze({
            "site_id": "TEST-03",
            "activities": ["Welding"],
            "fire_protection_adequate": False,
        })
        types = [h["hazard_type"] for h in result["hazards"]]
        self.assertIn(HazardType.FIRE, types)
        fire_hazard = next(h for h in result["hazards"] if h["hazard_type"] == HazardType.FIRE)
        self.assertEqual(fire_hazard["detection_source"], "RULE_ENGINE")
        self.assertEqual(fire_hazard["risk_level"], RiskCategory.HIGH)

    def test_rule_4_heavy_equipment_plus_overdue_inspection(self):
        """Rule 4: Heavy equipment + overdue inspection -> Equipment failure hazard."""
        result = self.analyzer.analyze({
            "site_id": "TEST-04",
            "equipment": [
                {"name": "Tower Crane TC-01", "status": "inspection_due"}
            ],
            "activities": ["General Construction"],
        })
        types = [h["hazard_type"] for h in result["hazards"]]
        self.assertIn(HazardType.EQUIPMENT, types)
        eq_hazard = next(h for h in result["hazards"] if h["hazard_type"] == HazardType.EQUIPMENT)
        self.assertEqual(eq_hazard["detection_source"], "RULE_ENGINE")
        self.assertIn("inspection", eq_hazard["evidence"].lower())

    def test_rule_5_scaffolding_plus_overdue_inspection_or_high_wind(self):
        """Rule 5: Scaffolding + high wind / uninspected -> Scaffolding safety hazard."""
        result = self.analyzer.analyze({
            "site_id": "TEST-05",
            "activities": ["Scaffolding"],
            "wind_speed": 42.0,
            "scaffolding_inspected": False,
        })
        types = [h["hazard_type"] for h in result["hazards"]]
        self.assertIn(HazardType.FALL, types)
        fall_hazard = next(h for h in result["hazards"] if h["hazard_type"] == HazardType.FALL)
        self.assertEqual(fall_hazard["risk_level"], RiskCategory.CRITICAL)

    def test_rule_6_poor_housekeeping_plus_blocked_pathway(self):
        """Rule 6: Poor housekeeping + blocked pathway -> Slip/trip/access hazard."""
        result = self.analyzer.analyze({
            "site_id": "TEST-06",
            "site_conditions": "Debris and blocked pathways near emergency egress",
            "activities": ["General Construction"],
        })
        self.assertTrue(any("housekeeping" in r.lower() or "obstruction" in r.lower() for r in result["reasoning"]))
        struct_hazards = [h for h in result["hazards"] if "egress" in h["description"].lower() or "trip" in h["description"].lower()]
        self.assertTrue(len(struct_hazards) > 0)

    def test_rule_7_high_risk_activity_plus_insufficient_safety_controls(self):
        """Rule 7: High-risk activity + insufficient safety controls -> Operational safety hazard."""
        result = self.analyzer.analyze({
            "site_id": "TEST-07",
            "activities": ["Demolition", "Excavation"],
            "safety_controls_adequate": False,
        })
        op_hazards = [h for h in result["hazards"] if h.get("type") == "operational"]
        self.assertTrue(len(op_hazards) > 0)
        self.assertEqual(op_hazards[0]["detection_source"], "RULE_ENGINE")

    def test_detection_source_is_always_rule_engine(self):
        """Verify strict rule: detection_source must be RULE_ENGINE, never falsely labeled AI."""
        result = self.analyzer.analyze({
            "site_id": "TEST-08",
            "weather_condition": "Heavy Rain",
            "water_accumulation": True,
            "activities": ["Excavation", "Electrical Work", "Welding"],
            "fire_protection_adequate": False,
        })
        self.assertEqual(result["detection_source"], "RULE_ENGINE")
        for h in result["hazards"]:
            self.assertEqual(h["detection_source"], "RULE_ENGINE")


class TestDeterministicDemoScenarios(unittest.TestCase):
    """Test all 5 deterministic demo scenarios requested in Step 20."""

    def setUp(self):
        self.analyzer = RuleBasedRiskAnalyzer()

    def test_scenario_1_low_risk(self):
        """SCENARIO 1: Normal weather + routine activity -> LOW."""
        sc = DEMO_SCENARIOS[1]
        result = self.analyzer.analyze(sc["input"])
        self.assertEqual(result["risk_level"], RiskCategory.LOW)
        self.assertLess(result["overall_risk_score"], 25.0)

    def test_scenario_2_medium_risk(self):
        """SCENARIO 2: Moderate conditions + minor issue -> MEDIUM."""
        sc = DEMO_SCENARIOS[2]
        result = self.analyzer.analyze(sc["input"])
        self.assertEqual(result["risk_level"], RiskCategory.MEDIUM)
        self.assertTrue(25.0 <= result["overall_risk_score"] < 50.0)

    def test_scenario_3_high_risk(self):
        """SCENARIO 3: Heavy equipment + overdue inspection + hot welding -> HIGH."""
        sc = DEMO_SCENARIOS[3]
        result = self.analyzer.analyze(sc["input"])
        self.assertEqual(result["risk_level"], RiskCategory.HIGH)
        self.assertTrue(50.0 <= result["overall_risk_score"] < 75.0)

    def test_scenario_4_critical_excavation_risk(self):
        """SCENARIO 4: Heavy rain + excavation + water accumulation -> CRITICAL."""
        sc = DEMO_SCENARIOS[4]
        result = self.analyzer.analyze(sc["input"])
        self.assertEqual(result["risk_level"], RiskCategory.CRITICAL)
        self.assertGreaterEqual(result["overall_risk_score"], 75.0)

    def test_scenario_5_critical_electrical_shock_risk(self):
        """SCENARIO 5: Electrical work + wet conditions -> CRITICAL."""
        sc = DEMO_SCENARIOS[5]
        result = self.analyzer.analyze(sc["input"])
        self.assertEqual(result["risk_level"], RiskCategory.CRITICAL)
        self.assertGreaterEqual(result["overall_risk_score"], 75.0)


class TestDatabasePersistenceAndLifecycle(unittest.TestCase):
    """Test database persistence of RiskScore, Hazards, Notifications, and Hazard Lifecycle."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.Session()

        # Seed site and user
        self.user = User(
            id=str(uuid.uuid4()),
            email="safety.tester@acrip.com",
            full_name="Safety Tester",
            hashed_password="hash",
            role=UserRole.SAFETY_OFFICER,
            is_active=True,
        )
        self.site = Site(
            id=str(uuid.uuid4()),
            site_id="SITE-TEST-01",
            name="Test Construction Yard",
            current_risk_score=10.0,
            risk_category=RiskCategory.LOW,
            worker_count=25,
            equipment_count=3,
        )
        self.db.add(self.user)
        self.db.add(self.site)
        self.db.commit()

        self.agent = SiteRiskAgent()

    def tearDown(self):
        self.db.close()

    def test_analyze_and_persist_flow(self):
        """Test Step 14: Agent runs, detects hazards, saves RiskScore, updates Site, generates notifications."""
        analysis = self.agent.analyze_and_persist(
            db=self.db,
            site_id=self.site.id,
            custom_input={
                "weather_condition": "Heavy Rain",
                "water_accumulation": True,
                "activities": ["Excavation", "Drainage Trenching"],
                "workers": 50,
            },
            source_label="unit_test_run"
        )

        # Verify analysis output
        self.assertEqual(analysis["risk_level"], RiskCategory.CRITICAL)
        self.assertGreaterEqual(analysis["overall_risk_score"], 75.0)
        self.assertTrue(len(analysis["hazards"]) > 0)
        self.assertTrue(len(analysis["recommendations"]) > 0)

        # Verify Site updated
        self.db.refresh(self.site)
        self.assertEqual(self.site.risk_category, RiskCategory.CRITICAL)
        self.assertEqual(self.site.current_risk_score, analysis["overall_risk_score"])

        # Verify RiskScore recorded in DB
        score_record = self.db.query(RiskScore).filter(RiskScore.site_id == self.site.id).first()
        self.assertIsNotNone(score_record)
        self.assertEqual(score_record.overall_score, analysis["overall_risk_score"])
        self.assertGreater(score_record.environmental_risk, 50.0)
        self.assertGreater(score_record.activity_risk, 50.0)

        # Verify Hazards recorded in DB
        hazards_in_db = self.db.query(Hazard).filter(Hazard.site_id == self.site.id).all()
        self.assertEqual(len(hazards_in_db), len(analysis["hazards"]))
        for h in hazards_in_db:
            self.assertEqual(h.detection_source, "RULE_ENGINE")
            self.assertEqual(h.status, HazardStatus.OPEN)

        # Verify Critical Notification created
        notifications = self.db.query(Notification).all()
        self.assertTrue(len(notifications) > 0)
        crit_notifs = [n for n in notifications if n.severity in ["critical", "warning"]]
        self.assertTrue(len(crit_notifs) > 0)

    def test_hazard_lifecycle_actions(self):
        """Test Step 17: Open -> Under Review (Acknowledge) -> Mitigated -> Closed."""
        # Create hazard
        hazard = Hazard(
            id=str(uuid.uuid4()),
            hazard_id="HAZ-TEST-001",
            site_id=self.site.id,
            hazard_type=HazardType.EXCAVATION,
            description="Trench wall instability",
            severity=4,
            probability=4,
            risk_score=64.0,
            risk_category=RiskCategory.HIGH,
            status=HazardStatus.OPEN,
            detected_at=datetime.utcnow(),
        )
        self.db.add(hazard)
        self.db.commit()

        # 1. Acknowledge -> UNDER_REVIEW
        hazard.status = HazardStatus.UNDER_REVIEW
        hazard.acknowledged_at = datetime.utcnow()
        hazard.acknowledged_by = self.user.id
        self.db.commit()
        self.db.refresh(hazard)
        self.assertEqual(hazard.status, HazardStatus.UNDER_REVIEW)
        self.assertIsNotNone(hazard.acknowledged_at)

        # 2. Mitigate -> MITIGATED
        hazard.status = HazardStatus.MITIGATED
        hazard.mitigated_at = datetime.utcnow()
        hazard.mitigated_by = self.user.id
        hazard.mitigation_notes = "Installed modular aluminum trench shield and dewatering submersible pumps."
        self.db.commit()
        self.db.refresh(hazard)
        self.assertEqual(hazard.status, HazardStatus.MITIGATED)
        self.assertIn("trench shield", hazard.mitigation_notes)

        # 3. Close -> CLOSED
        hazard.status = HazardStatus.CLOSED
        self.db.commit()
        self.db.refresh(hazard)
        self.assertEqual(hazard.status, HazardStatus.CLOSED)


class TestApiEndpoints(unittest.TestCase):
    """Test API route execution, RBAC, and JSON responses using FastAPI TestClient."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.security import create_access_token
        from app.database.session import get_db, SessionLocal, engine

        # Ensure all tables are created on the test engine
        Base.metadata.create_all(bind=engine)

        cls.client = TestClient(app)
        db = SessionLocal()

        # Ensure seed data exists
        from app.seed import seed_database
        try:
            seed_database()
        except Exception:
            pass

        user = db.query(User).filter(User.email == "admin@acriplatform.com").first()
        site = db.query(Site).first()
        cls.site_id = site.id if site else None
        token = create_access_token({"sub": user.id, "role": user.role.value})
        cls.headers = {"Authorization": f"Bearer {token}"}
        db.close()

    @classmethod
    def tearDownClass(cls):
        import os
        if os.path.exists("./test_acrip.db"):
            try:
                os.remove("./test_acrip.db")
            except Exception:
                pass

    def test_demo_scenarios_list_api(self):
        """GET /api/v1/risk/demo-scenarios returns catalog."""
        res = self.client.get("/api/v1/risk/demo-scenarios", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]["expected_level"], "LOW")
        self.assertEqual(data[3]["expected_level"], "CRITICAL")

    def test_site_risk_summary_api(self):
        """GET /api/v1/risk/sites/{id} returns current summary."""
        if not self.site_id:
            self.skipTest("No site available")
        res = self.client.get(f"/api/v1/risk/sites/{self.site_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("current_risk_score", data)
        self.assertIn("risk_category", data)

    def test_run_demo_scenario_api(self):
        """POST /api/v1/risk/demo-scenario executes deterministic scenario."""
        if not self.site_id:
            self.skipTest("No site available")
        res = self.client.post(
            "/api/v1/risk/demo-scenario",
            headers=self.headers,
            json={"site_id": self.site_id, "scenario_id": 4}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["risk_level"], "critical")
        self.assertGreaterEqual(data["overall_risk_score"], 75.0)
        self.assertEqual(data["detection_source"], "RULE_ENGINE")

    def test_analyze_site_api(self):
        """POST /api/v1/risk/analyze-site executes Site Risk Agent."""
        if not self.site_id:
            self.skipTest("No site available")
        res = self.client.post(
            "/api/v1/risk/analyze-site",
            headers=self.headers,
            json={
                "site_id": self.site_id,
                "weather_condition": "Clear",
                "temperature": 26.0,
                "wind_speed": 10.0,
                "water_accumulation": False,
                "activities": ["General Construction"]
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("overall_risk_score", data)
        self.assertIn("categories", data)
        self.assertIn("environmental", data["categories"])
        self.assertIn("equipment", data["categories"])
        self.assertIn("activity", data["categories"])
        self.assertIn("site_condition", data["categories"])
        self.assertIn("operational", data["categories"])

    def test_risk_history_api(self):
        """GET /api/v1/risk/sites/{id}/history returns records."""
        if not self.site_id:
            self.skipTest("No site available")
        res = self.client.get(f"/api/v1/risk/sites/{self.site_id}/history", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)


if __name__ == "__main__":
    unittest.main()

