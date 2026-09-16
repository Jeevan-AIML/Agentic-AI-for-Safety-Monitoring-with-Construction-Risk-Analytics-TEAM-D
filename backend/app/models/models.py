import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey,
    Integer, Float, Text, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database.session import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    PROJECT_MANAGER = "project_manager"
    SITE_MANAGER = "site_manager"
    SAFETY_OFFICER = "safety_officer"
    VIEWER = "viewer"


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class SiteStatus(str, enum.Enum):
    ACTIVE = "active"
    MONITORING = "monitoring"
    WARNING = "warning"
    CRITICAL = "critical"
    INACTIVE = "inactive"


class WorkerRole(str, enum.Enum):
    OPERATOR = "operator"
    ELECTRICIAN = "electrician"
    MASON = "mason"
    SUPERVISOR = "supervisor"
    WELDER = "welder"
    TECHNICIAN = "technician"
    GENERAL_WORKER = "general_worker"


class SafetyTrainingStatus(str, enum.Enum):
    CERTIFIED = "certified"
    IN_PROGRESS = "in_progress"
    EXPIRED = "expired"
    NOT_STARTED = "not_started"


class PPEStatus(str, enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"


class EquipmentStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    INSPECTION_DUE = "inspection_due"


class ActivityType(str, enum.Enum):
    EXCAVATION = "excavation"
    CONCRETE_WORK = "concrete_work"
    WELDING = "welding"
    ELECTRICAL_WORK = "electrical_work"
    MATERIAL_HANDLING = "material_handling"
    DEMOLITION = "demolition"
    SCAFFOLDING = "scaffolding"
    GENERAL_CONSTRUCTION = "general_construction"


class HazardType(str, enum.Enum):
    ENVIRONMENTAL = "environmental"
    EQUIPMENT = "equipment"
    STRUCTURAL = "structural"
    ELECTRICAL = "electrical"
    FIRE = "fire"
    FALL = "fall"
    EXCAVATION = "excavation"
    MATERIAL_HANDLING = "material_handling"
    OTHER = "other"


class HazardStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    MITIGATED = "mitigated"
    CLOSED = "closed"


class RiskCategory(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationCategory(str, enum.Enum):
    RISK = "risk"
    SAFETY = "safety"
    COMPLIANCE = "compliance"
    SYSTEM = "system"


class SafetyFindingStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    MITIGATED = "mitigated"
    CLOSED = "closed"


class PPEClass(str, enum.Enum):
    HARD_HAT = "HARD_HAT"
    SAFETY_VEST = "SAFETY_VEST"
    SAFETY_GOGGLES = "SAFETY_GOGGLES"
    GLOVES = "GLOVES"
    SAFETY_SHOES = "SAFETY_SHOES"
    HARNESS = "HARNESS"
    HEARING_PROTECTION = "HEARING_PROTECTION"
    RESPIRATORY_PROTECTION = "RESPIRATORY_PROTECTION"


class PPEComplianceStatus(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    UNCERTAIN = "UNCERTAIN"


class SafetyFindingType(str, enum.Enum):
    PPE_VIOLATION = "ppe_violation"
    PPE_DISCREPANCY = "ppe_discrepancy"
    EXPIRED_TRAINING = "expired_training"
    MISSING_TRAINING = "missing_training"
    UNSAFE_EQUIPMENT_OPERATION = "unsafe_equipment_operation"
    HIGH_RISK_ACTIVITY = "high_risk_activity"
    HIGH_RISK_ZONE_EXPOSURE = "high_risk_zone_exposure"
    TIME_IN_ZONE_EXCEEDED = "time_in_zone_exceeded"
    HAZARD_PROXIMITY = "hazard_proximity"
    EQUIPMENT_PROXIMITY = "equipment_proximity"
    OVERCROWDED_ZONE = "overcrowded_zone"
    UNSAFE_WORKER_EQUIPMENT_INTERACTION = "unsafe_worker_equipment_interaction"
    # Phase 3.2 Aerial findings
    AERIAL_HAZARD = "aerial_hazard"
    UNPROTECTED_EXCAVATION = "unprotected_excavation"
    RESTRICTED_ZONE_INTRUSION = "restricted_zone_intrusion"
    UNSAFE_EQUIPMENT_PLACEMENT = "unsafe_equipment_placement"
    MATERIAL_OBSTRUCTION = "material_obstruction"
    SCAFFOLDING_HAZARD = "scaffolding_hazard"
    WORKER_CONCENTRATION = "worker_concentration"
    # Phase 3.3 Multi-Modal Risk
    MULTI_MODAL_RISK = "multi_modal_risk"
    CORRELATED_HAZARD = "correlated_hazard"
    # Milestone 3 Compliance & Insurance
    REGULATORY_VIOLATION = "regulatory_violation"
    INSPECTION_OVERDUE = "inspection_overdue"
    INSURANCE_EXPOSURE = "insurance_exposure"


class WorkerSafetyStatus(str, enum.Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"


class AlertSeverity(str, enum.Enum):
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL_ADAPTER = "email_adapter"
    PUSH_ADAPTER = "push_adapter"


class AlertAuditEventType(str, enum.Enum):
    ALERT_CREATED = "alert_created"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_ESCALATED = "alert_escalated"
    ALERT_RESOLVED = "alert_resolved"
    ALERT_DISMISSED = "alert_dismissed"


class StreamStatus(str, enum.Enum):
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


class VideoSourceType(str, enum.Enum):
    DEMO = "demo"
    LOCAL = "local"
    RTSP = "rtsp"


class VideoEventType(str, enum.Enum):
    PERSON_DETECTED = "person_detected"
    PPE_VIOLATION = "ppe_violation"
    HIGH_RISK_ZONE_ENTRY = "high_risk_zone_entry"
    HAZARD_PROXIMITY = "hazard_proximity"
    EQUIPMENT_PROXIMITY = "equipment_proximity"
    OVERCROWDED_ZONE = "overcrowded_zone"
    UNSAFE_INTERACTION = "unsafe_interaction"


class ZoneType(str, enum.Enum):
    SAFE_AREA = "safe_area"
    EXCAVATION = "excavation"
    HEAVY_EQUIPMENT = "heavy_equipment"
    RESTRICTED = "restricted"
    ELECTRICAL = "electrical"
    GENERAL = "general"


# ── Models ─────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    assigned_site_id = Column(String(36), ForeignKey("sites.id"), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    managed_projects = relationship("Project", back_populates="manager", foreign_keys="Project.manager_id")
    managed_sites = relationship("Site", back_populates="manager", foreign_keys="Site.manager_id")
    notifications = relationship("Notification", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    client = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    expected_completion = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.PLANNING)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    # Location
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manager = relationship("User", back_populates="managed_projects", foreign_keys=[manager_id])
    sites = relationship("Site", back_populates="project")


class Site(Base):
    __tablename__ = "sites"

    id = Column(String(36), primary_key=True)
    site_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    site_type = Column(String(100), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(SAEnum(SiteStatus), default=SiteStatus.ACTIVE)
    current_risk_score = Column(Float, default=0.0)
    risk_category = Column(SAEnum(RiskCategory), default=RiskCategory.LOW)
    # Location
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    # Counts
    worker_count = Column(Integer, default=0)
    equipment_count = Column(Integer, default=0)
    # Dates
    last_inspection = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="sites")
    manager = relationship("User", back_populates="managed_sites", foreign_keys=[manager_id])
    workers = relationship("Worker", back_populates="site")
    equipment = relationship("Equipment", back_populates="site")
    activities = relationship("Activity", back_populates="site")
    hazards = relationship("Hazard", back_populates="site")
    risk_scores = relationship("RiskScore", back_populates="site")
    inspections = relationship("Inspection", back_populates="site")
    safety_findings = relationship("SafetyFinding", back_populates="site", cascade="all, delete-orphan")
    safety_analyses = relationship("SafetyAnalysis", back_populates="site", cascade="all, delete-orphan")
    ppe_analyses = relationship("PPEAnalysis", back_populates="site", cascade="all, delete-orphan")
    video_streams = relationship("VideoStream", back_populates="site", cascade="all, delete-orphan")
    camera_zones = relationship("CameraZone", back_populates="site", cascade="all, delete-orphan")
    compliance_assessments = relationship("ComplianceAssessment", back_populates="site", cascade="all, delete-orphan")
    compliance_findings = relationship("ComplianceFinding", back_populates="site", cascade="all, delete-orphan")
    inspection_requirements = relationship("InspectionRequirement", back_populates="site", cascade="all, delete-orphan")
    insurance_assessments = relationship("InsuranceRiskAssessment", back_populates="site", cascade="all, delete-orphan")
    insurance_claims = relationship("InsuranceClaimAssessment", back_populates="site", cascade="all, delete-orphan")
    claim_packages = relationship("ClaimDocumentationPackage", back_populates="site", cascade="all, delete-orphan")


class Worker(Base):
    __tablename__ = "workers"

    id = Column(String(36), primary_key=True)
    worker_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SAEnum(WorkerRole), nullable=False)
    department = Column(String(100), nullable=True)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=True)
    contact = Column(String(100), nullable=True)
    joining_date = Column(DateTime, nullable=True)
    safety_training = Column(SAEnum(SafetyTrainingStatus), default=SafetyTrainingStatus.NOT_STARTED)
    ppe_status = Column(SAEnum(PPEStatus), default=PPEStatus.NON_COMPLIANT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    site = relationship("Site", back_populates="workers")
    safety_findings = relationship("SafetyFinding", back_populates="worker")
    ppe_analyses = relationship("PPEAnalysis", back_populates="worker")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(String(36), primary_key=True)
    equipment_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    equipment_type = Column(String(100), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=True)
    operator_name = Column(String(255), nullable=True)
    status = Column(SAEnum(EquipmentStatus), default=EquipmentStatus.OPERATIONAL)
    last_inspection = Column(DateTime, nullable=True)
    maintenance_due = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    site = relationship("Site", back_populates="equipment")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(String(36), primary_key=True)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=False)
    activity_type = Column(SAEnum(ActivityType), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    start_time = Column(String(10), nullable=True)
    end_time = Column(String(10), nullable=True)
    workers_involved = Column(Integer, default=0)
    equipment_used = Column(JSON, nullable=True)
    environmental_conditions = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="activities")


class Hazard(Base):
    __tablename__ = "hazards"

    id = Column(String(36), primary_key=True)
    hazard_id = Column(String(50), unique=True, nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=False)
    hazard_type = Column(SAEnum(HazardType), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # Detection reason / evidence
    severity = Column(Integer, nullable=False)  # 1-5
    probability = Column(Integer, nullable=False)  # 1-5
    risk_score = Column(Float, nullable=False)  # 0-100
    risk_category = Column(SAEnum(RiskCategory), nullable=False)
    status = Column(SAEnum(HazardStatus), default=HazardStatus.OPEN)
    detected_at = Column(DateTime, default=datetime.utcnow)
    reported_by = Column(String(255), nullable=True)
    recommended_action = Column(Text, nullable=True)
    # Agent metadata
    detection_source = Column(String(50), default="RULE_ENGINE")  # RULE_ENGINE | MANUAL | AI_MODEL | FUTURE_AI
    detected_by_agent = Column(Boolean, default=False)
    agent_confidence = Column(Float, nullable=True)
    # Lifecycle tracking
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), nullable=True)
    mitigated_at = Column(DateTime, nullable=True)
    mitigated_by = Column(String(36), nullable=True)
    mitigation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    site = relationship("Site", back_populates="hazards")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    category = Column(SAEnum(RiskCategory), nullable=False)
    environmental_risk = Column(Float, default=0.0)
    equipment_risk = Column(Float, default=0.0)
    activity_risk = Column(Float, default=0.0)
    site_condition_risk = Column(Float, default=0.0)
    operational_risk = Column(Float, default=0.0)
    highest_hazard_score = Column(Float, default=0.0)
    active_hazards_count = Column(Integer, default=0)
    critical_hazards_count = Column(Integer, default=0)
    recommendations = Column(JSON, nullable=True)  # List of actionable recommendation strings
    reasoning = Column(JSON, nullable=True)  # List of auditability explanation bullet points
    # Source of the risk score
    calculated_by = Column(String(100), default="manual")  # "manual" | "site_risk_agent" | "demo_scenario"
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="risk_scores")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True)
    inspection_id = Column(String(50), unique=True, nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id"), nullable=False)
    inspector_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    inspector_name = Column(String(255), nullable=True)
    date = Column(DateTime, nullable=False)
    result = Column(String(50), nullable=True)  # Pass / Fail / Conditional
    findings = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="inspections")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # None = broadcast
    category = Column(SAEnum(NotificationCategory), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info | warning | error | critical
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class SafetyAnalysis(Base):
    __tablename__ = "safety_analyses"

    id = Column(String(36), primary_key=True)
    analysis_id = Column(String(50), unique=True, nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String(36), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    overall_safety_score = Column(Float, default=100.0)  # 0-100 (100 is best, lower = more safety violations)
    safety_level = Column(SAEnum(RiskCategory), default=RiskCategory.LOW)
    workers_analyzed = Column(Integer, default=0)
    violation_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    detection_source = Column(String(50), default="RULE_ENGINE")
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="safety_analyses")
    worker = relationship("Worker")
    findings = relationship("SafetyFinding", back_populates="analysis", cascade="all, delete-orphan")


class SafetyFinding(Base):
    __tablename__ = "safety_findings"

    id = Column(String(36), primary_key=True)
    finding_id = Column(String(50), unique=True, nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String(36), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    analysis_id = Column(String(36), ForeignKey("safety_analyses.id", ondelete="SET NULL"), nullable=True)
    finding_type = Column(SAEnum(SafetyFindingType), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    severity = Column(SAEnum(RiskCategory), nullable=False, default=RiskCategory.MEDIUM)
    status = Column(SAEnum(SafetyFindingStatus), default=SafetyFindingStatus.OPEN)
    recommendation = Column(Text, nullable=True)
    detection_source = Column(String(50), default="RULE_ENGINE")
    compliance_finding_id = Column(String(36), ForeignKey("compliance_findings.id", ondelete="SET NULL"), nullable=True)
    # Lifecycle tracking
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), nullable=True)
    mitigated_at = Column(DateTime, nullable=True)
    mitigated_by = Column(String(36), nullable=True)
    mitigation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="safety_findings")
    worker = relationship("Worker", back_populates="safety_findings")
    analysis = relationship("SafetyAnalysis", back_populates="findings")
    compliance_finding = relationship("ComplianceFinding", back_populates="safety_finding", foreign_keys=[compliance_finding_id])


class PPEAnalysis(Base):
    __tablename__ = "ppe_analyses"

    id = Column(String(36), primary_key=True)
    analysis_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    worker_id = Column(String(36), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    image_filename = Column(String(255), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_width = Column(Integer, default=0)
    image_height = Column(Integer, default=0)
    overall_compliance = Column(SAEnum(PPEComplianceStatus), default=PPEComplianceStatus.NON_COMPLIANT)
    compliance_score = Column(Float, default=0.0)
    total_persons_detected = Column(Integer, default=0)
    detected_ppe = Column(JSON, default=list)
    missing_ppe = Column(JSON, default=list)
    detections = Column(JSON, default=list)
    cross_verification = Column(JSON, nullable=True)
    confidence_threshold = Column(Float, default=0.65)
    detection_source = Column(String(50), default="COMPUTER_VISION")
    model_name = Column(String(100), default="OpenCV-HOG-PPE-v1.0")
    summary = Column(JSON, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="ppe_analyses")
    worker = relationship("Worker", back_populates="ppe_analyses")
    creator = relationship("User")


class SafetyMonitoringEvent(Base):
    __tablename__ = "safety_monitoring_events"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String(36), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    activity_name = Column(String(100), nullable=True)
    zone_name = Column(String(100), nullable=True)
    time_in_zone_minutes = Column(Integer, default=0)
    event_type = Column(String(100), nullable=False)
    severity = Column(SAEnum(RiskCategory), nullable=False, default=RiskCategory.MEDIUM)
    worker_safety_status = Column(SAEnum(WorkerSafetyStatus), default=WorkerSafetyStatus.SAFE)
    evidence = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    detection_source = Column(String(50), default="WORKER_MONITORING_ENGINE")
    finding_id = Column(String(36), ForeignKey("safety_findings.id", ondelete="SET NULL"), nullable=True)
    is_simulation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site")
    worker = relationship("Worker")
    finding = relationship("SafetyFinding")


class SiteMonitoringSession(Base):
    __tablename__ = "site_monitoring_sessions"

    id = Column(String(36), primary_key=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
    started_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_evaluated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    site = relationship("Site")
    starter = relationship("User")


class SafetyAlert(Base):
    __tablename__ = "safety_alerts"

    id = Column(String(36), primary_key=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String(36), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    finding_id = Column(String(36), ForeignKey("safety_findings.id", ondelete="SET NULL"), nullable=True)
    source_type = Column(String(50), nullable=False, default="SAFETY_FINDING")
    source_id = Column(String(100), nullable=True, index=True)
    severity = Column(SAEnum(AlertSeverity), nullable=False)
    priority = Column(SAEnum(AlertPriority), nullable=False, default=AlertPriority.HIGH)
    status = Column(SAEnum(AlertStatus), nullable=False, default=AlertStatus.OPEN)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    escalation_level = Column(Integer, default=0)
    escalation_timeout_minutes = Column(Integer, default=30)
    assigned_role = Column(String(50), default="safety_officer")
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    video_event_id = Column(String(36), ForeignKey("video_events.id", ondelete="SET NULL"), nullable=True)
    is_simulation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    site = relationship("Site")
    worker = relationship("Worker")
    finding = relationship("SafetyFinding")
    video_event = relationship("VideoEvent", foreign_keys=[video_event_id])
    notifications = relationship("AlertNotification", back_populates="alert", cascade="all, delete-orphan")
    audit_events = relationship("AlertAuditEvent", back_populates="alert", cascade="all, delete-orphan", order_by="AlertAuditEvent.created_at.desc()")


class AlertNotification(Base):
    __tablename__ = "alert_notifications"

    id = Column(String(36), primary_key=True)
    alert_id = Column(String(36), ForeignKey("safety_alerts.id", ondelete="CASCADE"), nullable=False)
    channel = Column(SAEnum(NotificationChannel), nullable=False)
    recipient_role = Column(String(50), nullable=False)
    recipient_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(30), default="DELIVERED")  # DELIVERED | SENT_MOCK
    delivery_details = Column(JSON, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    alert = relationship("SafetyAlert", back_populates="notifications")
    recipient_user = relationship("User")


class AlertAuditEvent(Base):
    __tablename__ = "alert_audit_events"

    id = Column(String(36), primary_key=True)
    alert_id = Column(String(36), ForeignKey("safety_alerts.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(SAEnum(AlertAuditEventType), nullable=False)
    actor_id = Column(String(36), nullable=True)
    actor_name = Column(String(100), nullable=True)
    actor_role = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    alert = relationship("SafetyAlert", back_populates="audit_events")


class CameraZone(Base):
    __tablename__ = "camera_zones"

    id = Column(String(36), primary_key=True)
    zone_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    zone_type = Column(SAEnum(ZoneType), nullable=False, default=ZoneType.GENERAL)
    boundary = Column(JSON, nullable=True)
    risk_level = Column(SAEnum(RiskCategory), nullable=False, default=RiskCategory.LOW)
    max_capacity = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="camera_zones")


class VideoStream(Base):
    __tablename__ = "video_streams"

    id = Column(String(36), primary_key=True)
    stream_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    camera_name = Column(String(100), nullable=False)
    source_type = Column(SAEnum(VideoSourceType), nullable=False, default=VideoSourceType.DEMO)
    source_url = Column(String(500), nullable=True)
    status = Column(SAEnum(StreamStatus), nullable=False, default=StreamStatus.ACTIVE)
    fps = Column(Float, default=15.0)
    resolution_width = Column(Integer, default=1280)
    resolution_height = Column(Integer, default=720)
    sampling_interval_frames = Column(Integer, default=5)
    confidence_threshold = Column(Float, default=0.65)
    total_frames_ingested = Column(Integer, default=0)
    processed_frames_count = Column(Integer, default=0)
    dropped_frames_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_simulation = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="video_streams")
    creator = relationship("User")
    events = relationship("VideoEvent", back_populates="stream", cascade="all, delete-orphan", order_by="VideoEvent.created_at.desc()")


class VideoEvent(Base):
    __tablename__ = "video_events"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    stream_id = Column(String(36), ForeignKey("video_streams.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String(36), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    finding_id = Column(String(36), ForeignKey("safety_findings.id", ondelete="SET NULL"), nullable=True)
    alert_id = Column(String(36), ForeignKey("safety_alerts.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(SAEnum(VideoEventType), nullable=False)
    severity = Column(SAEnum(RiskCategory), nullable=False, default=RiskCategory.MEDIUM)
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    zone_name = Column(String(100), nullable=True)
    bounding_box = Column(JSON, nullable=True)
    detected_ppe = Column(JSON, default=list)
    missing_ppe = Column(JSON, default=list)
    detection_source = Column(String(50), default="DEMO / SIMULATION")
    is_simulation = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stream = relationship("VideoStream", back_populates="events")
    site = relationship("Site")
    worker = relationship("Worker")
    finding = relationship("SafetyFinding")
    alert = relationship("SafetyAlert", foreign_keys=[alert_id])


# ── Milestone 3 Compliance Intelligence ──────────────────────────────────────

class ComplianceRuleCategory(str, enum.Enum):
    PPE = "PPE"
    WORKER_CERTIFICATION = "WORKER_CERTIFICATION"
    EQUIPMENT_CERTIFICATION = "EQUIPMENT_CERTIFICATION"
    SITE_INSPECTION = "SITE_INSPECTION"
    EXCAVATION_SAFETY = "EXCAVATION_SAFETY"
    ELECTRICAL_SAFETY = "ELECTRICAL_SAFETY"
    SCAFFOLDING_SAFETY = "SCAFFOLDING_SAFETY"
    EMERGENCY_DOCUMENTATION = "EMERGENCY_DOCUMENTATION"


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class InspectionRequirementStatus(str, enum.Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    WAIVED = "WAIVED"


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(String(36), primary_key=True)
    rule_id = Column(String(50), unique=True, nullable=False, index=True)
    standard_ref = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(SAEnum(ComplianceRuleCategory), nullable=False)
    requirement = Column(Text, nullable=False)
    applicable_activity = Column(String(100), nullable=True)
    applicable_zone = Column(String(100), nullable=True)
    severity = Column(SAEnum(RiskCategory), nullable=False, default=RiskCategory.MEDIUM)
    remediation_recommendation = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InspectionRequirement(Base):
    __tablename__ = "inspection_requirements"

    id = Column(String(36), primary_key=True)
    requirement_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    inspection_type = Column(String(100), nullable=False)
    regulatory_reference = Column(String(100), nullable=True)
    responsible_role = Column(String(50), nullable=False)
    due_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime, nullable=True)
    status = Column(SAEnum(InspectionRequirementStatus), default=InspectionRequirementStatus.PENDING)
    is_overdue = Column(Boolean, default=False)
    evidence_document_ref = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="inspection_requirements")


class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"

    id = Column(String(36), primary_key=True)
    finding_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String(50), nullable=True)
    worker_id = Column(String(36), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    inspection_requirement_id = Column(String(36), ForeignKey("inspection_requirements.id", ondelete="SET NULL"), nullable=True)
    standard_ref = Column(String(100), nullable=False)
    violation_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SAEnum(RiskCategory), nullable=False, default=RiskCategory.MEDIUM)
    evidence = Column(JSON, nullable=True)
    recommendation = Column(Text, nullable=False)
    status = Column(SAEnum(SafetyFindingStatus), default=SafetyFindingStatus.OPEN)
    detection_source = Column(String(50), default="COMPLIANCE_AGENT")
    is_simulation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="compliance_findings")
    worker = relationship("Worker")
    inspection_requirement = relationship("InspectionRequirement")
    safety_finding = relationship("SafetyFinding", back_populates="compliance_finding", uselist=False)


class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"

    id = Column(String(36), primary_key=True)
    assessment_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    compliance_score = Column(Float, nullable=False, default=100.0)
    compliance_status = Column(SAEnum(ComplianceStatus), nullable=False, default=ComplianceStatus.COMPLIANT)
    total_rules_evaluated = Column(Integer, default=0)
    rules_passed = Column(Integer, default=0)
    rules_violated = Column(Integer, default=0)
    critical_violations = Column(Integer, default=0)
    high_violations = Column(Integer, default=0)
    medium_violations = Column(Integer, default=0)
    total_inspections = Column(Integer, default=0)
    overdue_inspections = Column(Integer, default=0)
    findings_summary = Column(JSON, nullable=True)
    category_scores = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    detection_source = Column(String(50), default="COMPLIANCE_AGENT")
    is_simulation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="compliance_assessments")


# ── Milestone 3 Insurance Intelligence ───────────────────────────────────────

class InsuranceRiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ClaimRiskLevel(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class InsuranceRiskAssessment(Base):
    __tablename__ = "insurance_risk_assessments"

    id = Column(String(36), primary_key=True)
    assessment_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    insurance_risk_score = Column(Float, nullable=False, default=0.0)
    insurance_risk_level = Column(SAEnum(InsuranceRiskLevel), nullable=False, default=InsuranceRiskLevel.LOW)
    exposure_index = Column(Float, default=0.0)
    estimated_liability_exposure = Column(String(100), nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    category_exposures = Column(JSON, nullable=True)
    unresolved_findings_count = Column(Integer, default=0)
    active_critical_alerts_count = Column(Integer, default=0)
    compliance_deficit_penalty = Column(Float, default=0.0)
    underwriting_recommendations = Column(JSON, nullable=True)
    is_simulation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="insurance_assessments")


class InsuranceClaimAssessment(Base):
    __tablename__ = "insurance_claim_assessments"

    id = Column(String(36), primary_key=True)
    claim_assessment_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    incident_ref = Column(String(100), nullable=False)
    incident_title = Column(String(200), nullable=False)
    incident_date = Column(DateTime, default=datetime.utcnow)
    involved_worker_id = Column(String(36), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    involved_equipment_id = Column(String(36), ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    incident_severity = Column(SAEnum(RiskCategory), nullable=False, default=RiskCategory.MEDIUM)
    claim_risk_level = Column(SAEnum(ClaimRiskLevel), nullable=False, default=ClaimRiskLevel.MODERATE)
    claim_probability_pct = Column(Float, default=50.0)
    documentation_completeness_pct = Column(Float, default=60.0)
    potential_claim_indicators = Column(JSON, nullable=True)
    contributing_safety_factors = Column(JSON, nullable=True)
    contributing_compliance_factors = Column(JSON, nullable=True)
    missing_documentation = Column(JSON, nullable=True)
    status = Column(String(50), default="UNDER_REVIEW")
    is_simulation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="insurance_claims")
    worker = relationship("Worker")
    equipment = relationship("Equipment")
    package = relationship("ClaimDocumentationPackage", back_populates="claim_assessment", uselist=False)


class ClaimDocumentationPackage(Base):
    __tablename__ = "claim_documentation_packages"

    id = Column(String(36), primary_key=True)
    package_id = Column(String(50), unique=True, nullable=False, index=True)
    claim_assessment_id = Column(String(36), ForeignKey("insurance_claim_assessments.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    incident_summary = Column(Text, nullable=False)
    worker_dossier = Column(JSON, nullable=True)
    equipment_dossier = Column(JSON, nullable=True)
    safety_findings_dossier = Column(JSON, nullable=True)
    compliance_findings_dossier = Column(JSON, nullable=True)
    sensor_evidence_dossier = Column(JSON, nullable=True)
    missing_required_documents = Column(JSON, nullable=True)
    recommended_actions = Column(JSON, nullable=True)
    is_complete = Column(Boolean, default=False)
    is_simulation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="claim_packages")
    claim_assessment = relationship("InsuranceClaimAssessment", back_populates="package")



