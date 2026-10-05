"""
Construction Risk Intelligence Engine REST API Router — Milestone 4 Phase 4.2
=============================================================================
Exposes endpoints for multi-agent risk synthesis, project risk scoring,
recurring risk pattern detection, causal incident prediction, and
operational recommendation generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    RiskIntelligenceAnalysisRequest,
    RiskIntelligenceAssessmentOut,
    RecurringPatternOut,
    PotentialIncidentPredictionOut,
    OperationalRecommendationOut,
)
from app.services.risk_intelligence.intelligence_service import RiskIntelligenceService

router = APIRouter(prefix="/risk-intelligence", tags=["Construction Risk Intelligence"])
intelligence_service = RiskIntelligenceService()


@router.post("/analyze", response_model=RiskIntelligenceAssessmentOut, status_code=status.HTTP_201_CREATED)
def run_risk_intelligence_analysis(
    payload: RiskIntelligenceAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute comprehensive multi-agent risk consolidation for a site or project.
    Calculates 4-pillar risk scores, identifies recurring risk patterns,
    predicts potential incidents, and produces prioritized operational recommendations.
    """
    try:
        assessment = intelligence_service.perform_site_risk_analysis(
            db=db,
            site_id=payload.site_id,
            project_id=payload.project_id,
            window_days=payload.analysis_window_days or 30,
        )
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk intelligence assessment failed: {str(e)}"
        )


@router.get("/site/{site_id}", response_model=RiskIntelligenceAssessmentOut)
def get_latest_site_intelligence(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the most recent risk intelligence assessment for a site.
    If no assessment exists, dynamically triggers a fresh one.
    """
    assessment = intelligence_service.get_latest_assessment(db, site_id)
    if not assessment:
        try:
            assessment = intelligence_service.perform_site_risk_analysis(
                db=db,
                site_id=site_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return assessment


@router.get("/patterns/{site_id}", response_model=List[RecurringPatternOut])
def get_recurring_patterns(
    site_id: str,
    window_days: int = Query(30, ge=1, le=90),
    min_threshold: int = Query(2, ge=2, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze and retrieve recurring risk patterns (>= min_threshold occurrences)
    across all agent findings for a site.
    """
    try:
        patterns = intelligence_service.get_site_patterns(
            db=db,
            site_id=site_id,
            window_days=window_days,
            min_threshold=min_threshold,
        )
        return patterns
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/predictions/{site_id}", response_model=List[PotentialIncidentPredictionOut])
def get_potential_incident_predictions(
    site_id: str,
    window_days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve deterministic, explainable causal incident predictions based on
    cross-agent findings and known leading indicator chains.
    """
    try:
        predictions = intelligence_service.get_site_predictions(
            db=db,
            site_id=site_id,
            window_days=window_days,
        )
        return predictions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/recommendations/{site_id}", response_model=List[OperationalRecommendationOut])
def get_operational_recommendations(
    site_id: str,
    window_days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve operational recommendations categorized into immediate corrective,
    short-term preventative, and mid-term procedural actions.
    """
    try:
        recommendations = intelligence_service.get_site_recommendations(
            db=db,
            site_id=site_id,
            window_days=window_days,
        )
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/history/{site_id}", response_model=List[RiskIntelligenceAssessmentOut])
def get_site_intelligence_history(
    site_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve historical risk intelligence assessments for trend analysis.
    """
    return intelligence_service.get_assessment_history(db=db, site_id=site_id, limit=limit)
