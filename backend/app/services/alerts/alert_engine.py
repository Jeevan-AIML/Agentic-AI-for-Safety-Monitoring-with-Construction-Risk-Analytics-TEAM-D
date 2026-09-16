"""Alert Engine for ACRIP Safety Alert System (Phase 2.4).

Processes findings, events, and risks:
- LOW -> no alert (suppressed)
- MEDIUM -> no automatic alert (suppressed)
- HIGH -> HIGH alert (priority HIGH, timeout 30m)
- CRITICAL -> CRITICAL alert (priority CRITICAL, timeout 15m)
- Deduplication: checks for existing active alerts (OPEN, ACKNOWLEDGED, ESCALATED)
"""

import uuid
from datetime import datetime
from typing import Optional, Union, Tuple
from sqlalchemy.orm import Session

from app.models.models import (
    SafetyAlert, AlertSeverity, AlertStatus, AlertPriority,
    SafetyFinding, SafetyMonitoringEvent, PPEAnalysis, Hazard,
    RiskCategory, AlertAuditEvent, AlertAuditEventType
)
from app.core.config import settings


class AlertEngine:
    """Deterministic alert evaluation and deduplication engine."""

    def evaluate_severity(self, raw_severity: Union[RiskCategory, str]) -> Optional[AlertSeverity]:
        """Maps finding/hazard severity to AlertSeverity, suppressing LOW and MEDIUM."""
        sev_str = getattr(raw_severity, "value", str(raw_severity)).lower()
        if sev_str == "critical":
            return AlertSeverity.CRITICAL
        elif sev_str == "high":
            return AlertSeverity.HIGH
        # LOW and MEDIUM do not generate automatic alerts
        return None

    def find_active_duplicate(
        self,
        db: Session,
        site_id: str,
        source_type: str,
        source_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[SafetyAlert]:
        """Checks if an active (OPEN, ACKNOWLEDGED, ESCALATED) alert already exists for the event."""
        active_statuses = [AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.ESCALATED]
        
        # 1. Exact match on source_type and source_id
        if source_id:
            existing = (
                db.query(SafetyAlert)
                .filter(
                    SafetyAlert.site_id == site_id,
                    SafetyAlert.source_type == source_type,
                    SafetyAlert.source_id == str(source_id),
                    SafetyAlert.status.in_(active_statuses),
                )
                .first()
            )
            if existing:
                return existing

        # 2. Worker & title match to prevent redundant alerts for the same worker condition
        if worker_id and title:
            existing = (
                db.query(SafetyAlert)
                .filter(
                    SafetyAlert.site_id == site_id,
                    SafetyAlert.worker_id == worker_id,
                    SafetyAlert.title == title,
                    SafetyAlert.status.in_(active_statuses),
                )
                .first()
            )
            if existing:
                return existing

        return None

    def process_safety_finding(
        self,
        db: Session,
        finding: SafetyFinding,
        is_simulation: bool = False,
    ) -> Tuple[Optional[SafetyAlert], bool]:
        """Evaluates a SafetyFinding. Returns (alert, is_new)."""
        severity = self.evaluate_severity(finding.severity)
        if not severity:
            return None, False

        # Deduplicate
        existing = self.find_active_duplicate(
            db=db,
            site_id=finding.site_id,
            source_type="SAFETY_FINDING",
            source_id=finding.id,
            worker_id=finding.worker_id,
            title=f"Safety Violation: {finding.finding_type.value}",
        )
        if existing:
            return existing, False

        priority = AlertPriority.CRITICAL if severity == AlertSeverity.CRITICAL else AlertPriority.HIGH
        timeout = settings.ALERT_CRITICAL_TIMEOUT_MINUTES if severity == AlertSeverity.CRITICAL else settings.ALERT_HIGH_TIMEOUT_MINUTES

        alert_count = db.query(SafetyAlert).count() + 1
        date_str = datetime.utcnow().strftime("%Y%m%d")
        alert_id = f"ALT-{date_str}-{alert_count:04d}"

        alert = SafetyAlert(
            id=str(uuid.uuid4()),
            alert_id=alert_id,
            site_id=finding.site_id,
            worker_id=finding.worker_id,
            finding_id=finding.id,
            source_type="SAFETY_FINDING",
            source_id=finding.id,
            severity=severity,
            priority=priority,
            status=AlertStatus.OPEN,
            title=f"Safety Violation: {finding.finding_type.value.replace('_', ' ').title()}",
            description=finding.description,
            recommendation=finding.recommendation or "Review and correct safety non-compliance immediately.",
            evidence=finding.evidence,
            escalation_level=0,
            escalation_timeout_minutes=timeout,
            assigned_role="safety_officer",
            is_simulation=is_simulation,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return alert, True

    def process_monitoring_event(
        self,
        db: Session,
        event: SafetyMonitoringEvent,
    ) -> Tuple[Optional[SafetyAlert], bool]:
        """Evaluates a SafetyMonitoringEvent. Returns (alert, is_new)."""
        severity = self.evaluate_severity(event.severity)
        if not severity:
            return None, False

        existing = self.find_active_duplicate(
            db=db,
            site_id=event.site_id,
            source_type="MONITORING_EVENT",
            source_id=event.id,
            worker_id=event.worker_id,
            title=f"Monitoring Alert: {event.event_type}",
        )
        if existing:
            return existing, False

        priority = AlertPriority.CRITICAL if severity == AlertSeverity.CRITICAL else AlertPriority.HIGH
        timeout = settings.ALERT_CRITICAL_TIMEOUT_MINUTES if severity == AlertSeverity.CRITICAL else settings.ALERT_HIGH_TIMEOUT_MINUTES

        alert_count = db.query(SafetyAlert).count() + 1
        date_str = datetime.utcnow().strftime("%Y%m%d")
        alert_id = f"ALT-{date_str}-{alert_count:04d}"

        alert = SafetyAlert(
            id=str(uuid.uuid4()),
            alert_id=alert_id,
            site_id=event.site_id,
            worker_id=event.worker_id,
            finding_id=event.finding_id,
            source_type="MONITORING_EVENT",
            source_id=event.id,
            severity=severity,
            priority=priority,
            status=AlertStatus.OPEN,
            title=f"Monitoring Alert: {event.event_type}",
            description=f"Worker condition alert in zone {event.zone_name or 'unspecified'}. {event.evidence or ''}",
            recommendation=event.recommendation or "Conduct prompt worker intervention and clear hazardous conditions.",
            evidence=event.evidence,
            escalation_level=0,
            escalation_timeout_minutes=timeout,
            assigned_role="safety_officer",
            is_simulation=event.is_simulation,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return alert, True
