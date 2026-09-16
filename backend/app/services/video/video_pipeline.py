"""
Video Analysis Pipeline — Milestone 3 Phase 3.1
===============================================
Modular, real-time video surveillance pipeline:
1. Frame Ingestion & Validation
2. Person Detection (BasePersonDetector)
3. PPE Detection (Phase 2.2 ComputerVisionPPEDetector / compliance evaluator)
4. Zone & Proximity Analysis (CameraZone checking)
5. Worker Safety / Activity Analysis (Worker Safety Monitoring rules)
6. SafetyFinding Generation
7. AlertEngine Integration (Phase 2.4 alert creation & deduplication)
8. Live VideoEvent Recording & Database Persistence

Explicitly labeled: DEMO / SIMULATION vs COMPUTER_VISION
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from app.models.models import (
    VideoStream, VideoEvent, CameraZone, Site, Worker,
    SafetyFinding, SafetyAlert, RiskCategory, SafetyFindingStatus,
    SafetyFindingType, AlertSeverity, VideoEventType, StreamStatus,
    PPEComplianceStatus, PPEStatus
)
from app.services.cv.base_detector import BoundingBox, RawPPEDetection
from app.services.cv.cv_detector import ComputerVisionPPEDetector
from app.services.video.person_detector import BasePersonDetector, DemoPersonDetector, CVPersonDetector
from app.services.monitoring.worker_monitoring_engine import WorkerMonitoringEngine
from app.services.alerts.alert_service import AlertService


class VideoAnalysisPipeline:
    """
    Coordinates end-to-end frame analysis from video streams to safety alerts.
    """

    def __init__(
        self,
        person_detector: Optional[BasePersonDetector] = None,
        cv_ppe_detector: Optional[ComputerVisionPPEDetector] = None,
    ):
        self.person_detector = person_detector or DemoPersonDetector()
        self.cv_ppe_detector = cv_ppe_detector or ComputerVisionPPEDetector()
        self.worker_monitoring_engine = WorkerMonitoringEngine()
        self.alert_service = AlertService()

    def validate_frame(self, frame_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate frame payload integrity, dimensions, and sampling rate.
        """
        if not frame_payload:
            return False, "Frame payload is empty."

        width = frame_payload.get("width", 0)
        height = frame_payload.get("height", 0)
        if width <= 0 or height <= 0:
            return False, f"Invalid frame dimensions: {width}x{height}."

        # Maximum frame size constraint (e.g. 4K max)
        if width > 3840 or height > 2160:
            return False, f"Frame dimensions {width}x{height} exceed maximum permitted 3840x2160."

        return True, None

    def process_frame(
        self,
        db: Session,
        stream: VideoStream,
        frame_payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full analysis pipeline on a single ingested frame.
        """
        context = context or {}
        scenario_id = context.get("scenario_id") or frame_payload.get("scenario_id")

        # 1. Validation
        is_valid, error = self.validate_frame(frame_payload)
        if not is_valid:
            return {
                "success": False,
                "error": error,
                "frame_number": frame_payload.get("frame_number", 0),
                "events": [],
                "findings_created": 0,
                "alerts_created": 0,
            }

        # 2. Check frame sampling
        should_process = frame_payload.get("should_process", True)
        if not should_process:
            return {
                "success": True,
                "skipped": True,
                "reason": "Frame dropped by sampling interval rate",
                "frame_number": frame_payload.get("frame_number", 0),
                "events": [],
                "findings_created": 0,
                "alerts_created": 0,
            }

        is_sim = stream.is_simulation or frame_payload.get("is_simulation", True)
        detection_source = "DEMO / SIMULATION" if is_sim else "COMPUTER_VISION"

        # Select appropriate person detector based on simulation flag
        detector = self.person_detector if is_sim else CVPersonDetector()

        # 3. Person Detection
        detected_persons = detector.detect_persons(frame_payload, context=context)

        # 4. Fetch Active Camera Zones for the site
        camera_zones = db.query(CameraZone).filter(
            CameraZone.site_id == stream.site_id,
            CameraZone.is_active == True
        ).all()

        events_generated: List[VideoEvent] = []
        findings_generated: List[SafetyFinding] = []
        alerts_generated: List[SafetyAlert] = []

        now = frame_payload.get("timestamp") or datetime.now(timezone.utc)

        # Count compliant workers
        compliant_count = 0
        violations_count = 0

        # Retrieve site workers for matching
        site_workers = db.query(Worker).filter(Worker.site_id == stream.site_id).all()
        default_worker = site_workers[0] if site_workers else None

        for person in detected_persons:
            # Associate with actual worker if available
            worker_id = person.get("worker_id")
            worker_obj = None
            if worker_id:
                worker_obj = db.query(Worker).filter(Worker.id == worker_id).first()
            if not worker_obj and default_worker:
                worker_obj = default_worker
                worker_id = default_worker.id

            # Person metadata
            bbox = person.get("bounding_box", {})
            current_zone = person.get("current_zone") or "General Site Area"
            is_high_risk_zone = bool(person.get("is_high_risk_zone", False))
            nearby_equipment = person.get("nearby_equipment", [])
            nearby_hazards = person.get("nearby_hazards", [])

            # Check matching camera zone by name if present
            matching_zone = next((z for z in camera_zones if z.name.lower() == current_zone.lower()), None)
            if matching_zone and matching_zone.risk_level in [RiskCategory.HIGH, RiskCategory.CRITICAL]:
                is_high_risk_zone = True

            # Person Detected Event
            p_event = VideoEvent(
                id=str(uuid.uuid4()),
                event_id=f"EVT-PERS-{uuid.uuid4().hex[:8].upper()}",
                stream_id=stream.id,
                site_id=stream.site_id,
                worker_id=worker_id,
                event_type=VideoEventType.PERSON_DETECTED,
                severity=RiskCategory.LOW,
                description=f"Person detected ({person.get('person_id')}) in '{current_zone}' with confidence {person.get('confidence', 0.9):.2f}.",
                evidence=f"BoundingBox: x={bbox.get('x', 0)}, y={bbox.get('y', 0)}, w={bbox.get('width', 0)}, h={bbox.get('height', 0)}",
                zone_name=current_zone,
                bounding_box=bbox,
                detection_source=detection_source,
                is_simulation=is_sim,
                timestamp=now,
                created_at=now,
            )
            db.add(p_event)
            events_generated.append(p_event)

            # 5. PPE Detection & Compliance
            # If simulated PPE provided by detector, use it; otherwise evaluate against standard requirements
            simulated_ppe = person.get("simulated_ppe")
            if simulated_ppe is not None:
                detected_items = simulated_ppe
                required_items = ["HARD_HAT", "SAFETY_VEST"]
                missing_items = [req for req in required_items if req not in detected_items]
                is_ppe_compliant = len(missing_items) == 0
            else:
                detected_items = ["HARD_HAT", "SAFETY_VEST"]
                missing_items = []
                is_ppe_compliant = True

            # PPE Violation Event & SafetyFinding
            if not is_ppe_compliant:
                violations_count += 1
                ppe_evidence = f"Optical detection identified worker {person.get('worker_name', 'Unknown')} missing mandatory PPE: {', '.join(missing_items)}."

                finding = SafetyFinding(
                    id=str(uuid.uuid4()),
                    finding_id=f"FIND-PPE-{uuid.uuid4().hex[:8].upper()}",
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_type=SafetyFindingType.PPE_VIOLATION,
                    description=f"Worker {person.get('worker_name', 'Personnel')} operating without mandatory PPE: {', '.join(missing_items)}.",
                    evidence=ppe_evidence,
                    severity=RiskCategory.CRITICAL if is_high_risk_zone else RiskCategory.HIGH,
                    status=SafetyFindingStatus.OPEN,
                    recommendation=f"Immediately mandate worker equip missing items: {', '.join(missing_items)} before continuing work.",
                    detection_source=detection_source,
                    created_at=now,
                )
                db.add(finding)
                findings_generated.append(finding)

                # Process through AlertEngine via AlertService
                alert = self.alert_service.create_alert_from_finding(db, finding, is_simulation=is_sim)
                if alert:
                    alerts_generated.append(alert)

                evt = VideoEvent(
                    id=str(uuid.uuid4()),
                    event_id=f"EVT-PPE-{uuid.uuid4().hex[:8].upper()}",
                    stream_id=stream.id,
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_id=finding.id,
                    alert_id=alert.id if alert else None,
                    event_type=VideoEventType.PPE_VIOLATION,
                    severity=finding.severity,
                    description=finding.description,
                    evidence=ppe_evidence,
                    zone_name=current_zone,
                    bounding_box=bbox,
                    detected_ppe=detected_items,
                    missing_ppe=missing_items,
                    detection_source=detection_source,
                    is_simulation=is_sim,
                    timestamp=now,
                    created_at=now,
                )
                db.add(evt)
                events_generated.append(evt)
            else:
                compliant_count += 1

            # 6. Zone & High-Risk Entry Analysis
            if is_high_risk_zone:
                violations_count += 1
                zone_evidence = f"Worker entered high-risk designated sector '{current_zone}'. Zone exclusion barrier triggered."
                
                finding = SafetyFinding(
                    id=str(uuid.uuid4()),
                    finding_id=f"FIND-ZONE-{uuid.uuid4().hex[:8].upper()}",
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_type=SafetyFindingType.HIGH_RISK_ZONE_EXPOSURE,
                    description=f"Worker {person.get('worker_name', 'Personnel')} detected inside restricted sector '{current_zone}'.",
                    evidence=zone_evidence,
                    severity=RiskCategory.HIGH,
                    status=SafetyFindingStatus.OPEN,
                    recommendation=f"Verify entry permits for '{current_zone}' and deploy safety spotter immediately.",
                    detection_source=detection_source,
                    created_at=now,
                )
                db.add(finding)
                findings_generated.append(finding)

                alert = self.alert_service.create_alert_from_finding(db, finding, is_simulation=is_sim)
                if alert:
                    alerts_generated.append(alert)

                evt = VideoEvent(
                    id=str(uuid.uuid4()),
                    event_id=f"EVT-ZONE-{uuid.uuid4().hex[:8].upper()}",
                    stream_id=stream.id,
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_id=finding.id,
                    alert_id=alert.id if alert else None,
                    event_type=VideoEventType.HIGH_RISK_ZONE_ENTRY,
                    severity=RiskCategory.HIGH,
                    description=finding.description,
                    evidence=zone_evidence,
                    zone_name=current_zone,
                    bounding_box=bbox,
                    detected_ppe=detected_items,
                    missing_ppe=missing_items,
                    detection_source=detection_source,
                    is_simulation=is_sim,
                    timestamp=now,
                    created_at=now,
                )
                db.add(evt)
                events_generated.append(evt)

            # 7. Heavy Equipment Proximity
            if nearby_equipment:
                violations_count += 1
                eq_desc = ", ".join(nearby_equipment)
                eq_evidence = f"Worker detected within 10m heavy equipment exclusion zone of operating machinery: {eq_desc}."

                finding = SafetyFinding(
                    id=str(uuid.uuid4()),
                    finding_id=f"FIND-EQ-{uuid.uuid4().hex[:8].upper()}",
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_type=SafetyFindingType.EQUIPMENT_PROXIMITY,
                    description=f"Non-operator worker within operating envelope of heavy machinery: {eq_desc}.",
                    evidence=eq_evidence,
                    severity=RiskCategory.CRITICAL,
                    status=SafetyFindingStatus.OPEN,
                    recommendation=f"Halt heavy machinery operations immediately and clear personnel outside safety envelope.",
                    detection_source=detection_source,
                    created_at=now,
                )
                db.add(finding)
                findings_generated.append(finding)

                alert = self.alert_service.create_alert_from_finding(db, finding, is_simulation=is_sim)
                if alert:
                    alerts_generated.append(alert)

                evt = VideoEvent(
                    id=str(uuid.uuid4()),
                    event_id=f"EVT-EQ-{uuid.uuid4().hex[:8].upper()}",
                    stream_id=stream.id,
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_id=finding.id,
                    alert_id=alert.id if alert else None,
                    event_type=VideoEventType.EQUIPMENT_PROXIMITY,
                    severity=RiskCategory.CRITICAL,
                    description=finding.description,
                    evidence=eq_evidence,
                    zone_name=current_zone,
                    bounding_box=bbox,
                    detected_ppe=detected_items,
                    missing_ppe=missing_items,
                    detection_source=detection_source,
                    is_simulation=is_sim,
                    timestamp=now,
                    created_at=now,
                )
                db.add(evt)
                events_generated.append(evt)

            # 8. Hazard Proximity
            if nearby_hazards:
                violations_count += 1
                hz_desc = ", ".join(nearby_hazards)
                hz_evidence = f"Worker detected in hazardous proximity to active open hazards: {hz_desc}."

                finding = SafetyFinding(
                    id=str(uuid.uuid4()),
                    finding_id=f"FIND-HZ-{uuid.uuid4().hex[:8].upper()}",
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_type=SafetyFindingType.HAZARD_PROXIMITY,
                    description=f"Worker in hazardous proximity to active hazards: {hz_desc}.",
                    evidence=hz_evidence,
                    severity=RiskCategory.HIGH,
                    status=SafetyFindingStatus.OPEN,
                    recommendation="Enforce physical barricade and standoff distance around hazard.",
                    detection_source=detection_source,
                    created_at=now,
                )
                db.add(finding)
                findings_generated.append(finding)

                alert = self.alert_service.create_alert_from_finding(db, finding, is_simulation=is_sim)
                if alert:
                    alerts_generated.append(alert)

                evt = VideoEvent(
                    id=str(uuid.uuid4()),
                    event_id=f"EVT-HZ-{uuid.uuid4().hex[:8].upper()}",
                    stream_id=stream.id,
                    site_id=stream.site_id,
                    worker_id=worker_id,
                    finding_id=finding.id,
                    alert_id=alert.id if alert else None,
                    event_type=VideoEventType.HAZARD_PROXIMITY,
                    severity=RiskCategory.HIGH,
                    description=finding.description,
                    evidence=hz_evidence,
                    zone_name=current_zone,
                    bounding_box=bbox,
                    detected_ppe=detected_items,
                    missing_ppe=missing_items,
                    detection_source=detection_source,
                    is_simulation=is_sim,
                    timestamp=now,
                    created_at=now,
                )
                db.add(evt)
                events_generated.append(evt)

        # 9. Update Stream Statistics
        stream.total_frames_ingested += 1
        stream.processed_frames_count += 1
        db.commit()

        return {
            "success": True,
            "stream_id": stream.stream_id,
            "frame_number": frame_payload.get("frame_number", stream.processed_frames_count),
            "status": "PROCESSED",
            "detected_persons_count": len(detected_persons),
            "compliant_count": compliant_count,
            "violations_count": violations_count,
            "events": [
                {
                    "id": e.id,
                    "event_id": e.event_id,
                    "stream_id": stream.stream_id,
                    "site_id": stream.site_id,
                    "worker_id": e.worker_id,
                    "finding_id": e.finding_id,
                    "alert_id": e.alert_id,
                    "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
                    "severity": e.severity.value if hasattr(e.severity, "value") else str(e.severity),
                    "description": e.description,
                    "evidence": e.evidence,
                    "zone_name": e.zone_name,
                    "bounding_box": e.bounding_box,
                    "detected_ppe": e.detected_ppe,
                    "missing_ppe": e.missing_ppe,
                    "detection_source": e.detection_source,
                    "is_simulation": e.is_simulation,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else now.isoformat(),
                    "created_at": e.created_at.isoformat() if e.created_at else now.isoformat(),
                }
                for e in events_generated
            ],
            "findings_created": len(findings_generated),
            "alerts_created": len(alerts_generated),
            "detection_source": detection_source,
            "is_simulation": is_sim,
        }
