"""Notification Adapters for ACRIP Safety Alert System (Phase 2.4).

Provides pluggable multi-channel dispatch architecture:
- InAppNotificationAdapter: delivers in-app notifications into the database
- EmailNotificationAdapter: mock / stub email delivery adapter
- PushNotificationAdapter: mock / stub push notification delivery adapter
- NotificationDispatcher: coordinates multi-channel dispatch
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import (
    Notification, NotificationCategory,
    AlertNotification, NotificationChannel,
    SafetyAlert, AlertSeverity, User, UserRole
)


class BaseNotificationAdapter:
    """Abstract interface for alert notification delivery adapters."""

    def send(
        self,
        db: Session,
        alert: SafetyAlert,
        recipient_role: str,
        title: str,
        message: str,
        recipient_user_id: Optional[str] = None,
    ) -> AlertNotification:
        raise NotImplementedError


class InAppNotificationAdapter(BaseNotificationAdapter):
    """Delivers in-app notifications to the existing Notification model and tracks AlertNotification."""

    def send(
        self,
        db: Session,
        alert: SafetyAlert,
        recipient_role: str,
        title: str,
        message: str,
        recipient_user_id: Optional[str] = None,
    ) -> AlertNotification:
        # Create user notification in existing notifications table
        severity_str = "critical" if alert.severity == AlertSeverity.CRITICAL else "warning"
        
        in_app_notif = Notification(
            id=str(uuid.uuid4()),
            user_id=recipient_user_id,  # None means broadcast to role
            category=NotificationCategory.SAFETY,
            title=title,
            message=message,
            severity=severity_str,
            is_read=False,
            link=f"/safety?alert={alert.alert_id}",
            created_at=datetime.utcnow(),
        )
        db.add(in_app_notif)

        # Track in AlertNotification table
        alert_notif = AlertNotification(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            channel=NotificationChannel.IN_APP,
            recipient_role=recipient_role,
            recipient_user_id=recipient_user_id,
            title=title,
            message=message,
            status="DELIVERED",
            delivery_details={
                "in_app_notification_id": in_app_notif.id,
                "provider": "DATABASE_IN_APP",
                "delivered": True,
            },
            sent_at=datetime.utcnow(),
        )
        db.add(alert_notif)
        return alert_notif


class EmailNotificationAdapter(BaseNotificationAdapter):
    """Mock / Stub email delivery adapter.
    
    Clearly labeled mock delivery for demonstration where real SMTP/SES is not configured.
    """

    def send(
        self,
        db: Session,
        alert: SafetyAlert,
        recipient_role: str,
        title: str,
        message: str,
        recipient_user_id: Optional[str] = None,
    ) -> AlertNotification:
        mock_recipient_email = f"{recipient_role.lower().replace(' ', '_')}@acrip.local"
        mock_payload = {
            "to": mock_recipient_email,
            "subject": f"[ACRIP ALERT] {title}",
            "body": message,
            "provider": "MOCK_EMAIL_ADAPTER",
            "is_simulation": True,
            "delivery_note": "[MOCK / STUB] Simulated Email Dispatch to " + mock_recipient_email,
        }

        alert_notif = AlertNotification(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            channel=NotificationChannel.EMAIL_ADAPTER,
            recipient_role=recipient_role,
            recipient_user_id=recipient_user_id,
            title=f"[EMAIL] {title}",
            message=message,
            status="SENT_MOCK",
            delivery_details=mock_payload,
            sent_at=datetime.utcnow(),
        )
        db.add(alert_notif)
        return alert_notif


class PushNotificationAdapter(BaseNotificationAdapter):
    """Mock / Stub push notification delivery adapter.
    
    Clearly labeled mock delivery for demonstration where real APNS/FCM is not configured.
    """

    def send(
        self,
        db: Session,
        alert: SafetyAlert,
        recipient_role: str,
        title: str,
        message: str,
        recipient_user_id: Optional[str] = None,
    ) -> AlertNotification:
        mock_payload = {
            "topic": f"acrip-alerts-{recipient_role.lower()}",
            "title": title,
            "body": message,
            "priority": "high" if alert.severity == AlertSeverity.CRITICAL else "normal",
            "provider": "MOCK_PUSH_ADAPTER",
            "is_simulation": True,
            "delivery_note": f"[MOCK / STUB] Simulated Push Dispatch to role:{recipient_role}",
        }

        alert_notif = AlertNotification(
            id=str(uuid.uuid4()),
            alert_id=alert.id,
            channel=NotificationChannel.PUSH_ADAPTER,
            recipient_role=recipient_role,
            recipient_user_id=recipient_user_id,
            title=f"[PUSH] {title}",
            message=message,
            status="SENT_MOCK",
            delivery_details=mock_payload,
            sent_at=datetime.utcnow(),
        )
        db.add(alert_notif)
        return alert_notif


class NotificationDispatcher:
    """Coordinates dispatch across multiple notification adapters based on alert severity and recipient role."""

    def __init__(self):
        self.adapters: Dict[NotificationChannel, BaseNotificationAdapter] = {
            NotificationChannel.IN_APP: InAppNotificationAdapter(),
            NotificationChannel.EMAIL_ADAPTER: EmailNotificationAdapter(),
            NotificationChannel.PUSH_ADAPTER: PushNotificationAdapter(),
        }

    def dispatch(
        self,
        db: Session,
        alert: SafetyAlert,
        recipient_roles: List[str],
        title: Optional[str] = None,
        message: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> List[AlertNotification]:
        """Dispatches an alert to all specified roles across selected channels."""
        if channels is None:
            # Default: dispatch across all 3 channels
            channels = [
                NotificationChannel.IN_APP,
                NotificationChannel.EMAIL_ADAPTER,
                NotificationChannel.PUSH_ADAPTER,
            ]

        notif_title = title or f"[{alert.severity.value.upper()} ALERT] {alert.title}"
        notif_message = message or f"{alert.description}. Recommendation: {alert.recommendation or 'Immediate mitigation required.'}"

        dispatched: List[AlertNotification] = []
        for role in recipient_roles:
            for channel in channels:
                adapter = self.adapters.get(channel)
                if adapter:
                    record = adapter.send(
                        db=db,
                        alert=alert,
                        recipient_role=role,
                        title=notif_title,
                        message=notif_message,
                    )
                    dispatched.append(record)

        return dispatched
