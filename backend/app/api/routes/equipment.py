from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.models import Equipment, Site, User, UserRole
from app.schemas.schemas import EquipmentCreate, EquipmentUpdate, EquipmentOut
from app.api.dependencies import get_current_user, require_roles
import uuid

router = APIRouter(prefix="/equipment", tags=["Equipment"])

WRITE_ROLES = [UserRole.SUPER_ADMIN, UserRole.PROJECT_MANAGER, UserRole.SITE_MANAGER]


def _enrich(e: Equipment, db: Session) -> EquipmentOut:
    site_name = None
    if e.site_id:
        site = db.query(Site).filter(Site.id == e.site_id).first()
        site_name = site.name if site else None
    d = EquipmentOut.model_validate(e)
    d.site_name = site_name
    return d


@router.get("", response_model=List[EquipmentOut])
def list_equipment(
    site_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Equipment)
    if site_id:
        q = q.filter(Equipment.site_id == site_id)
    elif current_user.role == UserRole.SITE_MANAGER and current_user.assigned_site_id:
        q = q.filter(Equipment.site_id == current_user.assigned_site_id)
    return [_enrich(e, db) for e in q.all()]


@router.post("", response_model=EquipmentOut, status_code=201)
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    existing = db.query(Equipment).filter(Equipment.equipment_id == payload.equipment_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Equipment ID already exists")
    eq = Equipment(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(eq)
    if payload.site_id:
        site = db.query(Site).filter(Site.id == payload.site_id).first()
        if site:
            site.equipment_count = db.query(Equipment).filter(Equipment.site_id == payload.site_id).count() + 1
    db.commit()
    db.refresh(eq)
    return _enrich(eq, db)


@router.get("/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    e = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return _enrich(e, db)


@router.put("/{equipment_id}", response_model=EquipmentOut)
def update_equipment(
    equipment_id: str,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    e = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Equipment not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return _enrich(e, db)


@router.delete("/{equipment_id}")
def delete_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
):
    e = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db.delete(e)
    db.commit()
    return {"message": "Equipment deleted"}
