from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.models import Worker, Site, User, UserRole
from app.schemas.schemas import WorkerCreate, WorkerUpdate, WorkerOut
from app.api.dependencies import get_current_user, require_roles
import uuid

router = APIRouter(prefix="/workers", tags=["Workers"])

WRITE_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER]


def _enrich_worker(w: Worker, db: Session) -> WorkerOut:
    site_name = None
    if w.site_id:
        site = db.query(Site).filter(Site.id == w.site_id).first()
        site_name = site.name if site else None
    d = WorkerOut.model_validate(w)
    d.site_name = site_name
    return d


@router.get("", response_model=List[WorkerOut])
def list_workers(
    site_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Worker)
    if site_id:
        q = q.filter(Worker.site_id == site_id)
    elif current_user.role == UserRole.SITE_MANAGER and current_user.assigned_site_id:
        q = q.filter(Worker.site_id == current_user.assigned_site_id)
    return [_enrich_worker(w, db) for w in q.all()]


@router.post("", response_model=WorkerOut, status_code=201)
def create_worker(
    payload: WorkerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    existing = db.query(Worker).filter(Worker.worker_id == payload.worker_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Worker ID already exists")
    worker = Worker(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(worker)
    # Update site worker count
    if payload.site_id:
        site = db.query(Site).filter(Site.id == payload.site_id).first()
        if site:
            site.worker_count = db.query(Worker).filter(Worker.site_id == payload.site_id).count() + 1
    db.commit()
    db.refresh(worker)
    return _enrich_worker(worker, db)


@router.get("/{worker_id}", response_model=WorkerOut)
def get_worker(worker_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    w = db.query(Worker).filter(Worker.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Worker not found")
    return _enrich_worker(w, db)


@router.put("/{worker_id}", response_model=WorkerOut)
def update_worker(
    worker_id: str,
    payload: WorkerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    w = db.query(Worker).filter(Worker.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Worker not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(w, k, v)
    db.commit()
    db.refresh(w)
    return _enrich_worker(w, db)


@router.delete("/{worker_id}")
def delete_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    w = db.query(Worker).filter(Worker.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Worker not found")
    db.delete(w)
    db.commit()
    return {"message": "Worker deleted"}
