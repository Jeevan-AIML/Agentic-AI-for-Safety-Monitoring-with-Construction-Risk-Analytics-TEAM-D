from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from app.models.models import (
    UserRole, ProjectStatus, SiteStatus, WorkerRole,
    SafetyTrainingStatus, PPEStatus, EquipmentStatus,
    ActivityType, HazardType, HazardStatus, RiskCategory,
    NotificationCategory, SafetyFindingStatus, SafetyFindingType,
    PPEClass, PPEComplianceStatus, WorkerSafetyStatus,
    AlertSeverity, AlertStatus, AlertPriority, NotificationChannel,
    AlertAuditEventType, StreamStatus, VideoSourceType, VideoEventType, ZoneType,
    ComplianceRuleCategory, ComplianceStatus, InspectionRequirementStatus,
    InsuranceRiskLevel, ClaimRiskLevel,
    ReportType, ReportStatus
)


# ── Auth Schemas ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[UserRole] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        name = v.strip()
        if len(name) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return name

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    assigned_site_id: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.VIEWER
    phone: Optional[str] = None
    department: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    assigned_site_id: Optional[str] = None


# ── Project Schemas ────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    project_id: str
    name: str
    client: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    expected_completion: Optional[datetime] = None
    budget: Optional[float] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    manager_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    expected_completion: Optional[datetime] = None
    budget: Optional[float] = None
    status: Optional[ProjectStatus] = None
    manager_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProjectOut(BaseModel):
    id: str
    project_id: str
    name: str
    client: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    expected_completion: Optional[datetime] = None
    budget: Optional[float] = None
    status: ProjectStatus
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    site_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Site Schemas ───────────────────────────────────────────────────────────

class SiteCreate(BaseModel):
    site_id: str
    name: str
    site_type: Optional[str] = None
    project_id: Optional[str] = None
    manager_id: Optional[str] = None
    status: SiteStatus = SiteStatus.ACTIVE
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    site_type: Optional[str] = None
    project_id: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[SiteStatus] = None
    current_risk_score: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class SiteOut(BaseModel):
    id: str
    site_id: str
    name: str
    site_type: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    status: SiteStatus
    current_risk_score: float
    risk_category: RiskCategory
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    worker_count: int
    equipment_count: int
    last_inspection: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Worker Schemas ─────────────────────────────────────────────────────────

class WorkerCreate(BaseModel):
    worker_id: str
    name: str
    role: WorkerRole
    department: Optional[str] = None
    site_id: Optional[str] = None
    contact: Optional[str] = None
    joining_date: Optional[datetime] = None
    safety_training: SafetyTrainingStatus = SafetyTrainingStatus.NOT_STARTED
    ppe_status: PPEStatus = PPEStatus.NON_COMPLIANT

class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[WorkerRole] = None
    department: Optional[str] = None
    site_id: Optional[str] = None
    contact: Optional[str] = None
    safety_training: Optional[SafetyTrainingStatus] = None
    ppe_status: Optional[PPEStatus] = None
    is_active: Optional[bool] = None

class WorkerOut(BaseModel):
    id: str
    worker_id: str
    name: str
    role: WorkerRole
    department: Optional[str] = None
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    contact: Optional[str] = None
    joining_date: Optional[datetime] = None
    safety_training: SafetyTrainingStatus
    ppe_status: PPEStatus
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Equipment Schemas ──────────────────────────────────────────────────────

class EquipmentCreate(BaseModel):
    equipment_id: str
    name: str
    equipment_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    site_id: Optional[str] = None
    operator_name: Optional[str] = None
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    last_inspection: Optional[datetime] = None
    maintenance_due: Optional[datetime] = None

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    equipment_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    site_id: Optional[str] = None
    operator_name: Optional[str] = None
    status: Optional[EquipmentStatus] = None
    last_inspection: Optional[datetime] = None
    maintenance_due: Optional[datetime] = None

class EquipmentOut(BaseModel):
    id: str
    equipment_id: str
    name: str
    equipment_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    operator_name: Optional[str] = None
    status: EquipmentStatus
    last_inspection: Optional[datetime] = None
    maintenance_due: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Activity Schemas ───────────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    site_id: str
    activity_type: ActivityType
    description: Optional[str] = None
    date: datetime
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    workers_involved: int = 0
    equipment_used: Optional[List[str]] = None
    environmental_conditions: Optional[str] = None
    notes: Optional[str] = None

class ActivityOut(BaseModel):
    id: str
    site_id: str
    site_name: Optional[str] = None
    activity_type: ActivityType
    description: Optional[str] = None
    date: datetime
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    workers_involved: int
    equipment_used: Optional[List[str]] = None
    environmental_conditions: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Hazard Schemas ─────────────────────────────────────────────────────────

# ── Hazard Schemas ─────────────────────────────────────────────────────────

class HazardCreate(BaseModel):
    site_id: str
    hazard_type: HazardType
    description: str
    evidence: Optional[str] = None
    severity: int  # 1-5
    probability: int  # 1-5
    status: HazardStatus = HazardStatus.OPEN
    reported_by: Optional[str] = None
    recommended_action: Optional[str] = None
    detection_source: Optional[str] = "RULE_ENGINE"

    @field_validator("severity", "probability")
    @classmethod
    def validate_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Must be between 1 and 5")
        return v

class HazardUpdate(BaseModel):
    status: Optional[HazardStatus] = None
    severity: Optional[int] = None
    probability: Optional[int] = None
    recommended_action: Optional[str] = None
    mitigation_notes: Optional[str] = None

class HazardOut(BaseModel):
    id: str
    hazard_id: str
    site_id: str
    site_name: Optional[str] = None
    hazard_type: HazardType
    description: str
    evidence: Optional[str] = None
    severity: int
    probability: int
    risk_score: float
    risk_category: RiskCategory
    status: HazardStatus
    detected_at: datetime
    reported_by: Optional[str] = None
    recommended_action: Optional[str] = None
    detection_source: Optional[str] = "RULE_ENGINE"
    detected_by_agent: bool
    agent_confidence: Optional[float] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    mitigated_at: Optional[datetime] = None
    mitigated_by: Optional[str] = None
    mitigation_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Risk Score Schemas ─────────────────────────────────────────────────────

class RiskScoreOut(BaseModel):
    id: str
    site_id: str
    site_name: Optional[str] = None
    overall_score: float
    category: RiskCategory
    environmental_risk: float
    equipment_risk: float
    activity_risk: float = 0.0
    site_condition_risk: float
    operational_risk: float
    highest_hazard_score: float = 0.0
    active_hazards_count: int = 0
    critical_hazards_count: int = 0
    recommendations: Optional[List[str]] = None
    reasoning: Optional[List[str]] = None
    calculated_by: str
    notes: Optional[str] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Phase 1.2 Risk Analysis Schemas ────────────────────────────────────────

class SiteRiskAnalysisInput(BaseModel):
    site_id: str
    weather_condition: Optional[str] = "Clear"
    temperature: Optional[float] = 25.0
    wind_speed: Optional[float] = 10.0
    water_accumulation: Optional[bool] = False
    site_conditions: Optional[str] = None
    activities: Optional[List[str]] = None
    equipment_ids: Optional[List[str]] = None
    worker_count: Optional[int] = None
    fire_protection_adequate: Optional[bool] = True
    scaffolding_inspected: Optional[bool] = True
    safety_controls_adequate: Optional[bool] = True

class CategoryRiskScore(BaseModel):
    score: float
    level: RiskCategory
    explanation: str

class DetectedHazardDetail(BaseModel):
    id: Optional[str] = None
    hazard_id: Optional[str] = None
    site_id: Optional[str] = None
    type: str
    description: str
    evidence: str
    severity: int
    probability: int
    risk_score: float
    risk_level: RiskCategory
    recommended_action: str
    detection_source: str = "RULE_ENGINE"
    status: str = "open"

class SiteRiskAnalysisResponse(BaseModel):
    site_id: str
    site_name: Optional[str] = None
    timestamp: datetime
    overall_risk_score: float
    risk_level: RiskCategory
    highest_hazard_score: float
    active_hazards_count: int
    critical_hazards_count: int
    categories: dict[str, CategoryRiskScore]
    hazards: List[DetectedHazardDetail]
    recommendations: List[str]
    reasoning: List[str]
    detection_source: str = "RULE_ENGINE"

class HazardMitigateRequest(BaseModel):
    mitigation_notes: str

class DemoScenarioRequest(BaseModel):
    scenario_id: int  # 1 to 5
    site_id: str


# ── Inspection Schemas ─────────────────────────────────────────────────────

class InspectionCreate(BaseModel):
    site_id: str
    inspector_name: Optional[str] = None
    date: datetime
    result: Optional[str] = None
    findings: Optional[str] = None
    notes: Optional[str] = None

class InspectionOut(BaseModel):
    id: str
    inspection_id: str
    site_id: str
    site_name: Optional[str] = None
    inspector_name: Optional[str] = None
    date: datetime
    result: Optional[str] = None
    findings: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Notification Schemas ───────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    category: NotificationCategory
    title: str
    message: str
    severity: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Dashboard Schemas ──────────────────────────────────────────────────────

class DashboardKPI(BaseModel):
    overall_risk_score: float
    risk_category: RiskCategory
    active_hazards: int
    safety_observations: int
    open_incidents: int
    compliance_status: float
    site_monitoring: str
    total_sites: int
    total_projects: int
    total_workers: int
    total_equipment: int

class RiskBreakdown(BaseModel):
    environmental_risk: float
    equipment_risk: float
    site_condition_risk: float
    operational_risk: float
    overall_risk: float
    category: RiskCategory


# ── Safety Schemas (Phase 2.1) ──────────────────────────────────────────────

class SafetyFindingOut(BaseModel):
    id: str
    finding_id: str
    site_id: str
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    worker_code: Optional[str] = None
    analysis_id: Optional[str] = None
    finding_type: SafetyFindingType
    description: str
    evidence: Optional[str] = None
    severity: RiskCategory
    status: SafetyFindingStatus
    recommendation: Optional[str] = None
    detection_source: str = "RULE_ENGINE"
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    mitigated_at: Optional[datetime] = None
    mitigated_by: Optional[str] = None
    mitigation_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SafetyFindingUpdate(BaseModel):
    status: Optional[SafetyFindingStatus] = None
    mitigation_notes: Optional[str] = None


class SafetyFindingMitigateRequest(BaseModel):
    mitigation_notes: str


class SafetyAnalysisOut(BaseModel):
    id: str
    analysis_id: str
    site_id: str
    site_name: Optional[str] = None
    worker_id: Optional[str] = None
    overall_safety_score: float
    safety_level: RiskCategory
    workers_analyzed: int
    violation_count: int
    high_count: int
    critical_count: int
    detection_source: str
    summary: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyAnalysisResponse(BaseModel):
    id: Optional[str] = None
    analysis_id: Optional[str] = None
    site_id: str
    site_name: Optional[str] = None
    timestamp: str
    overall_safety_score: float
    safety_level: RiskCategory
    workers_analyzed: int
    violation_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[SafetyFindingOut]
    summary: Optional[Any] = None
    detection_source: str = "RULE_ENGINE"


class SafetyAnalyzeSiteRequest(BaseModel):
    site_id: str
    worker_id: Optional[str] = None


class SafetyDemoScenarioRequest(BaseModel):
    site_id: str
    scenario_id: int


class SafetyDemoScenarioOut(BaseModel):
    id: int
    name: str
    description: str
    expected_level: str
    expected_violations: int


# ── Phase 2.2 Computer Vision PPE Schemas ─────────────────────────────────

class BoundingBox(BaseModel):
    x: float          # Left coord (pixels or normalized)
    y: float          # Top coord (pixels or normalized)
    width: float      # Box width
    height: float     # Box height


class PPEDetectionItem(BaseModel):
    detection_id: str
    ppe_class: PPEClass
    confidence: float
    bounding_box: BoundingBox
    status: str = "DETECTED"          # DETECTED | LOW_CONFIDENCE | MISSING
    is_compliant: bool = True
    person_id: Optional[str] = None
    detection_source: str = "COMPUTER_VISION"
    timestamp: Optional[str] = None


class PersonPPEDetection(BaseModel):
    person_id: str
    bounding_box: BoundingBox
    confidence: float
    detected_ppe: List[PPEDetectionItem] = []
    missing_ppe: List[str] = []
    is_compliant: bool = False
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None


class PPECrossVerificationResult(BaseModel):
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    db_ppe_status: Optional[str] = None
    cv_compliance: PPEComplianceStatus
    has_discrepancy: bool = False
    discrepancy_details: Optional[str] = None


class PPEAnalysisOut(BaseModel):
    id: str
    analysis_id: str
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    image_filename: str
    image_url: str
    image_width: int
    image_height: int
    overall_compliance: PPEComplianceStatus
    compliance_score: float
    total_persons_detected: int
    detected_ppe: List[PPEDetectionItem]
    missing_ppe: List[str]
    detections: List[PPEDetectionItem]
    persons: List[PersonPPEDetection] = []
    cross_verification: Optional[PPECrossVerificationResult] = None
    confidence_threshold: float
    detection_source: str
    model_name: str
    recommendations: List[str] = []
    findings: List[SafetyFindingOut] = []
    summary: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PPEDemoScenarioOut(BaseModel):
    id: int
    name: str
    description: str
    expected_compliance: PPEComplianceStatus
    expected_findings_count: int
    detected_items: List[str]
    missing_items: List[str]


# ── Worker Safety Monitoring Schemas (Phase 2.3) ───────────────────────────

class WorkerMonitoringInput(BaseModel):
    worker_id: str
    site_id: Optional[str] = None
    current_activity: Optional[str] = None
    current_zone: Optional[str] = None
    is_high_risk_zone: bool = False
    time_in_zone_minutes: int = 0
    nearby_hazards: List[str] = []
    nearby_equipment: List[str] = []
    workers_in_zone_count: int = 1
    ppe_items_worn: Optional[List[str]] = None
    is_simulation: bool = False


class WorkerMonitoringFindingOut(BaseModel):
    rule_name: str
    finding_type: str
    severity: RiskCategory
    description: str
    evidence: str
    recommendation: Optional[str] = None


class WorkerMonitoringEvaluationOut(BaseModel):
    worker_id: str
    worker_name: str
    site_id: str
    site_name: Optional[str] = None
    safety_status: WorkerSafetyStatus
    current_activity: str
    current_zone: str
    time_in_zone_minutes: int
    is_high_risk_zone: bool
    ppe_status: str
    training_status: str
    workers_in_zone_count: int
    findings: List[WorkerMonitoringFindingOut] = []
    recommendations: List[str] = []
    detection_source: str = "WORKER_MONITORING_ENGINE"
    evaluated_at: datetime
    is_simulation: bool = False


class SafetyMonitoringEventOut(BaseModel):
    id: str
    event_id: str
    site_id: str
    worker_id: str
    worker_name: Optional[str] = None
    activity_name: Optional[str] = None
    zone_name: Optional[str] = None
    time_in_zone_minutes: int = 0
    event_type: str
    severity: RiskCategory
    worker_safety_status: WorkerSafetyStatus
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    detection_source: str
    is_simulation: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SiteMonitoringStatusOut(BaseModel):
    site_id: str
    site_name: str
    is_monitoring_active: bool
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    monitored_workers_count: int = 0
    active_warnings_count: int = 0
    active_high_risk_count: int = 0
    active_critical_count: int = 0
    recent_events: List[SafetyMonitoringEventOut] = []


class MonitoringDemoScenarioOut(BaseModel):
    id: int
    name: str
    description: str
    expected_status: WorkerSafetyStatus
    expected_findings_count: int
    context_summary: dict


# ── Phase 2.4 Safety Alert System Schemas ──────────────────────────────────

class AlertNotificationOut(BaseModel):
    id: str
    alert_id: str
    channel: NotificationChannel
    recipient_role: str
    recipient_user_id: Optional[str] = None
    title: str
    message: str
    status: str = "DELIVERED"
    delivery_details: Optional[Any] = None
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertAuditEventOut(BaseModel):
    id: str
    alert_id: str
    event_type: AlertAuditEventType
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyAlertOut(BaseModel):
    id: str
    alert_id: str
    site_id: str
    site_name: Optional[str] = None
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    finding_id: Optional[str] = None
    source_type: str
    source_id: Optional[str] = None
    severity: AlertSeverity
    priority: AlertPriority
    status: AlertStatus
    title: str
    description: str
    recommendation: Optional[str] = None
    evidence: Optional[str] = None
    escalation_level: int = 0
    escalation_timeout_minutes: int = 30
    assigned_role: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    escalated_at: Optional[datetime] = None
    is_simulation: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyAlertDetailOut(SafetyAlertOut):
    notifications: List[AlertNotificationOut] = []
    audit_events: List[AlertAuditEventOut] = []


class AlertAcknowledgeIn(BaseModel):
    notes: Optional[str] = None


class AlertResolveIn(BaseModel):
    notes: str


class AlertEscalateIn(BaseModel):
    reason: Optional[str] = None
    target_role: Optional[str] = None


class AlertCreateIn(BaseModel):
    site_id: str
    worker_id: Optional[str] = None
    finding_id: Optional[str] = None
    source_type: str = "SAFETY_FINDING"
    source_id: Optional[str] = None
    severity: AlertSeverity
    priority: Optional[AlertPriority] = None
    title: str
    description: str
    recommendation: Optional[str] = None
    evidence: Optional[str] = None


class AlertDemoScenarioOut(BaseModel):
    id: int
    name: str
    description: str
    expected_severity: AlertSeverity
    expected_status: AlertStatus
    summary: str


class AlertDemoScenarioRequest(BaseModel):
    scenario_id: int
    site_id: Optional[str] = None


# ── Phase 3.1 Real-Time Video Surveillance Schemas ─────────────────────────

class CameraZoneCreate(BaseModel):
    site_id: str
    name: str
    zone_type: ZoneType = ZoneType.GENERAL
    boundary: Optional[Any] = None
    risk_level: RiskCategory = RiskCategory.LOW
    max_capacity: int = 5


class CameraZoneOut(BaseModel):
    id: str
    zone_id: str
    site_id: str
    name: str
    zone_type: ZoneType
    boundary: Optional[Any] = None
    risk_level: RiskCategory
    max_capacity: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoStreamStartRequest(BaseModel):
    site_id: str
    camera_name: Optional[str] = "Main Site Camera 1"
    source_type: Optional[VideoSourceType] = VideoSourceType.DEMO
    source_url: Optional[str] = None
    fps: Optional[float] = 15.0
    sampling_interval_frames: Optional[int] = 5
    confidence_threshold: Optional[float] = 0.65


class VideoStreamOut(BaseModel):
    id: str
    stream_id: str
    site_id: str
    site_name: Optional[str] = None
    camera_name: str
    source_type: VideoSourceType
    source_url: Optional[str] = None
    status: StreamStatus
    fps: float
    resolution_width: int
    resolution_height: int
    sampling_interval_frames: int
    confidence_threshold: float
    total_frames_ingested: int
    processed_frames_count: int
    dropped_frames_count: int
    started_at: datetime
    stopped_at: Optional[datetime] = None
    created_by: Optional[str] = None
    is_simulation: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoEventOut(BaseModel):
    id: str
    event_id: str
    stream_id: str
    site_id: str
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    finding_id: Optional[str] = None
    alert_id: Optional[str] = None
    event_type: VideoEventType
    severity: RiskCategory
    description: str
    evidence: Optional[str] = None
    zone_name: Optional[str] = None
    bounding_box: Optional[Any] = None
    detected_ppe: Optional[List[Any]] = []
    missing_ppe: Optional[List[str]] = []
    detection_source: str = "DEMO / SIMULATION"
    is_simulation: bool = True
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoProcessFrameRequest(BaseModel):
    frame_number: Optional[int] = None
    image_base64: Optional[str] = None
    scenario_id: Optional[int] = None
    metadata: Optional[dict] = None


class VideoProcessFrameOut(BaseModel):
    stream_id: str
    frame_number: int
    status: str
    detected_persons_count: int
    compliant_count: int
    violations_count: int
    events: List[VideoEventOut] = []
    findings_created: int = 0
    alerts_created: int = 0
    detection_source: str
    is_simulation: bool


class VideoLiveStatusOut(BaseModel):
    site_id: str
    site_name: Optional[str] = None
    active_streams_count: int
    streams: List[VideoStreamOut] = []
    detected_personnel_count: int
    compliant_workers_count: int
    ppe_compliance_rate: float
    active_high_alerts_count: int
    active_critical_alerts_count: int
    recent_events: List[VideoEventOut] = []
    active_zones: List[CameraZoneOut] = []


class VideoDemoScenarioOut(BaseModel):
    id: int
    name: str
    description: str
    expected_violations: int
    expected_severity: Optional[str] = None
    summary: str


class VideoDemoScenarioRequest(BaseModel):
    scenario_id: int
    site_id: Optional[str] = None


# ── Milestone 3 Compliance Schemas ───────────────────────────────────────────

class ComplianceRuleOut(BaseModel):
    id: str
    rule_id: str
    standard_ref: str
    title: str
    category: ComplianceRuleCategory
    requirement: str
    applicable_activity: Optional[str] = None
    applicable_zone: Optional[str] = None
    severity: RiskCategory
    remediation_recommendation: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectionRequirementOut(BaseModel):
    id: str
    requirement_id: str
    site_id: str
    title: str
    inspection_type: str
    regulatory_reference: Optional[str] = None
    responsible_role: str
    due_date: datetime
    completed_date: Optional[datetime] = None
    status: InspectionRequirementStatus
    is_overdue: bool
    evidence_document_ref: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectionRequirementCreate(BaseModel):
    title: str
    inspection_type: str
    regulatory_reference: Optional[str] = None
    responsible_role: str = "safety_officer"
    due_date: datetime
    notes: Optional[str] = None


class ComplianceFindingOut(BaseModel):
    id: str
    finding_id: str
    site_id: str
    rule_id: Optional[str] = None
    worker_id: Optional[str] = None
    inspection_requirement_id: Optional[str] = None
    standard_ref: str
    violation_type: str
    description: str
    severity: RiskCategory
    evidence: Optional[Any] = None
    recommendation: str
    status: SafetyFindingStatus
    detection_source: str = "COMPLIANCE_AGENT"
    is_simulation: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ComplianceAssessmentOut(BaseModel):
    id: str
    assessment_id: str
    site_id: str
    compliance_score: float
    compliance_status: ComplianceStatus
    total_rules_evaluated: int
    rules_passed: int
    rules_violated: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    total_inspections: int
    overdue_inspections: int
    findings_summary: Optional[List[Any]] = None
    category_scores: Optional[Any] = None
    recommendations: Optional[List[str]] = None
    detection_source: str = "COMPLIANCE_AGENT"
    is_simulation: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceAnalysisRequest(BaseModel):
    is_simulation: Optional[bool] = False
    force_refresh: Optional[bool] = False


class ComplianceDemoScenarioOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    expected_status: str
    expected_violations: int
    narrative: str


class ComplianceDemoScenarioRequest(BaseModel):
    scenario_id: int
    site_id: Optional[str] = None


# ── Milestone 3 Insurance Schemas ────────────────────────────────────────────

class InsuranceRiskAssessmentOut(BaseModel):
    id: str
    assessment_id: str
    site_id: str
    insurance_risk_score: float
    insurance_risk_level: InsuranceRiskLevel
    exposure_index: float
    estimated_liability_exposure: Optional[str] = None
    contributing_factors: Optional[Any] = None
    category_exposures: Optional[Any] = None
    unresolved_findings_count: int
    active_critical_alerts_count: int
    compliance_deficit_penalty: float
    underwriting_recommendations: Optional[List[str]] = None
    is_simulation: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsuranceAnalysisRequest(BaseModel):
    is_simulation: Optional[bool] = False
    force_refresh: Optional[bool] = False


class InsuranceClaimAssessmentOut(BaseModel):
    id: str
    claim_assessment_id: str
    site_id: str
    incident_ref: str
    incident_title: str
    incident_date: datetime
    involved_worker_id: Optional[str] = None
    involved_equipment_id: Optional[str] = None
    incident_severity: RiskCategory
    claim_risk_level: ClaimRiskLevel
    claim_probability_pct: float
    documentation_completeness_pct: float
    potential_claim_indicators: Optional[List[str]] = None
    contributing_safety_factors: Optional[List[str]] = None
    contributing_compliance_factors: Optional[List[str]] = None
    missing_documentation: Optional[List[str]] = None
    status: str
    is_simulation: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimDocumentationPackageOut(BaseModel):
    id: str
    package_id: str
    claim_assessment_id: str
    site_id: str
    title: str
    incident_summary: str
    worker_dossier: Optional[Any] = None
    equipment_dossier: Optional[Any] = None
    safety_findings_dossier: Optional[Any] = None
    compliance_findings_dossier: Optional[Any] = None
    sensor_evidence_dossier: Optional[Any] = None
    missing_required_documents: Optional[List[str]] = None
    recommended_actions: Optional[List[str]] = None
    is_complete: bool
    is_simulation: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimDocumentationRequest(BaseModel):
    incident_ref: Optional[str] = None
    incident_title: Optional[str] = None
    worker_id: Optional[str] = None
    equipment_id: Optional[str] = None
    is_simulation: Optional[bool] = False


class InsuranceDemoScenarioOut(BaseModel):
    id: int
    name: str
    description: str
    expected_risk_level: str
    expected_score_range: str
    narrative: str


class InsuranceDemoScenarioRequest(BaseModel):
    scenario_id: int
    site_id: Optional[str] = None


# ── Milestone 4 Phase 4.1 Reporting Agent Schemas ──────────────────────────

class ReportGenerateRequest(BaseModel):
    site_id: str
    report_type: ReportType = ReportType.DAILY_SITE
    title: Optional[str] = None
    reporting_period_start: Optional[datetime] = None
    reporting_period_end: Optional[datetime] = None


class GeneratedReportSummaryOut(BaseModel):
    id: str
    report_id: str
    site_id: Optional[str] = None
    project_id: Optional[str] = None
    report_type: ReportType
    title: str
    reporting_period_start: Optional[datetime] = None
    reporting_period_end: Optional[datetime] = None
    generated_at: datetime
    status: ReportStatus
    summary: Optional[str] = None
    created_by: Optional[str] = None
    metrics: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class GeneratedReportOut(GeneratedReportSummaryOut):
    content: Any


class ReportTypeInfoOut(BaseModel):
    type: str
    name: str
    description: str
    target_audience: str
    frequency: str


# ── Milestone 4 Phase 4.2 Construction Risk Intelligence Engine Schemas ────

class RiskIntelligenceAnalysisRequest(BaseModel):
    site_id: str
    project_id: Optional[str] = None
    analysis_window_days: Optional[int] = 30
    include_predictions: Optional[bool] = True
    include_patterns: Optional[bool] = True
    include_recommendations: Optional[bool] = True


class CategoryRiskBreakdownOut(BaseModel):
    site_risk_score: float
    safety_risk_score: float
    compliance_risk_score: float
    insurance_risk_score: float
    weights: dict[str, float]


class RecurringPatternOut(BaseModel):
    pattern_id: str
    category: str
    pattern_type: str
    pattern_description: str
    occurrence_count: int
    first_observed: Optional[str] = None
    last_observed: Optional[str] = None
    time_window_hours: int
    severity: str
    velocity: str
    locations: List[str] = []
    sample_finding_ids: List[str] = []


class IncidentLeadingIndicatorOut(BaseModel):
    indicator: str
    severity: str
    observed_value: str


class PotentialIncidentPredictionOut(BaseModel):
    prediction_id: str
    incident_type: str
    probability_score: float
    severity_potential: str
    predicted_timeframe: str
    primary_driver: str
    causal_chain: List[str] = []
    leading_indicators: List[IncidentLeadingIndicatorOut] = []
    recommended_interventions: List[str] = []


class OperationalRecommendationOut(BaseModel):
    recommendation_id: str
    category: str
    priority: str
    timeframe: str
    title: str
    action_items: List[str] = []
    expected_risk_reduction: str
    target_hazard_types: List[str] = []
    cost_impact_level: str


class RiskIntelligenceAssessmentOut(BaseModel):
    id: str
    assessment_id: str
    project_id: Optional[str] = None
    site_id: str
    overall_risk_score: float
    risk_level: str
    category_scores: Optional[Any] = None
    recurring_patterns: Optional[Any] = None
    predicted_incidents: Optional[Any] = None
    recommendations: Optional[Any] = None
    findings_count: int
    critical_findings_count: int
    high_findings_count: int
    medium_findings_count: int
    low_findings_count: int
    assessed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("category_scores", mode="before")
    @classmethod
    def normalize_category_scores(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            return v
        scores = dict(v)
        for key in ["site_risk", "safety_risk", "compliance_risk", "insurance_risk"]:
            score_key = f"{key}_score"
            if score_key not in scores or scores[score_key] is None:
                pillar_val = scores.get(key)
                if isinstance(pillar_val, dict):
                    scores[score_key] = float(pillar_val.get("score", 0.0))
                elif isinstance(pillar_val, (int, float)):
                    scores[score_key] = float(pillar_val)
                else:
                    scores[score_key] = 0.0
        if "weights" not in scores or not isinstance(scores["weights"], dict):
            scores["weights"] = {
                "site_risk": 0.3,
                "safety_risk": 0.3,
                "compliance_risk": 0.2,
                "insurance_risk": 0.2,
            }
        return scores


# ── Milestone 4 Phase 4.3 Executive Project Dashboard Schemas ───────────────

class ExecutiveDashboardSiteInfo(BaseModel):
    site_id: str
    site_name: str
    site_code: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    status: str
    location: Optional[str] = None
    manager: Optional[str] = None


class ExecutiveDashboardAssessment(BaseModel):
    assessment_id: Optional[str] = None
    generated_at: Optional[datetime] = None
    overall_risk_score: float
    overall_risk_level: str
    scoring_explanation: Optional[str] = None
    category_scores: Optional[Dict[str, Any]] = None
    data_quality: Optional[Dict[str, Any]] = None


class ExecutiveDashboardHealth(BaseModel):
    health_status: str  # "HEALTHY" | "MODERATE_RISK" | "ELEVATED" | "CRITICAL_ACTION_REQUIRED"
    health_score: float  # 0 to 100 (100 = best health)
    total_active_findings: int
    critical_findings_count: int
    high_findings_count: int
    unresolved_issues_count: int
    active_safety_alerts_count: int
    compliance_violations_count: int
    overdue_inspections_count: int
    insurance_exposure_index: float
    open_insurance_claims_count: int
    active_workers_count: int
    active_equipment_count: int


class ExecutiveCriticalFinding(BaseModel):
    id: str
    finding_id: str
    source_agent: str  # "site_risk" | "safety" | "compliance" | "insurance"
    category: str
    severity: str
    risk_score: float
    title: str
    description: str
    location: Optional[str] = None
    status: str
    detected_at: Optional[datetime] = None
    evidence: Optional[str] = None
    navigation_url: Optional[str] = None


class ExecutiveSafetySnapshot(BaseModel):
    safety_score: float
    ppe_compliance_rate: float
    active_workers_count: int
    active_alerts_count: int
    critical_findings_count: int
    last_assessment_date: Optional[datetime] = None
    status: str


class ExecutiveComplianceSnapshot(BaseModel):
    compliance_score: float
    compliance_status: str
    total_rules_evaluated: int
    rules_passed: int
    rules_violated: int
    critical_violations_count: int
    overdue_inspections_count: int
    last_assessment_date: Optional[datetime] = None


class ExecutiveInsuranceSnapshot(BaseModel):
    insurance_risk_score: float
    insurance_risk_level: str
    exposure_index: float
    estimated_liability_exposure: Optional[str] = None
    unresolved_findings_count: int
    active_claims_count: int
    underwriting_recommendations: List[str] = []
    last_assessment_date: Optional[datetime] = None


class ExecutiveDashboardResponse(BaseModel):
    site: ExecutiveDashboardSiteInfo
    assessment: Optional[ExecutiveDashboardAssessment] = None
    health: ExecutiveDashboardHealth
    pillar_scores: Dict[str, Any]
    critical_findings: List[ExecutiveCriticalFinding] = []
    recurring_patterns: List[RecurringPatternOut] = []
    potential_incidents: List[PotentialIncidentPredictionOut] = []
    recommendations: List[OperationalRecommendationOut] = []
    safety_summary: ExecutiveSafetySnapshot
    compliance_summary: ExecutiveComplianceSnapshot
    insurance_summary: ExecutiveInsuranceSnapshot
    recent_reports: List[GeneratedReportSummaryOut] = []
    history: List[Any] = []
    last_analysis_time: Optional[datetime] = None
    data_freshness: str = "LIVE"


# ── Milestone 4 Phase 4.4 Agent Orchestration Schemas ─────────────────────

class AgentExecutionStatus(BaseModel):
    agent_name: str
    status: str
    duration_ms: float = 0.0
    error: Optional[str] = None
    message: Optional[str] = None
    output_summary: Optional[Dict[str, Any]] = None


class OrchestrationRequest(BaseModel):
    site_id: str
    project_id: Optional[str] = None
    agents: Optional[List[str]] = None
    mode: Optional[str] = "FULL_ANALYSIS"
    generate_report: Optional[bool] = False
    report_type: Optional[ReportType] = ReportType.EXECUTIVE_SUMMARY
    is_simulation: Optional[bool] = False


class OrchestrationRunResponse(BaseModel):
    id: str
    execution_id: str
    site_id: str
    project_id: Optional[str] = None
    status: str
    execution_mode: str
    requested_agents: List[str] = []
    agent_statuses: Dict[str, Any] = {}
    risk_intelligence_id: Optional[str] = None
    report_id: Optional[str] = None
    duration_ms: float = 0.0
    warnings: List[str] = []
    errors: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrchestrationHistoryResponse(BaseModel):
    runs: List[OrchestrationRunResponse]
    total: int
