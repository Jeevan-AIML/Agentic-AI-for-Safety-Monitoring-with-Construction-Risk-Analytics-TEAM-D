"""
Construction Risk Intelligence Engine — Milestone 4 Phase 4.2
==============================================================
Central analytical and predictive intelligence engine for ACRIP.
Consolidates findings from Site Risk, Safety, Compliance, and Insurance agents,
calculates overall project risk scores, detects recurring patterns, predicts
potential incidents, and generates actionable operational recommendations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from app.services.risk_intelligence.collector import RiskDataCollector, RiskIntelligenceFinding
from app.services.risk_intelligence.scorer import ProjectRiskScorer
from app.services.risk_intelligence.pattern_detector import RecurringRiskPatternDetector
from app.services.risk_intelligence.incident_predictor import PotentialIncidentPredictor
from app.services.risk_intelligence.recommender import OperationalRecommendationEngine


class ConstructionRiskIntelligenceEngine:
    """Enterprise risk intelligence analytical and predictive engine."""

    def __init__(self, min_pattern_occurrences: int = 2):
        self.collector = RiskDataCollector()
        self.scorer = ProjectRiskScorer()
        self.pattern_detector = RecurringRiskPatternDetector(min_threshold=min_pattern_occurrences)
        self.incident_predictor = PotentialIncidentPredictor()
        self.recommender = OperationalRecommendationEngine()

    def analyze(
        self,
        db: Optional[Session] = None,
        site_id: Optional[str] = None,
        project_id: Optional[str] = None,
        time_window_days: int = 30,
        custom_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes complete risk intelligence pipeline for a site or project.
        Returns consolidated analytical, pattern, prediction, and recommendation payload.
        """
        # 1. Collect and normalize domain findings
        collected = self.collector.collect(
            db=db,
            site_id=site_id,
            time_window_days=time_window_days,
            custom_context=custom_context,
        )

        site_info = collected["site"]
        data_quality = collected["data_quality"]
        findings = collected["findings"]
        raw_data = collected["raw"]

        # 2. Calculate deterministic project risk scores & category breakdowns
        score_data = self.scorer.calculate(collected)

        # 3. Detect recurring risk patterns
        pattern_data = self.pattern_detector.detect_patterns(
            findings=findings,
            time_window_days=time_window_days,
        )
        patterns = pattern_data["patterns"]

        # 4. Predict potential incidents via explainable causal chain modeling
        predictions = self.incident_predictor.predict_incidents(
            findings=findings,
            patterns=patterns,
            site_info=site_info,
            raw_data=raw_data,
        )

        # 5. Generate targeted operational recommendations
        recommendations = self.recommender.generate_recommendations(
            findings=findings,
            patterns=patterns,
            predictions=predictions,
            category_scores=score_data["category_scores"],
        )

        # 6. Extract critical findings
        critical_findings = [f.to_dict() for f in findings if f.severity == "CRITICAL"]

        intelligence_code = f"RKI-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        return {
            "intelligence_id": intelligence_code,
            "project_id": project_id or site_info.get("project_id"),
            "site_id": site_id or site_info.get("id"),
            "site_name": site_info.get("name"),
            "project_name": site_info.get("project_name"),
            "generated_at": datetime.utcnow().isoformat(),
            "time_window_days": time_window_days,
            "overall_risk_score": score_data["overall_risk_score"],
            "overall_risk_level": score_data["overall_risk_level"].value.upper() if hasattr(score_data["overall_risk_level"], "value") else str(score_data["overall_risk_level"]).upper(),
            "scoring_explanation": score_data["scoring_explanation"],
            "category_breakdown": score_data["category_scores"],
            "escalation_metrics": score_data["escalation_metrics"],
            "data_quality": data_quality,
            "critical_findings": critical_findings,
            "major_contributing_findings": score_data["major_contributing_findings"],
            "recurring_patterns": patterns,
            "recurring_patterns_summary": pattern_data["message"],
            "potential_incidents": predictions,
            "recommendations": recommendations,
            "supporting_metrics": {
                "total_findings_analyzed": len(findings),
                "critical_findings_count": len(critical_findings),
                "recurring_patterns_count": len(patterns),
                "predicted_incidents_count": len(predictions),
                "recommendations_count": len(recommendations),
                "workers_on_site": site_info.get("worker_count", 0),
                "equipment_on_site": site_info.get("equipment_count", 0),
            }
        }


# Singleton instance
risk_intelligence_engine = ConstructionRiskIntelligenceEngine()
