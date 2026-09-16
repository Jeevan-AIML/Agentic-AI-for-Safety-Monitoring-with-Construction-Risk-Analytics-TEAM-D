import type { RiskCategory, SiteStatus, HazardStatus, EquipmentStatus, ProjectStatus, UserRole, WorkerRole, SafetyTrainingStatus, PPEStatus } from '@/types';

// ── Risk ────────────────────────────────────────────────────────────────────

export const RISK_BADGE_MAP: Record<RiskCategory, string> = {
  low: 'badge-low',
  medium: 'badge-medium',
  high: 'badge-high',
  critical: 'badge-critical',
};

export const RISK_LABEL_MAP: Record<RiskCategory, string> = {
  low: 'LOW',
  medium: 'MEDIUM',
  high: 'HIGH',
  critical: 'CRITICAL',
};

// ── Site Status ─────────────────────────────────────────────────────────────

export const SITE_STATUS_BADGE: Record<SiteStatus, string> = {
  active: 'badge-active',
  monitoring: 'badge-monitoring',
  warning: 'badge-warning',
  critical: 'badge-critical',
  inactive: 'badge-inactive',
};

export const SITE_STATUS_LABEL: Record<SiteStatus, string> = {
  active: 'ACTIVE',
  monitoring: 'MONITORING',
  warning: 'WARNING',
  critical: 'CRITICAL',
  inactive: 'INACTIVE',
};

// ── Project Status ───────────────────────────────────────────────────────────

export const PROJECT_STATUS_BADGE: Record<ProjectStatus, string> = {
  planning: 'badge-monitoring',
  active: 'badge-active',
  on_hold: 'badge-warning',
  completed: 'badge-inactive',
};

export const PROJECT_STATUS_LABEL: Record<ProjectStatus, string> = {
  planning: 'Planning',
  active: 'Active',
  on_hold: 'On Hold',
  completed: 'Completed',
};

// ── Hazard Status ─────────────────────────────────────────────────────────

export const HAZARD_STATUS_BADGE: Record<HazardStatus, string> = {
  open: 'badge-critical',
  under_review: 'badge-warning',
  mitigated: 'badge-monitoring',
  closed: 'badge-inactive',
};

export const HAZARD_STATUS_LABEL: Record<HazardStatus, string> = {
  open: 'OPEN',
  under_review: 'UNDER REVIEW',
  mitigated: 'MITIGATED',
  closed: 'CLOSED',
};

// ── Equipment Status ─────────────────────────────────────────────────────

export const EQUIPMENT_STATUS_BADGE: Record<EquipmentStatus, string> = {
  operational: 'badge-active',
  maintenance: 'badge-warning',
  out_of_service: 'badge-critical',
  inspection_due: 'badge-warning',
};

export const EQUIPMENT_STATUS_LABEL: Record<EquipmentStatus, string> = {
  operational: 'Operational',
  maintenance: 'Maintenance',
  out_of_service: 'Out of Service',
  inspection_due: 'Inspection Due',
};

// ── Role Labels ─────────────────────────────────────────────────────────

export const ROLE_LABEL: Record<UserRole, string> = {
  super_admin: 'Super Admin',
  project_manager: 'Project Manager',
  site_manager: 'Site Manager',
  safety_officer: 'Safety Officer',
  viewer: 'Viewer',
};

export const ROLE_BADGE: Record<UserRole, string> = {
  super_admin: 'badge-role-admin',
  project_manager: 'badge-role-manager',
  site_manager: 'badge-role-site',
  safety_officer: 'badge-role-safety',
  viewer: 'badge-role-viewer',
};

export const WORKER_ROLE_LABEL: Record<WorkerRole, string> = {
  operator: 'Operator',
  electrician: 'Electrician',
  mason: 'Mason',
  supervisor: 'Supervisor',
  welder: 'Welder',
  technician: 'Technician',
  general_worker: 'General Worker',
};

export const TRAINING_STATUS_LABEL: Record<SafetyTrainingStatus, string> = {
  certified: 'Certified',
  in_progress: 'In Progress',
  expired: 'Expired',
  not_started: 'Not Started',
};

export const TRAINING_STATUS_BADGE: Record<SafetyTrainingStatus, string> = {
  certified: 'badge-active',
  in_progress: 'badge-monitoring',
  expired: 'badge-critical',
  not_started: 'badge-inactive',
};

export const PPE_STATUS_BADGE: Record<PPEStatus, string> = {
  compliant: 'badge-active',
  non_compliant: 'badge-critical',
  partial: 'badge-warning',
};

// ── Hazard Type Labels ────────────────────────────────────────────────────

export const HAZARD_TYPE_LABEL: Record<string, string> = {
  environmental: 'Environmental',
  equipment: 'Equipment',
  structural: 'Structural',
  electrical: 'Electrical',
  fire: 'Fire',
  fall: 'Fall',
  excavation: 'Excavation',
  material_handling: 'Material Handling',
  other: 'Other',
};

// ── Activity Type Labels ──────────────────────────────────────────────────

export const ACTIVITY_TYPE_LABEL: Record<string, string> = {
  excavation: 'Excavation',
  concrete_work: 'Concrete Work',
  welding: 'Welding',
  electrical_work: 'Electrical Work',
  material_handling: 'Material Handling',
  demolition: 'Demolition',
  scaffolding: 'Scaffolding',
  general_construction: 'General Construction',
};

// ── Formatting ───────────────────────────────────────────────────────────

export function formatDate(dateStr?: string): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

export function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function formatRelativeTime(dateStr?: string): string {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'Just now';
}

export function formatCurrency(amount?: number): string {
  if (amount == null) return '—';
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)} Cr`;
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)} L`;
  return `₹${amount.toLocaleString('en-IN')}`;
}

export function formatScore(score: number): string {
  return score.toFixed(0);
}
