"""
Operational Recommendation Engine — Milestone 4 Phase 4.2
==========================================================
Generates prioritized, non-generic operational recommendations linked directly
to detected patterns, predicted incidents, and active critical findings.
Categorizes actions into Immediate (0-24h), Short-term (1-7d), and Mid-term (7-30d).
"""

from typing import Dict, Any, List, Optional
from app.services.risk_intelligence.collector import RiskIntelligenceFinding


class OperationalRecommendationEngine:
    """Produces actionable recommendations linked to actual empirical risk findings."""

    def generate_recommendations(
        self,
        findings: List[RiskIntelligenceFinding],
        patterns: Optional[Any] = None,
        predictions: Optional[Any] = None,
        category_scores: Optional[Dict[str, Any]] = None,
        overall_risk_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Synthesizes prioritized operational action items with specific role assignments."""
        patterns = patterns or []
        predictions = predictions or []
        category_scores = category_scores or {}

        recommendations: List[Dict[str, Any]] = []
        seen_actions = set()

        # ── 1. Recommendations from Predicted Incidents (Immediate Horizon) ───
        for idx, pred in enumerate(predictions):
            p_meas = pred.get("recommended_interventions") or pred.get("preventive_measures") or []
            priority = pred.get("severity_potential") or pred.get("risk_level", "CRITICAL")
            inc_title = pred.get("incident_type") or pred.get("predicted_incident_category", "Identified Risk Scenario")
            cat = "SAFETY" if "fall" in inc_title.lower() or "struck" in inc_title.lower() else (
                "SITE_RISK" if "trench" in inc_title.lower() else "COMPLIANCE"
            )

            actions = list(p_meas) if p_meas else [f"Deploy emergency safety countermeasures for {inc_title}"]
            title = f"Immediate Preemptive Action: Prevent {inc_title}"
            if title not in seen_actions:
                seen_actions.add(title)
                recommendations.append({
                    "recommendation_id": f"REC-PRED-{idx+1}",
                    "category": cat,
                    "priority": priority,
                    "timeframe": "IMMEDIATE",
                    "title": title,
                    "action": actions[0],
                    "action_items": actions,
                    "expected_risk_reduction": "-25% Incident Probability",
                    "target_hazard_types": [cat],
                    "cost_impact_level": "Medium / Operational Control",
                    "target_role": "Safety Officer" if cat == "SAFETY" else "Site Manager",
                    "reason": f"Averts predicted scenario: {inc_title}.",
                    "supporting_findings": pred.get("supporting_findings", []),
                    "status": "PROPOSED",
                })

        # ── 2. Recommendations from Detected Recurring Patterns (Short-Term) ─
        for idx, pat in enumerate(patterns):
            action = pat.get("recommended_countermeasure") or f"Address repeated {pat.get('pattern_type', 'hazard')} occurrences"
            pat_name = pat.get("pattern_name") or pat.get("pattern_description", "Recurring Pattern")
            if action not in seen_actions:
                seen_actions.add(action)
                p_sev = pat.get("severity", "HIGH")
                p_type = pat.get("pattern_type", "HAZARD_CLUSTER")
                cat = "SITE_RISK" if "HAZARD" in str(p_type) else ("SAFETY" if "SAFETY" in str(p_type) or "PPE" in str(p_type) else "COMPLIANCE")

                recommendations.append({
                    "recommendation_id": f"REC-PAT-{idx+1}",
                    "category": cat,
                    "priority": p_sev,
                    "timeframe": "SHORT_TERM",
                    "title": f"Corrective Control: Mitigate {pat_name}",
                    "action": action,
                    "action_items": [
                        action,
                        f"Assign dedicated supervisor to verify continuous compliance in affected zones.",
                        "Re-evaluate pattern velocity in next weekly multi-agent intelligence cycle.",
                    ],
                    "expected_risk_reduction": "-15% Recurrence Likelihood",
                    "target_hazard_types": [str(p_type)],
                    "cost_impact_level": "Low / Procedural Adjustment",
                    "target_role": "Superintendent" if cat == "SITE_RISK" else "Safety Officer",
                    "reason": f"Mitigates pattern: {pat_name}.",
                    "supporting_findings": pat.get("supporting_finding_ids") or pat.get("sample_finding_ids", []),
                    "status": "PROPOSED",
                })

        # ── 3. Recommendations from Standalone Critical / High Findings ─────
        crit_high_findings = [f for f in findings if f.severity in ["CRITICAL", "HIGH"] and not f.is_resolved]
        for idx, f in enumerate(crit_high_findings[:3]):
            act = (f.metadata or {}).get("recommended_action") or (f.metadata or {}).get("recommendation") or f.description
            if act not in seen_actions:
                seen_actions.add(act)
                recommendations.append({
                    "recommendation_id": f"REC-FND-{idx+1}",
                    "category": f.source_agent.upper(),
                    "priority": f.severity,
                    "timeframe": "IMMEDIATE" if f.severity == "CRITICAL" else "SHORT_TERM",
                    "title": f"Direct Mitigation: {f.description[:60]}",
                    "action": act,
                    "action_items": [act],
                    "expected_risk_reduction": "-10% Hazard Exposure",
                    "target_hazard_types": [f.finding_type or f.category],
                    "cost_impact_level": "Low / Direct Action",
                    "target_role": "Safety Officer" if f.source_agent == "safety" else "Site Manager",
                    "reason": f"Immediate resolution for {f.severity} finding.",
                    "supporting_findings": [f.finding_id],
                    "status": "PROPOSED",
                })

        # ── 4. Mid-Term Systemic Improvements ───────────────────────────────
        recommendations.append({
            "recommendation_id": f"REC-SYS-01",
            "category": "OPERATIONAL",
            "priority": "MEDIUM",
            "timeframe": "MID_TERM",
            "title": "Systemic Procedural Governance & Subcontractor Audit",
            "action": "Implement bi-weekly subcontractor safety audits and integrate multi-agent sensor tracking into daily morning briefings.",
            "action_items": [
                "Conduct cross-trade toolbox talks focusing on leading risk drivers.",
                "Review inspection logs and verify closeout of past corrective action notices.",
            ],
            "expected_risk_reduction": "-20% Site-Wide Risk Index",
            "target_hazard_types": ["GENERAL", "SYSTEMIC"],
            "cost_impact_level": "Medium / Administrative Governance",
            "target_role": "Project Manager",
            "reason": "Mid-term systemic improvement across all trade subcontracts.",
            "supporting_findings": [],
            "status": "PROPOSED",
        })

        # Sort recommendations by priority (CRITICAL -> HIGH -> MEDIUM -> LOW)
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 2))

        return recommendations
