"""
Project Risk Scorer — Milestone 4 Phase 4.2
===========================================
Deterministic, explainable, and reproducible multi-pillar project risk calculation.
Integrates Site Risk, Safety Risk, Compliance Risk, and Insurance Risk.
"""

from typing import Dict, Any, List, Tuple
from app.models.models import RiskCategory
from app.services.risk_scoring import get_risk_category
from app.services.risk_intelligence.collector import RiskIntelligenceFinding


class ProjectRiskScorer:
    """Calculates consolidated project risk scores and category-level risk breakdowns."""

    DEFAULT_WEIGHTS = {
        "site_risk": 0.30,
        "safety_risk": 0.30,
        "compliance_risk": 0.20,
        "insurance_risk": 0.20,
    }

    def calculate(
        self,
        collected_data: Dict[str, Any],
        custom_weights: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """
        Calculates overall project risk score (0-100), overall risk category,
        category breakdowns, percentage contributions, and an explainable breakdown.
        """
        weights = custom_weights or self.DEFAULT_WEIGHTS
        site = collected_data["site"]
        findings: List[RiskIntelligenceFinding] = collected_data["findings"]
        raw = collected_data["raw"]

        # ── 1. Calculate Standardized Category Risk Scores (0-100) ──────────

        # A. Site Risk (Direct 0-100 scale: higher = more hazard risk)
        latest_rs = raw.get("latest_risk_score")
        if latest_rs:
            site_risk_raw = getattr(latest_rs, "overall_risk_score", None)
            if site_risk_raw is None and isinstance(latest_rs, dict):
                site_risk_raw = latest_rs.get("overall_risk_score")
        else:
            site_risk_raw = site.get("current_risk_score", 30.0)

        site_risk_score = round(float(site_risk_raw or 0.0), 2)

        # B. Safety Risk (Invert safety score: higher = more risk)
        latest_sa = raw.get("latest_safety_analysis")
        if latest_sa:
            safety_perf = getattr(latest_sa, "overall_safety_score", None)
            if safety_perf is None and isinstance(latest_sa, dict):
                safety_perf = latest_sa.get("overall_safety_score")
        else:
            safety_perf = 85.0
        safety_perf = float(safety_perf or 85.0)

        # Active safety violations penalty
        active_safety_crit = sum(1 for f in findings if f.source_agent == "safety" and f.severity == "CRITICAL" and f.status in ["OPEN", "TRIGGERED"])
        active_safety_high = sum(1 for f in findings if f.source_agent == "safety" and f.severity == "HIGH" and f.status in ["OPEN", "TRIGGERED"])

        base_safety_risk = 100.0 - safety_perf
        safety_risk_score = round(min(base_safety_risk + (active_safety_crit * 5.0) + (active_safety_high * 2.5), 100.0), 2)

        # C. Compliance Risk (Invert compliance score: higher = more risk)
        latest_ca = raw.get("latest_compliance")
        if latest_ca:
            comp_perf = getattr(latest_ca, "compliance_score", None)
            if comp_perf is None and isinstance(latest_ca, dict):
                comp_perf = latest_ca.get("compliance_score")
        else:
            comp_perf = 85.0
        comp_perf = float(comp_perf or 85.0)

        # Overdue inspection penalties
        inspections = raw.get("inspections", [])
        overdue_count = sum(1 for i in inspections if getattr(i, "is_overdue", False) or (isinstance(i, dict) and i.get("is_overdue")))
        active_comp_crit = sum(1 for f in findings if f.source_agent == "compliance" and f.severity == "CRITICAL" and f.status == "OPEN")

        base_compliance_risk = 100.0 - comp_perf
        compliance_risk_score = round(min(base_compliance_risk + (overdue_count * 5.0) + (active_comp_crit * 5.0), 100.0), 2)

        # D. Insurance Risk (Direct 0-100 scale: higher = more exposure)
        latest_ins = raw.get("latest_insurance")
        if latest_ins:
            ins_raw = getattr(latest_ins, "insurance_risk_score", None)
            if ins_raw is None and isinstance(latest_ins, dict):
                ins_raw = latest_ins.get("insurance_risk_score")
        else:
            ins_raw = 25.0
        insurance_risk_score = round(float(ins_raw or 25.0), 2)

        # ── 2. Weighted Composite Calculation ───────────────────────────────
        weighted_site = site_risk_score * weights["site_risk"]
        weighted_safety = safety_risk_score * weights["safety_risk"]
        weighted_comp = compliance_risk_score * weights["compliance_risk"]
        weighted_ins = insurance_risk_score * weights["insurance_risk"]

        base_composite = weighted_site + weighted_safety + weighted_comp + weighted_ins

        # Critical severity escalation bonus (additive penalty for open critical hazards across all agents)
        total_critical = sum(1 for f in findings if f.severity == "CRITICAL" and f.status in ["OPEN", "TRIGGERED", "UNDER_REVIEW"])
        total_high = sum(1 for f in findings if f.severity == "HIGH" and f.status in ["OPEN", "TRIGGERED", "UNDER_REVIEW"])
        escalation_penalty = min(total_critical * 2.5 + total_high * 1.0, 15.0)

        overall_risk_score = round(min(base_composite + escalation_penalty, 100.0), 2)
        overall_risk_level = get_risk_category(overall_risk_score)

        # ── 3. Category Contributions Calculation ───────────────────────────
        if base_composite > 0:
            site_contrib = round((weighted_site / base_composite) * 100.0, 1)
            safety_contrib = round((weighted_safety / base_composite) * 100.0, 1)
            comp_contrib = round((weighted_comp / base_composite) * 100.0, 1)
            ins_contrib = round((weighted_ins / base_composite) * 100.0, 1)
        else:
            site_contrib = safety_contrib = 30.0
            comp_contrib = ins_contrib = 20.0

        # ── 4. Major Contributing Findings ───────────────────────────────────
        sorted_findings = sorted(
            findings,
            key=lambda f: (
                0 if f.severity == "CRITICAL" else (1 if f.severity == "HIGH" else 2),
                -f.risk_score
            )
        )
        major_contributors = [f.to_dict() for f in sorted_findings[:6]]

        # ── 5. Mathematical Explanation ──────────────────────────────────────
        explanation = (
            f"Consolidated project risk score calculated at {overall_risk_score}/100 ({overall_risk_level.value.upper()}). "
            f"Formula: (Site Risk {site_risk_score} × {weights['site_risk']}) + "
            f"(Safety Risk {safety_risk_score} × {weights['safety_risk']}) + "
            f"(Compliance Risk {compliance_risk_score} × {weights['compliance_risk']}) + "
            f"(Insurance Risk {insurance_risk_score} × {weights['insurance_risk']}) = {base_composite:.2f} "
            f"+ Escalation Penalty {escalation_penalty:.1f} ({total_critical} critical, {total_high} high findings). "
            f"Primary risk drivers: Site Risk ({site_contrib}%) and Safety Risk ({safety_contrib}%)."
        )

        return {
            "overall_risk_score": overall_risk_score,
            "overall_risk_level": overall_risk_level,
            "scoring_explanation": explanation,
            "category_scores": {
                "site_risk": {
                    "score": site_risk_score,
                    "level": get_risk_category(site_risk_score).value.upper(),
                    "weight_pct": int(weights["site_risk"] * 100),
                    "contribution_pct": site_contrib,
                },
                "safety_risk": {
                    "score": safety_risk_score,
                    "level": get_risk_category(safety_risk_score).value.upper(),
                    "weight_pct": int(weights["safety_risk"] * 100),
                    "contribution_pct": safety_contrib,
                },
                "compliance_risk": {
                    "score": compliance_risk_score,
                    "level": get_risk_category(compliance_risk_score).value.upper(),
                    "weight_pct": int(weights["compliance_risk"] * 100),
                    "contribution_pct": comp_contrib,
                },
                "insurance_risk": {
                    "score": insurance_risk_score,
                    "level": get_risk_category(insurance_risk_score).value.upper(),
                    "weight_pct": int(weights["insurance_risk"] * 100),
                    "contribution_pct": ins_contrib,
                },
                "site_risk_score": site_risk_score,
                "safety_risk_score": safety_risk_score,
                "compliance_risk_score": compliance_risk_score,
                "insurance_risk_score": insurance_risk_score,
                "weights": weights,
            },
            "escalation_metrics": {
                "total_critical": total_critical,
                "total_high": total_high,
                "escalation_penalty": escalation_penalty,
            },
            "major_contributing_findings": major_contributors,
        }

    def _determine_risk_level(self, score: float) -> str:
        """Strict risk tier boundaries mapping."""
        if score <= 25.0:
            return "LOW"
        elif score <= 50.0:
            return "MEDIUM"
        elif score <= 75.0:
            return "HIGH"
        else:
            return "CRITICAL"

    def calculate_project_risk(
        self,
        findings: List[RiskIntelligenceFinding],
        site_conditions: Optional[Dict[str, Any]] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Calculates project risk directly from a findings list."""
        weights = custom_weights or self.DEFAULT_WEIGHTS

        # Categorize findings
        site_f = [f for f in findings if f.source_agent in ["site_risk", "SITE_RISK"] or f.category in ["SITE_RISK", "HAZARD"]]
        safety_f = [f for f in findings if f.source_agent in ["safety", "SAFETY"] or f.category in ["SAFETY", "SAFETY_VIOLATION"]]
        comp_f = [f for f in findings if f.source_agent in ["compliance", "COMPLIANCE"] or f.category in ["COMPLIANCE", "REGULATORY_BREACH"]]
        ins_f = [f for f in findings if f.source_agent in ["insurance", "INSURANCE"] or f.category in ["INSURANCE", "INSURANCE_CLAIM"]]

        site_score = round(sum(f.risk_score for f in site_f) / len(site_f), 2) if site_f else 15.0
        safety_score = round(sum(f.risk_score for f in safety_f) / len(safety_f), 2) if safety_f else 15.0
        comp_score = round(sum(f.risk_score for f in comp_f) / len(comp_f), 2) if comp_f else 15.0
        ins_score = round(sum(f.risk_score for f in ins_f) / len(ins_f), 2) if ins_f else 15.0

        base_composite = (
            site_score * weights["site_risk"] +
            safety_score * weights["safety_risk"] +
            comp_score * weights["compliance_risk"] +
            ins_score * weights["insurance_risk"]
        )

        crit_count = sum(1 for f in findings if f.severity == "CRITICAL" and not f.is_resolved)
        high_count = sum(1 for f in findings if f.severity == "HIGH" and not f.is_resolved)
        penalty = min(crit_count * 2.5 + high_count * 1.0, 15.0)

        overall_score = round(min(base_composite + penalty, 100.0), 2)
        risk_level = self._determine_risk_level(overall_score)

        return {
            "overall_score": overall_score,
            "overall_risk_score": overall_score,
            "risk_level": risk_level,
            "category_scores": {
                "site_risk": site_score,
                "safety_risk": safety_score,
                "compliance_risk": comp_score,
                "insurance_risk": ins_score,
                "site_risk_score": site_score,
                "safety_risk_score": safety_score,
                "compliance_risk_score": comp_score,
                "insurance_risk_score": ins_score,
                "weights": weights,
            },
            "findings_count": len(findings),
            "critical_count": crit_count,
            "high_count": high_count,
        }

