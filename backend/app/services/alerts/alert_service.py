"""Alert Service for ACRIP Safety Alert System (Phase 2.4).

Manages complete alert lifecycle:
- Creation, Deduplication & Notification
- Acknowledgment
- Resolution & SafetyFinding synchronization
- Tiered Escalation & Timeout detection
- Audit trail recording
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.models import (
    SafetyAlert, AlertStatus, AlertSeverity, AlertPriority,
    AlertAuditEvent, AlertAuditEventType, SafetyFinding,
    SafetyFindingStatus, User, UserRole
)
from app.services.alerts.alert_engine import AlertEngine
from app.services.alerts.notification_adapters import NotificationDispatcher


class AlertService:
    """Service encapsulating alert management and lifecycle operations."""

    def __init__(self):
        self.engine = AlertEngine()
        self.dispatcher = NotificationDispatcher()

    def get_alert_by_id(self, db: Session, alert_id: str) -> Optional[SafetyAlert]:
        """Retrieves an alert by database UUID or human-readable alert_id."""
        return (
            db.query(SafetyAlert)
            .filter((SafetyAlert.id == alert_id) | (SafetyAlert.alert_id == alert_id))
            .first()
        )

    def list_alerts(
        self,
        db: Session,
        site_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[SafetyAlert]:
        """Filters safety alerts with optional criteria."""
        query = db.query(SafetyAlert)
        if site_id:
            query = query.filter(SafetyAlert.site_id == site_id)
        if worker_id:
            query = query.filter(SafetyAlert.worker_id == worker_id)
        if status:
            query = query.filter(SafetyAlert.status == status.lower())
        if severity:
            query = query.filter(SafetyAlert.severity == severity.lower())
        return query.order_by(SafetyAlert.created_at.desc()).limit(limit).all()

    def create_alert_from_finding(
        self,
        db: Session,
        finding: SafetyFinding,
        is_simulation: bool = False,
    ) -> Optional[SafetyAlert]:
        """Processes a SafetyFinding, creates a SafetyAlert if HIGH/CRITICAL, dispatches notifications, and logs audit event."""
        alert, is_new = self.engine.process_safety_finding(db, finding, is_simulation=is_simulation)
        if not alert or not is_new:
            return alert

        db.add(alert)
        db.flush()

        # Audit Event
        audit = AlertAuditEvent(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            event_type=AlertAuditEventType.ALERT_CREATED,
            actor_id="SYSTEM",
            actor_name="SafetyAlertEngine",
            actor_role="system",
            details=f"Alert created from SafetyFinding {finding.finding_id or finding.id} (Severity: {alert.severity.value})",
            created_at=datetime.utcnow(),
        )
        db.add(audit)

        # Dispatch Notifications
        roles = ["safety_officer"]
        if alert.severity == AlertSeverity.CRITICAL:
            roles.append("site_manager")

        self.dispatcher.dispatch(
            db=db,
            alert=alert,
            recipient_roles=roles,
        )

        db.commit()
        db.refresh(alert)
        return alert

    def acknowledge_alert(
        self,
        db: Session,
        alert_id: str,
        user: User,
        notes: Optional[str] = None,
    ) -> SafetyAlert:
        """Transitions alert to ACKNOWLEDGED, logs actor, and saves audit event."""
        alert = self.get_alert_by_id(db, alert_id)
        if not alert:
            raise ValueError(f"SafetyAlert {alert_id} not found")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user.id
        alert.updated_at = datetime.utcnow()

        # Audit event
        audit = AlertAuditEvent(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            event_type=AlertAuditEventType.ALERT_ACKNOWLEDGED,
            actor_id=user.id,
            actor_name=user.full_name,
            actor_role=getattr(user.role, "value", str(user.role)),
            details=notes or f"Alert acknowledged by {user.full_name}",
            created_at=datetime.utcnow(),
        )
        db.add(audit)

        # If there's an associated finding, mark it acknowledged as well
        if alert.finding_id:
            finding = db.query(SafetyFinding).filter(SafetyFinding.id == alert.finding_id).first()
            if finding and finding.status == SafetyFindingStatus.OPEN:
                finding.status = SafetyFindingStatus.ACKNOWLEDGED
                finding.acknowledged_at = datetime.utcnow()
                finding.acknowledged_by = user.id

        db.commit()
        db.refresh(alert)
        return alert

    def resolve_alert(
        self,
        db: Session,
        alert_id: str,
        user: User,
        notes: str,
    ) -> SafetyAlert:
        """Transitions alert to RESOLVED, synchronizes finding, and saves audit event."""
        alert = self.get_alert_by_id(db, alert_id)
        if not alert:
            raise ValueError(f"SafetyAlert {alert_id} not found")

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user.id
        alert.resolution_notes = notes
        alert.updated_at = datetime.utcnow()

        # Audit event
        audit = AlertAuditEvent(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            event_type=AlertAuditEventType.ALERT_RESOLVED,
            actor_id=user.id,
            actor_name=user.full_name,
            actor_role=getattr(user.role, "value", str(user.role)),
            details=f"Resolved: {notes}",
            created_at=datetime.utcnow(),
        )
        db.add(audit)

        # Synchronize associated SafetyFinding if present
        if alert.finding_id:
            finding = db.query(SafetyFinding).filter(SafetyFinding.id == alert.finding_id).first()
            if finding and finding.status in [SafetyFindingStatus.OPEN, SafetyFindingStatus.ACKNOWLEDGED]:
                finding.status = SafetyFindingStatus.MITIGATED
                finding.mitigated_at = datetime.utcnow()
                finding.mitigated_by = user.id
                finding.mitigation_notes = notes

        db.commit()
        db.refresh(alert)
        return alert

    def escalate_alert(
        self,
        db: Session,
        alert_id: str,
        user: Optional[User] = None,
        reason: Optional[str] = None,
        target_role: Optional[str] = None,
    ) -> SafetyAlert:
        """Transitions alert to ESCALATED, increments level, reassigns role, and dispatches escalation notifications."""
        alert = self.get_alert_by_id(db, alert_id)
        if not alert:
            raise ValueError(f"SafetyAlert {alert_id} not found")

        alert.escalation_level += 1
        alert.status = AlertStatus.ESCALATED
        alert.escalated_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()

        # Determine escalated role
        if target_role:
            escalated_role = target_role
        elif alert.escalation_level == 1:
            escalated_role = "site_manager"
        else:
            escalated_role = "super_admin"

        alert.assigned_role = escalated_role

        # Audit event
        actor_id = user.id if user else "SYSTEM"
        actor_name = user.full_name if user else "Automated Escalation Service"
        actor_role = getattr(user.role, "value", str(user.role)) if user else "system"
        escalation_reason = reason or f"Escalated to Level {alert.escalation_level} ({escalated_role})"

        audit = AlertAuditEvent(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            event_type=AlertAuditEventType.ALERT_ESCALATED,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            details=escalation_reason,
            created_at=datetime.utcnow(),
        )
        db.add(audit)

        # Dispatch escalation notifications to higher role
        self.dispatcher.dispatch(
            db=db,
            alert=alert,
            recipient_roles=[escalated_role],
            title=f"[ESCALATED L{alert.escalation_level}] {alert.title}",
            message=f"Alert {alert.alert_id} escalated to {escalated_role}. Reason: {escalation_reason}",
        )

        db.commit()
        db.refresh(alert)
        return alert

    def check_escalation_timeouts(self, db: Session) -> List[SafetyAlert]:
        """Scans for open alerts whose acknowledgment timeout has expired and escalates them."""
        now = datetime.utcnow()
        open_alerts = (
            db.query(SafetyAlert)
            .filter(SafetyAlert.status == AlertStatus.OPEN)
            .all()
        )

        escalated_alerts = []
        for alert in open_alerts:
            elapsed_minutes = (now - alert.created_at).total_seconds() / 60.0
            if elapsed_minutes >= alert.escalation_timeout_minutes:
                escalated = self.escalate_alert(
                    db=db,
                    alert_id=alert.id,
                    user=None,
                    reason=f"Acknowledgment timeout of {alert.escalation_timeout_minutes} minutes expired ({elapsed_minutes:.1f}m elapsed)",
                )
                escalated_alerts.append(escalated)

        return escalated_alerts
