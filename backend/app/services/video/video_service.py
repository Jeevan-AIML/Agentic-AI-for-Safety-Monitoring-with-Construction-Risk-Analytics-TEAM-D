"""
Video Surveillance Service — Milestone 3 Phase 3.1
==================================================
Manages video surveillance sessions, stream lifecycle, camera zones,
deterministic demo scenario execution, and real-time live status aggregation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from app.models.models import (
    VideoStream, VideoEvent, CameraZone, Site, Worker, User,
    StreamStatus, VideoSourceType, VideoEventType, ZoneType,
    RiskCategory, SafetyAlert, AlertSeverity, AlertStatus
)
from app.services.video.providers import (
    BaseVideoStreamProvider, DemoVideoProvider, LocalVideoProvider, FutureRTSPProvider
)
from app.services.video.video_pipeline import VideoAnalysisPipeline
from app.services.video.demo_scenarios import VIDEO_DEMO_SCENARIOS


# Default zones to initialize on site monitoring
DEFAULT_SITE_ZONES = [
    {"name": "Safe Laydown Area", "zone_type": ZoneType.SAFE_AREA, "risk_level": RiskCategory.LOW, "max_capacity": 10, "boundary": {"x": 50, "y": 50, "w": 400, "h": 300}},
    {"name": "Excavation Zone", "zone_type": ZoneType.EXCAVATION, "risk_level": RiskCategory.HIGH, "max_capacity": 3, "boundary": {"x": 500, "y": 50, "w": 400, "h": 350}},
    {"name": "Heavy Equipment Zone", "zone_type": ZoneType.HEAVY_EQUIPMENT, "risk_level": RiskCategory.CRITICAL, "max_capacity": 2, "boundary": {"x": 500, "y": 420, "w": 400, "h": 280}},
    {"name": "Restricted Zone", "zone_type": ZoneType.RESTRICTED, "risk_level": RiskCategory.HIGH, "max_capacity": 1, "boundary": {"x": 920, "y": 50, "w": 300, "h": 300}},
    {"name": "Electrical Work Zone", "zone_type": ZoneType.ELECTRICAL, "risk_level": RiskCategory.HIGH, "max_capacity": 2, "boundary": {"x": 920, "y": 380, "w": 300, "h": 320}},
]


class VideoSurveillanceService:
    """Orchestrates video stream sessions and real-time surveillance operations."""

    def __init__(self):
        self.pipeline = VideoAnalysisPipeline()
        self._active_providers: Dict[str, BaseVideoStreamProvider] = {}

    def ensure_default_zones(self, db: Session, site_id: str) -> List[CameraZone]:
        """Ensure standard demo/scene zones exist for a site."""
        existing_zones = db.query(CameraZone).filter(CameraZone.site_id == site_id).all()
        if existing_zones:
            return existing_zones

        created = []
        for zd in DEFAULT_SITE_ZONES:
            zone = CameraZone(
                id=str(uuid.uuid4()),
                zone_id=f"ZONE-{uuid.uuid4().hex[:6].upper()}",
                site_id=site_id,
                name=zd["name"],
                zone_type=zd["zone_type"],
                boundary=zd["boundary"],
                risk_level=zd["risk_level"],
                max_capacity=zd["max_capacity"],
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(zone)
            created.append(zone)

        db.commit()
        return created

    def start_stream(
        self,
        db: Session,
        site_id: str,
        camera_name: str = "Site Camera",
        source_type: VideoSourceType = VideoSourceType.DEMO,
        source_url: Optional[str] = None,
        fps: float = 15.0,
        sampling_interval_frames: int = 5,
        confidence_threshold: float = 0.65,
        user_id: Optional[str] = None,
    ) -> VideoStream:
        """Start a new video stream session for a site."""
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site not found with ID: {site_id}")

        # Ensure default camera zones exist
        self.ensure_default_zones(db, site_id)

        stream_id = f"STRM-{uuid.uuid4().hex[:8].upper()}"
        is_simulation = (source_type == VideoSourceType.DEMO)

        # Initialize provider
        if source_type == VideoSourceType.DEMO:
            provider = DemoVideoProvider(
                stream_id=stream_id,
                site_id=site_id,
                camera_name=camera_name,
                fps=fps,
                sampling_interval_frames=sampling_interval_frames,
                confidence_threshold=confidence_threshold,
            )
        elif source_type == VideoSourceType.LOCAL:
            provider = LocalVideoProvider(
                stream_id=stream_id,
                site_id=site_id,
                video_path_or_device=source_url or 0,
                camera_name=camera_name,
                fps=fps,
                sampling_interval_frames=sampling_interval_frames,
                confidence_threshold=confidence_threshold,
            )
        elif source_type == VideoSourceType.RTSP:
            provider = FutureRTSPProvider(
                stream_id=stream_id,
                site_id=site_id,
                rtsp_url=source_url or "rtsp://demo-stream:554/live",
                camera_name=camera_name,
                fps=fps,
                sampling_interval_frames=sampling_interval_frames,
                confidence_threshold=confidence_threshold,
            )
        else:
            provider = DemoVideoProvider(stream_id=stream_id, site_id=site_id)

        provider.start()
        self._active_providers[stream_id] = provider

        now = datetime.now(timezone.utc)
        stream = VideoStream(
            id=str(uuid.uuid4()),
            stream_id=stream_id,
            site_id=site_id,
            camera_name=camera_name,
            source_type=source_type,
            source_url=source_url,
            status=StreamStatus.ACTIVE,
            fps=fps,
            resolution_width=provider.resolution_width,
            resolution_height=provider.resolution_height,
            sampling_interval_frames=sampling_interval_frames,
            confidence_threshold=confidence_threshold,
            total_frames_ingested=0,
            processed_frames_count=0,
            dropped_frames_count=0,
            started_at=now,
            created_by=user_id,
            is_simulation=is_simulation,
            created_at=now,
            updated_at=now,
        )
        db.add(stream)
        db.commit()
        db.refresh(stream)
        return stream

    def stop_stream(self, db: Session, stream_id: str) -> VideoStream:
        """Stop an active stream session."""
        stream = db.query(VideoStream).filter(
            (VideoStream.stream_id == stream_id) | (VideoStream.id == stream_id)
        ).first()

        if not stream:
            raise ValueError(f"Stream not found: {stream_id}")

        if stream_id in self._active_providers:
            self._active_providers[stream_id].stop()
            del self._active_providers[stream_id]

        stream.status = StreamStatus.STOPPED
        stream.stopped_at = datetime.now(timezone.utc)
        stream.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(stream)
        return stream

    def get_stream(self, db: Session, stream_id: str) -> Optional[VideoStream]:
        return db.query(VideoStream).filter(
            (VideoStream.stream_id == stream_id) | (VideoStream.id == stream_id)
        ).first()

    def list_streams(
        self,
        db: Session,
        site_id: Optional[str] = None,
        status: Optional[StreamStatus] = None,
        limit: int = 50,
    ) -> List[VideoStream]:
        q = db.query(VideoStream)
        if site_id:
            q = q.filter(VideoStream.site_id == site_id)
        if status:
            q = q.filter(VideoStream.status == status)
        return q.order_by(VideoStream.created_at.desc()).limit(limit).all()

    def get_stream_events(
        self,
        db: Session,
        stream_id: str,
        limit: int = 100,
    ) -> List[VideoEvent]:
        stream = self.get_stream(db, stream_id)
        if not stream:
            return []
        return (
            db.query(VideoEvent)
            .filter(VideoEvent.stream_id == stream.id)
            .order_by(VideoEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    def process_frame(
        self,
        db: Session,
        stream_id: str,
        frame_number: Optional[int] = None,
        scenario_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ingest and process a single frame from the stream."""
        stream = self.get_stream(db, stream_id)
        if not stream:
            raise ValueError(f"Stream not found: {stream_id}")

        if stream.status != StreamStatus.ACTIVE:
            raise ValueError(f"Cannot process frame for stream {stream.stream_id} with status {stream.status.value}.")

        now = datetime.now(timezone.utc)
        fn = frame_number or (stream.processed_frames_count + 1)

        frame_payload = {
            "frame_number": fn,
            "timestamp": now,
            "width": stream.resolution_width,
            "height": stream.resolution_height,
            "should_process": True,
            "is_simulation": stream.is_simulation,
            "scenario_id": scenario_id or 1,
            "detection_source": "DEMO / SIMULATION" if stream.is_simulation else "COMPUTER_VISION",
            "frame_data": None,
        }

        context = {
            "scenario_id": scenario_id or 1,
            "metadata": metadata or {},
        }

        return self.pipeline.process_frame(
            db=db,
            stream=stream,
            frame_payload=frame_payload,
            context=context,
        )

    def get_site_live_status(self, db: Session, site_id: str) -> Dict[str, Any]:
        """Aggregate real-time video surveillance metrics for a site."""
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site not found with ID: {site_id}")

        active_streams = db.query(VideoStream).filter(
            VideoStream.site_id == site_id,
            VideoStream.status == StreamStatus.ACTIVE,
        ).all()

        all_streams = db.query(VideoStream).filter(
            VideoStream.site_id == site_id,
        ).order_by(VideoStream.created_at.desc()).limit(10).all()

        recent_events = (
            db.query(VideoEvent)
            .filter(VideoEvent.site_id == site_id)
            .order_by(VideoEvent.created_at.desc())
            .limit(20)
            .all()
        )

        active_zones = db.query(CameraZone).filter(
            CameraZone.site_id == site_id,
            CameraZone.is_active == True,
        ).all()

        active_high_alerts = db.query(SafetyAlert).filter(
            SafetyAlert.site_id == site_id,
            SafetyAlert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.ESCALATED]),
            SafetyAlert.severity == AlertSeverity.HIGH,
        ).count()

        active_critical_alerts = db.query(SafetyAlert).filter(
            SafetyAlert.site_id == site_id,
            SafetyAlert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.ESCALATED]),
            SafetyAlert.severity == AlertSeverity.CRITICAL,
        ).count()

        # Calculate compliance estimate from recent events
        ppe_violation_events = [e for e in recent_events if e.event_type == VideoEventType.PPE_VIOLATION]
        total_person_events = [e for e in recent_events if e.event_type == VideoEventType.PERSON_DETECTED]
        detected_personnel = len(total_person_events) if total_person_events else (site.worker_count or 2)

        violations_count = len(ppe_violation_events)
        compliant_workers = max(0, detected_personnel - violations_count)
        compliance_rate = round((compliant_workers / detected_personnel * 100.0), 1) if detected_personnel > 0 else 100.0

        return {
            "site_id": site.id,
            "site_name": site.name,
            "active_streams_count": len(active_streams),
            "streams": all_streams,
            "detected_personnel_count": detected_personnel,
            "compliant_workers_count": compliant_workers,
            "ppe_compliance_rate": compliance_rate,
            "active_high_alerts_count": active_high_alerts,
            "active_critical_alerts_count": active_critical_alerts,
            "recent_events": recent_events,
            "active_zones": active_zones,
        }

    def run_demo_scenario(
        self,
        db: Session,
        scenario_id: int,
        site_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a predefined deterministic demo scenario."""
        if scenario_id not in VIDEO_DEMO_SCENARIOS:
            raise ValueError(f"Invalid demo scenario ID: {scenario_id}. Must be 1 to 5.")

        scenario = VIDEO_DEMO_SCENARIOS[scenario_id]

        # Use given site or first active site in DB
        site = None
        if site_id:
            site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            site = db.query(Site).first()
        if not site:
            raise ValueError("No construction sites exist in database. Please seed or create a site.")

        # Ensure default zones
        self.ensure_default_zones(db, site.id)

        # Get or create active demo stream for this site
        stream = db.query(VideoStream).filter(
            VideoStream.site_id == site.id,
            VideoStream.status == StreamStatus.ACTIVE,
            VideoStream.source_type == VideoSourceType.DEMO,
        ).first()

        if not stream:
            stream = self.start_stream(
                db=db,
                site_id=site.id,
                camera_name=f"Demo Camera — {scenario['name']}",
                source_type=VideoSourceType.DEMO,
                user_id=user_id,
            )

        # Process frame with scenario context
        result = self.process_frame(
            db=db,
            stream_id=stream.stream_id,
            scenario_id=scenario_id,
            metadata=scenario["scenario_data"],
        )

        return {
            "scenario": scenario,
            "stream_id": stream.stream_id,
            "site_id": site.id,
            "site_name": site.name,
            "result": result,
        }


# Singleton service instance
video_service = VideoSurveillanceService()
