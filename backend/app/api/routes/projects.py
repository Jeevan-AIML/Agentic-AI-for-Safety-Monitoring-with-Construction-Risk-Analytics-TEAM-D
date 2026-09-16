from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.models import Project, Site, User, UserRole
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectOut
from app.api.dependencies import get_current_user, require_roles
import uuid
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])

WRITE_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER]


def _enrich_project(p: Project, db: Session) -> ProjectOut:
    manager_name = None
    if p.manager_id:
        mgr = db.query(User).filter(User.id == p.manager_id).first()
        manager_name = mgr.full_name if mgr else None
    site_count = db.query(Site).filter(Site.project_id == p.id).count()
    d = ProjectOut.model_validate(p)
    d.manager_name = manager_name
    d.site_count = site_count
    return d


@router.get("", response_model=List[ProjectOut])
def list_projects(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    if current_user.role == UserRole.PROJECT_MANAGER:
        q = q.filter(Project.manager_id == current_user.id)
    projects = q.order_by(Project.created_at.desc()).all()
    return [_enrich_project(p, db) for p in projects]


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    existing = db.query(Project).filter(Project.project_id == payload.project_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project ID already exists")
    project = Project(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return _enrich_project(project, db)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return _enrich_project(p, db)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return _enrich_project(p, db)


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(p)
    db.commit()
    return {"message": "Project deleted"}
