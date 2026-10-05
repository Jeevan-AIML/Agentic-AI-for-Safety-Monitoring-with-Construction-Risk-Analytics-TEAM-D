from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.models import Site, Project, User, UserRole, RiskScore
from app.schemas.schemas import SiteCreate, SiteUpdate, SiteOut, RiskScoreOut
from app.api.dependencies import get_current_user, require_roles
import uuid
from datetime import datetime

router = APIRouter(prefix="/sites", tags=["Sites"])

WRITE_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER, UserRole.SAFETY_OFFICER, UserRole.VIEWER]


def _enrich_site(s: Site, db: Session) -> SiteOut:
    project_name = None
    if s.project_id:
        proj = db.query(Project).filter(Project.id == s.project_id).first()
        project_name = proj.name if proj else None
    manager_name = None
    if s.manager_id:
        mgr = db.query(User).filter(User.id == s.manager_id).first()
        manager_name = mgr.full_name if mgr else None
    d = SiteOut.model_validate(s)
    d.project_name = project_name
    d.manager_name = manager_name
    return d


@router.get("", response_model=List[SiteOut])
def list_sites(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Site)
    if project_id:
        q = q.filter(Site.project_id == project_id)
    if status:
        q = q.filter(Site.status == status)
    # Site managers only see their assigned site
    if current_user.role == UserRole.SITE_MANAGER and current_user.assigned_site_id:
        q = q.filter(Site.id == current_user.assigned_site_id)
    sites = q.order_by(Site.created_at.desc()).all()
    return [_enrich_site(s, db) for s in sites]


@router.post("", response_model=SiteOut, status_code=201)
def create_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    existing = db.query(Site).filter(Site.site_id == payload.site_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site ID already exists")
    site_data = payload.model_dump()
    if not site_data.get("project_id"):
        site_data["project_id"] = None
    if not site_data.get("manager_id"):
        site_data["manager_id"] = None
    if not site_data.get("site_type"):
        site_data["site_type"] = None
    site = Site(id=str(uuid.uuid4()), **site_data)
    db.add(site)
    db.commit()
    db.refresh(site)
    return _enrich_site(site, db)


@router.get("/{site_id}", response_model=SiteOut)
def get_site(
    site_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    s = db.query(Site).filter(Site.id == site_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Site not found")
    return _enrich_site(s, db)


@router.put("/{site_id}", response_model=SiteOut)
def update_site(
    site_id: str,
    payload: SiteUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    s = db.query(Site).filter(Site.id == site_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Site not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    s.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return _enrich_site(s, db)


@router.delete("/{site_id}")
def delete_site(
    site_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER)),
):
    s = db.query(Site).filter(Site.id == site_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Site not found")
    db.delete(s)
    db.commit()
    return {"message": "Site deleted"}


@router.get("/{site_id}/risk-history", response_model=List[RiskScoreOut])
def get_site_risk_history(
    site_id: str,
    limit: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    s = db.query(Site).filter(Site.id == site_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Site not found")
    scores = (
        db.query(RiskScore)
        .filter(RiskScore.site_id == site_id)
        .order_by(RiskScore.recorded_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for sc in scores:
        d = RiskScoreOut.model_validate(sc)
        d.site_name = s.name
        results.append(d)
    return results
