"""ACRIP Safety Alert System package (Phase 2.4)."""

from app.services.alerts.notification_adapters import (
    NotificationDispatcher,
    InAppNotificationAdapter,
    EmailNotificationAdapter,
    PushNotificationAdapter,
)
from app.services.alerts.alert_engine import AlertEngine
from app.services.alerts.alert_service import AlertService
from app.services.alerts.demo_scenarios import AlertDemoRunner, DEMO_SCENARIOS_CATALOG

__all__ = [
    "NotificationDispatcher",
    "InAppNotificationAdapter",
    "EmailNotificationAdapter",
    "PushNotificationAdapter",
    "AlertEngine",
    "AlertService",
    "AlertDemoRunner",
    "DEMO_SCENARIOS_CATALOG",
]
