from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.database.session import get_db
from app.models.models import (
    Site, Worker, User, UserRole, RiskCategory,
    SafetyFinding, SafetyAnalysis, SafetyFindingStatus
)
from app.schemas.schemas import (
    SafetyFindingOut, SafetyFindingUpdate, SafetyFindingMitigateRequest,
    SafetyAnalysisOut, SafetyAnalysisResponse,
    SafetyAnalyzeSiteRequest, SafetyDemoScenarioRequest, SafetyDemoScenarioOut
)
from app.api.dependencies import get_current_user, require_roles
from app.agents.safety_agent import safety_agent, SAFETY_DEMO_SCENARIOS

router = APIRouter(prefix="/safety", tags=["Safety Agent"])

WRITE_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PROJECT_MANAGER,
    UserRole.SITE_MANAGER,
    UserRole.SAFETY_OFFICER,
]


def _enrich_finding(f: SafetyFinding, db: Session) -> SafetyFindingOut:
    out = SafetyFindingOut.model_validate(f)
    if f.worker_id:
        worker = db.query(Worker).filter(Worker.id == f.worker_id).first()
        if worker:
            out.worker_name = worker.name
            out.worker_code = worker.worker_id
    return out


# ── Analysis Endpoints ──────────────────────────────────────────────────────

@router.post("/analyze/site/{site_id}", response_model=SafetyAnalysisResponse)
def analyze_site_safety(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    """
    Execute the specialized Safety Agent against all active workers at the site.
    Evaluates rules 1-6 (PPE, Training, Unsafe Equipment, High-Risk Activity, Zone Exposure),
    persists new SafetyAnalysis and SafetyFinding records, and dispatches high/critical alerts.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")

    try:
        result = safety_agent.analyze_and_persist(
            db=db,
            site_id=site.id,
            source_label=f"Safety Agent ({current_user.full_name})"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        print(f"[ERROR] Safety analysis failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Safety analysis failed: {str(e)}")


@router.post("/analyze/worker/{worker_id}", response_model=SafetyAnalysisResponse)
def analyze_worker_safety(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    """
    Execute Safety Agent compliance checks for a single worker at their assigned site.
    """
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")
    if not worker.site_id:
        raise HTTPException(status_code=400, detail="Worker is not currently assigned to any active site")

    try:
        result = safety_agent.analyze_and_persist(
            db=db,
            site_id=worker.site_id,
            worker_id=worker.id,
            source_label=f"Safety Agent — Worker Inspection ({current_user.full_name})"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Worker safety analysis failed: {str(e)}")


# ── Safety Summaries & History ──────────────────────────────────────────────

@router.get("/site/{site_id}")
def get_site_safety_summary(
    site_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Retrieve latest safety compliance summary, active findings counts,
    and latest safety analysis for a site.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")

    latest_analysis = db.query(SafetyAnalysis).filter(
        SafetyAnalysis.site_id == site_id
    ).order_by(SafetyAnalysis.created_at.desc()).first()

    open_findings = db.query(SafetyFinding).filter(
        SafetyFinding.site_id == site_id,
        SafetyFinding.status.in_([SafetyFindingStatus.OPEN, SafetyFindingStatus.ACKNOWLEDGED])
    ).all()

    workers_count = db.query(Worker).filter(
        Worker.site_id == site_id,
        Worker.is_active == True
    ).count()

    return {
        "site_id": site.id,
        "site_name": site.name,
        "workers_count": workers_count,
        "latest_analysis": SafetyAnalysisOut.model_validate(latest_analysis) if latest_analysis else None,
        "open_findings_count": len(open_findings),
        "critical_findings_count": sum(1 for f in open_findings if f.severity == RiskCategory.CRITICAL),
        "high_findings_count": sum(1 for f in open_findings if f.severity == RiskCategory.HIGH),
        "detection_source": "RULE_ENGINE",
        "agent_name": safety_agent.name,
        "agent_status": safety_agent.get_status(),
    }


@router.get("/site/{site_id}/findings", response_model=List[SafetyFindingOut])
def get_site_safety_findings(
    site_id: str,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    List safety findings for a site with optional status and severity filtering.
    """
    q = db.query(SafetyFinding).filter(SafetyFinding.site_id == site_id)
    if status:
        q = q.filter(SafetyFinding.status == status)
    if severity:
        q = q.filter(SafetyFinding.severity == severity)
    findings = q.order_by(SafetyFinding.created_at.desc()).all()
    return [_enrich_finding(f, db) for f in findings]


@router.get("/workers/{worker_id}/findings", response_model=List[SafetyFindingOut])
def get_worker_safety_findings(
    worker_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Retrieve all historical safety compliance findings for a specific worker.
    """
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' not found")

    findings = db.query(SafetyFinding).filter(
        SafetyFinding.worker_id == worker_id
    ).order_by(SafetyFinding.created_at.desc()).all()

    return [_enrich_finding(f, db) for f in findings]


@router.get("/analysis/{analysis_id}", response_model=SafetyAnalysisOut)
def get_safety_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Retrieve specific safety analysis run and summary.
    """
    analysis = db.query(SafetyAnalysis).filter(
        (SafetyAnalysis.id == analysis_id) | (SafetyAnalysis.analysis_id == analysis_id)
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Safety analysis record not found")
    return SafetyAnalysisOut.model_validate(analysis)


# ── Finding Lifecycle Actions ───────────────────────────────────────────────

@router.patch("/findings/{finding_id}", response_model=SafetyFindingOut)
def update_safety_finding(
    finding_id: str,
    payload: SafetyFindingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    """
    Update finding lifecycle status (ACKNOWLEDGED, MITIGATED, CLOSED).
    Restricted to authorized roles (Safety Officer, Site Manager, Project Manager, Admin).
    """
    finding = db.query(SafetyFinding).filter(SafetyFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Safety finding not found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if payload.status:
        # Validate transitions
        if finding.status == SafetyFindingStatus.CLOSED and payload.status != SafetyFindingStatus.CLOSED:
            raise HTTPException(status_code=400, detail="Cannot transition closed finding")

        finding.status = payload.status
        if payload.status == SafetyFindingStatus.ACKNOWLEDGED:
            finding.acknowledged_at = now
            finding.acknowledged_by = current_user.id
        elif payload.status == SafetyFindingStatus.MITIGATED:
            finding.mitigated_at = now
            finding.mitigated_by = current_user.id
            if payload.mitigation_notes:
                finding.mitigation_notes = payload.mitigation_notes
        elif payload.status == SafetyFindingStatus.CLOSED:
            if not finding.mitigated_at:
                finding.mitigated_at = now
                finding.mitigated_by = current_user.id

    if payload.mitigation_notes:
        finding.mitigation_notes = payload.mitigation_notes

    finding.updated_at = now
    db.commit()
    db.refresh(finding)
    return _enrich_finding(finding, db)


# ── Demo Scenarios ──────────────────────────────────────────────────────────

@router.get("/demo-scenarios", response_model=List[SafetyDemoScenarioOut])
def list_safety_demo_scenarios(_: User = Depends(get_current_user)):
    """
    List the 5 deterministic worker safety demo scenarios.
    """
    return [
        SafetyDemoScenarioOut(
            id=s_id,
            name=s_data["name"],
            description=s_data["description"],
            expected_level=s_data["expected_level"].value.upper(),
            expected_violations=s_data["expected_violations"],
        )
        for s_id, s_data in SAFETY_DEMO_SCENARIOS.items()
    ]


@router.post("/demo-scenario", response_model=SafetyAnalysisResponse)
def run_safety_demo_scenario(
    payload: SafetyDemoScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    """
    Execute one of the 5 deterministic worker safety demo scenarios.
    Allows reviewers to verify PPE violations, expired certifications,
    unsafe equipment operation, and high-risk activity enforcement.
    """
    if payload.scenario_id not in SAFETY_DEMO_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario ID {payload.scenario_id}. Choose between 1 and 5."
        )

    site = db.query(Site).filter(Site.id == payload.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{payload.site_id}' not found")

    scenario = SAFETY_DEMO_SCENARIOS[payload.scenario_id]
    custom_data = dict(scenario["input"])

    try:
        result = safety_agent.analyze_and_persist(
            db=db,
            site_id=site.id,
            custom_input=custom_data,
            source_label=f"safety_demo_scenario_{payload.scenario_id} ({scenario['name']})"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo scenario execution failed: {str(e)}")
