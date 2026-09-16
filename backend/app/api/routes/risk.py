from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.models import Activity, Site, User, UserRole, Hazard, RiskScore, RiskCategory, HazardStatus
from app.schemas.schemas import (
    ActivityCreate, ActivityOut, HazardCreate, HazardUpdate, HazardOut, RiskScoreOut,
    SiteRiskAnalysisInput, SiteRiskAnalysisResponse, DemoScenarioRequest, HazardMitigateRequest
)
from app.api.dependencies import get_current_user, require_roles
from app.services.risk_scoring import calculate_risk_score, get_risk_category, calculate_overall_site_risk
import uuid
from datetime import datetime, timezone

# ── Activities ─────────────────────────────────────────────────────────────

activities_router = APIRouter(prefix="/activities", tags=["Activities"])

WRITE_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER]


@activities_router.get("", response_model=List[ActivityOut])
def list_activities(
    site_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Activity)
    if site_id:
        q = q.filter(Activity.site_id == site_id)
    elif current_user.role == UserRole.SITE_MANAGER and current_user.assigned_site_id:
        q = q.filter(Activity.site_id == current_user.assigned_site_id)
    activities = q.order_by(Activity.date.desc()).all()
    results = []
    for a in activities:
        d = ActivityOut.model_validate(a)
        site = db.query(Site).filter(Site.id == a.site_id).first()
        d.site_name = site.name if site else None
        results.append(d)
    return results


@activities_router.post("", response_model=ActivityOut, status_code=201)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    site = db.query(Site).filter(Site.id == payload.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    activity = Activity(
        id=str(uuid.uuid4()),
        created_by=current_user.id,
        **payload.model_dump()
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    d = ActivityOut.model_validate(activity)
    d.site_name = site.name
    return d


# ── Hazards ────────────────────────────────────────────────────────────────

hazards_router = APIRouter(prefix="/hazards", tags=["Hazards"])


def _make_hazard_id(db: Session) -> str:
    count = db.query(Hazard).count()
    return f"HAZ-{count + 1:04d}"


@hazards_router.get("", response_model=List[HazardOut])
def list_hazards(
    site_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Hazard)
    if site_id:
        q = q.filter(Hazard.site_id == site_id)
    if status:
        q = q.filter(Hazard.status == status)
    hazards = q.order_by(Hazard.detected_at.desc()).all()
    results = []
    for h in hazards:
        d = HazardOut.model_validate(h)
        site = db.query(Site).filter(Site.id == h.site_id).first()
        d.site_name = site.name if site else None
        results.append(d)
    return results


@hazards_router.post("", response_model=HazardOut, status_code=201)
def create_hazard(
    payload: HazardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    site = db.query(Site).filter(Site.id == payload.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    risk_score = calculate_risk_score(payload.probability, payload.severity)
    risk_cat = get_risk_category(risk_score)

    hazard = Hazard(
        id=str(uuid.uuid4()),
        hazard_id=_make_hazard_id(db),
        risk_score=risk_score,
        risk_category=risk_cat,
        **payload.model_dump(),
    )
    db.add(hazard)
    db.commit()
    db.refresh(hazard)

    d = HazardOut.model_validate(hazard)
    d.site_name = site.name
    return d


@hazards_router.put("/{hazard_id}", response_model=HazardOut)
def update_hazard(
    hazard_id: str,
    payload: HazardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    h = db.query(Hazard).filter(Hazard.id == hazard_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hazard not found")
    update_data = payload.model_dump(exclude_none=True)
    prob = update_data.pop("probability", h.probability)
    sev = update_data.pop("severity", h.severity)
    h.probability = prob
    h.severity = sev
    h.risk_score = calculate_risk_score(prob, sev)
    h.risk_category = get_risk_category(h.risk_score)
    for k, v in update_data.items():
        setattr(h, k, v)
    h.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(h)
    d = HazardOut.model_validate(h)
    site = db.query(Site).filter(Site.id == h.site_id).first()
    d.site_name = site.name if site else None
    return d


@hazards_router.post("/{hazard_id}/acknowledge", response_model=HazardOut)
def acknowledge_hazard(
    hazard_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    h = db.query(Hazard).filter(Hazard.id == hazard_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hazard not found")
    if h.status == HazardStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Cannot acknowledge a closed hazard")
    if h.status == HazardStatus.MITIGATED:
        raise HTTPException(status_code=400, detail="Cannot acknowledge an already mitigated hazard")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    h.status = HazardStatus.UNDER_REVIEW
    h.acknowledged_at = now
    h.acknowledged_by = current_user.id
    h.updated_at = now
    db.commit()
    db.refresh(h)
    d = HazardOut.model_validate(h)
    site = db.query(Site).filter(Site.id == h.site_id).first()
    d.site_name = site.name if site else None
    return d


@hazards_router.post("/{hazard_id}/mitigate", response_model=HazardOut)
def mitigate_hazard(
    hazard_id: str,
    payload: HazardMitigateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    h = db.query(Hazard).filter(Hazard.id == hazard_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hazard not found")
    if h.status == HazardStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Cannot mitigate an already closed hazard")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    h.status = HazardStatus.MITIGATED
    h.mitigated_at = now
    h.mitigated_by = current_user.id
    h.mitigation_notes = payload.mitigation_notes
    h.updated_at = now
    db.commit()
    db.refresh(h)
    d = HazardOut.model_validate(h)
    site = db.query(Site).filter(Site.id == h.site_id).first()
    d.site_name = site.name if site else None
    return d


@hazards_router.post("/{hazard_id}/close", response_model=HazardOut)
def close_hazard(
    hazard_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    h = db.query(Hazard).filter(Hazard.id == hazard_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hazard not found")
    if h.status == HazardStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Hazard is already closed")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    h.status = HazardStatus.CLOSED
    h.updated_at = now
    db.commit()
    db.refresh(h)
    d = HazardOut.model_validate(h)
    site = db.query(Site).filter(Site.id == h.site_id).first()
    d.site_name = site.name if site else None
    return d


# ── Risk Scores ────────────────────────────────────────────────────────────

risk_router = APIRouter(prefix="/risk-scores", tags=["Risk"])


@risk_router.get("", response_model=List[RiskScoreOut])
def list_risk_scores(
    site_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(RiskScore)
    if site_id:
        q = q.filter(RiskScore.site_id == site_id)
    scores = q.order_by(RiskScore.recorded_at.desc()).limit(100).all()
    results = []
    for sc in scores:
        d = RiskScoreOut.model_validate(sc)
        site = db.query(Site).filter(Site.id == sc.site_id).first()
        d.site_name = site.name if site else None
        results.append(d)
    return results


# ── Phase 1.2: Site Risk Intelligence Router (/risk) ───────────────────────

risk_intel_router = APIRouter(prefix="/risk", tags=["Site Risk Intelligence"])


@risk_intel_router.post("/analyze-site", response_model=SiteRiskAnalysisResponse)
def analyze_site_risk(
    payload: SiteRiskAnalysisInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    """
    Run the Site Risk Agent against the specified site.
    Ingests site environment, activity, and equipment data, executes the
    RuleBasedRiskAnalyzer, calculates multi-dimensional risk scores,
    persists new RiskScore and Hazards, and generates high/critical notifications.
    """
    from app.agents.site_risk_agent import site_risk_agent
    site = db.query(Site).filter(Site.id == payload.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{payload.site_id}' not found")

    custom_data = payload.model_dump(exclude_none=True)
    # Fix: map worker_count → workers (the key the RuleBasedRiskAnalyzer reads)
    if "worker_count" in custom_data and "workers" not in custom_data:
        custom_data["workers"] = custom_data.pop("worker_count")
    try:
        result = site_risk_agent.analyze_and_persist(
            db=db,
            site_id=payload.site_id,
            custom_input=custom_data,
            source_label=f"Site Risk Agent ({current_user.full_name})"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        print(f"[ERROR] Site risk analysis failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Site risk analysis failed. Please check site data and try again.")



@risk_intel_router.post("/demo-scenario", response_model=SiteRiskAnalysisResponse)
def run_demo_scenario(
    payload: DemoScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    """
    Execute one of the 5 deterministic construction risk demo scenarios
    on the specified site. Allows judges and reviewers to rapidly test
    various deterministic risk levels and hazard rule activations.
    """
    from app.agents.site_risk_agent import site_risk_agent, DEMO_SCENARIOS
    if payload.scenario_id not in DEMO_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario ID {payload.scenario_id}. Choose 1 through 5.")

    site = db.query(Site).filter(Site.id == payload.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{payload.site_id}' not found")

    scenario = DEMO_SCENARIOS[payload.scenario_id]
    custom_data = dict(scenario["input"])

    try:
        result = site_risk_agent.analyze_and_persist(
            db=db,
            site_id=payload.site_id,
            custom_input=custom_data,
            source_label=f"demo_scenario_{payload.scenario_id} ({scenario['name']})"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo scenario execution failed: {str(e)}")


@risk_intel_router.get("/demo-scenarios")
def list_demo_scenarios(_: User = Depends(get_current_user)):
    """Return catalog of the 5 deterministic demo scenarios for the frontend."""
    from app.agents.site_risk_agent import DEMO_SCENARIOS
    return [
        {
            "id": s_id,
            "name": s_data["name"],
            "description": s_data["description"],
            "expected_level": s_data["expected_level"].value.upper(),
        }
        for s_id, s_data in DEMO_SCENARIOS.items()
    ]


@risk_intel_router.get("/sites/{site_id}")
def get_site_risk_summary(
    site_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get the latest risk intelligence summary for a site."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    latest_score = db.query(RiskScore).filter(RiskScore.site_id == site_id).order_by(RiskScore.recorded_at.desc()).first()
    active_hazards = db.query(Hazard).filter(
        Hazard.site_id == site_id,
        Hazard.status.in_([HazardStatus.OPEN, HazardStatus.UNDER_REVIEW])
    ).all()

    return {
        "site_id": site.id,
        "site_name": site.name,
        "current_risk_score": site.current_risk_score,
        "risk_category": site.risk_category,
        "latest_score": RiskScoreOut.model_validate(latest_score) if latest_score else None,
        "active_hazards_count": len(active_hazards),
        "critical_hazards_count": sum(1 for h in active_hazards if h.risk_category == RiskCategory.CRITICAL),
    }


@risk_intel_router.get("/sites/{site_id}/history", response_model=List[RiskScoreOut])
def get_site_risk_history(
    site_id: str,
    limit: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve historical risk analyses and category breakdown for trend charts."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    scores = db.query(RiskScore).filter(RiskScore.site_id == site_id).order_by(RiskScore.recorded_at.desc()).limit(limit).all()
    results = []
    for sc in scores:
        d = RiskScoreOut.model_validate(sc)
        d.site_name = site.name
        results.append(d)
    return results


@risk_intel_router.get("/sites/{site_id}/hazards", response_model=List[HazardOut])
def get_site_hazards(
    site_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve all hazards detected at a site with optional status filtering."""
    q = db.query(Hazard).filter(Hazard.site_id == site_id)
    if status:
        q = q.filter(Hazard.status == status)
    hazards = q.order_by(Hazard.detected_at.desc()).all()
    results = []
    for h in hazards:
        d = HazardOut.model_validate(h)
        site = db.query(Site).filter(Site.id == h.site_id).first()
        d.site_name = site.name if site else None
        results.append(d)
    return results


# Forwarding lifecycle routes under /risk/hazards/... for convenience
@risk_intel_router.post("/hazards/{hazard_id}/acknowledge", response_model=HazardOut)
def acknowledge_hazard_alias(
    hazard_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    return acknowledge_hazard(hazard_id=hazard_id, db=db, current_user=current_user)


@risk_intel_router.post("/hazards/{hazard_id}/mitigate", response_model=HazardOut)
def mitigate_hazard_alias(
    hazard_id: str,
    payload: HazardMitigateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    return mitigate_hazard(hazard_id=hazard_id, payload=payload, db=db, current_user=current_user)


@risk_intel_router.post("/hazards/{hazard_id}/close", response_model=HazardOut)
def close_hazard_alias(
    hazard_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES, UserRole.SAFETY_OFFICER)),
):
    return close_hazard(hazard_id=hazard_id, db=db, current_user=current_user)

