"""
Site Risk Agent — Milestone 1 Phase 1.3
========================================
Agentic Risk Intelligence and Hazard Detection Engine.

Architecture:
    SiteRiskAgent
         ↓
    BaseRiskAnalyzer (Interface)
         ↓
    RuleBasedRiskAnalyzer (Phase 1.2 implementation)
      [Future: LLMRiskAnalyzer, ComputerVisionRiskAnalyzer, HybridRiskAnalyzer]
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid

from app.models.models import (
    Hazard, RiskScore, Site, Notification,
    HazardType, HazardStatus, RiskCategory, NotificationCategory
)
from app.services.risk_scoring import (
    calculate_risk_score, get_risk_category, RISK_THRESHOLDS
)


# ── Abstract Base Analyzer ──────────────────────────────────────────────────

class BaseRiskAnalyzer(ABC):
    """
    Abstract interface for risk analysis engines.
    Allows transparent swapping between RuleBased, LLM, Computer Vision, or Hybrid analyzers.
    """

    @abstractmethod
    def analyze(self, site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze site context and return detected hazards, category scores,
        overall score, recommendations, and audit reasoning.
        """
        pass


# ── Rule-Based Risk Analyzer ────────────────────────────────────────────────

class RuleBasedRiskAnalyzer(BaseRiskAnalyzer):
    """
    Deterministic rule-based hazard detection and risk analysis engine.
    Applies empirical construction safety rules, evidence-based probability,
    and impact-based severity assessments.
    """

    def analyze(self, site_data: Dict[str, Any]) -> Dict[str, Any]:
        site_id = site_data.get("site_id", "")
        weather = (site_data.get("weather_condition") or "").lower()
        temp = float(site_data.get("temperature", 25.0))
        wind = float(site_data.get("wind_speed", 10.0))
        water_accum = bool(site_data.get("water_accumulation", False))
        site_conditions = (site_data.get("site_conditions") or "").lower()
        activities = [a.lower() for a in site_data.get("activities", [])]
        equipment_list = site_data.get("equipment", [])
        workers_count = int(site_data.get("workers", site_data.get("worker_count", 20)))
        fire_protection_ok = bool(site_data.get("fire_protection_adequate", True))
        scaffolding_inspected = bool(site_data.get("scaffolding_inspected", True))
        safety_controls_adequate = bool(site_data.get("safety_controls_adequate", True))

        detected_hazards: List[Dict[str, Any]] = []
        reasoning: List[str] = []

        # ── Rule 1: Excavation + Heavy Rain / Water Accumulation ───────────
        is_excavating = any("excavat" in a for a in activities)
        is_heavy_rain = "heavy rain" in weather or "downpour" in weather or "monsoon" in weather
        has_water = water_accum or "water" in site_conditions or "flooding" in site_conditions

        if is_excavating and (is_heavy_rain or has_water):
            prob = 5 if (is_heavy_rain and has_water) else 4
            sev = 5  # Collapse/engulfment risk
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "excavation",
                "hazard_type": HazardType.EXCAVATION,
                "description": "Critical excavation collapse and trench flooding hazard",
                "evidence": f"Active excavation detected in conjunction with {'heavy rain' if is_heavy_rain else 'standing water accumulation'}. Saturated soil significantly increases trench wall slip failure.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Immediately suspend excavation operations. Evacuate trench zone, pump out standing water, and require structural engineer soil-stability recertification before re-entry.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Excavation active during heavy rain/water accumulation -> Soil liquefaction and trench collapse risk ({score}/100).")
        elif is_excavating and ("rain" in weather or "wet" in site_conditions):
            prob = 3
            sev = 4
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "excavation",
                "hazard_type": HazardType.EXCAVATION,
                "description": "Excavation slope instability under wet ground conditions",
                "evidence": f"Rainfall ({weather}) reported with ongoing earthwork. Moisture reduces shear strength of unreinforced slopes.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Install shoring or trench boxes, construct diversion berms, and inspect trench perimeters hourly.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Wet ground near excavation zone -> Elevated slope instability hazard ({score}/100).")

        # ── Rule 2: Electrical Work + Water Accumulation ────────────────────
        is_electrical = any("electric" in a for a in activities)
        if is_electrical and has_water:
            prob = 4
            sev = 5  # Electrocution is catastrophic
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "electrical",
                "hazard_type": HazardType.ELECTRICAL,
                "description": "High-voltage electrocution risk from water contact with active wiring",
                "evidence": "Electrical installation / cable work observed adjacent to standing water or wet ground. Water bridges insulation paths.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "De-energize main distribution panels immediately. Apply lockout/tagout (LOTO) protocols, isolate standing water, and test insulation resistance before restoring power.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Electrical activity in wet environment -> Catastrophic electrocution hazard ({score}/100).")
        elif is_electrical and is_heavy_rain:
            prob = 4
            sev = 4
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "electrical",
                "hazard_type": HazardType.ELECTRICAL,
                "description": "Outdoor electrical distribution exposure to heavy rainfall",
                "evidence": "Temporary distribution boards exposed to precipitation without NEMA 4X / IP66 weatherproofing enclosures.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Cover all temporary junction boxes with certified weatherproof shrouds; install Ground Fault Circuit Interrupters (GFCI).",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Outdoor electrical infrastructure exposed to rainfall ({score}/100).")

        # ── Rule 3: Welding / Hot Work + Inadequate Fire Protection ─────────
        is_welding = any("weld" in a or "hot work" in a for a in activities)
        if is_welding and (not fire_protection_ok or "combustible" in site_conditions or temp > 35):
            prob = 4
            sev = 4  # Major fire
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "fire",
                "hazard_type": HazardType.FIRE,
                "description": "Elevated fire and combustible ignition hazard during hot work",
                "evidence": f"Welding/cutting active with {'high ambient temperature (' + str(temp) + '°C)' if temp > 35 else 'compromised fire watch controls'} and nearby combustible materials.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Mandate dedicated fire watch for minimum 30 minutes post-work. Verify minimum 2 operational 10kg ABC dry-chemical extinguishers within 10 meters and clear 11m radius of combustibles.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Hot work/welding with fire protection concerns -> Fire ignition hazard ({score}/100).")

        # ── Rule 4: Heavy Equipment Active + Overdue Inspection/Maintenance ──
        has_overdue_equipment = False
        overdue_names = []
        for eq in equipment_list:
            status = eq.get("status", "").lower()
            if "maintenance" in status or "overdue" in status or "inspection" in status:
                has_overdue_equipment = True
                overdue_names.append(eq.get("name", "Equipment"))

        if has_overdue_equipment or "equipment overdue" in site_conditions:
            prob = 3
            sev = 4  # Mechanical failure of heavy equipment
            score = calculate_risk_score(prob, sev)
            eq_detail = ", ".join(overdue_names) if overdue_names else "Heavy machinery units"
            detected_hazards.append({
                "type": "equipment",
                "hazard_type": HazardType.EQUIPMENT,
                "description": "Catastrophic mechanical failure risk on overdue equipment",
                "evidence": f"Active machinery operating with overdue mandatory safety inspection/maintenance ({eq_detail}). Risk of brake failure, hydraulic line rupture, or structural boom fatigue.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": f"Red-tag and ground {eq_detail} immediately. Require certified 3rd-party mechanical fitness certification before return to service.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Overdue equipment in active operation ({eq_detail}) -> Mechanical failure hazard ({score}/100).")

        # ── Rule 5: Scaffolding + High Wind or Overdue Inspection ───────────
        is_scaffolding = any("scaffold" in a for a in activities)
        if is_scaffolding and (wind > 35 or not scaffolding_inspected):
            prob = 4
            sev = 5 if wind > 40 else 4  # Fall from height / scaffold collapse
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "fall",
                "hazard_type": HazardType.FALL,
                "description": "Scaffolding structural instability and high-altitude fall hazard",
                "evidence": f"Scaffolding work active under high wind gusts ({wind} km/h) and {'unverified inspection green-tags' if not scaffolding_inspected else 'excessive lateral forces'}.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Order full halt of work at height on scaffolding. Inspect all base plates, ledger ties, and anchor points. Re-affix safety green tags once certified by scaffold competent person.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Scaffolding exposed to high wind ({wind} km/h) or unverified inspection -> Fall/collapse risk ({score}/100).")

        # ── Rule 6: Extreme Heat + Heavy Workforce ─────────────────────────
        if temp >= 38:
            prob = 4
            sev = 3  # Significant worker injury / heat stroke
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "environmental",
                "hazard_type": HazardType.ENVIRONMENTAL,
                "description": "Occupational heat stress, dehydration, and cognitive impairment",
                "evidence": f"Ambient temperature reaches {temp}°C on site with {workers_count} active workers. High heat indexes severely degrade motor control and increase accident frequency.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Implement OSHA Heat Stress standard work-rest cycles (15 min break every 45 min). Provide chilled electrolyte drinks and erect shaded cooling stations.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Extreme heat stress conditions ({temp}°C) -> Worker cognitive/physical fatigue risk ({score}/100).")

        # ── Rule 7: High Worker Density + Heavy Material Handling ─────────
        is_material_handling = any("material" in a or "crane" in a or "lifting" in a for a in activities)
        if is_material_handling and workers_count > 50:
            prob = 3
            sev = 4
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "material_handling",
                "hazard_type": HazardType.MATERIAL_HANDLING,
                "description": "Crush and struck-by hazards in congested material handling corridor",
                "evidence": f"Heavy overhead/ground material transport operating in zone with high worker density ({workers_count} personnel).",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Erect rigid barricades creating dedicated heavy transit corridors. Assign two designated banksmen/spotters with high-decibel air horns for all transit movements.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"High worker congestion during material handling operations ({score}/100).")

        # ── Rule 8: Poor Housekeeping / Blocked Pathways ───────────────────
        if "housekeeping" in site_conditions or "blocked" in site_conditions or "debris" in site_conditions:
            prob = 4
            sev = 2  # Moderate slip/trip
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "structural",
                "hazard_type": HazardType.STRUCTURAL,
                "description": "Emergency egress impedance and trip hazard from disordered storage",
                "evidence": "Construction debris, rebar off-cuts, and unorganized pallet stacks restricting primary pedestrian egress routes.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Conduct immediate 1-hour site-wide housekeeping stand-down. Clear all egress corridors to minimum 1.2m clear width.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Housekeeping and pathway obstructions observed ({score}/100).")

        # ── Rule 7: High-Risk Activity + Insufficient Safety Controls ──────
        high_risk_trades = ["excavat", "weld", "demolition", "scaffold", "electric", "material", "lifting", "crane"]
        active_high_risk = [a for a in activities if any(hr in a for hr in high_risk_trades)]
        if active_high_risk and not safety_controls_adequate:
            prob = 4
            sev = 4
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "operational",
                "hazard_type": HazardType.OTHER,
                "description": f"Operational safety hazard: Inadequate safety controls for high-risk operations ({', '.join(active_high_risk)})",
                "evidence": f"Active high-risk activities ({', '.join(active_high_risk)}) underway without verified standard safety controls, work permits, or dedicated supervision.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Halt high-risk work immediately. Enforce formal Permit-to-Work (PTW) protocols, post certified safety observers, and verify PPE before recommencing.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"High-risk activity ({', '.join(active_high_risk)}) lacking verified safety controls -> Operational safety hazard ({score}/100).")

        # ── Rule 8: Demolition Work ────────────────────────────────────────
        if any("demolition" in a for a in activities):
            prob = 3
            sev = 4
            score = calculate_risk_score(prob, sev)
            detected_hazards.append({
                "type": "structural",
                "hazard_type": HazardType.STRUCTURAL,
                "description": "Uncontrolled structural collapse and airborne silica dust exposure",
                "evidence": "Structural demolition operations underway. Risk of premature slab failure and hazardous dust plumes.",
                "probability": prob,
                "severity": sev,
                "risk_score": score,
                "risk_level": get_risk_category(score),
                "recommended_action": "Enforce minimum 1.5x height exclusion boundary. Deploy continuous dust misting cannons and ensure N95/P100 respirator adherence.",
                "detection_source": "RULE_ENGINE",
            })
            reasoning.append(f"Demolition operations active -> Structural collapse and airborne particulate hazards ({score}/100).")

        # ── Multi-Dimensional Category Scoring ─────────────────────────────
        env_score = self._calc_category_score(detected_hazards, [HazardType.ENVIRONMENTAL], base=12.0)
        if is_heavy_rain:
            env_score = max(env_score, 76.0)
        elif "rain" in weather or wind > 30 or temp > 36:
            env_score = max(env_score, 52.0)

        eqp_score = self._calc_category_score(detected_hazards, [HazardType.EQUIPMENT], base=10.0)
        if has_overdue_equipment:
            eqp_score = max(eqp_score, 72.0)

        act_score = self._calc_category_score(
            detected_hazards,
            [HazardType.EXCAVATION, HazardType.FIRE, HazardType.FALL, HazardType.MATERIAL_HANDLING, HazardType.ELECTRICAL],
            base=15.0
        )
        if is_excavating and (is_heavy_rain or has_water):
            act_score = max(act_score, 85.0)
        elif is_electrical and (has_water or is_heavy_rain):
            act_score = max(act_score, 82.0)

        cond_score = self._calc_category_score(
            detected_hazards,
            [HazardType.EXCAVATION, HazardType.STRUCTURAL, HazardType.ELECTRICAL],
            base=10.0
        )
        if has_water:
            cond_score = max(cond_score, 74.0)

        ops_score = round(min(100.0, (workers_count * 0.2) + (len(detected_hazards) * 12.0) + 10.0), 1)

        # ── Weighted Overall Site Risk (Step 11 & Step 20) ─────────────────
        # Deterministic formula balancing:
        # 1. Peak Hazard Severity (highest hazard score)
        # 2. Critical & High hazard density
        # 3. Weighted category average across all 5 dimensions
        highest_hazard_score = max([h["risk_score"] for h in detected_hazards], default=0.0)
        crit_count = sum(1 for h in detected_hazards if h["risk_level"] == RiskCategory.CRITICAL)
        high_count = sum(1 for h in detected_hazards if h["risk_level"] == RiskCategory.HIGH)

        cat_avg = (
            env_score * 0.22
            + eqp_score * 0.22
            + act_score * 0.26
            + cond_score * 0.18
            + ops_score * 0.12
        )

        if crit_count > 0:
            # When active critical hazard(s) exist, overall site risk escalates to CRITICAL (>= 75.0)
            base_crit = max(76.0, (highest_hazard_score * 0.65) + (cat_avg * 0.35))
            overall_score = min(100.0, base_crit + min(14.0, (crit_count - 1) * 6.0))
        elif high_count > 0:
            # When high hazard(s) exist, overall site risk enters HIGH (50.0 - 74.0)
            base_high = max(52.0, (highest_hazard_score * 0.55) + (cat_avg * 0.45))
            overall_score = min(74.0, base_high + min(12.0, (high_count - 1) * 4.0))
        elif len(detected_hazards) > 0:
            # Active medium or low hazards present
            overall_score = min(49.0, max(26.0, (highest_hazard_score * 0.40) + (cat_avg * 0.60)))
        else:
            # Quiet site baseline without any triggered hazard conditions
            overall_score = min(24.0, cat_avg * 0.70)

        overall_score = round(min(100.0, max(0.0, overall_score)), 1)
        overall_level = get_risk_category(overall_score)

        # ── Global Actionable Recommendations ──────────────────────────────
        recommendations = []
        for h in detected_hazards:
            if h["risk_level"] in [RiskCategory.HIGH, RiskCategory.CRITICAL]:
                recommendations.append(h["recommended_action"])

        if overall_level == RiskCategory.CRITICAL:
            recommendations.insert(0, "MANDATORY: Issue immediate site safety stand-down for affected operational zones until all critical hazards are verified mitigated.")
        elif overall_level == RiskCategory.HIGH:
            recommendations.insert(0, "Conduct immediate joint Site Manager and Safety Officer audit across all active work fronts.")
        elif not recommendations:
            recommendations.append("Continue routine safety oversight and maintain shift toolbox talk documentation.")

        if not reasoning:
            reasoning.append("Normal site operating parameters. No critical rule thresholds exceeded.")

        if site_id:
            for h in detected_hazards:
                h["site_id"] = site_id

        return {
            "site_id": site_id,
            "overall_risk_score": overall_score,
            "risk_level": overall_level,
            "highest_hazard_score": highest_hazard_score,
            "active_hazards_count": len(detected_hazards),
            "critical_hazards_count": crit_count,
            "categories": {
                "environmental": {
                    "score": env_score,
                    "level": get_risk_category(env_score),
                    "explanation": f"Weather ({weather or 'Normal'}), {temp}°C, wind {wind} km/h, water accumulation: {'Yes' if has_water else 'No'}."
                },
                "equipment": {
                    "score": eqp_score,
                    "level": get_risk_category(eqp_score),
                    "explanation": f"Active machinery units: {len(equipment_list)}. Overdue inspections: {'Detected' if has_overdue_equipment else 'None'}."
                },
                "activity": {
                    "score": act_score,
                    "level": get_risk_category(act_score),
                    "explanation": f"Current active trades: {', '.join(activities) if activities else 'Routine construction'}."
                },
                "site_condition": {
                    "score": cond_score,
                    "level": get_risk_category(cond_score),
                    "explanation": f"Ground condition: {'Waterlogged / Mud' if has_water else 'Stable'}. Egress: {'Restricted' if 'blocked' in site_conditions else 'Clear'}."
                },
                "operational": {
                    "score": ops_score,
                    "level": get_risk_category(ops_score),
                    "explanation": f"Workforce density: {workers_count} personnel on site with {len(detected_hazards)} identified active risk factors."
                }
            },
            "hazards": detected_hazards,
            "recommendations": recommendations,
            "reasoning": reasoning,
            "detection_source": "RULE_ENGINE"
        }

    def _calc_category_score(self, hazards: List[Dict[str, Any]], match_types: List[HazardType], base: float) -> float:
        matching = [h["risk_score"] for h in hazards if h["hazard_type"] in match_types]
        if matching:
            return round(min(100.0, max(matching) * 0.8 + base), 1)
        return round(base, 1)


# ── Deterministic Demo Scenarios ────────────────────────────────────────────

DEMO_SCENARIOS = {
    1: {
        "name": "Scenario 1 — Low Risk Baseline",
        "description": "Clear pleasant weather, routine general construction, all equipment inspected, full PPE compliance.",
        "input": {
            "weather_condition": "Clear, Sunny",
            "temperature": 24.0,
            "wind_speed": 10.0,
            "water_accumulation": False,
            "site_conditions": "Clean pathways, organized material storage, no hazards noted",
            "activities": ["General Construction", "Interior Painting"],
            "workers": 35,
            "equipment": [
                {"name": "Scissor Lift SL-01", "status": "operational", "last_inspection": "2026-09-10"}
            ],
            "fire_protection_adequate": True,
            "scaffolding_inspected": True,
        },
        "expected_level": RiskCategory.LOW
    },
    2: {
        "name": "Scenario 2 — Medium Risk Operations",
        "description": "Cloudy warm weather, concrete work and material handling, minor material storage near access route.",
        "input": {
            "weather_condition": "Overcast, Cloudy",
            "temperature": 30.0,
            "wind_speed": 15.0,
            "water_accumulation": False,
            "site_conditions": "Minor housekeeping debris near west perimeter access",
            "activities": ["Concrete Work", "Material Handling"],
            "workers": 55,
            "equipment": [
                {"name": "Concrete Mixer CM-01", "status": "operational", "last_inspection": "2026-09-08"}
            ],
            "fire_protection_adequate": True,
            "scaffolding_inspected": True,
        },
        "expected_level": RiskCategory.MEDIUM
    },
    3: {
        "name": "Scenario 3 — High Equipment & Hot Work Risk",
        "description": "High temperature, structural welding with dry surroundings, heavy crane overdue for periodic maintenance.",
        "input": {
            "weather_condition": "Hot and Dry",
            "temperature": 37.0,
            "wind_speed": 20.0,
            "water_accumulation": False,
            "site_conditions": "Dry vegetation near south fence, heavy equipment active",
            "activities": ["Welding", "Structural Steel Erection"],
            "workers": 65,
            "equipment": [
                {"name": "Tower Crane TC-01", "status": "inspection_due", "last_inspection": "2026-07-15"}
            ],
            "fire_protection_adequate": False,
            "scaffolding_inspected": True,
        },
        "expected_level": RiskCategory.HIGH
    },
    4: {
        "name": "Scenario 4 — Critical Trench Excavation & Flood Hazard",
        "description": "Heavy monsoon rainfall, deep trench excavation active, standing water accumulation near trench edge with 18 workers nearby.",
        "input": {
            "weather_condition": "Heavy Rain, Downpour",
            "temperature": 22.0,
            "wind_speed": 35.0,
            "water_accumulation": True,
            "site_conditions": "Water accumulation and muddy slope erosion directly adjacent to main foundation excavation",
            "activities": ["Excavation", "Drainage Trenching"],
            "workers": 75,
            "equipment": [
                {"name": "Excavator EX-02", "status": "operational", "last_inspection": "2026-09-01"}
            ],
            "fire_protection_adequate": True,
            "scaffolding_inspected": False,
        },
        "expected_level": RiskCategory.CRITICAL
    },
    5: {
        "name": "Scenario 5 — Critical Electrical Shock & Water Intrusion",
        "description": "Water pooled directly around temporary electrical distribution panels during active conduit installation.",
        "input": {
            "weather_condition": "Rainy, Damp",
            "temperature": 24.0,
            "wind_speed": 18.0,
            "water_accumulation": True,
            "site_conditions": "Standing puddle 5cm deep around live 415V distribution board, cable insulation worn",
            "activities": ["Electrical Work", "Cable Pulling"],
            "workers": 40,
            "equipment": [],
            "fire_protection_adequate": True,
            "scaffolding_inspected": True,
        },
        "expected_level": RiskCategory.CRITICAL
    }
}


# ── Site Risk Agent Implementation ──────────────────────────────────────────

class SiteRiskAgent:
    """
    Site Risk Agent (Phase 1.2)
    Coordinates data collection, execution through BaseRiskAnalyzer,
    database persistence of RiskScore and Hazards, and automated notification alerts.
    """

    def __init__(self, analyzer: Optional[BaseRiskAnalyzer] = None):
        self.agent_id = "site_risk_agent_v1"
        self.name = "Site Risk Agent"
        self.version = "1.0.0-phase1.3"
        self.is_active = True
        self.last_run: Optional[datetime] = None
        self.analyzer: BaseRiskAnalyzer = analyzer or RuleBasedRiskAnalyzer()

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "is_active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "status": "active" if self.is_active else "inactive",
            "analyzer": self.analyzer.__class__.__name__,
        }

    async def run(self, site_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis on provided site context."""
        self.last_run = datetime.now(timezone.utc).replace(tzinfo=None)
        return self.analyzer.analyze(site_data)

    def analyze_and_persist(self, db, site_id: str, custom_input: Optional[Dict[str, Any]] = None, source_label: str = "site_risk_agent") -> Dict[str, Any]:
        """
        Execute analysis for a site, persist new RiskScore, update Site current score,
        save new Hazards, and broadcast Notifications for HIGH and CRITICAL risks.
        """
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site '{site_id}' not found")

        # Prepare context by aggregating DB entities if not overridden
        context: Dict[str, Any] = {"site_id": site.id}
        if custom_input:
            context.update(custom_input)
            context["site_id"] = site.id
        else:
            # Build context from database
            from app.models.models import Worker, Equipment, Activity
            workers_count = db.query(Worker).filter(Worker.site_id == site.id, Worker.is_active == True).count()
            equipment_rows = db.query(Equipment).filter(Equipment.site_id == site.id).all()
            recent_activities = db.query(Activity).filter(Activity.site_id == site.id).order_by(Activity.date.desc()).limit(5).all()

            context["weather_condition"] = "Clear"
            context["temperature"] = 28.0
            context["wind_speed"] = 12.0
            context["water_accumulation"] = False
            context["site_conditions"] = "Active operational construction site"
            context["activities"] = [a.activity_type.value for a in recent_activities] if recent_activities else ["General Construction"]
            context["workers"] = max(workers_count, site.worker_count or 10)
            context["equipment"] = [{"name": e.name, "status": e.status.value} for e in equipment_rows]

        # Execute analysis through analyzer
        analysis = self.analyzer.analyze(context)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.last_run = now

        # Update Site entity
        site.current_risk_score = analysis["overall_risk_score"]
        site.risk_category = analysis["risk_level"]
        site.updated_at = now

        # Create RiskScore record for historical auditing
        cats = analysis["categories"]
        risk_record = RiskScore(
            id=str(uuid.uuid4()),
            site_id=site.id,
            overall_score=analysis["overall_risk_score"],
            category=analysis["risk_level"],
            environmental_risk=cats["environmental"]["score"],
            equipment_risk=cats["equipment"]["score"],
            activity_risk=cats["activity"]["score"],
            site_condition_risk=cats["site_condition"]["score"],
            operational_risk=cats["operational"]["score"],
            highest_hazard_score=analysis["highest_hazard_score"],
            active_hazards_count=analysis["active_hazards_count"],
            critical_hazards_count=analysis["critical_hazards_count"],
            recommendations=analysis["recommendations"],
            reasoning=analysis["reasoning"],
            calculated_by=source_label,
            notes=f"Automated analysis by {self.name} ({source_label})",
            recorded_at=now,
        )
        db.add(risk_record)

        # Persist detected hazards
        created_hazard_objects = []
        base_count = db.query(Hazard).count()
        for idx, h_data in enumerate(analysis["hazards"]):
            haz_code = f"HAZ-AI-{base_count + idx + 1:04d}"

            haz_entity = Hazard(
                id=str(uuid.uuid4()),
                hazard_id=haz_code,
                site_id=site.id,
                hazard_type=h_data["hazard_type"],
                description=h_data["description"],
                evidence=h_data.get("evidence"),
                severity=h_data["severity"],
                probability=h_data["probability"],
                risk_score=h_data["risk_score"],
                risk_category=h_data["risk_level"],
                status=HazardStatus.OPEN,
                detected_at=now,
                reported_by="Site Risk Agent (Rule Engine)",
                recommended_action=h_data.get("recommended_action"),
                detection_source=h_data.get("detection_source", "RULE_ENGINE"),
                detected_by_agent=True,
                agent_confidence=0.92,
            )
            db.add(haz_entity)
            created_hazard_objects.append(haz_entity)

            # Generate automated Notification for High or Critical hazards (preventing duplicate unread alerts)
            if h_data["risk_level"] in [RiskCategory.HIGH, RiskCategory.CRITICAL]:
                sev_level = "critical" if h_data["risk_level"] == RiskCategory.CRITICAL else "warning"
                notif_title = f"{'CRITICAL' if sev_level == 'critical' else 'High-Risk'} Hazard: {h_data['description'][:50]}"
                existing_hazard_notif = db.query(Notification).filter(
                    Notification.category == NotificationCategory.RISK,
                    Notification.title == notif_title,
                    Notification.link == f"/sites/{site.id}",
                    Notification.is_read == False
                ).first()
                if not existing_hazard_notif:
                    notif = Notification(
                        id=str(uuid.uuid4()),
                        user_id=None,  # Broadcast to all project/site users
                        category=NotificationCategory.RISK,
                        title=notif_title,
                        message=f"Site Risk Agent detected {h_data['risk_level'].value.upper()} risk ({h_data['risk_score']}/100) at {site.name}. Recommended Action: {h_data['recommended_action']}",
                        severity=sev_level,
                        is_read=False,
                        link=f"/sites/{site.id}",
                        created_at=now,
                    )
                    db.add(notif)

        # If overall site score is CRITICAL or HIGH, also generate a site-level risk notification (prevent duplicates)
        if analysis["risk_level"] in [RiskCategory.HIGH, RiskCategory.CRITICAL]:
            site_sev = "critical" if analysis["risk_level"] == RiskCategory.CRITICAL else "warning"
            site_notif_title = f"Elevated Site Risk Alert: {site.name} ({analysis['overall_risk_score']}/100)"
            existing_site_notif = db.query(Notification).filter(
                Notification.category == NotificationCategory.RISK,
                Notification.title == site_notif_title,
                Notification.link == f"/sites/{site.id}",
                Notification.is_read == False
            ).first()
            if not existing_site_notif:
                site_notif = Notification(
                    id=str(uuid.uuid4()),
                    user_id=None,
                    category=NotificationCategory.RISK,
                    title=site_notif_title,
                    message=f"Overall risk escalated to {analysis['risk_level'].value.upper()} ({analysis['overall_risk_score']}/100). {len(analysis['hazards'])} active hazard factors detected.",
                    severity=site_sev,
                    is_read=False,
                    link=f"/sites/{site.id}",
                    created_at=now,
                )
                db.add(site_notif)

        db.commit()
        db.refresh(risk_record)

        # Include site name in response
        analysis["site_name"] = site.name
        analysis["timestamp"] = now
        analysis["record_id"] = risk_record.id

        # Attach generated IDs and site_id to returned hazards
        for i, h in enumerate(analysis["hazards"]):
            h["site_id"] = site.id
            if i < len(created_hazard_objects):
                h["id"] = created_hazard_objects[i].id
                h["hazard_id"] = created_hazard_objects[i].hazard_id

        return analysis


# Global singleton instance
site_risk_agent = SiteRiskAgent()
