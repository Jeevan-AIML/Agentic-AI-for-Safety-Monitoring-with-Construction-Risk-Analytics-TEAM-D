"""
PPE Detection Service
=====================
Orchestrates Computer Vision PPE detection, file validation, compliance logic,
confidence thresholding, worker cross-verification, and SafetyAgent finding dispatch.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
from sqlalchemy.orm import Session

from app.models.models import (
    Site, Worker, User, SafetyFinding, SafetyAnalysis,
    PPEComplianceStatus, PPEStatus, RiskCategory, SafetyFindingStatus,
    SafetyFindingType, Notification, NotificationCategory, PPEAnalysis
)
from app.core.config import settings
from app.services.cv.base_detector import (
    BasePPEDetector, DetectorOutput, PersonDetection, RawPPEDetection, BoundingBox
)
from app.services.cv.cv_detector import ComputerVisionPPEDetector
from app.services.cv.mock_detector import MockPPEDetector


# 5 Deterministic PPE Demo Scenarios
PPE_DEMO_SCENARIOS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Scenario 1 — Fully Compliant Worker",
        "description": "Worker wearing certified Hard Hat, High-Visibility Vest, and Safety Goggles. Full compliance verified by Computer Vision.",
        "expected_compliance": PPEComplianceStatus.COMPLIANT,
        "expected_findings_count": 0,
        "detected_items": ["HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"],
        "missing_items": [],
    },
    2: {
        "id": 2,
        "name": "Scenario 2 — Missing Hard Hat",
        "description": "Worker wearing Safety Vest and Goggles, but Hard Hat is absent in active construction zone.",
        "expected_compliance": PPEComplianceStatus.NON_COMPLIANT,
        "expected_findings_count": 1,
        "detected_items": ["SAFETY_VEST", "SAFETY_GOGGLES"],
        "missing_items": ["HARD_HAT"],
    },
    3: {
        "id": 3,
        "name": "Scenario 3 — Multiple PPE Violations",
        "description": "Worker with multiple critical PPE deficiencies (Missing Hard Hat and Missing Goggles) during active construction activity.",
        "expected_compliance": PPEComplianceStatus.NON_COMPLIANT,
        "expected_findings_count": 2,
        "detected_items": ["SAFETY_VEST"],
        "missing_items": ["HARD_HAT", "SAFETY_GOGGLES"],
    },
    4: {
        "id": 4,
        "name": "Scenario 4 — Low Confidence Detection",
        "description": "Obscured camera angle or low lighting causing optical detection confidence to fall below threshold (0.65). Marked as UNCERTAIN.",
        "expected_compliance": PPEComplianceStatus.UNCERTAIN,
        "expected_findings_count": 1,
        "detected_items": ["HARD_HAT (LOW_CONFIDENCE)", "SAFETY_VEST (LOW_CONFIDENCE)"],
        "missing_items": [],
    },
    5: {
        "id": 5,
        "name": "Scenario 5 — Database vs CV Discrepancy",
        "description": "Worker recorded as COMPLIANT in safety registry, but Computer Vision analysis reveals missing Hard Hat on active site.",
        "expected_compliance": PPEComplianceStatus.NON_COMPLIANT,
        "expected_findings_count": 2,
        "detected_items": ["SAFETY_VEST"],
        "missing_items": ["HARD_HAT"],
    },
}


class PPEDetectionService:
    """
    Service coordinating Computer Vision PPE detection pipelines,
    compliance verification, and SafetyAgent finding generation.
    """

    def __init__(self, detector: Optional[BasePPEDetector] = None):
        self.detector = detector or ComputerVisionPPEDetector()
        self.upload_dir = os.path.abspath(settings.PPE_UPLOAD_DIR)
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_image(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Helper method to validate file upload without saving.
        Returns (is_valid, error_message).
        """
        try:
            if not file_bytes or len(file_bytes) == 0:
                return False, "Uploaded file is empty (0 bytes)."

            max_bytes = settings.PPE_MAX_FILE_SIZE_MB * 1024 * 1024
            if len(file_bytes) > max_bytes:
                return False, f"File size exceeds maximum allowed limit of {settings.PPE_MAX_FILE_SIZE_MB} MB."

            ext = os.path.splitext(filename)[1].lower().lstrip(".")
            if ext not in settings.allowed_ppe_extensions_list:
                return False, f"Invalid file extension '.{ext}'. Allowed formats: {', '.join(settings.allowed_ppe_extensions_list)}."

            import io
            try:
                pil_img = Image.open(io.BytesIO(file_bytes))
                pil_img.verify()
                pil_img = Image.open(io.BytesIO(file_bytes))
                fmt = (pil_img.format or "").lower()
                if fmt not in ["jpeg", "png", "jpg"]:
                    return False, f"Unsupported format {fmt}. Must be JPEG or PNG."
            except Exception as e:
                return False, f"Corrupted or invalid image file: {str(e)}"

            return True, None
        except Exception as ex:
            return False, str(ex)

    def evaluate_compliance(
        self,
        detections: List[RawPPEDetection],
        required_classes: List[str],
        confidence_threshold: float = 0.65
    ) -> Tuple[PPEComplianceStatus, List[str], List[str]]:
        """
        Deterministic PPE compliance evaluator.
        Returns (status, missing_classes, uncertain_classes).
        """
        detected_high_conf = set()
        uncertain_classes = []

        for d in detections:
            if d.confidence >= confidence_threshold:
                detected_high_conf.add(d.ppe_class)
            else:
                uncertain_classes.append(d.ppe_class)

        missing_classes = [req for req in required_classes if req not in detected_high_conf and req not in uncertain_classes]

        if missing_classes:
            return PPEComplianceStatus.NON_COMPLIANT, missing_classes, uncertain_classes
        elif uncertain_classes:
            return PPEComplianceStatus.UNCERTAIN, missing_classes, uncertain_classes
        else:
            return PPEComplianceStatus.COMPLIANT, missing_classes, uncertain_classes

    def validate_and_save_upload(
        self,
        file_bytes: bytes,
        original_filename: str
    ) -> Tuple[str, str, int, int]:
        """
        Validate image buffer and persist to safe storage.
        Returns (saved_filepath, public_url_path, width, height).
        """
        # 1. Empty file validation
        if not file_bytes or len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty (0 bytes). Please upload a valid image.")

        # 2. File size limit
        max_bytes = settings.PPE_MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValueError(
                f"File size ({len(file_bytes) / (1024*1024):.1f} MB) exceeds maximum allowed limit "
                f"of {settings.PPE_MAX_FILE_SIZE_MB} MB."
            )

        # 3. Extension check
        ext = os.path.splitext(original_filename)[1].lower().lstrip(".")
        allowed = settings.allowed_ppe_extensions_list
        if ext not in allowed:
            raise ValueError(
                f"Invalid file extension '.{ext}'. Allowed formats: {', '.join(allowed)}."
            )

        # 4. Content verification using PIL to prevent code execution or corrupt buffers
        import io
        try:
            pil_img = Image.open(io.BytesIO(file_bytes))
            pil_img.verify()  # Verify image integrity
            # Reopen to read dimensions (verify() closes buffer state in PIL)
            pil_img = Image.open(io.BytesIO(file_bytes))
            width, height = pil_img.size
            img_format = (pil_img.format or "").lower()
            if img_format not in ["jpeg", "png", "jpg"]:
                raise ValueError(f"Unsupported image format: {img_format}. Must be JPEG or PNG.")
        except Exception as e:
            raise ValueError(f"Corrupt or invalid image file: {str(e)}")

        # 5. Save with UUID-based filename (prevent path traversal)
        safe_filename = f"ppe_{uuid.uuid4().hex}.{ext}"
        saved_path = os.path.join(self.upload_dir, safe_filename)
        with open(saved_path, "wb") as f:
            f.write(file_bytes)

        url_path = f"/api/v1/safety/ppe/image/{safe_filename}"
        return saved_path, url_path, width, height

    def analyze_image_ppe(
        self,
        db: Session,
        image_path: str,
        image_url: str,
        site_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        is_high_risk: bool = False,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute full Computer Vision PPE compliance analysis on an image:
        1. Run CV detector (HOG / Haar / Spectral)
        2. Evaluate person compliance
        3. Cross-verify with database record if worker_id provided
        4. Integrate findings with SafetyAgent
        5. Persist PPEAnalysis & SafetyFinding entities
        """
        now = datetime.now(timezone.utc)
        ctx = dict(context or {})
        if worker_id:
            worker = db.query(Worker).filter(Worker.id == worker_id).first()
            if worker:
                ctx["worker_id"] = worker.id
                ctx["worker_name"] = worker.name
                if not site_id:
                    site_id = worker.site_id

        site = db.query(Site).filter(Site.id == site_id).first() if site_id else None

        # Execute CV Detector
        det_output: DetectorOutput = self.detector.detect(image_path, context=ctx)

        # Evaluate compliance across all detected persons
        conf_thresh = float(settings.PPE_CONFIDENCE_THRESHOLD)
        total_persons = len(det_output.persons)
        all_missing_ppe: List[str] = []
        has_low_confidence = False
        all_detections_clean: List[Dict[str, Any]] = []

        for d in det_output.detections:
            d_dict = d.to_dict()
            all_detections_clean.append(d_dict)
            if d.status == "LOW_CONFIDENCE":
                has_low_confidence = True

        for p in det_output.persons:
            for m in p.missing_ppe:
                if m not in all_missing_ppe:
                    all_missing_ppe.append(m)

        # Determine overall compliance state
        if all_missing_ppe:
            overall_compliance = PPEComplianceStatus.NON_COMPLIANT
        elif has_low_confidence:
            overall_compliance = PPEComplianceStatus.UNCERTAIN
        else:
            overall_compliance = PPEComplianceStatus.COMPLIANT

        # Compliance score calculation (0 - 100)
        # Deduct 30 for missing hard hat, 30 for missing vest, 20 for missing goggles, 15 for low confidence
        deductions = 0.0
        if "HARD_HAT" in all_missing_ppe:
            deductions += 35.0
        if "SAFETY_VEST" in all_missing_ppe:
            deductions += 35.0
        if "SAFETY_GOGGLES" in all_missing_ppe:
            deductions += 20.0
        if has_low_confidence:
            deductions += 15.0

        compliance_score = max(0.0, min(100.0, round(100.0 - deductions, 1)))

        # ── Cross-Verification with Database Worker Record ───────────────────
        cross_ver_data: Optional[Dict[str, Any]] = None
        has_discrepancy = False

        if worker_id:
            worker = db.query(Worker).filter(Worker.id == worker_id).first()
            if worker:
                db_status = worker.ppe_status.value if hasattr(worker.ppe_status, "value") else str(worker.ppe_status)
                # Discrepancy: Database says COMPLIANT or PARTIAL, but CV detects missing critical PPE
                if db_status in ["compliant", "partial"] and overall_compliance == PPEComplianceStatus.NON_COMPLIANT:
                    has_discrepancy = True
                    discrepancy_msg = (
                        f"PPE status discrepancy: Worker {worker.name} ({worker.worker_id}) is marked '{db_status.upper()}' "
                        f"in registry, but Computer Vision analysis detected missing PPE ({', '.join(all_missing_ppe)})."
                    )
                else:
                    discrepancy_msg = f"Computer Vision detection aligns with database PPE record ({db_status})."

                cross_ver_data = {
                    "worker_id": worker.id,
                    "worker_name": worker.name,
                    "db_ppe_status": db_status,
                    "cv_compliance": overall_compliance,
                    "has_discrepancy": has_discrepancy,
                    "discrepancy_details": discrepancy_msg,
                }

        # ── Generate Safety Findings & Recommendations ───────────────────────
        created_findings: List[SafetyFinding] = []
        recommendations: List[str] = []
        base_fnd_count = db.query(SafetyFinding).count()

        # Generate specific findings for missing PPE
        if "HARD_HAT" in all_missing_ppe:
            f_code = f"SAF-CV-{base_fnd_count + len(created_findings) + 1:04d}"
            rec = "Require the worker to wear an approved hard hat before entering the active construction zone."
            recommendations.append(rec)
            sev = RiskCategory.CRITICAL if (is_high_risk or len(all_missing_ppe) > 1) else RiskCategory.HIGH
            fnd = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f_code,
                site_id=site.id if site else (worker.site_id if worker else "general-site"),
                worker_id=worker_id,
                finding_type=SafetyFindingType.PPE_VIOLATION,
                description=f"Computer Vision detected missing Hard Hat{' for ' + worker.name if worker_id and worker else ''}",
                evidence=f"Computer Vision ({det_output.model_name}) analyzed image and confirmed absence of industrial safety helmet.",
                severity=sev,
                status=SafetyFindingStatus.OPEN,
                recommendation=rec,
                detection_source=det_output.detection_source,
                created_at=now,
                updated_at=now,
            )
            db.add(fnd)
            created_findings.append(fnd)

        if "SAFETY_VEST" in all_missing_ppe:
            f_code = f"SAF-CV-{base_fnd_count + len(created_findings) + 1:04d}"
            rec = "Require high-visibility safety vest before continuing site activity."
            recommendations.append(rec)
            sev = RiskCategory.CRITICAL if (is_high_risk or len(all_missing_ppe) > 1) else RiskCategory.HIGH
            fnd = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f_code,
                site_id=site.id if site else (worker.site_id if worker else "general-site"),
                worker_id=worker_id,
                finding_type=SafetyFindingType.PPE_VIOLATION,
                description=f"Computer Vision detected missing Safety Vest{' for ' + worker.name if worker_id and worker else ''}",
                evidence=f"Computer Vision ({det_output.model_name}) confirmed lack of high-visibility safety vest in torso region.",
                severity=sev,
                status=SafetyFindingStatus.OPEN,
                recommendation=rec,
                detection_source=det_output.detection_source,
                created_at=now,
                updated_at=now,
            )
            db.add(fnd)
            created_findings.append(fnd)

        if "SAFETY_GOGGLES" in all_missing_ppe:
            f_code = f"SAF-CV-{base_fnd_count + len(created_findings) + 1:04d}"
            rec = "Provide eye protection / certified safety goggles prior to hazardous optical or particulate tasks."
            recommendations.append(rec)
            sev = RiskCategory.HIGH if is_high_risk else RiskCategory.MEDIUM
            fnd = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f_code,
                site_id=site.id if site else (worker.site_id if worker else "general-site"),
                worker_id=worker_id,
                finding_type=SafetyFindingType.PPE_VIOLATION,
                description=f"Computer Vision detected missing Safety Goggles{' for ' + worker.name if worker_id and worker else ''}",
                evidence=f"Computer Vision ({det_output.model_name}) confirmed absence of eye protection.",
                severity=sev,
                status=SafetyFindingStatus.OPEN,
                recommendation=rec,
                detection_source=det_output.detection_source,
                created_at=now,
                updated_at=now,
            )
            db.add(fnd)
            created_findings.append(fnd)

        # Cross-verification discrepancy finding
        if has_discrepancy:
            f_code = f"SAF-CV-{base_fnd_count + len(created_findings) + 1:04d}"
            rec = "Conduct an on-site physical inspection to reconcile physical PPE compliance with worker registration records."
            recommendations.append(rec)
            fnd = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f_code,
                site_id=site.id if site else (worker.site_id if worker else "general-site"),
                worker_id=worker_id,
                finding_type=SafetyFindingType.PPE_DISCREPANCY,
                description=f"PPE compliance discrepancy detected between database record and Computer Vision analysis ({worker.name if worker else ''})",
                evidence=cross_ver_data["discrepancy_details"],
                severity=RiskCategory.HIGH,
                status=SafetyFindingStatus.OPEN,
                recommendation=rec,
                detection_source="CROSS_VERIFICATION",
                created_at=now,
                updated_at=now,
            )
            db.add(fnd)
            created_findings.append(fnd)

        # Low confidence warning finding
        if has_low_confidence and not all_missing_ppe:
            f_code = f"SAF-CV-{base_fnd_count + len(created_findings) + 1:04d}"
            rec = "Request a clearer high-resolution photo or secondary inspection angle due to low optical detection confidence."
            recommendations.append(rec)
            fnd = SafetyFinding(
                id=str(uuid.uuid4()),
                finding_id=f_code,
                site_id=site.id if site else (worker.site_id if worker else "general-site"),
                worker_id=worker_id,
                finding_type=SafetyFindingType.PPE_VIOLATION,
                description="Low confidence optical PPE detection requiring secondary visual inspection",
                evidence=f"Computer Vision detection score below confidence threshold ({conf_thresh}). Classification uncertain.",
                severity=RiskCategory.LOW,
                status=SafetyFindingStatus.OPEN,
                recommendation=rec,
                detection_source=det_output.detection_source,
                created_at=now,
                updated_at=now,
            )
            db.add(fnd)
            created_findings.append(fnd)

        # Multiple PPE violations recommendation
        if len(all_missing_ppe) >= 2:
            recommendations.insert(0, "Stop the worker from entering the active work zone until all required PPE is correctly worn.")

        # Notifications dispatch for HIGH/CRITICAL findings with deduplication
        for f in created_findings:
            if f.severity in [RiskCategory.HIGH, RiskCategory.CRITICAL]:
                sev_level = "critical" if f.severity == RiskCategory.CRITICAL else "warning"
                target_site_name = site.name if site else "Construction Site"
                notif_title = f"{'CRITICAL' if sev_level == 'critical' else 'HIGH'} PPE Alert: {f.description[:50]}"
                existing = db.query(Notification).filter(
                    Notification.category == NotificationCategory.SAFETY,
                    Notification.title == notif_title,
                    Notification.is_read == False
                ).first()
                if not existing:
                    db.add(Notification(
                        id=str(uuid.uuid4()),
                        user_id=None,
                        category=NotificationCategory.SAFETY,
                        title=notif_title,
                        message=f"CV PPE Detection at {target_site_name}: {f.description}. Recommendation: {f.recommendation}",
                        severity=sev_level,
                        is_read=False,
                        link=f"/safety",
                        created_at=now,
                    ))

        # ── Persist PPEAnalysis Record ───────────────────────────────────────
        analysis_count = db.query(PPEAnalysis).count()
        analysis_code = f"PPE-ANL-{analysis_count + 1:04d}"

        detected_ppe_clean = [d.to_dict() for d in det_output.detections]
        persons_clean = [p.to_dict() for p in det_output.persons]

        summary_data = {
            "total_persons_detected": total_persons,
            "detected_ppe_count": len(detected_ppe_clean),
            "missing_ppe": all_missing_ppe,
            "overall_compliance": overall_compliance.value,
            "compliance_score": compliance_score,
            "confidence_threshold": conf_thresh,
            "model_name": det_output.model_name,
            "detection_source": det_output.detection_source,
            "recommendations": recommendations,
        }

        ppe_analysis_entity = PPEAnalysis(
            id=str(uuid.uuid4()),
            analysis_id=analysis_code,
            site_id=site.id if site else None,
            worker_id=worker_id,
            image_filename=os.path.basename(image_path),
            image_url=image_url,
            image_width=det_output.image_width,
            image_height=det_output.image_height,
            overall_compliance=overall_compliance,
            compliance_score=compliance_score,
            total_persons_detected=total_persons,
            detected_ppe=detected_ppe_clean,
            missing_ppe=all_missing_ppe,
            detections=detected_ppe_clean,
            cross_verification=cross_ver_data,
            confidence_threshold=conf_thresh,
            detection_source=det_output.detection_source,
            model_name=det_output.model_name,
            summary=summary_data,
            created_by=user_id,
            created_at=now,
        )
        db.add(ppe_analysis_entity)
        db.commit()
        db.refresh(ppe_analysis_entity)

        # Format output
        findings_out = []
        for f in created_findings:
            findings_out.append({
                "id": f.id,
                "finding_id": f.finding_id,
                "site_id": f.site_id,
                "worker_id": f.worker_id,
                "worker_name": worker.name if worker_id and worker else None,
                "worker_code": worker.worker_id if worker_id and worker else None,
                "finding_type": f.finding_type,
                "description": f.description,
                "evidence": f.evidence,
                "severity": f.severity,
                "status": f.status,
                "recommendation": f.recommendation,
                "detection_source": f.detection_source,
                "created_at": f.created_at,
                "updated_at": f.updated_at,
            })

        return {
            "id": ppe_analysis_entity.id,
            "analysis_id": ppe_analysis_entity.analysis_id,
            "site_id": site.id if site else None,
            "site_name": site.name if site else None,
            "worker_id": worker_id,
            "worker_name": worker.name if worker_id and worker else None,
            "image_filename": ppe_analysis_entity.image_filename,
            "image_url": ppe_analysis_entity.image_url,
            "image_width": ppe_analysis_entity.image_width,
            "image_height": ppe_analysis_entity.image_height,
            "overall_compliance": overall_compliance,
            "compliance_score": compliance_score,
            "total_persons_detected": total_persons,
            "detected_ppe": detected_ppe_clean,
            "missing_ppe": all_missing_ppe,
            "detections": detected_ppe_clean,
            "persons": persons_clean,
            "cross_verification": cross_ver_data,
            "confidence_threshold": conf_thresh,
            "detection_source": det_output.detection_source,
            "model_name": det_output.model_name,
            "recommendations": recommendations,
            "findings": findings_out,
            "summary": summary_data,
            "created_at": now,
        }

    def run_demo_scenario(
        self,
        db: Session,
        scenario_id: int,
        site_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute one of the 5 deterministic PPE demo scenarios using the MockPPEDetector.
        Ensures consistent, verifiable evaluation for Hackathon demonstrations.
        """
        if scenario_id not in PPE_DEMO_SCENARIOS:
            raise ValueError(f"Invalid demo scenario ID {scenario_id}. Must be between 1 and 5.")

        # Create a sample synthetic demo image in upload directory
        demo_filename = f"demo_scenario_{scenario_id}.png"
        demo_filepath = os.path.join(self.upload_dir, demo_filename)
        if not os.path.exists(demo_filepath):
            img = Image.new("RGB", (800, 600), color=(30, 41, 59))
            img.save(demo_filepath)

        demo_url = f"/api/v1/safety/ppe/image/{demo_filename}"

        # Use MockPPEDetector forced to the requested scenario
        mock_detector = MockPPEDetector(forced_scenario=scenario_id)
        original_detector = self.detector
        try:
            self.detector = mock_detector
            context = {"scenario_id": scenario_id}

            # For scenario 5, ensure worker is associated and marked compliant in DB
            if scenario_id == 5 and not worker_id:
                sample_worker = db.query(Worker).first()
                if sample_worker:
                    worker_id = sample_worker.id
                    sample_worker.ppe_status = PPEStatus.COMPLIANT
                    db.commit()

            result = self.analyze_image_ppe(
                db=db,
                image_path=demo_filepath,
                image_url=demo_url,
                site_id=site_id,
                worker_id=worker_id,
                context=context,
                user_id=user_id,
            )
            return result
        finally:
            self.detector = original_detector


# Global singleton instance
ppe_detection_service = PPEDetectionService()
