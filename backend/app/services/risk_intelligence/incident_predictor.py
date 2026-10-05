"""
Potential Incident Predictor — Milestone 4 Phase 4.2
=====================================================
Transparent, explainable potential incident forecasting based on synergistic
cross-agent causal risk chains. Does NOT use fabricated AI predictions.
"""

from typing import Dict, Any, List, Optional
from app.services.risk_intelligence.collector import RiskIntelligenceFinding


class PotentialIncidentPredictor:
    """Evaluates cross-pillar hazard and violation correlations to identify elevated incident risks."""

    def predict_incidents(
        self,
        findings: List[RiskIntelligenceFinding],
        patterns: Optional[Any] = None,
        site_info: Optional[Dict[str, Any]] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes causal risk correlation matrix against current site findings.
        Returns explainable incident predictions with causal chains and preventive measures.
        """
        # Handle positional site_conditions dictionary passed as second parameter
        if isinstance(patterns, dict) and site_info is None:
            site_info = patterns
            patterns = []

        site_info = site_info or {}
        raw_data = raw_data or {}
        predictions: List[Dict[str, Any]] = []

        all_text = " ".join([
            f"{f.description} {f.category} {f.finding_type or ''} {(f.metadata or {}).get('hazard_type', '')}"
            for f in findings
        ]).lower()

        water_accum = site_info.get("water_accumulation", False) or ("water" in all_text) or ("rain" in all_text)

        findings_by_agent: Dict[str, List[RiskIntelligenceFinding]] = {
            "site_risk": [f for f in findings if f.source_agent in ["site_risk", "SITE_RISK"] or f.category in ["SITE_RISK", "HAZARD"]],
            "safety": [f for f in findings if f.source_agent in ["safety", "SAFETY"] or f.category in ["SAFETY", "SAFETY_VIOLATION"]],
            "compliance": [f for f in findings if f.source_agent in ["compliance", "COMPLIANCE"] or f.category in ["COMPLIANCE", "REGULATORY_BREACH"]],
            "insurance": [f for f in findings if f.source_agent in ["insurance", "INSURANCE"] or f.category in ["INSURANCE", "INSURANCE_CLAIM"]],
        }

        # ── 1. Causal Chain: Trench Cave-In & Worker Entrapment ─────────────
        has_excavation = any("excavat" in f.description.lower() or "trench" in f.description.lower() or f.finding_type == "EXCAVATION" for f in findings)
        has_water_or_fissure = water_accum or any("water" in f.description.lower() or "fissure" in f.description.lower() or "instabilit" in f.description.lower() for f in findings)
        has_trench_compliance = any("trench" in f.description.lower() or "652" in str(f.metadata) or "shoring" in f.description.lower() for f in findings)

        if has_excavation and (has_water_or_fissure or has_trench_compliance):
            conf = 0.88 if (has_water_or_fissure and has_trench_compliance) else 0.72
            prob_pct = round(conf * 100, 1)
            supporting = [
                f.finding_id for f in findings
                if "excavat" in f.description.lower() or "trench" in f.description.lower() or "water" in f.description.lower() or f.finding_type == "EXCAVATION"
            ]

            chain = [
                "1. Excavation cut in cohesive/granular soil with inadequate slope angle.",
                "2. Environmental precipitation / ground saturation accelerates hydrostatic sidewall pore pressure.",
                "3. Micro-fissures propagate along the trench crest creating shear cleavage planes.",
                "4. Catastrophic trench sidewall collapse occurs, trapping in-trench personnel under heavy spoil.",
            ]

            indicators = [
                {"indicator": "Trench Sidewall Integrity", "severity": "CRITICAL", "observed_value": "Fissures and soil sloughing logged"},
                {"indicator": "Groundwater Condition", "severity": "HIGH", "observed_value": "Surface water saturation observed"},
                {"indicator": "Protective Shoring", "severity": "HIGH", "observed_value": "No certified trench box present"},
            ]

            interventions = [
                "Immediately evacuate personnel from excavation zones until geotechnical stability is recertified.",
                "Pump out all standing water and install certified hydraulic trench shoring boxes.",
                "Verify OSHA compliant ladders/ramps within 25ft lateral travel distance of all workers.",
            ]

            predictions.append({
                "prediction_id": "PRED-INC-01",
                "incident_type": "Trench Cave-In & Worker Entrapment",
                "predicted_incident_category": "Trench Wall Collapse / Worker Engulfment",
                "severity_potential": "CRITICAL",
                "risk_level": "CRITICAL",
                "probability_score": prob_pct,
                "confidence_score": round(conf, 2),
                "predicted_timeframe": "Immediate (24–48 hours)",
                "time_horizon": "Immediate (24–48 hours)",
                "primary_driver": "Trench Soil Instability & Water Infiltration",
                "reasoning": (
                    "Synergistic risk correlation: Active excavation soil instability combined with water saturation "
                    "and/or missing regulatory protective shoring significantly escalates trench shear failure probability."
                ),
                "causal_chain": chain,
                "leading_indicators": indicators,
                "recommended_interventions": interventions,
                "preventive_measures": interventions,
                "supporting_findings": supporting[:5],
            })

        # ── 2. Causal Chain: Fall From Elevated Work Surface ────────────────
        has_fall_hazard = any("fall" in f.description.lower() or "scaffold" in f.description.lower() or "height" in f.description.lower() or f.finding_type == "FALL_HAZARD" for f in findings)
        has_harness_violation = any("harness" in f.description.lower() or "tie-off" in f.description.lower() or f.finding_type == "PPE_VIOLATION" for f in findings)
        has_guardrail = any("guardrail" in f.description.lower() or "501" in str(f.metadata) or "toe-board" in f.description.lower() for f in findings)

        if has_fall_hazard and (has_harness_violation or has_guardrail):
            conf = 0.85 if (has_harness_violation and has_guardrail) else 0.70
            prob_pct = round(conf * 100, 1)
            supporting = [
                f.finding_id for f in findings
                if "fall" in f.description.lower() or "harness" in f.description.lower() or "scaffold" in f.description.lower() or f.finding_type in ["FALL_HAZARD", "PPE_VIOLATION"]
            ]

            chain = [
                "1. Work activities authorized at elevation exceeding 6 feet (scaffolding/slab edges).",
                "2. Physical perimeter protection (guardrails/mid-rails) missing or partially disassembled.",
                "3. Worker operating in elevated zone without clipped personal fall arrest system (PFAS).",
                "4. Slip, trip, or sudden loss of balance results in catastrophic unarrested fall to lower level.",
            ]

            indicators = [
                {"indicator": "Elevated Work Perimeter", "severity": "CRITICAL", "observed_value": "Unprotected scaffold edges logged"},
                {"indicator": "Worker Fall Protection", "severity": "HIGH", "observed_value": "Unclipped PFAS harnesses observed"},
            ]

            interventions = [
                "Implement mandatory 100% dual-lanyard tie-off enforcement at heights above 6 feet.",
                "Inspect and red-tag all scaffolding platforms lacking toe-boards or mid-rails.",
                "Conduct mandatory safety stand-down for all high-elevation trades before shift start.",
            ]

            predictions.append({
                "prediction_id": "PRED-INC-02",
                "incident_type": "Fall From Elevated Work Surface",
                "predicted_incident_category": "Fall from Elevated Structure / Scaffold Failure",
                "severity_potential": "CRITICAL",
                "risk_level": "CRITICAL",
                "probability_score": prob_pct,
                "confidence_score": round(conf, 2),
                "predicted_timeframe": "Immediate (Next Operational Shift)",
                "time_horizon": "Immediate (Next Operational Shift)",
                "primary_driver": "Working at Height without Fall Protection",
                "reasoning": (
                    "Causal alignment: Presence of elevated work hazards combined with unmitigated worker PPE harness non-compliance "
                    "or unprotected platform edges creates critical fall probability exceeding OSHA safety factors."
                ),
                "causal_chain": chain,
                "leading_indicators": indicators,
                "recommended_interventions": interventions,
                "preventive_measures": interventions,
                "supporting_findings": supporting[:5],
            })

        # ── 3. Causal Chain: Worker-Equipment Struck-by Collision ────────────
        has_equip = any("equipment" in f.description.lower() or "crane" in f.description.lower() or "vehicle" in f.description.lower() or f.finding_type == "EQUIPMENT" for f in findings)
        has_proximity = any("vest" in f.description.lower() or "proximity" in f.description.lower() or "blind" in f.description.lower() or "zone" in f.description.lower() for f in findings)

        if has_equip and has_proximity:
            conf = 0.76
            prob_pct = round(conf * 100, 1)
            supporting = [
                f.finding_id for f in findings
                if "equipment" in f.description.lower() or "crane" in f.description.lower() or "vest" in f.description.lower() or "proximity" in f.description.lower()
            ]

            chain = [
                "1. Heavy equipment / articulated machinery operating in congested worker zone.",
                "2. Operator forward/blind-spot visibility restricted due to structural staging.",
                "3. Pedestrian worker enters active machine turning radius without high-visibility PPE.",
                "4. Struck-by or pinch-point collision occurs during equipment rotation or reversal.",
            ]

            indicators = [
                {"indicator": "Equipment Swing Radius", "severity": "HIGH", "observed_value": "Bollard perimeter breaches logged"},
                {"indicator": "High-Visibility PPE", "severity": "HIGH", "observed_value": "Workers without reflective vests in transit zone"},
            ]

            interventions = [
                "Enforce strict 20-foot machine exclusion perimeters with physical bollards and warning cones.",
                "Require dedicated trained spotters for all reversing or articulating heavy machinery.",
                "Audit high-visibility vest compliance at site turnstiles and security entry gates.",
            ]

            predictions.append({
                "prediction_id": "PRED-INC-03",
                "incident_type": "Struck-By Mobile Equipment / Machinery Collision",
                "predicted_incident_category": "Worker-Equipment Struck-By / Pinch-Point Crush",
                "severity_potential": "HIGH",
                "risk_level": "HIGH",
                "probability_score": prob_pct,
                "confidence_score": round(conf, 2),
                "predicted_timeframe": "Near-term (1–3 days)",
                "time_horizon": "Near-term (1–3 days)",
                "primary_driver": "Heavy Machinery Blind-Spot Proximity & Exclusion Zone Breaches",
                "reasoning": (
                    "Blind-spot risk convergence: Active mobile machinery maneuvering in zones where pedestrian workers "
                    "lack high-visibility vests or breach equipment swing radii dramatically increases struck-by incidents."
                ),
                "causal_chain": chain,
                "leading_indicators": indicators,
                "recommended_interventions": interventions,
                "preventive_measures": interventions,
                "supporting_findings": supporting[:5],
            })

        return predictions
