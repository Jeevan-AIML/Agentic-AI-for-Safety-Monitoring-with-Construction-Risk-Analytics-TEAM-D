"""
PPE Compliance Detection API Endpoints.
Milestone 2 - Phase 2.2: Computer Vision PPE Compliance Detection.
"""

from typing import List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.core.config import settings
from app.models.models import User, UserRole, PPEAnalysis
from app.schemas.schemas import (
    PPEAnalysisOut,
    PPEDemoScenarioOut,
)
from app.services.cv.ppe_service import ppe_detection_service
from app.services.cv.mock_detector import PPE_DEMO_SCENARIOS

router = APIRouter(prefix="/safety/ppe", tags=["safety-ppe"])


@router.post("/analyze", response_model=PPEAnalysisOut)
async def analyze_ppe_image(
    file: UploadFile = File(...),
    site_id: str = Form(...),
    worker_id: Optional[str] = Form(None),
    is_high_risk: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PROJECT_MANAGER,
            UserRole.SITE_MANAGER,
            UserRole.SAFETY_OFFICER,
        )
    ),
):
    """
    Upload and analyze a construction site image for PPE compliance using Computer Vision.
    Accessible to Safety Officers, Site Managers, Project Managers, and Admins.
    """
    try:
        file_bytes = await file.read()
        saved_path, url_path, _, _ = ppe_detection_service.validate_and_save_upload(
            file_bytes=file_bytes,
            original_filename=file.filename or "upload.jpg",
        )
        analysis_result = ppe_detection_service.analyze_image_ppe(
            db=db,
            image_path=saved_path,
            image_url=url_path,
            site_id=site_id,
            worker_id=worker_id,
            is_high_risk=is_high_risk,
            user_id=current_user.id,
        )
        return analysis_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PPE analysis failed: {str(e)}",
        )


@router.get("/analysis/{analysis_id}", response_model=PPEAnalysisOut)
def get_ppe_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific PPE analysis result by ID.
    Accessible to all authenticated users (including Viewer).
    """
    analysis = db.query(PPEAnalysis).filter(PPEAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PPE analysis with ID '{analysis_id}' not found.",
        )
    return analysis


@router.get("/site/{site_id}", response_model=List[PPEAnalysisOut])
def get_site_ppe_analyses(
    site_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all PPE analyses recorded for a specific construction site.
    Accessible to all authenticated users.
    """
    analyses = (
        db.query(PPEAnalysis)
        .filter(PPEAnalysis.site_id == site_id)
        .order_by(PPEAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )
    return analyses


@router.get("/worker/{worker_id}", response_model=List[PPEAnalysisOut])
def get_worker_ppe_analyses(
    worker_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List PPE analyses associated with a specific worker.
    Accessible to all authenticated users.
    """
    analyses = (
        db.query(PPEAnalysis)
        .filter(PPEAnalysis.worker_id == worker_id)
        .order_by(PPEAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )
    return analyses


@router.get("/image/{filename}")
def get_ppe_image(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """
    Safely serve stored PPE analysis images.
    Prevents path traversal and verifies authenticated session.
    """
    clean_filename = os.path.basename(filename)
    file_path = os.path.join(settings.PPE_UPLOAD_DIR, clean_filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    ext = os.path.splitext(clean_filename)[1].lower()
    media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
    return FileResponse(file_path, media_type=media_type)


@router.get("/demo-scenarios", response_model=List[PPEDemoScenarioOut])
def list_demo_scenarios(
    current_user: User = Depends(get_current_user),
):
    """
    List predefined Phase 2.2 deterministic demo scenarios.
    All 5 required demonstration fixtures for testing and evaluation.
    """
    scenarios = [
        PPEDemoScenarioOut(
            id=v["id"],
            name=v["name"],
            description=v["description"],
            expected_compliance=v["expected_compliance"],
            expected_findings_count=v["expected_findings_count"],
            detected_items=v["detected_items"],
            missing_items=v["missing_items"],
        )
        for k, v in PPE_DEMO_SCENARIOS.items()
    ]
    return scenarios


@router.post("/demo-scenario", response_model=PPEAnalysisOut)
def execute_demo_scenario(
    scenario_id: int = Query(..., ge=1, le=5, description="ID of demo scenario (1 to 5)"),
    site_id: Optional[str] = Query(None, description="Site ID to associate demo run with"),
    worker_id: Optional[str] = Query(None, description="Optional worker ID"),
    is_high_risk: bool = Query(False, description="Whether activity is high risk"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PROJECT_MANAGER,
            UserRole.SITE_MANAGER,
            UserRole.SAFETY_OFFICER,
        )
    ),
):
    """
    Execute one of the 5 predefined deterministic PPE demo scenarios.
    Explicitly labeled as 'DEMO / MOCK' per user mandate.
    """
    try:
        analysis = ppe_detection_service.run_demo_scenario(
            db=db,
            scenario_id=scenario_id,
            site_id=site_id,
            worker_id=worker_id,
            user_id=current_user.id,
        )
        return analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo execution failed: {str(e)}",
        )
