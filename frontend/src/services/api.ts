import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clearAuth();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// ── Auth ───────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  listUsers: () => api.get('/auth/users'),
  createUser: (data: object) => api.post('/auth/users', data),
  updateUser: (id: string, data: object) => api.put(`/auth/users/${id}`, data),
  deleteUser: (id: string) => api.delete(`/auth/users/${id}`),
};

// ── Dashboard ──────────────────────────────────────────────────────────────

export const dashboardApi = {
  getKPI: () => api.get('/dashboard/kpi'),
  getRiskBreakdown: (siteId?: string) =>
    api.get('/dashboard/risk-breakdown', { params: siteId ? { site_id: siteId } : {} }),
};

// ── Projects ───────────────────────────────────────────────────────────────

export const projectsApi = {
  list: (status?: string) => api.get('/projects', { params: status ? { status } : {} }),
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: object) => api.post('/projects', data),
  update: (id: string, data: object) => api.put(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
};

// ── Sites ──────────────────────────────────────────────────────────────────

export const sitesApi = {
  list: (projectId?: string) => api.get('/sites', { params: projectId ? { project_id: projectId } : {} }),
  get: (id: string) => api.get(`/sites/${id}`),
  create: (data: object) => api.post('/sites', data),
  update: (id: string, data: object) => api.put(`/sites/${id}`, data),
  delete: (id: string) => api.delete(`/sites/${id}`),
  getRiskHistory: (id: string, limit = 30) =>
    api.get(`/sites/${id}/risk-history`, { params: { limit } }),
};

// ── Workers ────────────────────────────────────────────────────────────────

export const workersApi = {
  list: (siteId?: string) => api.get('/workers', { params: siteId ? { site_id: siteId } : {} }),
  get: (id: string) => api.get(`/workers/${id}`),
  create: (data: object) => api.post('/workers', data),
  update: (id: string, data: object) => api.put(`/workers/${id}`, data),
  delete: (id: string) => api.delete(`/workers/${id}`),
};

// ── Equipment ──────────────────────────────────────────────────────────────

export const equipmentApi = {
  list: (siteId?: string) => api.get('/equipment', { params: siteId ? { site_id: siteId } : {} }),
  get: (id: string) => api.get(`/equipment/${id}`),
  create: (data: object) => api.post('/equipment', data),
  update: (id: string, data: object) => api.put(`/equipment/${id}`, data),
  delete: (id: string) => api.delete(`/equipment/${id}`),
};

// ── Activities ─────────────────────────────────────────────────────────────

export const activitiesApi = {
  list: (siteId?: string) => api.get('/activities', { params: siteId ? { site_id: siteId } : {} }),
  create: (data: object) => api.post('/activities', data),
};

// ── Hazards ────────────────────────────────────────────────────────────────

export const hazardsApi = {
  list: (siteId?: string, status?: string) =>
    api.get('/hazards', { params: { ...(siteId ? { site_id: siteId } : {}), ...(status ? { status } : {}) } }),
  create: (data: object) => api.post('/hazards', data),
  update: (id: string, data: object) => api.put(`/hazards/${id}`, data),
  acknowledge: (id: string) => api.post(`/hazards/${id}/acknowledge`),
  mitigate: (id: string, notes: string) => api.post(`/hazards/${id}/mitigate`, { mitigation_notes: notes }),
  close: (id: string) => api.post(`/hazards/${id}/close`),
};

// ── Risk Scores ────────────────────────────────────────────────────────────

export const riskApi = {
  list: (siteId?: string) => api.get('/risk-scores', { params: siteId ? { site_id: siteId } : {} }),
};

// ── Phase 1.2: Site Risk Intelligence ──────────────────────────────────────

export const riskIntelApi = {
  analyzeSite: (data: {
    site_id: string;
    weather_condition?: string;
    temperature?: number;
    wind_speed?: number;
    water_accumulation?: boolean;
    site_conditions?: string;
    activities?: string[];
    worker_count?: number;
    fire_protection_adequate?: boolean;
    scaffolding_inspected?: boolean;
    safety_controls_adequate?: boolean;
  }) => api.post('/risk/analyze-site', data),

  runDemoScenario: (siteId: string, scenarioId: number) =>
    api.post('/risk/demo-scenario', { site_id: siteId, scenario_id: scenarioId }),

  listDemoScenarios: () => api.get('/risk/demo-scenarios'),

  getSiteRiskSummary: (siteId: string) => api.get(`/risk/sites/${siteId}`),

  getSiteRiskHistory: (siteId: string, limit = 30) =>
    api.get(`/risk/sites/${siteId}/history`, { params: { limit } }),

  getSiteHazards: (siteId: string, status?: string) =>
    api.get(`/risk/sites/${siteId}/hazards`, { params: status ? { status } : {} }),
};

// ── Notifications ──────────────────────────────────────────────────────────

export const notificationsApi = {
  list: (unreadOnly = false) => api.get('/notifications', { params: { unread_only: unreadOnly } }),
  markRead: (id: string) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),
};

// ── Phase 2.1: Safety Agent ────────────────────────────────────────────────

export const safetyApi = {
  /** Execute Safety Agent on all active workers at a site */
  analyzeSite: (siteId: string) =>
    api.post(`/safety/analyze/site/${siteId}`),

  /** Execute Safety Agent compliance check for a single worker */
  analyzeWorker: (workerId: string) =>
    api.post(`/safety/analyze/worker/${workerId}`),

  /** Get the latest safety summary for a site */
  getSiteSummary: (siteId: string) =>
    api.get(`/safety/site/${siteId}`),

  /** Get safety findings for a site with optional filters */
  getSiteFindings: (siteId: string, status?: string, severity?: string) =>
    api.get(`/safety/site/${siteId}/findings`, {
      params: { ...(status ? { status } : {}), ...(severity ? { severity } : {}) },
    }),

  /** Get safety findings for a specific worker */
  getWorkerFindings: (workerId: string) =>
    api.get(`/safety/workers/${workerId}/findings`),

  /** Get a specific safety analysis by ID */
  getAnalysis: (analysisId: string) =>
    api.get(`/safety/analysis/${analysisId}`),

  /** Update finding lifecycle status (acknowledge, mitigate, close) */
  updateFinding: (findingId: string, data: { status?: string; mitigation_notes?: string }) =>
    api.patch(`/safety/findings/${findingId}`, data),

    /** List all 5 deterministic demo scenarios */
  listDemoScenarios: () =>
    api.get('/safety/demo-scenarios'),

  /** Run a specific demo scenario (1–5) against a site */
  runDemoScenario: (siteId: string, scenarioId: number) =>
    api.post('/safety/demo-scenario', { site_id: siteId, scenario_id: scenarioId }),
};

// ── PPE Computer Vision Detection APIs (Phase 2.2) ───────────────────────────

export const ppeApi = {
  /** Upload and analyze a construction site image for PPE compliance */
  analyzeImage: (formData: FormData) =>
    api.post('/safety/ppe/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  /** Retrieve a specific PPE analysis result by ID */
  getAnalysis: (analysisId: string) =>
    api.get(`/safety/ppe/analysis/${analysisId}`),

  /** List PPE analyses for a specific construction site */
  getSiteAnalyses: (siteId: string, limit = 50) =>
    api.get(`/safety/ppe/site/${siteId}`, { params: { limit } }),

  /** List PPE analyses associated with a worker */
  getWorkerAnalyses: (workerId: string, limit = 50) =>
    api.get(`/safety/ppe/worker/${workerId}`, { params: { limit } }),

  /** List predefined Phase 2.2 deterministic demo scenarios */
  listDemoScenarios: () =>
    api.get('/safety/ppe/demo-scenarios'),

  /** Execute one of the 5 predefined deterministic PPE demo scenarios */
  runDemoScenario: (scenarioId: number, siteId?: string, workerId?: string, isHighRisk = false) =>
    api.post('/safety/ppe/demo-scenario', null, {
      params: {
        scenario_id: scenarioId,
        site_id: siteId,
        worker_id: workerId,
        is_high_risk: isHighRisk,
      },
    }),
};

// ── Worker Safety Monitoring APIs (Phase 2.3) ───────────────────────────────

export const monitoringApi = {
  /** Start live safety monitoring on a site */
  startMonitoring: (siteId: string) =>
    api.post(`/safety/monitoring/start/${siteId}`),

  /** Stop live safety monitoring on a site */
  stopMonitoring: (siteId: string) =>
    api.post(`/safety/monitoring/stop/${siteId}`),

  /** Evaluate real-time safety conditions for a worker against 8 monitoring rules */
  evaluateWorker: (workerId: string, data?: object) =>
    api.post(`/safety/monitoring/evaluate/${workerId}`, data || {}),

  /** Get live monitoring status and active alerts for a site */
  getSiteMonitoring: (siteId: string) =>
    api.get(`/safety/monitoring/site/${siteId}`),

  /** Get recent safety monitoring events for a worker */
  getWorkerMonitoringHistory: (workerId: string) =>
    api.get(`/safety/monitoring/worker/${workerId}`),

  /** List deterministic demo scenarios for Phase 2.3 */
  listDemoScenarios: () =>
    api.get('/safety/monitoring/demo-scenarios'),

  /** Run a deterministic demo scenario */
  runDemoScenario: (scenarioId: number, siteId?: string) =>
    api.post('/safety/monitoring/demo-scenario', { scenario_id: scenarioId, site_id: siteId }),
};

// ── Safety Alert System APIs (Phase 2.4) ────────────────────────────────────

export const alertsApi = {
  /** List alerts with optional filtering */
  getAlerts: (params?: { site_id?: string; worker_id?: string; status?: string; severity?: string; limit?: number }) =>
    api.get('/safety/alerts', { params }),

  /** Get detailed alert data including audit trail and dispatched notifications */
  getAlertDetail: (alertId: string) =>
    api.get(`/safety/alerts/${alertId}`),

  /** Acknowledge an alert */
  acknowledgeAlert: (alertId: string, notes?: string) =>
    api.post(`/safety/alerts/${alertId}/acknowledge`, { notes }),

  /** Resolve an alert with corrective notes */
  resolveAlert: (alertId: string, notes: string) =>
    api.post(`/safety/alerts/${alertId}/resolve`, { notes }),

  /** Escalate an alert */
  escalateAlert: (alertId: string, reason?: string, targetRole?: string) =>
    api.post(`/safety/alerts/${alertId}/escalate`, { reason, target_role: targetRole }),

  /** Get alerts for a site */
  getSiteAlerts: (siteId: string) =>
    api.get(`/safety/alerts/site/${siteId}`),

  /** Get alerts for a worker */
  getWorkerAlerts: (workerId: string) =>
    api.get(`/safety/alerts/worker/${workerId}`),

  /** List deterministic demo scenarios */
  listDemoScenarios: () =>
    api.get('/safety/alerts/demo-scenarios'),

  /** Run a deterministic demo scenario */
  runDemoScenario: (scenarioId: number, siteId?: string) =>
    api.post('/safety/alerts/demo-scenario', { scenario_id: scenarioId, site_id: siteId }),

  /** Check and evaluate escalation timeouts */
  checkTimeouts: () =>
    api.post('/safety/alerts/check-timeouts'),
};

// ── Real-Time Video Surveillance APIs (Phase 3.1) ───────────────────────────

export const videoApi = {
  /** Start a live/demo/RTSP video surveillance stream */
  startStream: (data: {
    site_id: string;
    camera_name?: string;
    source_type?: string;
    source_url?: string;
    fps?: number;
    sampling_interval_frames?: number;
    confidence_threshold?: number;
  }) => api.post('/safety/video/streams/start', data),

  /** Stop an active video surveillance stream */
  stopStream: (streamId: string) =>
    api.post(`/safety/video/streams/stop/${streamId}`),

  /** List video streams with optional filters */
  listStreams: (params?: { site_id?: string; status?: string; limit?: number }) =>
    api.get('/safety/video/streams', { params }),

  /** Get detailed stream info */
  getStream: (streamId: string) =>
    api.get(`/safety/video/streams/${streamId}`),

  /** Get stream safety events */
  getStreamEvents: (streamId: string, limit = 50) =>
    api.get(`/safety/video/streams/${streamId}/events`, { params: { limit } }),

  /** Process a single frame */
  processFrame: (streamId: string, data?: { frame_number?: number; scenario_id?: number; metadata?: object }) =>
    api.post(`/safety/video/streams/${streamId}/process-frame`, data || {}),

  /** Get streams for a site */
  getSiteStreams: (siteId: string, limit = 50) =>
    api.get(`/safety/video/sites/${siteId}/streams`, { params: { limit } }),

  /** Get aggregated live surveillance status for a site */
  getSiteLiveStatus: (siteId: string) =>
    api.get(`/safety/video/sites/${siteId}/live-status`),

  /** Get camera/scene zones configured for a site */
  getSiteZones: (siteId: string) =>
    api.get(`/safety/video/zones/${siteId}`),

  /** Configure a new camera zone */
  createZone: (data: object) =>
    api.post('/safety/video/zones', data),

  /** List deterministic demo scenarios for Phase 3.1 */
  listDemoScenarios: () =>
    api.get('/safety/video/demo-scenarios'),

  /** Execute a deterministic video surveillance demo scenario */
  runDemoScenario: (scenarioId: number, siteId?: string) =>
    api.post('/safety/video/demo-scenario', { scenario_id: scenarioId, site_id: siteId }),
};

// ── Phase 3.2 Drone Aerial Inspection API ────────────────────────────────────

export const droneApi = {
  /** Start a drone aerial inspection session for a site */
  startInspection: (siteId: string, data?: { drone_identifier?: string; notes?: string; is_simulation?: boolean }) =>
    api.post(`/safety/drone/inspection/start/${siteId}`, data || {}),

  /** Stop active drone inspection session for a site */
  stopInspection: (siteId: string, data?: { notes?: string }) =>
    api.post(`/safety/drone/inspection/stop/${siteId}`, data || {}),

  /** Get inspection session details */
  getInspection: (inspectionId: string) =>
    api.get(`/safety/drone/inspection/${inspectionId}`),

  /** List inspection sessions for a site */
  getSiteInspections: (siteId: string) =>
    api.get(`/safety/drone/inspection/site/${siteId}`),

  /** Execute aerial analysis and photogrammetry hazard detection */
  analyzeInspection: (inspectionId: string, data?: { scenario_id?: number; coverage_area_sqm?: number; altitude_m?: number }) =>
    api.post(`/safety/drone/inspection/${inspectionId}/analyze`, data || {}),

  /** Get aerial hazard findings for an inspection */
  getInspectionFindings: (inspectionId: string) =>
    api.get(`/safety/drone/inspection/${inspectionId}/findings`),

  /** Get flight path telemetry points */
  getFlightPath: (inspectionId: string) =>
    api.get(`/safety/drone/inspection/${inspectionId}/flight-path`),

  /** List deterministic drone demo scenarios */
  listDemoScenarios: () =>
    api.get('/safety/drone/demo-scenarios'),

  /** Execute a deterministic demo scenario */
  runDemoScenario: (scenarioId: number, siteId?: string) =>
    api.post('/safety/drone/demo-scenario', { scenario_id: scenarioId, site_id: siteId }),
};

// ── Phase 3.3 Multi-Modal Hazard Correlation & Predictive Spatial Risk ────────

export const correlationApi = {
  /** Trigger multi-modal correlation assessment for a site */
  analyzeSite: (siteId: string, data?: { is_simulation?: boolean; force_refresh?: boolean }) =>
    api.post(`/safety/correlation/analyze/${siteId}`, data || {}),

  /** Get latest assessment for a site */
  getSiteAssessment: (siteId: string) =>
    api.get(`/safety/correlation/site/${siteId}`),

  /** Get assessment by ID */
  getAssessment: (assessmentId: string) =>
    api.get(`/safety/correlation/assessment/${assessmentId}`),

  /** Get spatial risk zones & heatmaps */
  getSpatialRisk: (siteId: string) =>
    api.get(`/safety/correlation/site/${siteId}/spatial-risk`),

  /** Get active correlated hazards */
  getSiteCorrelations: (siteId: string) =>
    api.get(`/safety/correlation/site/${siteId}/correlations`),

  /** List deterministic correlation demo scenarios */
  listDemoScenarios: () =>
    api.get('/safety/correlation/demo-scenarios'),

  /** Execute a deterministic correlation demo scenario */
  runDemoScenario: (scenarioId: number, siteId?: string) =>
    api.post('/safety/correlation/demo-scenarios/run', { scenario_id: scenarioId, site_id: siteId }),
};

// ── Milestone 3 Compliance Intelligence ────────────────────────────────────

export const complianceApi = {
  /** Trigger regulatory compliance analysis for a site */
  analyzeSite: (siteId: string, data?: { is_simulation?: boolean; scenario_id?: number }) =>
    api.post(`/compliance/analyze/${siteId}`, data || {}),

  /** Get latest compliance assessment for a site */
  getLatestAssessment: (siteId: string) =>
    api.get(`/compliance/assessments/${siteId}/latest`),

  /** List active regulatory compliance rules */
  listRules: (category?: string) =>
    api.get('/compliance/rules', { params: category ? { category } : {} }),

  /** List compliance findings for a site */
  listFindings: (siteId: string, ruleId?: string) =>
    api.get(`/compliance/findings/${siteId}`, { params: ruleId ? { rule_id: ruleId } : {} }),

  /** List statutory inspection requirements */
  listInspections: (siteId: string, status?: string) =>
    api.get(`/compliance/inspections/${siteId}`, { params: status ? { status } : {} }),

  /** Create a new statutory inspection requirement */
  createInspection: (siteId: string, data: any) =>
    api.post(`/compliance/inspections/${siteId}`, data),

  /** Get structured executive compliance report */
  getComplianceReport: (siteId: string) =>
    api.get(`/compliance/reports/${siteId}`),

  /** List deterministic compliance demo scenarios */
  listDemoScenarios: () =>
    api.get('/compliance/demo-scenarios'),

  /** Run a deterministic compliance demo scenario */
  runDemoScenario: (scenarioId: number, siteId?: string) =>
    api.post('/compliance/demo-scenarios/run', { scenario_id: scenarioId, site_id: siteId }),
};

// ── Milestone 3 Insurance Intelligence ─────────────────────────────────────

export const insuranceApi = {
  /** Assess underwriting insurance exposure for a site */
  assessSite: (siteId: string, data?: { is_simulation?: boolean; scenario_id?: number }) =>
    api.post(`/insurance/assess/${siteId}`, data || {}),

  /** Get latest insurance risk assessment for a site */
  getLatestAssessment: (siteId: string) =>
    api.get(`/insurance/assessments/${siteId}/latest`),

  /** Evaluate incident severity and calculate claim risk */
  assessClaim: (siteId: string, data: any) =>
    api.post(`/insurance/claims/assess/${siteId}`, data),

  /** Generate verified claim documentation package */
  generateClaimPackage: (claimAssessmentId: string, data?: any) =>
    api.post(`/insurance/claims/${claimAssessmentId}/package`, data || {}),

  /** Retrieve claim documentation package */
  getClaimPackage: (claimAssessmentId: string) =>
    api.get(`/insurance/claims/${claimAssessmentId}/package`),

  /** List deterministic insurance demo scenarios */
  listDemoScenarios: () =>
    api.get('/insurance/demo-scenarios'),

  /** Run a deterministic insurance demo scenario */
  runDemoScenario: (scenarioId: number, siteId?: string) =>
    api.post('/insurance/demo-scenarios/run', { scenario_id: scenarioId, site_id: siteId }),
};




