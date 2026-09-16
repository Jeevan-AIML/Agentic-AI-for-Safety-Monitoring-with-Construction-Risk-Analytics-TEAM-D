"""
Worker Safety Monitoring Service — Milestone 2 Phase 2.3
=========================================================
Coordinates site monitoring sessions, worker evaluation, finding persistence,
notification dispatch, and demo scenario execution.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import (
    Worker, Site, Activity, Equipment, Hazard, User,
    SafetyFinding, SafetyFindingStatus, SafetyFindingType,
    RiskCategory, WorkerSafetyStatus, Notification, NotificationCategory,
    SafetyMonitoringEvent, SiteMonitoringSession
)
from app.services.monitoring.worker_monitoring_engine import WorkerMonitoringEngine
from app.services.monitoring.demo_scenarios import MONITORING_DEMO_SCENARIOS


class WorkerMonitoringService:
    def __init__(self):
        self.engine = WorkerMonitoringEngine()

    def start_monitoring(self, db: Session, site_id: str, user_id: Optional[str] = None) -> SiteMonitoringSession:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site '{site_id}' not found")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        session = db.query(SiteMonitoringSession).filter(SiteMonitoringSession.site_id == site_id).first()
        if not session:
            session = SiteMonitoringSession(
                id=str(uuid.uuid4()),
                site_id=site_id,
                is_active=True,
                started_at=now,
                started_by=user_id,
                last_evaluated_at=now,
            )
            db.add(session)
        else:
            session.is_active = True
            session.started_at = now
            session.stopped_at = None
            session.started_by = user_id
            session.last_evaluated_at = now

        # Create system notification
        notif = Notification(
            id=str(uuid.uuid4()),
            category=NotificationCategory.SAFETY,
            title="Worker Safety Monitoring Started",
            message=f"Live safety monitoring active for site: {site.name}. Telemetry rules active.",
            severity="info",
            link=f"/safety?site_id={site_id}",
            created_at=now,
        )
        db.add(notif)
        db.commit()
        db.refresh(session)
        return session

    def stop_monitoring(self, db: Session, site_id: str, user_id: Optional[str] = None) -> SiteMonitoringSession:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site '{site_id}' not found")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        session = db.query(SiteMonitoringSession).filter(SiteMonitoringSession.site_id == site_id).first()
        if not session:
            session = SiteMonitoringSession(
                id=str(uuid.uuid4()),
                site_id=site_id,
                is_active=False,
                started_at=now,
                stopped_at=now,
                started_by=user_id,
            )
            db.add(session)
        else:
            session.is_active = False
            session.stopped_at = now

        db.commit()
        db.refresh(session)
        return session

    def evaluate_worker(
        self,
        db: Session,
        worker_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a worker's safety conditions against the 8 monitoring rules.
        Persists SafetyFinding and SafetyMonitoringEvent entities.
        Dispatches Notifications for HIGH and CRITICAL risks.
        """
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            raise ValueError(f"Worker '{worker_id}' not found")

        site = db.query(Site).filter(Site.id == worker.site_id).first() if worker.site_id else None
        site_id = site.id if site else "default-site"
        site_name = site.name if site else "Construction Site"

        # Prepare worker info
        worker_info = {
            "id": worker.id,
            "worker_id": worker.worker_id,
            "name": worker.name,
            "role": worker.role,
            "safety_training": worker.safety_training,
            "ppe_status": worker.ppe_status,
        }

        # Prepare context (merge input data with real site defaults if missing)
        context = input_data.copy() if input_data else {}
        if not context.get("current_activity"):
            # Check for existing activity assigned to site
            recent_act = db.query(Activity).filter(Activity.site_id == site_id).order_by(Activity.date.desc()).first()
            context["current_activity"] = recent_act.activity_type.value if recent_act else "general_construction"

        if not context.get("current_zone"):
            context["current_zone"] = "Zone A — General Work Sector"

        # Run monitoring evaluation
        result = self.engine.evaluate(worker_info, context)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Update monitoring session last_evaluated_at
        session = db.query(SiteMonitoringSession).filter(SiteMonitoringSession.site_id == site_id).first()
        if session:
            session.last_evaluated_at = now

        # Persist findings & monitoring events
        for f_data in result["findings"]:
            # Check for existing open finding of this type for this worker to prevent duplicates
            f_type_str = f_data["finding_type"]
            try:
                f_type_enum = SafetyFindingType(f_type_str)
            except ValueError:
                f_type_enum = SafetyFindingType.HIGH_RISK_ZONE_EXPOSURE

            existing_finding = db.query(SafetyFinding).filter(
                SafetyFinding.worker_id == worker.id,
                SafetyFinding.finding_type == f_type_enum,
                SafetyFinding.status == SafetyFindingStatus.OPEN
            ).first()

            if not existing_finding:
                finding = SafetyFinding(
                    id=str(uuid.uuid4()),
                    finding_id=f"FIND-MON-{uuid.uuid4().hex[:6].upper()}",
                    site_id=site_id,
                    worker_id=worker.id,
                    finding_type=f_type_enum,
                    description=f_data["description"],
                    evidence=f_data["evidence"],
                    severity=f_data["severity"],
                    status=SafetyFindingStatus.OPEN,
                    recommendation=f_data["recommendation"],
                    detection_source="WORKER_MONITORING_ENGINE",
                    created_at=now,
                )
                db.add(finding)
                db.flush()
                finding_id = finding.id
            else:
                finding_id = existing_finding.id

            # Create SafetyMonitoringEvent
            event = SafetyMonitoringEvent(
                id=str(uuid.uuid4()),
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                site_id=site_id,
                worker_id=worker.id,
                activity_name=result["current_activity"],
                zone_name=result["current_zone"],
                time_in_zone_minutes=result["time_in_zone_minutes"],
                event_type=f_data["rule_name"],
                severity=f_data["severity"],
                worker_safety_status=result["safety_status"],
                evidence=f_data["evidence"],
                recommendation=f_data["recommendation"],
                detection_source="WORKER_MONITORING_ENGINE",
                finding_id=finding_id,
                is_simulation=result["is_simulation"],
                created_at=now,
            )
            db.add(event)

        # Dispatch notification if HIGH or CRITICAL
        safety_status = result["safety_status"]
        if safety_status in [WorkerSafetyStatus.HIGH_RISK, WorkerSafetyStatus.CRITICAL]:
            severity_str = "critical" if safety_status == WorkerSafetyStatus.CRITICAL else "error"
            notif = Notification(
                id=str(uuid.uuid4()),
                category=NotificationCategory.SAFETY,
                title=f"Worker Safety Alert: {worker.name} ({safety_status.value})",
                message=f"Worker monitoring detected {len(result['findings'])} active safety violation(s) in {result['current_zone']}.",
                severity=severity_str,
                link=f"/safety?worker_id={worker.id}",
                created_at=now,
            )
            db.add(notif)

        db.commit()

        # Add site_name to output
        result["site_id"] = site_id
        result["site_name"] = site_name
        return result

    def get_site_monitoring_status(self, db: Session, site_id: str) -> Dict[str, Any]:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site '{site_id}' not found")

        session = db.query(SiteMonitoringSession).filter(SiteMonitoringSession.site_id == site_id).first()
        is_active = session.is_active if session else False
        started_at = session.started_at if session else None
        stopped_at = session.stopped_at if session else None

        # Recent events for site
        recent_events = (
            db.query(SafetyMonitoringEvent)
            .filter(SafetyMonitoringEvent.site_id == site_id)
            .order_by(desc(SafetyMonitoringEvent.created_at))
            .limit(10)
            .all()
        )

        # Worker metrics
        workers_count = db.query(Worker).filter(Worker.site_id == site_id, Worker.is_active == True).count()

        # Count active findings by severity
        open_findings = db.query(SafetyFinding).filter(
            SafetyFinding.site_id == site_id,
            SafetyFinding.status == SafetyFindingStatus.OPEN,
            SafetyFinding.detection_source == "WORKER_MONITORING_ENGINE"
        ).all()

        active_critical = sum(1 for f in open_findings if f.severity == RiskCategory.CRITICAL)
        active_high = sum(1 for f in open_findings if f.severity == RiskCategory.HIGH)
        active_warnings = sum(1 for f in open_findings if f.severity in [RiskCategory.MEDIUM, RiskCategory.LOW])

        return {
            "site_id": site.id,
            "site_name": site.name,
            "is_monitoring_active": is_active,
            "started_at": started_at,
            "stopped_at": stopped_at,
            "monitored_workers_count": workers_count,
            "active_warnings_count": active_warnings,
            "active_high_risk_count": active_high,
            "active_critical_count": active_critical,
            "recent_events": [
                {
                    "id": e.id,
                    "event_id": e.event_id,
                    "site_id": e.site_id,
                    "worker_id": e.worker_id,
                    "worker_name": e.worker.name if e.worker else "Worker",
                    "activity_name": e.activity_name,
                    "zone_name": e.zone_name,
                    "time_in_zone_minutes": e.time_in_zone_minutes,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "worker_safety_status": e.worker_safety_status,
                    "evidence": e.evidence,
                    "recommendation": e.recommendation,
                    "detection_source": e.detection_source,
                    "is_simulation": e.is_simulation,
                    "created_at": e.created_at,
                }
                for e in recent_events
            ]
        }

    def get_worker_monitoring_history(self, db: Session, worker_id: str) -> List[Dict[str, Any]]:
        events = (
            db.query(SafetyMonitoringEvent)
            .filter(SafetyMonitoringEvent.worker_id == worker_id)
            .order_by(desc(SafetyMonitoringEvent.created_at))
            .limit(10)
            .all()
        )
        return [
            {
                "id": e.id,
                "event_id": e.event_id,
                "site_id": e.site_id,
                "worker_id": e.worker_id,
                "worker_name": e.worker.name if e.worker else "Worker",
                "activity_name": e.activity_name,
                "zone_name": e.zone_name,
                "time_in_zone_minutes": e.time_in_zone_minutes,
                "event_type": e.event_type,
                "severity": e.severity,
                "worker_safety_status": e.worker_safety_status,
                "evidence": e.evidence,
                "recommendation": e.recommendation,
                "detection_source": e.detection_source,
                "is_simulation": e.is_simulation,
                "created_at": e.created_at,
            }
            for e in events
        ]

    def list_demo_scenarios(self) -> List[Dict[str, Any]]:
        scenarios = []
        for s_id, s in MONITORING_DEMO_SCENARIOS.items():
            scenarios.append({
                "id": s["id"],
                "name": s["name"],
                "description": s["description"],
                "expected_status": s["expected_status"],
                "expected_findings_count": s["expected_findings_count"],
                "context_summary": {
                    "activity": s["context"].get("current_activity"),
                    "zone": s["context"].get("current_zone"),
                    "time_in_zone": s["context"].get("time_in_zone_minutes"),
                    "nearby_hazards": len(s["context"].get("nearby_hazards", [])),
                    "nearby_equipment": len(s["context"].get("nearby_equipment", [])),
                }
            })
        return scenarios

    def run_demo_scenario(self, db: Session, scenario_id: int, site_id: Optional[str] = None) -> Dict[str, Any]:
        if scenario_id not in MONITORING_DEMO_SCENARIOS:
            raise ValueError(f"Demo scenario {scenario_id} not found. Valid IDs: 1-6")

        scenario = MONITORING_DEMO_SCENARIOS[scenario_id]
        worker_info = scenario["worker_info"]
        context = scenario["context"]

        # Run evaluation through engine
        result = self.engine.evaluate(worker_info, context)

        # Attach demo label
        result["site_id"] = site_id or "demo-site-01"
        result["site_name"] = "Demo Construction Site"
        result["detection_source"] = "DEMO / SIMULATION"
        result["is_simulation"] = True
        return result


monitoring_service = WorkerMonitoringService()
