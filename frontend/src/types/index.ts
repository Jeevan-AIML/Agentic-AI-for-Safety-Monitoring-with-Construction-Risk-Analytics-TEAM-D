// ── User & Auth Types ──────────────────────────────────────────────────────

export type UserRole = 'super_admin' | 'project_manager' | 'site_manager' | 'safety_officer' | 'viewer';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  assigned_site_id?: string;
  avatar_url?: string;
  phone?: string;
  department?: string;
  created_at: string;
  last_login?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

// ── Project Types ──────────────────────────────────────────────────────────

export type ProjectStatus = 'planning' | 'active' | 'on_hold' | 'completed';

export interface Project {
  id: string;
  project_id: string;
  name: string;
  client: string;
  description?: string;
  start_date?: string;
  expected_completion?: string;
  budget?: number;
  status: ProjectStatus;
  manager_id?: string;
  manager_name?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  site_count: number;
  created_at: string;
  updated_at: string;
}

// ── Site Types ─────────────────────────────────────────────────────────────

export type SiteStatus = 'active' | 'monitoring' | 'warning' | 'critical' | 'inactive';
export type RiskCategory = 'low' | 'medium' | 'high' | 'critical';

export interface Site {
  id: string;
  site_id: string;
  name: string;
  site_type?: string;
  project_id?: string;
  project_name?: string;
  manager_id?: string;
  manager_name?: string;
  status: SiteStatus;
  current_risk_score: number;
  risk_category: RiskCategory;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  worker_count: number;
  equipment_count: number;
  last_inspection?: string;
  created_at: string;
  updated_at: string;
}

// ── Worker Types ───────────────────────────────────────────────────────────

export type WorkerRole = 'operator' | 'electrician' | 'mason' | 'supervisor' | 'welder' | 'technician' | 'general_worker';
export type SafetyTrainingStatus = 'certified' | 'in_progress' | 'expired' | 'not_started';
export type PPEStatus = 'compliant' | 'non_compliant' | 'partial';

export interface Worker {
  id: string;
  worker_id: string;
  name: string;
  role: WorkerRole;
  department?: string;
  site_id?: string;
  site_name?: string;
  contact?: string;
  joining_date?: string;
  safety_training: SafetyTrainingStatus;
  ppe_status: PPEStatus;
  is_active: boolean;
  created_at: string;
}

// ── Equipment Types ────────────────────────────────────────────────────────

export type EquipmentStatus = 'operational' | 'maintenance' | 'out_of_service' | 'inspection_due';

export interface Equipment {
  id: string;
  equipment_id: string;
  name: string;
  equipment_type: string;
  manufacturer?: string;
  model?: string;
  site_id?: string;
  site_name?: string;
  operator_name?: string;
  status: EquipmentStatus;
  last_inspection?: string;
  maintenance_due?: string;
  created_at: string;
}

// ── Activity Types ─────────────────────────────────────────────────────────

export type ActivityType =
  | 'excavation' | 'concrete_work' | 'welding' | 'electrical_work'
  | 'material_handling' | 'demolition' | 'scaffolding' | 'general_construction';

export interface Activity {
  id: string;
  site_id: string;
  site_name?: string;
  activity_type: ActivityType;
  description?: string;
  date: string;
  start_time?: string;
  end_time?: string;
  workers_involved: number;
  equipment_used?: string[];
  environmental_conditions?: string;
  notes?: string;
  created_at: string;
}

// ── Hazard Types ───────────────────────────────────────────────────────────

export type HazardType =
  | 'environmental' | 'equipment' | 'structural' | 'electrical'
  | 'fire' | 'fall' | 'excavation' | 'material_handling' | 'other';

export type HazardStatus = 'open' | 'under_review' | 'mitigated' | 'closed';

export interface Hazard {
  id: string;
  hazard_id: string;
  site_id: string;
  site_name?: string;
  hazard_type: HazardType;
  description: string;
  evidence?: string;
  severity: number;
  probability: number;
  risk_score: number;
  risk_category: RiskCategory;
  status: HazardStatus;
  detected_at: string;
  reported_by?: string;
  recommended_action?: string;
  detection_source?: string;
  detected_by_agent: boolean;
  agent_confidence?: number;
  acknowledged_at?: string;
  acknowledged_by?: string;
  mitigated_at?: string;
  mitigated_by?: string;
  mitigation_notes?: string;
  created_at: string;
  updated_at?: string;
}

// ── Risk Score Types ───────────────────────────────────────────────────────

export interface RiskScore {
  id: string;
  site_id: string;
  site_name?: string;
  overall_score: number;
  category: RiskCategory;
  environmental_risk: number;
  equipment_risk: number;
  activity_risk: number;
  site_condition_risk: number;
  operational_risk: number;
  highest_hazard_score?: number;
  active_hazards_count?: number;
  critical_hazards_count?: number;
  recommendations?: string[];
  reasoning?: string[];
  calculated_by: string;
  notes?: string;
  recorded_at: string;
}

export interface CategoryRiskScore {
  score: number;
  level: RiskCategory;
  explanation: string;
}

export interface DetectedHazardDetail {
  id?: string;
  hazard_id?: string;
  site_id: string;
  type: string;
  description: string;
  evidence: string;
  severity: number;
  probability: number;
  risk_score: number;
  risk_level: RiskCategory;
  recommended_action: string;
  detection_source: string;
  status: string;
}

export interface SiteRiskAnalysisResponse {
  site_id: string;
  site_name?: string;
  timestamp: string;
  overall_risk_score: number;
  risk_level: RiskCategory;
  highest_hazard_score: number;
  active_hazards_count: number;
  critical_hazards_count: number;
  categories: {
    environmental: CategoryRiskScore;
    equipment: CategoryRiskScore;
    activity: CategoryRiskScore;
    site_condition: CategoryRiskScore;
    operational: CategoryRiskScore;
    [key: string]: CategoryRiskScore;
  };
  hazards: DetectedHazardDetail[];
  recommendations: string[];
  reasoning: string[];
  detection_source: string;
}

export interface DemoScenario {
  id: number;
  name: string;
  description: string;
  expected_level: string;
}

// ── Inspection Types ───────────────────────────────────────────────────────

export interface Inspection {
  id: string;
  inspection_id: string;
  site_id: string;
  site_name?: string;
  inspector_name?: string;
  date: string;
  result?: string;
  findings?: string;
  notes?: string;
  created_at: string;
}

// ── Notification Types ─────────────────────────────────────────────────────

export type NotificationCategory = 'risk' | 'safety' | 'compliance' | 'system';

export interface Notification {
  id: string;
  user_id?: string;
  category: NotificationCategory;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  is_read: boolean;
  link?: string;
  created_at: string;
}

// ── Dashboard Types ────────────────────────────────────────────────────────

export interface DashboardKPI {
  overall_risk_score: number;
  risk_category: RiskCategory;
  active_hazards: number;
  safety_observations: number;
  open_incidents: number;
  compliance_status: number;
  site_monitoring: string;
  total_sites: number;
  total_projects: number;
  total_workers: number;
  total_equipment: number;
}

export interface RiskBreakdown {
  environmental_risk: number;
  equipment_risk: number;
  site_condition_risk: number;
  operational_risk: number;
  overall_risk: number;
  category: RiskCategory;
}

// ── API Response ───────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
}

// ── Safety Agent Types (Phase 2.1) ─────────────────────────────────────────

export type SafetyFindingStatus = 'open' | 'acknowledged' | 'mitigated' | 'closed';
export type SafetyFindingType =
  | 'ppe_violation'
  | 'expired_training'
  | 'missing_training'
  | 'unsafe_equipment_operation'
  | 'high_risk_activity'
  | 'high_risk_zone_exposure';

export interface SafetyFinding {
  id: string;
  finding_id: string;
  site_id: string;
  worker_id?: string;
  worker_name?: string;
  worker_code?: string;
  analysis_id?: string;
  finding_type: SafetyFindingType;
  description: string;
  evidence?: string;
  severity: RiskCategory;
  status: SafetyFindingStatus;
  recommendation?: string;
  detection_source: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  mitigated_at?: string;
  mitigated_by?: string;
  mitigation_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface SafetyAnalysis {
  id: string;
  analysis_id: string;
  site_id: string;
  worker_id?: string;
  overall_safety_score: number;
  safety_level: RiskCategory;
  workers_analyzed: number;
  violation_count: number;
  high_count: number;
  critical_count: number;
  detection_source: string;
  summary?: Record<string, unknown>;
  created_at: string;
}

export interface SafetyAnalysisResponse {
  id?: string;
  analysis_id?: string;
  site_id?: string;
  site_name?: string;
  timestamp?: string;
  overall_safety_score?: number;
  safety_level?: RiskCategory;
  workers_analyzed?: number;
  violation_count?: number;
  critical_count?: number;
  high_count?: number;
  medium_count?: number;
  low_count?: number;
  analysis?: SafetyAnalysis;
  findings: SafetyFinding[];
  summary: {
    workers_analyzed: number;
    overall_safety_score: number;
    safety_level: RiskCategory;
    violation_count: number;
    high_count: number;
    critical_count: number;
    medium_count?: number;
    low_count?: number;
    notifications_sent?: number;
    detection_source: string;
    agent?: string;
    [key: string]: any;
  };
  detection_source?: string;
}

export interface SafetyDemoScenario {
  id: number;
  name: string;
  description: string;
  expected_level: string;
  expected_violations: number;
}

export interface SiteSafetySummary {
  site_id: string;
  site_name: string;
  workers_count: number;
  latest_analysis?: SafetyAnalysis;
  open_findings_count: number;
  critical_findings_count: number;
  high_findings_count: number;
  detection_source: string;
  agent_name: string;
  agent_status: Record<string, unknown>;
}

// ── PPE Computer Vision Types (Phase 2.2) ─────────────────────────────────

export type PPEClass = 'HARD_HAT' | 'SAFETY_VEST' | 'SAFETY_GOGGLES' | 'GLOVES' | 'SAFETY_SHOES';
export type PPEComplianceStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'UNCERTAIN';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PPEDetectionItem {
  detection_id: string;
  ppe_class: PPEClass | string;
  confidence: number;
  bounding_box: BoundingBox;
  status: 'DETECTED' | 'LOW_CONFIDENCE' | 'MISSING';
  is_compliant: boolean;
  person_id?: string;
  detection_source: string;
}

export interface PersonPPEDetection {
  person_id: string;
  bounding_box: BoundingBox;
  confidence: number;
  detected_ppe: PPEDetectionItem[];
  missing_ppe: string[];
  is_compliant: boolean;
  worker_id?: string;
  worker_name?: string;
}

export interface PPECrossVerification {
  worker_id?: string;
  worker_name?: string;
  db_ppe_status?: string;
  cv_compliance: PPEComplianceStatus;
  has_discrepancy: boolean;
  discrepancy_details?: string;
}

export interface PPEAnalysis {
  id: string;
  analysis_id: string;
  site_id?: string;
  site_name?: string;
  worker_id?: string;
  worker_name?: string;
  image_filename: string;
  image_url: string;
  image_width: number;
  image_height: number;
  overall_compliance: PPEComplianceStatus;
  compliance_score: number;
  total_persons_detected: number;
  detected_ppe: PPEDetectionItem[];
  missing_ppe: string[];
  detections: PPEDetectionItem[];
  persons: PersonPPEDetection[];
  cross_verification?: PPECrossVerification;
  confidence_threshold: number;
  detection_source: string;
  model_name: string;
  recommendations: string[];
  findings: SafetyFinding[];
  summary?: any;
  created_at: string;
}

export interface PPEDemoScenario {
  id: number;
  name: string;
  description: string;
  expected_compliance: PPEComplianceStatus;
  expected_findings_count: number;
  detected_items: string[];
  missing_items: string[];
}

// ── Worker Safety Monitoring Types (Phase 2.3) ───────────────────────────────

export type WorkerSafetyStatus = 'SAFE' | 'WARNING' | 'HIGH_RISK' | 'CRITICAL';

export interface WorkerMonitoringFinding {
  rule_name: string;
  finding_type: string;
  severity: RiskCategory;
  description: string;
  evidence: string;
  recommendation?: string;
}

export interface WorkerMonitoringEvaluation {
  worker_id: string;
  worker_name: string;
  site_id: string;
  site_name?: string;
  safety_status: WorkerSafetyStatus;
  current_activity: string;
  current_zone: string;
  time_in_zone_minutes: number;
  is_high_risk_zone: boolean;
  ppe_status: string;
  training_status: string;
  workers_in_zone_count: number;
  findings: WorkerMonitoringFinding[];
  recommendations: string[];
  detection_source: string;
  evaluated_at: string;
  is_simulation: boolean;
}

export interface SafetyMonitoringEvent {
  id: string;
  event_id: string;
  site_id: string;
  worker_id: string;
  worker_name?: string;
  activity_name?: string;
  zone_name?: string;
  time_in_zone_minutes: number;
  event_type: string;
  severity: RiskCategory;
  worker_safety_status: WorkerSafetyStatus;
  evidence?: string;
  recommendation?: string;
  detection_source: string;
  is_simulation: boolean;
  created_at: string;
}

export interface SiteMonitoringStatus {
  site_id: string;
  site_name: string;
  is_monitoring_active: boolean;
  started_at?: string;
  stopped_at?: string;
  monitored_workers_count: number;
  active_warnings_count: number;
  active_high_risk_count: number;
  active_critical_count: number;
  recent_events: SafetyMonitoringEvent[];
}

export interface MonitoringDemoScenario {
  id: number;
  name: string;
  description: string;
  expected_status: WorkerSafetyStatus;
  expected_findings_count: number;
  context_summary: {
    activity?: string;
    zone?: string;
    time_in_zone?: number;
    nearby_hazards?: number;
    nearby_equipment?: number;
  };
}

// ── Safety Alert System Types (Phase 2.4) ──────────────────────────────────

export type AlertSeverity = 'high' | 'critical';
export type AlertStatus = 'open' | 'acknowledged' | 'escalated' | 'resolved' | 'dismissed';
export type AlertPriority = 'critical' | 'high' | 'medium';
export type NotificationChannel = 'in_app' | 'email_adapter' | 'push_adapter';
export type AlertAuditEventType =
  | 'alert_created'
  | 'alert_acknowledged'
  | 'alert_escalated'
  | 'alert_resolved'
  | 'alert_dismissed';

export interface AlertNotification {
  id: string;
  alert_id: string;
  channel: NotificationChannel;
  recipient_role: string;
  recipient_user_id?: string;
  title: string;
  message: string;
  status: string;
  delivery_details?: any;
  sent_at: string;
}

export interface AlertAuditEvent {
  id: string;
  alert_id: string;
  event_type: AlertAuditEventType;
  actor_id?: string;
  actor_name?: string;
  actor_role?: string;
  details?: string;
  created_at: string;
}

export interface SafetyAlert {
  id: string;
  alert_id: string;
  site_id: string;
  site_name?: string;
  worker_id?: string;
  worker_name?: string;
  finding_id?: string;
  source_type: string;
  source_id?: string;
  severity: AlertSeverity;
  priority: AlertPriority;
  status: AlertStatus;
  title: string;
  description: string;
  recommendation?: string;
  evidence?: string;
  escalation_level: number;
  escalation_timeout_minutes: number;
  assigned_role?: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_notes?: string;
  escalated_at?: string;
  is_simulation: boolean;
  created_at: string;
  updated_at: string;
  notifications?: AlertNotification[];
  audit_events?: AlertAuditEvent[];
}

export interface AlertDemoScenario {
  id: number;
  name: string;
  description: string;
  expected_severity: AlertSeverity;
  expected_status: AlertStatus;
  summary: string;
}

// ── Phase 3.1 Video Surveillance Types ─────────────────────────────────────

export type StreamStatus = 'active' | 'stopped' | 'error';
export type VideoSourceType = 'demo' | 'local' | 'rtsp';
export type VideoEventType =
  | 'person_detected'
  | 'ppe_violation'
  | 'high_risk_zone_entry'
  | 'hazard_proximity'
  | 'equipment_proximity'
  | 'overcrowded_zone'
  | 'unsafe_interaction';

export type ZoneType =
  | 'safe_area'
  | 'excavation'
  | 'heavy_equipment'
  | 'restricted'
  | 'electrical'
  | 'general';

export interface CameraZone {
  id: string;
  zone_id: string;
  site_id: string;
  name: string;
  zone_type: ZoneType;
  boundary?: { x: number; y: number; w: number; h: number } | any;
  risk_level: RiskCategory;
  max_capacity: number;
  is_active: boolean;
  created_at: string;
}

export interface VideoStream {
  id: string;
  stream_id: string;
  site_id: string;
  site_name?: string;
  camera_name: string;
  source_type: VideoSourceType;
  source_url?: string;
  status: StreamStatus;
  fps: number;
  resolution_width: number;
  resolution_height: number;
  sampling_interval_frames: number;
  confidence_threshold: number;
  total_frames_ingested: number;
  processed_frames_count: number;
  dropped_frames_count: number;
  started_at: string;
  stopped_at?: string;
  created_by?: string;
  is_simulation: boolean;
  created_at: string;
}

export interface VideoEvent {
  id: string;
  event_id: string;
  stream_id: string;
  site_id: string;
  worker_id?: string;
  worker_name?: string;
  finding_id?: string;
  alert_id?: string;
  event_type: VideoEventType;
  severity: RiskCategory;
  description: string;
  evidence?: string;
  zone_name?: string;
  bounding_box?: { x: number; y: number; width: number; height: number };
  detected_ppe?: string[];
  missing_ppe?: string[];
  detection_source: string;
  is_simulation: boolean;
  timestamp: string;
  created_at: string;
}

export interface VideoLiveStatus {
  site_id: string;
  site_name?: string;
  active_streams_count: number;
  streams: VideoStream[];
  detected_personnel_count: number;
  compliant_workers_count: number;
  ppe_compliance_rate: number;
  active_high_alerts_count: number;
  active_critical_alerts_count: number;
  recent_events: VideoEvent[];
  active_zones: CameraZone[];
}

export interface VideoDemoScenario {
  id: number;
  name: string;
  description: string;
  expected_violations: number;
  expected_severity?: string;
  summary: string;
}

// ── Phase 3.2 Drone Aerial Inspection Types ─────────────────────────────────

export type DroneSessionStatus = 'idle' | 'active' | 'completed' | 'failed';

export interface DroneFlightPoint {
  id: string;
  session_id: string;
  sequence: number;
  latitude: number;
  longitude: number;
  altitude: number;
  heading: number;
  speed: number;
  inspection_area?: string;
  timestamp: string;
}

export interface AerialInspectionPoint {
  id: string;
  point_id: string;
  session_id: string;
  sequence: number;
  name: string;
  latitude: number;
  longitude: number;
  altitude: number;
  status: 'PENDING' | 'INSPECTED' | 'HAZARD_DETECTED' | string;
  captured_image_ref?: string;
  hazards_count: number;
  risk_level: RiskCategory;
  timestamp: string;
}

export interface AerialFinding {
  id: string;
  finding_id: string;
  session_id: string;
  site_id: string;
  hazard_id?: string;
  safety_finding_id?: string;
  alert_id?: string;
  hazard_type: string;
  location_zone: string;
  latitude?: number;
  longitude?: number;
  altitude?: number;
  severity: RiskCategory;
  confidence: number;
  evidence?: string;
  recommendation?: string;
  detection_source: string;
  image_reference?: string;
  orthomosaic_metadata?: any;
  is_simulation: boolean;
  created_at: string;
}

export interface DroneInspectionSession {
  id: string;
  session_id: string;
  site_id: string;
  site_name?: string;
  drone_identifier: string;
  status: DroneSessionStatus;
  inspection_source: string;
  is_simulation: boolean;
  total_waypoints: number;
  inspected_waypoints: number;
  total_hazards_detected: number;
  critical_hazards_count: number;
  high_hazards_count: number;
  started_at: string;
  completed_at?: string;
  created_by?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  flight_points?: DroneFlightPoint[];
  inspection_points?: AerialInspectionPoint[];
  findings?: AerialFinding[];
}

export interface AerialAnalysisResult {
  session_id: string;
  site_id: string;
  status: string;
  waypoints_inspected: number;
  hazards_detected_count: number;
  findings: AerialFinding[];
  safety_findings_created: number;
  alerts_created: number;
  orthomosaic_summary?: Record<string, any>;
  detection_source: string;
  is_simulation: boolean;
}

export interface DroneDemoScenario {
  id: number;
  name: string;
  description: string;
  expected_hazards: number;
  expected_severity?: string;
  summary: string;
}

// ── Multi-Modal Hazard Correlation & Predictive Spatial Risk (Phase 3.3) ───

export type MultiModalRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface CorrelatedHazard {
  id: string;
  title: string;
  hazard_type: string;
  severity: string;
  confidence: number;
  contributing_sources: string[];
  location_zone?: string;
  latitude?: number;
  longitude?: number;
  affected_workers: string[];
  affected_equipment: string[];
  correlation_reason: string;
  recommended_action: string;
  source_event_ids: string[];
}

export interface SpatialRegionRisk {
  region_id: string;
  name: string;
  risk_score: number;
  risk_level: string;
  hazard_count: number;
  workers_count: number;
  equipment_count: number;
  active_sources: string[];
}

export interface MultiModalRiskAssessment {
  id: string;
  assessment_id: string;
  site_id: string;
  risk_score: number;
  risk_level: MultiModalRiskLevel;
  contributing_sources: string[];
  correlated_hazards: CorrelatedHazard[];
  affected_workers: any[];
  affected_equipment: any[];
  spatial_regions: SpatialRegionRisk[];
  evidence?: Record<string, any>;
  correlation_summary?: string;
  recommendations: string[];
  detection_source: string;
  is_simulation: boolean;
  created_at: string;
}

export interface CorrelationDemoScenario {
  id: number;
  name: string;
  description: string;
  contributing_sources: string[];
  expected_risk_level: string;
  expected_correlated_hazards: number;
  narrative: string;
}

// ── Navigation ─────────────────────────────────────────────────────────────

export interface NavItem {
  label: string;
  path: string;
  icon: string;
  badge?: number;
  roles?: UserRole[];
  comingSoon?: boolean;
}

// ── Milestone 3 Compliance Intelligence Types ──────────────────────────────

export type ComplianceRuleCategory =
  | 'PPE'
  | 'SCAFFOLDING'
  | 'EXCAVATION'
  | 'ELECTRICAL'
  | 'FALL_PROTECTION'
  | 'ENVIRONMENTAL'
  | 'STATUTORY_INSPECTION'
  | 'TRAINING_CERTIFICATION';

export type ComplianceStatus =
  | 'COMPLIANT'
  | 'PARTIALLY_COMPLIANT'
  | 'NON_COMPLIANT'
  | 'CRITICAL_NON_COMPLIANT';

export type InspectionRequirementStatus =
  | 'SCHEDULED'
  | 'PENDING'
  | 'COMPLETED'
  | 'OVERDUE'
  | 'WAIVED';

export interface ComplianceRule {
  id: string;
  rule_id: string;
  category: ComplianceRuleCategory;
  standard_name: string;
  standard_code: string;
  title: string;
  description: string;
  severity_weight: number;
  is_active: boolean;
  jurisdiction: string;
  regulatory_url?: string;
  created_at: string;
}

export interface InspectionRequirement {
  id: string;
  requirement_id: string;
  site_id: string;
  title: string;
  inspection_type: string;
  regulatory_reference: string;
  responsible_role: string;
  due_date: string;
  completed_date?: string;
  status: InspectionRequirementStatus;
  is_overdue: boolean;
  evidence_document_ref?: string;
  notes?: string;
  created_at: string;
}

export interface ComplianceFinding {
  id: string;
  finding_id: string;
  site_id: string;
  rule_id: string;
  standard_ref: string;
  violation_type: string;
  severity: string;
  description: string;
  location_zone?: string;
  evidence_data?: Record<string, any>;
  recommendation: string;
  fine_exposure_estimate: number;
  status: string;
  created_at: string;
}

export interface ComplianceAssessment {
  id: string;
  assessment_id: string;
  site_id: string;
  compliance_score: number;
  compliance_status: ComplianceStatus;
  total_rules_evaluated: number;
  rules_passed: number;
  rules_failed: number;
  critical_violations: number;
  high_violations: number;
  medium_violations: number;
  low_violations: number;
  overdue_inspections: number;
  category_scores: Record<string, number>;
  findings_summary?: Record<string, any>;
  recommendations: string[];
  is_simulation: boolean;
  created_at: string;
}

export interface ComplianceReport {
  site_id: string;
  assessment_id: string;
  compliance_score: number;
  compliance_status: ComplianceStatus;
  critical_violations_count: number;
  high_violations_count: number;
  total_rules_evaluated: number;
  rules_passed: number;
  overdue_inspections_count: number;
  category_scores: Record<string, number>;
  recommendations: string[];
  findings: Array<{
    finding_id: string;
    standard_ref: string;
    violation_type: string;
    severity: string;
    description: string;
    recommendation: string;
  }>;
  inspections: Array<{
    requirement_id: string;
    title: string;
    inspection_type: string;
    due_date?: string;
    status: string;
    is_overdue: boolean;
  }>;
  generated_at: string;
  disclaimer: string;
}

export interface ComplianceDemoScenario {
  id: number;
  name: string;
  description: string;
  expected_status: ComplianceStatus;
  expected_score: number;
  expected_violations: number;
  focus_standards: string[];
}

// ── Milestone 3 Insurance Intelligence Types ───────────────────────────────

export type InsuranceRiskLevel = 'NEGLIGIBLE' | 'LOW' | 'MODERATE' | 'ELEVATED' | 'HIGH' | 'CRITICAL';
export type ClaimRiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';

export interface InsuranceRiskAssessment {
  id: string;
  assessment_id: string;
  site_id: string;
  insurance_risk_score: number;
  risk_level: InsuranceRiskLevel;
  exposure_bracket: string;
  compliance_factor: number;
  incident_factor: number;
  hazard_factor: number;
  inspection_factor: number;
  claim_frequency_factor: number;
  estimated_annual_premium_impact_pct: number;
  recommended_deductible_multiplier: number;
  underwriting_concerns: string[];
  loss_control_recommendations: string[];
  score_breakdown: Record<string, number>;
  is_simulation: boolean;
  created_at: string;
}

export interface InsuranceClaimAssessment {
  id: string;
  claim_id: string;
  site_id: string;
  incident_title: string;
  incident_type: string;
  estimated_loss_amount: number;
  claim_risk_level: ClaimRiskLevel;
  subrogation_potential: string;
  contributing_violations: string[];
  causal_factors: string[];
  documentation_completeness_pct: number;
  adjuster_notes: string;
  created_at: string;
}

export interface ClaimDocumentationPackage {
  id: string;
  package_id: string;
  claim_assessment_id: string;
  site_id: string;
  executive_summary: string;
  incident_chronology: any[];
  safety_audit_trail: any[];
  compliance_records: any[];
  weather_and_site_conditions: Record<string, any>;
  drone_aerial_evidence?: any[];
  video_surveillance_evidence?: any[];
  package_checksum: string;
  is_verified: boolean;
  created_at: string;
}

export interface InsuranceDemoScenario {
  id: number;
  name: string;
  description: string;
  scenario_type: string;
  expected_risk_level?: string;
  expected_risk_score?: number;
  expected_exposure_bracket?: string;
  claim_type?: string;
  estimated_loss?: number;
  focus_areas: string[];
}

// ── Milestone 4 Phase 4.1 Reporting Agent Types ──────────────────────────

export type ReportType = 'DAILY_SITE' | 'EXECUTIVE_SUMMARY' | 'AUDIT_READY' | 'PROJECT_HEALTH';
export type ReportStatus = 'GENERATING' | 'COMPLETED' | 'FAILED' | 'ARCHIVED';

export interface ReportTypeInfo {
  type: ReportType;
  name: string;
  description: string;
  target_audience: string;
  frequency: string;
}

export interface GeneratedReportSummary {
  id: string;
  report_id: string;
  site_id?: string;
  project_id?: string;
  report_type: ReportType;
  title: string;
  reporting_period_start?: string;
  reporting_period_end?: string;
  generated_at: string;
  status: ReportStatus;
  summary?: string;
  created_by?: string;
  metrics?: any;
}

export interface GeneratedReport extends GeneratedReportSummary {
  content: any;
}

// ── Milestone 4 Phase 4.2 Construction Risk Intelligence Engine Types ──────

export interface CategoryRiskBreakdown {
  site_risk_score: number;
  safety_risk_score: number;
  compliance_risk_score: number;
  insurance_risk_score: number;
  weights: {
    site_risk: number;
    safety_risk: number;
    compliance_risk: number;
    insurance_risk: number;
  };
  site_risk?: any;
  safety_risk?: any;
  compliance_risk?: any;
  insurance_risk?: any;
}

export interface RecurringPattern {
  pattern_id: string;
  category: string;
  pattern_type: string;
  pattern_description: string;
  occurrence_count: number;
  first_observed?: string;
  last_observed?: string;
  time_window_hours: number;
  severity: string;
  velocity: string;
  locations: string[];
  sample_finding_ids: string[];
}

export interface IncidentLeadingIndicator {
  indicator: string;
  severity: string;
  observed_value: string;
}

export interface PotentialIncidentPrediction {
  prediction_id: string;
  incident_type: string;
  probability_score: number;
  severity_potential: string;
  predicted_timeframe: string;
  primary_driver: string;
  causal_chain: string[];
  leading_indicators: IncidentLeadingIndicator[];
  recommended_interventions: string[];
}

export interface OperationalRecommendation {
  recommendation_id: string;
  category: string;
  priority: string;
  timeframe: string;
  title: string;
  action_items: string[];
  expected_risk_reduction: string;
  target_hazard_types: string[];
  cost_impact_level: string;
}

export interface RiskIntelligenceAssessment {
  id: string;
  assessment_id: string;
  project_id?: string;
  site_id: string;
  overall_risk_score: number;
  risk_level: string;
  category_scores?: CategoryRiskBreakdown;
  recurring_patterns?: RecurringPattern[];
  predicted_incidents?: PotentialIncidentPrediction[];
  recommendations?: OperationalRecommendation[];
  findings_count: number;
  critical_findings_count: number;
  high_findings_count: number;
  medium_findings_count: number;
  low_findings_count: number;
  assessed_at: string;
  created_at: string;
}

// ── Phase 4.3: Executive Project Dashboard Types ─────────────────────────

export interface ExecutiveDashboardSiteInfo {
  site_id: string;
  site_name: string;
  site_code?: string;
  project_id?: string;
  project_name?: string;
  status: string;
  location?: string;
  manager?: string;
}

export interface ExecutiveDashboardAssessment {
  assessment_id: string;
  generated_at: string;
  overall_risk_score: number;
  overall_risk_level: string;
  scoring_explanation?: string;
  category_scores?: Record<string, any>;
  data_quality?: Record<string, any>;
}

export interface ExecutiveDashboardHealth {
  health_status: 'HEALTHY' | 'MODERATE_RISK' | 'ELEVATED' | 'CRITICAL_ACTION_REQUIRED' | string;
  health_score: number;
  total_active_findings: number;
  critical_findings_count: number;
  high_findings_count: number;
  unresolved_issues_count: number;
  active_safety_alerts_count: number;
  compliance_violations_count: number;
  overdue_inspections_count: number;
  insurance_exposure_index: number;
  open_insurance_claims_count: number;
  active_workers_count: number;
  active_equipment_count: number;
}

export interface ExecutiveCriticalFinding {
  id: string;
  finding_id: string;
  source_agent: string;
  category: string;
  severity: string;
  risk_score: number;
  title: string;
  description: string;
  location?: string;
  status: string;
  detected_at?: string;
  evidence?: string;
  navigation_url: string;
}

export interface ExecutiveSafetySnapshot {
  safety_score: number;
  ppe_compliance_rate: number;
  active_workers_count: number;
  active_alerts_count: number;
  critical_findings_count: number;
  last_assessment_date?: string;
  status: string;
}

export interface ExecutiveComplianceSnapshot {
  compliance_score: number;
  compliance_status: string;
  overdue_inspections_count: number;
  active_violations_count: number;
  critical_violations_count: number;
  last_inspection_date?: string;
  total_rules_evaluated: number;
}

export interface ExecutiveInsuranceSnapshot {
  insurance_risk_score: number;
  insurance_risk_level: string;
  exposure_index: number;
  estimated_liability_exposure: string;
  unresolved_findings_count: number;
  active_claims_count: number;
  underwriting_recommendations: string[];
  last_assessment_date?: string;
}

export interface ExecutiveDashboardResponse {
  site: ExecutiveDashboardSiteInfo;
  assessment: ExecutiveDashboardAssessment;
  health: ExecutiveDashboardHealth;
  pillar_scores: {
    site_risk?: any;
    safety_risk?: any;
    compliance_risk?: any;
    insurance_risk?: any;
    site_risk_score?: number;
    safety_risk_score?: number;
    compliance_risk_score?: number;
    insurance_risk_score?: number;
    weights?: Record<string, number>;
    [key: string]: any;
  };
  critical_findings: ExecutiveCriticalFinding[];
  recurring_patterns: RecurringPattern[];
  potential_incidents: PotentialIncidentPrediction[];
  recommendations: OperationalRecommendation[];
  safety_summary: ExecutiveSafetySnapshot;
  compliance_summary: ExecutiveComplianceSnapshot;
  insurance_summary: ExecutiveInsuranceSnapshot;
  recent_reports: GeneratedReport[];
  history: Array<{
    assessment_id: string;
    generated_at?: string;
    overall_risk_score: number;
    overall_risk_level: string;
    site_risk: number;
    safety_risk: number;
    compliance_risk: number;
    insurance_risk: number;
  }>;
  last_analysis_time: string;
  data_freshness: string;
}

// ── Agent Orchestration Types (Phase 4.4) ──────────────────────────────────

export type OrchestrationStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'PARTIAL' | 'FAILED' | 'SKIPPED';
export type OrchestrationMode = 'FULL_ANALYSIS' | 'TARGETED_ANALYSIS' | 'REFRESH' | 'REPORT_REFRESH';

export interface AgentExecutionStatus {
  agent_name: string;
  status: OrchestrationStatus;
  duration_ms: number;
  error?: string | null;
  message?: string | null;
  output_summary?: Record<string, any> | null;
}

export interface OrchestrationRunResponse {
  id: string;
  execution_id: string;
  site_id: string;
  project_id?: string | null;
  status: OrchestrationStatus;
  execution_mode: OrchestrationMode;
  requested_agents: string[];
  agent_statuses: Record<string, AgentExecutionStatus>;
  risk_intelligence_id?: string | null;
  report_id?: string | null;
  duration_ms: number;
  warnings: string[];
  errors: string[];
  created_by?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface OrchestrationRequest {
  site_id: string;
  project_id?: string | null;
  mode?: OrchestrationMode;
  agents?: string[];
  generate_report?: boolean;
  report_type?: string;
  is_simulation?: boolean;
}

export interface OrchestrationHistoryResponse {
  total: number;
  items: OrchestrationRunResponse[];
}
