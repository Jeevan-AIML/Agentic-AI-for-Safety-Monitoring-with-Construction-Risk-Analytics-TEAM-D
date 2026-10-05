"""
Risk Intelligence Service — Milestone 4 Phase 4.2
=================================================
Orchestrates risk intelligence execution, database persistence,
pattern querying, prediction retrieval, and history tracking.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from app.models.models import ProjectRiskIntelligence, Site, Project, RiskCategory
from app.services.risk_intelligence.engine import ConstructionRiskIntelligenceEngine


class RiskIntelligenceService:
    """Service encapsulating database persistence and queries for risk intelligence."""

    def __init__(self):
        self.engine = ConstructionRiskIntelligenceEngine()

    def analyze_and_save(
        self,
        db: Session,
        site_id: str,
        project_id: Optional[str] = None,
        time_window_days: int = 30,
        is_simulation: bool = False,
        created_by: str = "ConstructionRiskIntelligenceEngine",
        custom_context: Optional[Dict[str, Any]] = None,
    ) -> ProjectRiskIntelligence:
        """Executes intelligence analysis and persists ProjectRiskIntelligence record in DB."""
        analysis = self.engine.analyze(
            db=db if not custom_context else None,
            site_id=site_id,
            project_id=project_id,
            time_window_days=time_window_days,
            custom_context=custom_context,
        )

        site = db.query(Site).filter(Site.id == site_id).first()
        proj_id = project_id or (site.project_id if site else None)

        level_str = analysis.get("overall_risk_level")
        if hasattr(level_str, "value"):
            level_val = str(level_str.value).lower()
        elif isinstance(level_str, str):
            level_val = level_str.lower()
        else:
            level_val = "low"
        try:
            risk_cat = RiskCategory(level_val)
        except (ValueError, KeyError, AttributeError):
            risk_cat = RiskCategory.MEDIUM

        record = ProjectRiskIntelligence(
            id=str(uuid.uuid4()),
            intelligence_id=analysis["intelligence_id"],
            project_id=proj_id,
            site_id=site_id,
            overall_risk_score=analysis["overall_risk_score"],
            overall_risk_level=risk_cat,
            scoring_explanation=analysis["scoring_explanation"],
            category_scores=analysis["category_breakdown"],
            data_quality=analysis["data_quality"],
            critical_findings=analysis["critical_findings"],
            recurring_patterns=analysis["recurring_patterns"],
            potential_incidents=analysis["potential_incidents"],
            recommendations=analysis["recommendations"],
            supporting_metrics=analysis["supporting_metrics"],
            time_window_days=time_window_days,
            is_simulation=is_simulation,
            created_by=created_by,
            generated_at=datetime.utcnow(),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record

    def get_latest_assessment(
        self,
        db: Session,
        site_id: str,
        auto_generate_if_missing: bool = True,
    ) -> Optional[ProjectRiskIntelligence]:
        """Retrieves most recent saved intelligence assessment, or computes on demand."""
        latest = (
            db.query(ProjectRiskIntelligence)
            .filter(ProjectRiskIntelligence.site_id == site_id)
            .order_by(ProjectRiskIntelligence.generated_at.desc())
            .first()
        )
        if not latest and auto_generate_if_missing:
            site = db.query(Site).filter(Site.id == site_id).first()
            if site:
                return self.analyze_and_save(db, site_id=site_id)
        return latest

    def get_patterns(
        self,
        db: Session,
        site_id: str,
        time_window_days: int = 30,
    ) -> Dict[str, Any]:
        """Runs pattern detection specifically for a site over specified window."""
        analysis = self.engine.analyze(
            db=db,
            site_id=site_id,
            time_window_days=time_window_days,
        )
        return {
            "site_id": site_id,
            "time_window_days": time_window_days,
            "patterns_count": len(analysis["recurring_patterns"]),
            "patterns": analysis["recurring_patterns"],
            "summary": analysis["recurring_patterns_summary"],
        }

    def get_predictions(
        self,
        db: Session,
        site_id: str,
    ) -> List[Dict[str, Any]]:
        """Runs explainable potential incident prediction for a site."""
        analysis = self.engine.analyze(db=db, site_id=site_id)
        return analysis["potential_incidents"]

    def get_recommendations(
        self,
        db: Session,
        site_id: str,
    ) -> List[Dict[str, Any]]:
        """Retrieves operational recommendations for a site."""
        analysis = self.engine.analyze(db=db, site_id=site_id)
        return analysis["recommendations"]

    def list_history(
        self,
        db: Session,
        site_id: str,
        limit: int = 20,
    ) -> List[ProjectRiskIntelligence]:
        """Lists historical intelligence assessments for a site."""
        return (
            db.query(ProjectRiskIntelligence)
            .filter(ProjectRiskIntelligence.site_id == site_id)
            .order_by(ProjectRiskIntelligence.generated_at.desc())
            .limit(limit)
            .all()
        )

    def perform_site_risk_analysis(
        self,
        db: Session,
        site_id: str,
        project_id: Optional[str] = None,
        window_days: int = 30,
        is_simulation: bool = False,
    ) -> ProjectRiskIntelligence:
        return self.analyze_and_save(
            db=db,
            site_id=site_id,
            project_id=project_id,
            time_window_days=window_days,
            is_simulation=is_simulation,
        )

    def get_site_patterns(
        self,
        db: Session,
        site_id: str,
        window_days: int = 30,
        min_threshold: int = 2,
    ) -> List[Dict[str, Any]]:
        pat_data = self.get_patterns(db=db, site_id=site_id, time_window_days=window_days)
        return pat_data.get("patterns", [])

    def get_site_predictions(
        self,
        db: Session,
        site_id: str,
        window_days: int = 30,
    ) -> List[Dict[str, Any]]:
        return self.get_predictions(db=db, site_id=site_id)

    def get_site_recommendations(
        self,
        db: Session,
        site_id: str,
        window_days: int = 30,
    ) -> List[Dict[str, Any]]:
        return self.get_recommendations(db=db, site_id=site_id)

    def get_assessment_history(
        self,
        db: Session,
        site_id: str,
        limit: int = 20,
    ) -> List[ProjectRiskIntelligence]:
        return self.list_history(db=db, site_id=site_id, limit=limit)

