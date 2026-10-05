import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  HardHat, ShieldCheck, AlertTriangle, Zap, Play, ChevronDown,
  RefreshCw, X, CheckCircle2, Wrench, Lock, Eye, BarChart3,
  Users, FileSearch, Search, Filter, Activity, Shield,
  Camera, Upload, Sparkles, Image as ImageIcon,
  Radio, Square, AlertOctagon, Clock, UserCheck, Check, ShieldAlert,
  BellRing, ArrowUpRight, MessageSquare, AlertCircle, History, Video,
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import { safetyApi, sitesApi, ppeApi, monitoringApi, workersApi, alertsApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { EmptyState } from '@/components/common';
import { PPEViewer } from '@/components/common/PPEViewer';
import { LiveVideoMonitoring } from './LiveVideoMonitoring';
import { RISK_BADGE_MAP, RISK_LABEL_MAP, formatDate, formatRelativeTime } from '@/utils/display';
import type {
  SafetyFinding, SafetyAnalysisResponse, SafetyDemoScenario,
  SiteSafetySummary, Site, PPEAnalysis, PPEDemoScenario,
  WorkerMonitoringEvaluation, SiteMonitoringStatus, MonitoringDemoScenario,
  WorkerSafetyStatus, Worker, SafetyAlert, AlertSeverity, AlertStatus,
  AlertDemoScenario, AlertAuditEvent, AlertNotification,
} from '@/types';

// ── Constants ────────────────────────────────────────────────────────────────

const WRITE_ROLES = ['super_admin', 'project_manager', 'site_manager', 'safety_officer', 'viewer'];

const FINDING_TYPE_LABEL: Record<string, string> = {
  ppe_violation: 'PPE Violation',
  expired_training: 'Expired Training',
  missing_training: 'Missing Training',
  unsafe_equipment_operation: 'Unsafe Equipment',
  high_risk_activity: 'High-Risk Activity',
  high_risk_zone_exposure: 'Zone Exposure',
};

const FINDING_TYPE_ICON: Record<string, React.ReactNode> = {
  ppe_violation: <HardHat size={12} />,
  expired_training: <AlertTriangle size={12} />,
  missing_training: <AlertTriangle size={12} />,
  unsafe_equipment_operation: <Zap size={12} />,
  high_risk_activity: <ShieldCheck size={12} />,
  high_risk_zone_exposure: <Shield size={12} />,
};

const FINDING_STATUS_BADGE: Record<string, string> = {
  open: 'badge-critical',
  acknowledged: 'badge-warning',
  mitigated: 'badge-monitoring',
  closed: 'badge-active',
};

const FINDING_STATUS_LABEL: Record<string, string> = {
  open: 'Open',
  acknowledged: 'Acknowledged',
  mitigated: 'Mitigated',
  closed: 'Closed',
};

const ALERT_STATUS_BADGE: Record<string, string> = {
  open: 'badge-critical',
  acknowledged: 'badge-warning',
  escalated: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  resolved: 'badge-active',
  dismissed: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const ALERT_SEVERITY_BADGE: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-warning',
};

const SCENARIO_COLORS = [
  'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20',
  'from-amber-500/20 to-amber-600/5 border-amber-500/20',
  'from-orange-500/20 to-orange-600/5 border-orange-500/20',
  'from-red-500/20 to-red-600/5 border-red-500/20',
  'from-red-600/20 to-red-700/5 border-red-600/20',
];

const SCENARIO_LEVEL_COLOR = [
  'text-emerald-400',
  'text-amber-400',
  'text-orange-400',
  'text-red-400',
  'text-red-500',
];

// ── Sub-components ────────────────────────────────────────────────────────────

function AgentStatusBadge() {
  return (
    <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
      <div className="relative flex items-center justify-center">
        <span className="absolute w-3 h-3 rounded-full bg-emerald-500 animate-ping opacity-40" />
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
      </div>
      <div className="flex flex-col leading-tight">
        <span className="text-xs font-bold text-emerald-300 tracking-wide">SafetyAgent v1.0.0</span>
        <span className="text-[10px] text-emerald-500/80 font-mono">RULE_ENGINE · ACTIVE</span>
      </div>
    </div>
  );
}

function MetricCard({
  label, value, sub, color = 'text-slate-200', icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
  icon: React.ReactNode;
}) {
  const bgClass =
    color === 'text-red-400' ? 'bg-red-500/10' :
    color === 'text-amber-400' ? 'bg-amber-500/10' :
    color === 'text-emerald-400' ? 'bg-emerald-500/10' :
    color === 'text-orange-400' ? 'bg-orange-500/10' :
    'bg-primary-500/10';

  return (
    <div className="card p-5 flex items-start gap-4">
      <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center shrink-0', bgClass)}>
        <span className={color}>{icon}</span>
      </div>
      <div>
        <div className={clsx('text-2xl font-bold', color)}>{value}</div>
        <div className="text-xs text-slate-500 font-medium mt-0.5">{label}</div>
        {sub && <div className="text-[11px] text-slate-600 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

interface FindingRowProps {
  finding: SafetyFinding;
  canWrite: boolean;
  onAcknowledge: (id: string) => void;
  onMitigate: (f: SafetyFinding) => void;
  onClose: (id: string) => void;
}

function FindingRow({ finding, canWrite, onAcknowledge, onMitigate, onClose }: FindingRowProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="cursor-pointer hover:bg-white/[0.02] transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        <td className="font-mono text-xs text-slate-500 font-semibold">{finding.finding_id}</td>
        <td>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">{FINDING_TYPE_ICON[finding.finding_type]}</span>
            <span className="text-xs text-slate-300">{FINDING_TYPE_LABEL[finding.finding_type]}</span>
          </div>
        </td>
        <td>
          {finding.worker_name ? (
            <div className="flex flex-col">
              <span className="text-sm font-medium text-slate-200">{finding.worker_name}</span>
              <span className="text-[10px] font-mono text-slate-600">{finding.worker_code}</span>
            </div>
          ) : (
            <span className="text-slate-600 text-xs">Site-wide</span>
          )}
        </td>
        <td>
          <span className={clsx('badge text-xs uppercase', RISK_BADGE_MAP[finding.severity])}>
            {RISK_LABEL_MAP[finding.severity]}
          </span>
        </td>
        <td>
          <span className={clsx('badge text-xs', FINDING_STATUS_BADGE[finding.status])}>
            {FINDING_STATUS_LABEL[finding.status]}
          </span>
        </td>
        <td className="text-xs text-slate-500">{formatRelativeTime(finding.created_at)}</td>
        <td onClick={e => e.stopPropagation()}>
          <div className="flex gap-1.5">
            {finding.status === 'open' && canWrite && (
              <button
                className="btn-ghost text-xs py-1 px-2"
                onClick={() => onAcknowledge(finding.id)}
              >
                Acknowledge
              </button>
            )}
            {finding.status === 'acknowledged' && canWrite && (
              <button
                className="btn-ghost text-xs py-1 px-2 text-emerald-400 border-emerald-500/20"
                onClick={() => onMitigate(finding)}
              >
                Mitigate
              </button>
            )}
            {finding.status === 'mitigated' && canWrite && (
              <button
                className="btn-ghost text-xs py-1 px-2 text-slate-400"
                onClick={() => onClose(finding.id)}
              >
                Close
              </button>
            )}
            {!canWrite && (
              <span className="text-xs text-slate-700 flex items-center gap-1">
                <Lock size={10} /> View only
              </span>
            )}
          </div>
        </td>
        <td>
          <ChevronDown
            size={14}
            className={clsx('text-slate-600 transition-transform', expanded && 'rotate-180')}
          />
        </td>
      </tr>
      <AnimatePresence>
        {expanded && (
          <tr>
            <td colSpan={8} className="p-0 border-0">
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="px-5 py-4 bg-surface-800/50 border-b border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wider">Evidence</p>
                    <p className="text-slate-300">{finding.evidence || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wider">Recommendation</p>
                    <p className="text-slate-300">{finding.recommendation || '—'}</p>
                  </div>
                  {finding.mitigation_notes && (
                    <div className="md:col-span-2">
                      <p className="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wider">Mitigation Notes</p>
                      <p className="text-slate-300">{finding.mitigation_notes}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wider">Detection Source</p>
                    <span className="font-mono text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded">
                      {finding.detection_source}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wider">Detected</p>
                    <p className="text-slate-400">{formatDate(finding.created_at)}</p>
                  </div>
                </div>
              </motion.div>
            </td>
          </tr>
        )}
      </AnimatePresence>
    </>
  );
}

// ── Mitigate Modal ────────────────────────────────────────────────────────────

function MitigateModal({
  finding, onClose, onSubmit,
}: {
  finding: SafetyFinding;
  onClose: () => void;
  onSubmit: (notes: string) => void;
}) {
  const [notes, setNotes] = useState('');
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="card w-full max-w-md p-6"
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <Wrench size={16} className="text-emerald-400" />
            </div>
            <h3 className="font-semibold text-slate-200">Mark as Mitigated</h3>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5">
            <X size={16} />
          </button>
        </div>
        <p className="text-sm text-slate-400 mb-1">
          Finding: <span className="text-slate-300 font-medium">{finding.finding_id}</span>
        </p>
        <p className="text-sm text-slate-500 mb-4">{finding.description}</p>
        <label className="block text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">
          Mitigation Notes <span className="text-red-400">*</span>
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Describe the corrective actions taken…"
          rows={4}
          className="input resize-none w-full text-sm"
        />
        <div className="flex gap-3 mt-5">
          <button className="btn-ghost flex-1" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary flex-1"
            disabled={!notes.trim()}
            onClick={() => onSubmit(notes.trim())}
          >
            <CheckCircle2 size={14} /> Confirm Mitigation
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── Alert Modals (Phase 2.4) ──────────────────────────────────────────────────

function AlertDetailModal({
  alert,
  onClose,
  onAcknowledge,
  onResolve,
  onEscalate,
  canAck,
  canResolve,
  canEscalate,
}: {
  alert: SafetyAlert;
  onClose: () => void;
  onAcknowledge: () => void;
  onResolve: () => void;
  onEscalate: () => void;
  canAck: boolean;
  canResolve: boolean;
  canEscalate: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="card w-full max-w-2xl max-h-[90vh] flex flex-col p-6 overflow-hidden my-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className={clsx(
              'w-9 h-9 rounded-xl flex items-center justify-center',
              alert.severity === 'critical' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'
            )}>
              <AlertOctagon size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-slate-400">{alert.alert_id}</span>
                <span className={clsx('badge text-[10px] uppercase font-mono', ALERT_SEVERITY_BADGE[alert.severity])}>
                  {alert.severity}
                </span>
                <span className={clsx('badge text-[10px] uppercase font-mono', ALERT_STATUS_BADGE[alert.status])}>
                  {alert.status}
                </span>
                {alert.is_simulation && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 font-bold">
                    DEMO / SIMULATION
                  </span>
                )}
              </div>
              <h3 className="text-base font-bold text-slate-100 mt-0.5">{alert.title}</h3>
            </div>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5">
            <X size={16} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 text-xs">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-lg bg-surface-950/60 border border-slate-800/80">
            <div>
              <span className="text-slate-500 text-[11px] block">Site</span>
              <span className="font-medium text-slate-200">{alert.site_name || alert.site_id}</span>
            </div>
            <div>
              <span className="text-slate-500 text-[11px] block">Worker</span>
              <span className="font-medium text-slate-200">{alert.worker_name || alert.worker_id || 'All / Site-wide'}</span>
            </div>
            <div>
              <span className="text-slate-500 text-[11px] block">Assigned Role</span>
              <span className="font-mono text-primary-400 font-semibold">{alert.assigned_role || 'safety_officer'}</span>
            </div>
            <div>
              <span className="text-slate-500 text-[11px] block">Escalation Tier</span>
              <span className="font-mono font-bold text-purple-400">Level {alert.escalation_level}</span>
            </div>
          </div>

          {/* Description & Evidence */}
          <div className="space-y-2">
            <div>
              <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px]">Description</h4>
              <p className="text-slate-300 mt-1 leading-relaxed">{alert.description}</p>
            </div>
            {alert.evidence && (
              <div>
                <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px]">Telemetry Evidence</h4>
                <div className="p-2.5 rounded bg-surface-950/80 border border-slate-800/80 text-slate-300 font-mono text-[11px] mt-1">
                  {alert.evidence}
                </div>
              </div>
            )}
            {alert.recommendation && (
              <div>
                <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px]">Required Recommendation</h4>
                <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs mt-1">
                  {alert.recommendation}
                </div>
              </div>
            )}
            {alert.resolution_notes && (
              <div>
                <h4 className="font-semibold text-emerald-400 uppercase tracking-wider text-[11px]">Resolution Notes</h4>
                <div className="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs mt-1">
                  {alert.resolution_notes}
                </div>
              </div>
            )}
          </div>

          {/* Dispatched Notifications */}
          <div>
            <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] flex items-center gap-1.5 mb-2">
              <BellRing size={13} className="text-primary-400" />
              Dispatched Multi-Channel Notifications ({alert.notifications?.length || 0})
            </h4>
            {(!alert.notifications || alert.notifications.length === 0) ? (
              <p className="text-slate-500 italic text-[11px]">No notifications recorded for this alert.</p>
            ) : (
              <div className="space-y-1.5">
                {alert.notifications.map((n, i) => (
                  <div
                    key={n.id || i}
                    className="p-2 rounded bg-surface-950/60 border border-slate-800/70 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5"
                  >
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        'px-1.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase',
                        n.channel === 'in_app'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : n.channel === 'email_adapter'
                          ? 'bg-blue-500/20 text-blue-300'
                          : 'bg-purple-500/20 text-purple-300'
                      )}>
                        {n.channel}
                      </span>
                      <span className="font-medium text-slate-300">To: {n.recipient_role}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono">
                      <span className={n.status === 'DELIVERED' ? 'text-emerald-400 font-semibold' : 'text-amber-400'}>
                        {n.status}
                      </span>
                      <span>·</span>
                      <span>{formatRelativeTime(n.sent_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Audit History Timeline */}
          <div>
            <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] flex items-center gap-1.5 mb-2">
              <History size={13} className="text-amber-400" />
              Audit Trail &amp; Lifecycle Transitions ({alert.audit_events?.length || 0})
            </h4>
            {(!alert.audit_events || alert.audit_events.length === 0) ? (
              <p className="text-slate-500 italic text-[11px]">No audit events logged.</p>
            ) : (
              <div className="space-y-2 border-l-2 border-slate-800 pl-3 ml-1.5">
                {alert.audit_events.map((evt, i) => (
                  <div key={evt.id || i} className="relative">
                    <div className="absolute -left-[19px] top-1 w-2.5 h-2.5 rounded-full bg-slate-700 border-2 border-surface-900" />
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="font-mono font-bold text-slate-300 text-[11px] uppercase">
                        {evt.event_type}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {formatRelativeTime(evt.created_at)}
                      </span>
                    </div>
                    <p className="text-slate-400 text-xs mt-0.5">{evt.details}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      Actor: <strong className="text-slate-400">{evt.actor_name || 'System'}</strong> ({evt.actor_role || 'system'})
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2">
          <div className="text-[11px] text-slate-500">
            Created: {formatDate(alert.created_at)}
          </div>
          <div className="flex items-center gap-2">
            {alert.status !== 'resolved' && (
              <>
                {canAck && alert.status === 'open' && (
                  <button
                    className="btn-ghost text-xs border border-amber-500/30 text-amber-300 hover:bg-amber-500/10"
                    onClick={onAcknowledge}
                  >
                    <Check size={12} /> Acknowledge
                  </button>
                )}
                {canEscalate && (
                  <button
                    className="btn-ghost text-xs border border-purple-500/30 text-purple-300 hover:bg-purple-500/10"
                    onClick={onEscalate}
                  >
                    <ArrowUpRight size={12} /> Escalate
                  </button>
                )}
                {canResolve && (
                  <button
                    className="btn-primary text-xs"
                    onClick={onResolve}
                  >
                    <CheckCircle2 size={12} /> Resolve Alert
                  </button>
                )}
              </>
            )}
            <button className="btn-ghost text-xs" onClick={onClose}>Close</button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function AlertAckModal({
  alert,
  onClose,
  onSubmit,
}: {
  alert: SafetyAlert;
  onClose: () => void;
  onSubmit: (notes?: string) => void;
}) {
  const [notes, setNotes] = useState('');
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="card w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
              <Check size={16} />
            </div>
            <h3 className="font-semibold text-slate-200">Acknowledge Alert</h3>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5"><X size={16} /></button>
        </div>
        <p className="text-xs text-slate-400 mb-1">
          Alert: <span className="font-mono text-slate-300 font-semibold">{alert.alert_id}</span>
        </p>
        <p className="text-xs text-slate-500 mb-4">{alert.title}</p>
        <label className="block text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">
          Acknowledgment Notes (Optional)
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="e.g. Safety officer responding to site location..."
          rows={3}
          className="input resize-none w-full text-xs"
        />
        <div className="flex gap-2.5 mt-5">
          <button className="btn-ghost flex-1 text-xs" onClick={onClose}>Cancel</button>
          <button className="btn-primary flex-1 text-xs" onClick={() => onSubmit(notes.trim() || undefined)}>
            Confirm Acknowledgment
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function AlertResolveModal({
  alert,
  onClose,
  onSubmit,
}: {
  alert: SafetyAlert;
  onClose: () => void;
  onSubmit: (notes: string) => void;
}) {
  const [notes, setNotes] = useState('');
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="card w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <CheckCircle2 size={16} />
            </div>
            <h3 className="font-semibold text-slate-200">Resolve Safety Alert</h3>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5"><X size={16} /></button>
        </div>
        <p className="text-xs text-slate-400 mb-1">
          Alert: <span className="font-mono text-slate-300 font-semibold">{alert.alert_id}</span>
        </p>
        <p className="text-xs text-slate-500 mb-4">{alert.title}</p>
        <label className="block text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">
          Corrective Action / Mitigation Notes <span className="text-red-400">*</span>
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Describe how the hazard was remediated and worker conditions stabilized..."
          rows={4}
          className="input resize-none w-full text-xs"
        />
        <div className="flex gap-2.5 mt-5">
          <button className="btn-ghost flex-1 text-xs" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary flex-1 text-xs"
            disabled={!notes.trim()}
            onClick={() => onSubmit(notes.trim())}
          >
            Confirm Resolution
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function AlertEscalateModal({
  alert,
  onClose,
  onSubmit,
}: {
  alert: SafetyAlert;
  onClose: () => void;
  onSubmit: (reason?: string, targetRole?: string) => void;
}) {
  const [reason, setReason] = useState('');
  const [targetRole, setTargetRole] = useState(alert.escalation_level === 0 ? 'site_manager' : 'super_admin');
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="card w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
              <ArrowUpRight size={16} />
            </div>
            <h3 className="font-semibold text-slate-200">Escalate Alert</h3>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5"><X size={16} /></button>
        </div>
        <p className="text-xs text-slate-400 mb-1">
          Escalating: <span className="font-mono text-slate-300 font-semibold">{alert.alert_id}</span>
        </p>
        <p className="text-xs text-slate-500 mb-4">Current Level: {alert.escalation_level} ({alert.assigned_role || 'safety_officer'})</p>

        <label className="block text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">
          Target Role
        </label>
        <select
          value={targetRole}
          onChange={e => setTargetRole(e.target.value)}
          className="input text-xs w-full mb-3"
        >
          <option value="site_manager">Site Manager (Level 1)</option>
          <option value="project_manager">Project Manager (Level 1)</option>
          <option value="super_admin">Super Admin (Level 2)</option>
        </select>

        <label className="block text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">
          Escalation Reason (Optional)
        </label>
        <textarea
          value={reason}
          onChange={e => setReason(e.target.value)}
          placeholder="e.g. Unresponsive onsite response or immediate supervisor intervention needed..."
          rows={3}
          className="input resize-none w-full text-xs"
        />
        <div className="flex gap-2.5 mt-5">
          <button className="btn-ghost flex-1 text-xs" onClick={onClose}>Cancel</button>
          <button className="btn-primary flex-1 text-xs" onClick={() => onSubmit(reason.trim() || undefined, targetRole)}>
            Confirm Escalation
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function SafetyPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const canWrite = WRITE_ROLES.includes(user?.role ?? '');

  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [analysisResult, setAnalysisResult] = useState<SafetyAnalysisResponse | null>(null);
  const [mitigateTarget, setMitigateTarget] = useState<SafetyFinding | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [runningScenario, setRunningScenario] = useState<number | null>(null);

  // ── Data Fetching ──────────────────────────────────────────────────────────

  const { data: sites } = useQuery<Site[]>({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  useEffect(() => {
    if (!selectedSiteId && sites && sites.length > 0) {
      setSelectedSiteId(sites[0].id);
    }
  }, [selectedSiteId, sites]);

  const { data: safetySummary, refetch: refetchSummary } = useQuery<SiteSafetySummary>({
    queryKey: ['safety-summary', selectedSiteId],
    queryFn: () => safetyApi.getSiteSummary(selectedSiteId).then(r => r.data),
    enabled: !!selectedSiteId,
  });

  const { data: findings, refetch: refetchFindings } = useQuery<SafetyFinding[]>({
    queryKey: ['safety-findings', selectedSiteId, filterStatus, filterSeverity],
    queryFn: () =>
      safetyApi.getSiteFindings(selectedSiteId, filterStatus || undefined, filterSeverity || undefined)
        .then(r => r.data),
    enabled: !!selectedSiteId,
  });

  const { data: demoScenarios } = useQuery<SafetyDemoScenario[]>({
    queryKey: ['safety-demo-scenarios'],
    queryFn: () => safetyApi.listDemoScenarios().then(r => r.data),
  });

  // ── Mutations ──────────────────────────────────────────────────────────────

  const analyzeMutation = useMutation({
    mutationFn: () => safetyApi.analyzeSite(selectedSiteId),
    onSuccess: r => {
      setAnalysisResult(r.data);
      refetchSummary();
      refetchFindings();
      queryClient.invalidateQueries({ queryKey: ['safety-findings', selectedSiteId] });
      toast.success(`Analysis complete — ${r.data.summary.violation_count} finding(s) detected`);
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Safety analysis failed');
    },
  });

  const scenarioMutation = useMutation({
    mutationFn: ({ scenarioId }: { scenarioId: number }) =>
      safetyApi.runDemoScenario(selectedSiteId, scenarioId),
    onSuccess: (r, { scenarioId }) => {
      setRunningScenario(null);
      setAnalysisResult(r.data);
      refetchSummary();
      refetchFindings();
      const lvl = r.data.summary.safety_level?.toUpperCase();
      toast.success(`Scenario ${scenarioId} → ${lvl} · ${r.data.summary.violation_count} finding(s)`);
    },
    onError: (err: any) => {
      setRunningScenario(null);
      toast.error(err.response?.data?.detail || 'Demo scenario failed');
    },
  });

  const findingUpdateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: object }) =>
      safetyApi.updateFinding(id, data),
    onSuccess: () => {
      refetchFindings();
      refetchSummary();
      setMitigateTarget(null);
      toast.success('Finding updated');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Update failed');
    },
  });

  const handleRunScenario = (id: number) => {
    if (!selectedSiteId) {
      toast.error('Select a site first');
      return;
    }
    setRunningScenario(id);
    scenarioMutation.mutate({ scenarioId: id });
  };

  const [activeTab, setActiveTab] = useState<'monitoring' | 'ppe_vision' | 'worker_monitoring' | 'live_video'>('monitoring');
  const [ppeFile, setPpeFile] = useState<File | null>(null);
  const [ppeWorkerId, setPpeWorkerId] = useState<string>('');
  const [ppeIsHighRisk, setPpeIsHighRisk] = useState<boolean>(false);
  const [ppeAnalysisResult, setPpeAnalysisResult] = useState<PPEAnalysis | null>(null);
  const [runningPpeScenario, setRunningPpeScenario] = useState<number | null>(null);

  // ── Phase 2.3 Worker Monitoring State ───────────────────────────────────────
  const [selectedWorkerId, setSelectedWorkerId] = useState<string>('');
  const [monActivity, setMonActivity] = useState<string>('excavation');
  const [monZone, setMonZone] = useState<string>('Zone A — Deep Excavation Pit');
  const [monIsHighRiskZone, setMonIsHighRiskZone] = useState<boolean>(true);
  const [monTimeInZone, setMonTimeInZone] = useState<number>(30);
  const [monNearbyHazards, setMonNearbyHazards] = useState<string>('HAZ-002: Trench Wall Instability');
  const [monNearbyEquipment, setMonNearbyEquipment] = useState<string>('');
  const [monWorkersInZone, setMonWorkersInZone] = useState<number>(2);
  const [monEvaluationResult, setMonEvaluationResult] = useState<WorkerMonitoringEvaluation | null>(null);
  const [runningMonScenario, setRunningMonScenario] = useState<number | null>(null);

  // Queries for Phase 2.3
  const { data: siteMonitoring, refetch: refetchSiteMonitoring } = useQuery<SiteMonitoringStatus>({
    queryKey: ['site-monitoring', selectedSiteId],
    queryFn: () => monitoringApi.getSiteMonitoring(selectedSiteId).then(r => r.data),
    enabled: !!selectedSiteId,
    refetchInterval: 10000,
  });

  const { data: siteWorkers } = useQuery<Worker[]>({
    queryKey: ['site-workers', selectedSiteId],
    queryFn: () => workersApi.list(selectedSiteId).then(r => r.data),
    enabled: !!selectedSiteId,
  });

  const { data: monDemoScenarios } = useQuery<MonitoringDemoScenario[]>({
    queryKey: ['monitoring-demo-scenarios'],
    queryFn: () => monitoringApi.listDemoScenarios().then(r => r.data),
  });

  // Mutations for Phase 2.3
  const startMonitoringMutation = useMutation({
    mutationFn: () => monitoringApi.startMonitoring(selectedSiteId),
    onSuccess: () => {
      refetchSiteMonitoring();
      toast.success('Worker Safety Monitoring started — Telemetry active');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to start monitoring');
    },
  });

  const stopMonitoringMutation = useMutation({
    mutationFn: () => monitoringApi.stopMonitoring(selectedSiteId),
    onSuccess: () => {
      refetchSiteMonitoring();
      toast.success('Worker Safety Monitoring stopped');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to stop monitoring');
    },
  });

  const evaluateWorkerMutation = useMutation({
    mutationFn: () => {
      if (!selectedWorkerId) throw new Error('Please select a worker to evaluate');
      const hazardsList = monNearbyHazards.trim() ? monNearbyHazards.split(',').map(s => s.trim()) : [];
      const equipmentList = monNearbyEquipment.trim() ? monNearbyEquipment.split(',').map(s => s.trim()) : [];
      return monitoringApi.evaluateWorker(selectedWorkerId, {
        current_activity: monActivity,
        current_zone: monZone,
        is_high_risk_zone: monIsHighRiskZone,
        time_in_zone_minutes: monTimeInZone,
        nearby_hazards: hazardsList,
        nearby_equipment: equipmentList,
        workers_in_zone_count: monWorkersInZone,
      });
    },
    onSuccess: r => {
      setMonEvaluationResult(r.data);
      refetchSiteMonitoring();
      refetchFindings();
      refetchSummary();
      const statusLabel = r.data.safety_status;
      if (statusLabel === 'CRITICAL') {
        toast.error(`Worker Status: CRITICAL — ${r.data.findings.length} violation(s) detected`);
      } else if (statusLabel === 'HIGH_RISK') {
        toast.error(`Worker Status: HIGH RISK — Immediate attention required`);
      } else if (statusLabel === 'WARNING') {
        toast(`Worker Status: WARNING — Review advisories`, { icon: '⚠️' });
      } else {
        toast.success(`Worker Status: SAFE — All rules compliant`);
      }
    },
    onError: (err: any) => {
      toast.error(err.message || err.response?.data?.detail || 'Evaluation failed');
    },
  });

  const runMonDemoMutation = useMutation({
    mutationFn: (scenarioId: number) => monitoringApi.runDemoScenario(scenarioId, selectedSiteId || undefined),
    onSuccess: (r, scenarioId) => {
      setRunningMonScenario(null);
      setMonEvaluationResult(r.data);
      refetchSiteMonitoring();
      toast.success(`Demo Scenario ${scenarioId} executed: ${r.data.safety_status} (DEMO / SIMULATION)`);
    },
    onError: (err: any) => {
      setRunningMonScenario(null);
      toast.error(err.response?.data?.detail || 'Demo execution failed');
    },
  });

  // ── PPE Data & Mutations ───────────────────────────────────────────────────

  const { data: ppeDemoScenarios } = useQuery<PPEDemoScenario[]>({
    queryKey: ['ppe-demo-scenarios'],
    queryFn: () => ppeApi.listDemoScenarios().then(r => r.data),
  });

  const ppeUploadMutation = useMutation({
    mutationFn: (formData: FormData) => ppeApi.analyzeImage(formData),
    onSuccess: r => {
      setPpeAnalysisResult(r.data);
      setPpeFile(null);
      refetchFindings();
      refetchSummary();
      toast.success('Computer Vision PPE detection complete');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'PPE Image Analysis failed');
    },
  });

  const ppeScenarioMutation = useMutation({
    mutationFn: ({ scenarioId }: { scenarioId: number }) =>
      ppeApi.runDemoScenario(scenarioId, selectedSiteId || undefined, ppeWorkerId || undefined, ppeIsHighRisk),
    onSuccess: (r, { scenarioId }) => {
      setRunningPpeScenario(null);
      setPpeAnalysisResult(r.data);
      refetchFindings();
      refetchSummary();
      toast.success(`Demo Scenario ${scenarioId} executed (MOCK / DEMO)`);
    },
    onError: (err: any) => {
      setRunningPpeScenario(null);
      toast.error(err.response?.data?.detail || 'Demo execution failed');
    },
  });

  const handleUploadPPE = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ppeFile) {
      toast.error('Please select an image file');
      return;
    }
    if (!selectedSiteId) {
      toast.error('Please select an active site');
      return;
    }
    const fd = new FormData();
    fd.append('file', ppeFile);
    fd.append('site_id', selectedSiteId);
    if (ppeWorkerId) fd.append('worker_id', ppeWorkerId);
    fd.append('is_high_risk', ppeIsHighRisk ? 'true' : 'false');
    ppeUploadMutation.mutate(fd);
  };

  const handleRunPpeScenario = (id: number) => {
    setRunningPpeScenario(id);
    ppeScenarioMutation.mutate({ scenarioId: id });
  };

  // ── Filtered Findings ──────────────────────────────────────────────────────

  const filteredFindings = (findings ?? []).filter(f => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      f.finding_id.toLowerCase().includes(q) ||
      f.description.toLowerCase().includes(q) ||
      (f.worker_name ?? '').toLowerCase().includes(q) ||
      (FINDING_TYPE_LABEL[f.finding_type] ?? '').toLowerCase().includes(q)
    );
  });

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">

      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Safety Intelligence &amp; PPE Detection</h1>
          <p className="page-subtitle">
            Autonomous Safety Intelligence, Computer Vision PPE Compliance & Real-Time Monitoring
          </p>
        </div>
        <div className="flex items-center gap-3">
          <AgentStatusBadge />
          <div className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
            <Camera className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-xs font-bold text-indigo-300">OpenCV-HOG PPE v1.0</span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-800 gap-6">
        <button
          onClick={() => setActiveTab('monitoring')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'monitoring'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Safety Agent &amp; Rule Engine
        </button>
        <button
          onClick={() => setActiveTab('ppe_vision')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'ppe_vision'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Camera className="w-4 h-4" />
          Computer Vision PPE Analysis
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-indigo-500/20 text-indigo-300 font-bold">
            Computer Vision
          </span>
        </button>
        <button
          id="btn-tab-worker-monitoring"
          onClick={() => setActiveTab('worker_monitoring')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'worker_monitoring'
              ? 'border-amber-500 text-amber-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Radio className="w-4 h-4" />
          Worker Safety Monitoring
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 font-bold">
            Real-Time
          </span>
        </button>
        <button
          id="btn-tab-live-video"
          onClick={() => setActiveTab('live_video')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'live_video'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Video className="w-4 h-4" />
          Live Video Monitoring
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 font-bold">
            Surveillance
          </span>
        </button>
      </div>

      {/* Tab 1: Safety Agent & Rule Engine Monitoring */}
      {activeTab === 'monitoring' && (
        <>
          {/* Site selector + Analyze button */}
          <div className="card p-5">
            <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
              <div className="flex items-center gap-2 shrink-0">
                <Activity size={16} className="text-slate-500" />
                <span className="text-sm font-medium text-slate-400">Active Site:</span>
              </div>
              <select
                id="select-safety-site"
                className="input text-sm flex-1 max-w-xs"
                value={selectedSiteId}
                onChange={e => {
                  setSelectedSiteId(e.target.value);
                  setAnalysisResult(null);
                }}
              >
                <option value="">— Select a site —</option>
                {(sites ?? []).map(s => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.site_id})
                  </option>
                ))}
              </select>

              {selectedSiteId && (
                <>
                  <button
                    id="btn-analyze-safety"
                    className="btn-primary text-sm gap-2"
                    disabled={analyzeMutation.isPending || !canWrite}
                    onClick={() => analyzeMutation.mutate()}
                  >
                    {analyzeMutation.isPending ? (
                      <RefreshCw size={14} className="animate-spin" />
                    ) : (
                      <ShieldCheck size={14} />
                    )}
                    {analyzeMutation.isPending ? 'Analyzing…' : 'Analyze Worker Safety'}
                  </button>
                  {!canWrite && (
                    <span className="flex items-center gap-1 text-xs text-slate-600">
                      <Lock size={11} /> Viewer — read only
                    </span>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Metrics strip */}
          {safetySummary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Workers on Site"
                value={safetySummary.workers_count}
                icon={<Users size={18} />}
                color="text-primary-400"
              />
              <MetricCard
                label="Open Findings"
                value={safetySummary.open_findings_count}
                sub={`${safetySummary.high_findings_count} HIGH`}
                icon={<FileSearch size={18} />}
                color={safetySummary.open_findings_count > 0 ? 'text-amber-400' : 'text-emerald-400'}
              />
              <MetricCard
                label="Critical Findings"
                value={safetySummary.critical_findings_count}
                icon={<AlertTriangle size={18} />}
                color={safetySummary.critical_findings_count > 0 ? 'text-red-400' : 'text-emerald-400'}
              />
              <MetricCard
                label="Safety Score"
                value={
                  safetySummary.latest_analysis
                    ? `${safetySummary.latest_analysis.overall_safety_score.toFixed(0)}/100`
                    : '—'
                }
                sub={
                  safetySummary.latest_analysis
                    ? `Level: ${RISK_LABEL_MAP[safetySummary.latest_analysis.safety_level]}`
                    : 'No analysis yet'
                }
                icon={<BarChart3 size={18} />}
                color={
                  !safetySummary.latest_analysis
                    ? 'text-slate-500'
                    : safetySummary.latest_analysis.safety_level === 'low'
                    ? 'text-emerald-400'
                    : safetySummary.latest_analysis.safety_level === 'medium'
                    ? 'text-amber-400'
                    : safetySummary.latest_analysis.safety_level === 'high'
                    ? 'text-orange-400'
                    : 'text-red-400'
                }
              />
            </div>
          )}

          {/* Last analysis result banner */}
          <AnimatePresence>
            {analysisResult && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={clsx(
                  'card p-5 border',
                  analysisResult.summary.safety_level === 'low'
                    ? 'border-emerald-500/30 bg-emerald-500/5'
                    : analysisResult.summary.safety_level === 'medium'
                    ? 'border-amber-500/30 bg-amber-500/5'
                    : analysisResult.summary.safety_level === 'high'
                    ? 'border-orange-500/30 bg-orange-500/5'
                    : 'border-red-500/30 bg-red-500/5',
                )}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <ShieldCheck
                      size={28}
                      className={clsx(
                        analysisResult.summary.safety_level === 'low' ? 'text-emerald-400'
                        : analysisResult.summary.safety_level === 'medium' ? 'text-amber-400'
                        : analysisResult.summary.safety_level === 'high' ? 'text-orange-400'
                        : 'text-red-400',
                      )}
                    />
                    <div>
                      <p className="font-semibold text-slate-200">
                        Safety Analysis Complete —&nbsp;
                        <span
                          className={clsx(
                            'font-bold',
                            analysisResult.summary.safety_level === 'low' ? 'text-emerald-400'
                            : analysisResult.summary.safety_level === 'medium' ? 'text-amber-400'
                            : analysisResult.summary.safety_level === 'high' ? 'text-orange-400'
                            : 'text-red-400',
                          )}
                        >
                          {analysisResult.summary.safety_level?.toUpperCase()}
                        </span>
                      </p>
                      <p className="text-sm text-slate-400 mt-0.5">
                        {analysisResult.summary.workers_analyzed} worker(s) analyzed ·&nbsp;
                        {analysisResult.summary.violation_count} violation(s) detected ·&nbsp;
                        Score: {analysisResult.summary.overall_safety_score.toFixed(0)}/100 ·&nbsp;
                        {analysisResult.summary.notifications_sent} alert(s) sent
                      </p>
                    </div>
                  </div>
                  <button
                    className="btn-ghost p-1.5 shrink-0"
                    onClick={() => setAnalysisResult(null)}
                  >
                    <X size={14} />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Demo Scenarios */}
          <div className="card">
            <div className="flex items-center gap-3 p-5 border-b border-slate-800">
              <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
                <Play size={16} className="text-primary-400" />
              </div>
              <div>
                <h3 className="section-title">Safety Agent Demo Scenario Launcher</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  5 deterministic rule-trigger scenarios — validates SafetyAgent&apos;s 6 core rules
                </p>
              </div>
              {!canWrite && (
                <span className="ml-auto flex items-center gap-1 text-xs text-slate-700 badge">
                  <Lock size={10} /> Viewer
                </span>
              )}
            </div>
            <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
              {(demoScenarios ?? []).map((scenario, idx) => (
                <motion.div
                  key={scenario.id}
                  whileHover={canWrite ? { scale: 1.02 } : {}}
                  className={clsx(
                    'rounded-xl border bg-gradient-to-b p-4 flex flex-col gap-3',
                    SCENARIO_COLORS[idx % SCENARIO_COLORS.length],
                    !canWrite && 'opacity-60',
                  )}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Scenario {scenario.id}
                    </span>
                    <span className={clsx('text-xs font-bold', SCENARIO_LEVEL_COLOR[idx])}>
                      {scenario.expected_level}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200 leading-snug">{scenario.name}</p>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{scenario.description}</p>
                  </div>
                  <div className="mt-auto text-[10px] text-slate-600">
                    Expected: {scenario.expected_violations} finding(s)
                  </div>
                  <button
                    id={`btn-scenario-${scenario.id}`}
                    className={clsx(
                      'w-full text-xs font-semibold py-2 rounded-lg border transition-all',
                      canWrite && selectedSiteId
                        ? 'border-white/10 bg-white/5 hover:bg-white/10 text-slate-200'
                        : 'border-slate-800 bg-transparent text-slate-700 cursor-not-allowed',
                    )}
                    disabled={!canWrite || !selectedSiteId || scenarioMutation.isPending}
                    onClick={() => handleRunScenario(scenario.id)}
                  >
                    {runningScenario === scenario.id ? (
                      <span className="flex items-center justify-center gap-1.5">
                        <RefreshCw size={11} className="animate-spin" /> Running…
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-1.5">
                        <Play size={11} /> Run
                      </span>
                    )}
                  </button>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Safety Findings Table */}
          <div className="card">
            <div className="p-5 border-b border-slate-800">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="section-title">Safety Findings</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {selectedSiteId
                      ? `${filteredFindings.length} finding(s) · Detected by RULE_ENGINE`
                      : 'Select a site to view findings'}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <div className="relative">
                    <Search
                      size={13}
                      className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-600 pointer-events-none"
                    />
                    <input
                      className="input text-xs pl-8 py-1.5 w-44"
                      placeholder="Search findings…"
                      value={searchTerm}
                      onChange={e => setSearchTerm(e.target.value)}
                    />
                  </div>
                  <div className="relative">
                    <Filter
                      size={12}
                      className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-600 pointer-events-none"
                    />
                    <select
                      className="input text-xs pl-8 py-1.5"
                      value={filterStatus}
                      onChange={e => setFilterStatus(e.target.value)}
                    >
                      <option value="">All Statuses</option>
                      <option value="open">Open</option>
                      <option value="acknowledged">Acknowledged</option>
                      <option value="mitigated">Mitigated</option>
                      <option value="closed">Closed</option>
                    </select>
                  </div>
                  <select
                    className="input text-xs py-1.5"
                    value={filterSeverity}
                    onChange={e => setFilterSeverity(e.target.value)}
                  >
                    <option value="">All Severities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>
            </div>

            {!selectedSiteId ? (
              <EmptyState
                icon={<HardHat size={24} />}
                title="No site selected"
                description="Select a site above to view safety findings"
              />
            ) : filteredFindings.length === 0 ? (
              <EmptyState
                icon={<ShieldCheck size={24} />}
                title="No findings found"
                description={
                  !findings || findings.length === 0
                    ? 'Run a safety analysis or demo scenario to detect compliance violations'
                    : 'No findings match the current filters'
                }
              />
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Finding ID</th>
                      <th>Type</th>
                      <th>Worker</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Detected</th>
                      <th>Action</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFindings.map(f => (
                      <FindingRow
                        key={f.id}
                        finding={f}
                        canWrite={canWrite}
                        onAcknowledge={id =>
                          findingUpdateMutation.mutate({ id, data: { status: 'acknowledged' } })
                        }
                        onMitigate={setMitigateTarget}
                        onClose={id =>
                          findingUpdateMutation.mutate({ id, data: { status: 'closed' } })
                        }
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* Tab 2: Computer Vision PPE Detection (Phase 2.2) */}
      {activeTab === 'ppe_vision' && (
        <div className="space-y-6">
          {/* Site Selection & Upload Form */}
          <div className="card p-6 border border-slate-800">
            <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
              <Camera className="w-5 h-5 text-indigo-400" />
              Computer Vision Construction Image PPE Analysis
            </h3>

            <form onSubmit={handleUploadPPE} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">
                    Target Construction Site *
                  </label>
                  <select
                    id="select-ppe-site"
                    className="input text-sm w-full"
                    value={selectedSiteId}
                    onChange={e => setSelectedSiteId(e.target.value)}
                    required
                  >
                    <option value="">— Select Site —</option>
                    {(sites ?? []).map(s => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.site_id})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">
                    Optional Worker ID (Audit Link)
                  </label>
                  <input
                    type="text"
                    className="input text-sm w-full"
                    placeholder="Worker UUID or leave blank"
                    value={ppeWorkerId}
                    onChange={e => setPpeWorkerId(e.target.value)}
                  />
                </div>

                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="ppe-high-risk"
                    checked={ppeIsHighRisk}
                    onChange={e => setPpeIsHighRisk(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="ppe-high-risk" className="text-sm font-medium text-slate-300">
                    High-Risk Zone Activity
                  </label>
                </div>
              </div>

              {/* Upload Dropzone */}
              <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-xl p-6 text-center transition-colors bg-slate-950/40">
                <input
                  type="file"
                  id="ppe-file-input"
                  accept=".jpg,.jpeg,.png"
                  onChange={e => setPpeFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <label
                  htmlFor="ppe-file-input"
                  className="cursor-pointer flex flex-col items-center justify-center gap-2"
                >
                  <div className="p-3 rounded-full bg-indigo-500/10 text-indigo-400">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-medium text-slate-200">
                    {ppeFile ? (
                      <span className="text-indigo-400 font-semibold">{ppeFile.name} ({(ppeFile.size / 1024).toFixed(0)} KB)</span>
                    ) : (
                      <>Click to select or drop construction site photo (JPEG, PNG &bull; max 15MB)</>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    Image is securely checked for corruption and passed to the OpenCV detection pipeline.
                  </p>
                </label>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="submit"
                  id="btn-analyze-ppe"
                  disabled={!ppeFile || !selectedSiteId || ppeUploadMutation.isPending || !canWrite}
                  className="btn-primary text-sm gap-2"
                >
                  {ppeUploadMutation.isPending ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  {ppeUploadMutation.isPending ? 'Running Computer Vision…' : 'Analyze Image with Computer Vision'}
                </button>
              </div>
            </form>
          </div>

          {/* 5 Deterministic Demo Scenarios for Phase 2.2 */}
          <div className="card p-5 border border-slate-800">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-800 mb-4">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                <Play size={16} className="text-indigo-400" />
              </div>
              <div>
                <h3 className="section-title">Deterministic PPE Demo Fixtures</h3>
                <p className="text-xs text-slate-500">
                  Clearly labeled <span className="font-mono text-amber-400">DEMO / MOCK</span> test scenarios verifying all 5 required edge cases
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {(ppeDemoScenarios ?? []).map((scenario) => (
                <div
                  key={scenario.id}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-between gap-3 hover:border-slate-700 transition-colors"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                        DEMO {scenario.id}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          scenario.expected_compliance === 'COMPLIANT'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : scenario.expected_compliance === 'NON_COMPLIANT'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}
                      >
                        {scenario.expected_compliance}
                      </span>
                    </div>
                    <h4 className="text-xs font-semibold text-slate-200 mb-1">{scenario.name}</h4>
                    <p className="text-[11px] text-slate-400 line-clamp-3 leading-relaxed">
                      {scenario.description}
                    </p>
                  </div>

                  <button
                    id={`btn-ppe-demo-${scenario.id}`}
                    disabled={!selectedSiteId || runningPpeScenario === scenario.id || !canWrite}
                    onClick={() => handleRunPpeScenario(scenario.id)}
                    className="w-full py-1.5 px-2.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 text-xs font-medium transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
                  >
                    {runningPpeScenario === scenario.id ? (
                      <RefreshCw className="w-3 h-3 animate-spin" />
                    ) : (
                      <Play className="w-3 h-3" />
                    )}
                    Run Demo {scenario.id}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Active PPE Analysis Viewer */}
          {ppeAnalysisResult ? (
            <div className="card p-6 border border-slate-800">
              <PPEViewer analysis={ppeAnalysisResult} />
            </div>
          ) : (
            <EmptyState
              icon={<Camera size={28} />}
              title="No PPE Analysis Loaded"
              description="Upload an image or launch one of the 5 demo scenarios above to inspect Computer Vision bounding boxes and compliance results."
            />
          )}
        </div>
      )}

      {/* Tab 3: Worker Safety Monitoring (Live) */}
      {activeTab === 'worker_monitoring' && (
        <div className="space-y-6">
          {/* Site Control & Live Session Bar */}
          <div className="card p-5 border border-amber-500/20 bg-gradient-to-r from-surface-900 via-surface-900 to-amber-950/20">
            <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <Activity size={16} className="text-amber-400" />
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Site:</span>
                </div>
                <select
                  id="select-monitoring-site"
                  className="input text-xs py-1.5 px-3 min-w-[220px]"
                  value={selectedSiteId}
                  onChange={e => {
                    setSelectedSiteId(e.target.value);
                    setMonEvaluationResult(null);
                  }}
                >
                  <option value="">— Select Site —</option>
                  {(sites ?? []).map(s => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.site_id})
                    </option>
                  ))}
                </select>

                {/* Live Status Badge */}
                {siteMonitoring?.is_monitoring_active ? (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-bold font-mono">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                    LIVE MONITORING ACTIVE
                  </div>
                ) : (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-xs font-mono">
                    <Square size={10} />
                    MONITORING IDLE
                  </div>
                )}
              </div>

              {/* Start / Stop Monitoring Buttons */}
              <div className="flex items-center gap-2 self-end lg:self-center">
                {siteMonitoring?.is_monitoring_active ? (
                  <button
                    id="btn-stop-monitoring"
                    onClick={() => stopMonitoringMutation.mutate()}
                    disabled={stopMonitoringMutation.isPending || !canWrite}
                    className="btn-danger text-xs py-2 px-3.5 flex items-center gap-2 shadow-lg shadow-red-500/10"
                  >
                    {stopMonitoringMutation.isPending ? (
                      <RefreshCw size={14} className="animate-spin" />
                    ) : (
                      <Square size={14} />
                    )}
                    <span>STOP MONITORING</span>
                  </button>
                ) : (
                  <button
                    id="btn-start-monitoring"
                    onClick={() => startMonitoringMutation.mutate()}
                    disabled={startMonitoringMutation.isPending || !canWrite || !selectedSiteId}
                    className="btn-primary text-xs py-2 px-4 flex items-center gap-2 shadow-lg shadow-primary-500/20"
                  >
                    {startMonitoringMutation.isPending ? (
                      <RefreshCw size={14} className="animate-spin" />
                    ) : (
                      <Play size={14} />
                    )}
                    <span>START MONITORING</span>
                  </button>
                )}
              </div>
            </div>

            {/* Telemetry Metrics Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800">
              <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                <span className="text-[11px] text-slate-400 block mb-0.5">Monitored Personnel</span>
                <span className="text-xl font-bold font-mono text-slate-200">
                  {siteMonitoring?.monitored_workers_count ?? (siteWorkers?.length ?? 0)}
                </span>
                <span className="text-[10px] text-slate-500 block">Active on site</span>
              </div>
              <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                <span className="text-[11px] text-amber-400 block mb-0.5">Active Warnings</span>
                <span className="text-xl font-bold font-mono text-amber-400">
                  {siteMonitoring?.active_warnings_count ?? 0}
                </span>
                <span className="text-[10px] text-amber-500/70 block">Low/Med Advisories</span>
              </div>
              <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                <span className="text-[11px] text-orange-400 block mb-0.5">High Risk Violations</span>
                <span className="text-xl font-bold font-mono text-orange-400">
                  {siteMonitoring?.active_high_risk_count ?? 0}
                </span>
                <span className="text-[10px] text-orange-500/70 block">Zone/dwell/hazard alerts</span>
              </div>
              <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                <span className="text-[11px] text-red-400 block mb-0.5">Critical Conflicts</span>
                <span className="text-xl font-bold font-mono text-red-400">
                  {siteMonitoring?.active_critical_count ?? 0}
                </span>
                <span className="text-[10px] text-red-500/70 block">Equipment &amp; PPE breaches</span>
              </div>
            </div>
          </div>

          {/* 6 Deterministic Demo Scenarios */}
          <div className="card p-5 border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-amber-400" />
                <h3 className="section-title text-sm">Deterministic Demo Scenarios</h3>
                <span className="text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded">
                  DEMO / SIMULATION
                </span>
              </div>
              <span className="text-xs text-slate-500 font-mono">6 Predefined Tests</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {(monDemoScenarios ?? []).map(sc => {
                const isRunning = runningMonScenario === sc.id;
                const statusColor =
                  sc.expected_status === 'CRITICAL'
                    ? 'text-red-400 border-red-500/30 bg-red-500/10'
                    : sc.expected_status === 'HIGH_RISK'
                    ? 'text-orange-400 border-orange-500/30 bg-orange-500/10'
                    : sc.expected_status === 'WARNING'
                    ? 'text-amber-400 border-amber-500/30 bg-amber-500/10'
                    : 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';

                return (
                  <button
                    key={sc.id}
                    id={`btn-mon-scenario-${sc.id}`}
                    onClick={() => {
                      setRunningMonScenario(sc.id);
                      runMonDemoMutation.mutate(sc.id);
                    }}
                    disabled={isRunning || !canWrite}
                    className="text-left p-3.5 rounded-xl border border-slate-800 bg-surface-950/60 hover:bg-surface-800/80 hover:border-slate-700 transition-all group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-xs font-bold text-slate-200 group-hover:text-primary-300 transition-colors">
                          {sc.name}
                        </span>
                        <span className={clsx('text-[10px] font-bold font-mono px-1.5 py-0.5 rounded border', statusColor)}>
                          {sc.expected_status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed mb-2">
                        {sc.description}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px] text-slate-500 font-mono">
                      <span>{sc.expected_findings_count} finding(s)</span>
                      <span className="text-primary-400 group-hover:underline flex items-center gap-1">
                        {isRunning ? <RefreshCw size={10} className="animate-spin" /> : <Play size={10} />}
                        Execute
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Interactive Worker Safety Evaluator & Telemetry Configuration */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-5 card p-5 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <UserCheck size={16} className="text-primary-400" />
                  <h3 className="section-title text-sm">Worker Telemetry Evaluator</h3>
                </div>
                <span className="text-[10px] font-mono text-slate-500">8 Rules Engine</span>
              </div>

              {/* Worker Selection */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Select Worker</label>
                <select
                  id="select-mon-worker"
                  className="input text-xs w-full"
                  value={selectedWorkerId}
                  onChange={e => setSelectedWorkerId(e.target.value)}
                >
                  <option value="">— Choose Worker on Site —</option>
                  {(siteWorkers ?? []).map(w => (
                    <option key={w.id} value={w.id}>
                      {w.name} ({w.role}) — {w.worker_id}
                    </option>
                  ))}
                </select>
              </div>

              {/* Activity & Zone */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Current Activity</label>
                  <select
                    className="input text-xs w-full"
                    value={monActivity}
                    onChange={e => setMonActivity(e.target.value)}
                  >
                    <option value="excavation">Excavation</option>
                    <option value="welding">Welding</option>
                    <option value="scaffolding">Scaffolding</option>
                    <option value="concrete_work">Concrete Work</option>
                    <option value="electrical_work">Electrical Work</option>
                    <option value="material_handling">Material Handling</option>
                    <option value="general_construction">General Construction</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Current Zone</label>
                  <input
                    type="text"
                    className="input text-xs w-full"
                    value={monZone}
                    onChange={e => setMonZone(e.target.value)}
                    placeholder="e.g. Zone A — Excavation Pit"
                  />
                </div>
              </div>

              {/* High Risk Toggle & Dwell Time */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-surface-950/60 border border-slate-800">
                  <input
                    type="checkbox"
                    id="chk-mon-high-risk"
                    checked={monIsHighRiskZone}
                    onChange={e => setMonIsHighRiskZone(e.target.checked)}
                    className="rounded border-slate-700 text-amber-500 focus:ring-amber-500/20"
                  />
                  <label htmlFor="chk-mon-high-risk" className="text-xs text-slate-300 cursor-pointer font-medium">
                    Designated High-Risk Zone
                  </label>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-slate-400">Time in Zone:</span>
                    <span className="font-mono font-bold text-slate-200">{monTimeInZone} mins</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="120"
                    step="5"
                    value={monTimeInZone}
                    onChange={e => setMonTimeInZone(parseInt(e.target.value))}
                    className="w-full accent-amber-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
                    <span>0 min</span>
                    <span className="text-amber-500/80">Limit: 45m</span>
                    <span>120m</span>
                  </div>
                </div>
              </div>

              {/* Nearby Hazards & Equipment */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Active Nearby Hazards (comma separated)
                </label>
                <input
                  type="text"
                  className="input text-xs w-full"
                  value={monNearbyHazards}
                  onChange={e => setMonNearbyHazards(e.target.value)}
                  placeholder="e.g. HAZ-002: Trench Wall Instability"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Operating Machinery Nearby (comma separated)
                </label>
                <input
                  type="text"
                  className="input text-xs w-full"
                  value={monNearbyEquipment}
                  onChange={e => setMonNearbyEquipment(e.target.value)}
                  placeholder="e.g. EQP-001: 30-Ton CAT Excavator"
                />
              </div>

              {/* Workers in zone density */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-400">Personnel in Zone:</span>
                  <span className="font-mono font-bold text-slate-200">{monWorkersInZone} workers</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="8"
                  value={monWorkersInZone}
                  onChange={e => setMonWorkersInZone(parseInt(e.target.value))}
                  className="w-full accent-primary-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
                  <span>1 (Solo)</span>
                  <span className="text-amber-500/80">Max: 3</span>
                  <span>8 (Crowded)</span>
                </div>
              </div>

              <button
                id="btn-evaluate-worker"
                onClick={() => evaluateWorkerMutation.mutate()}
                disabled={evaluateWorkerMutation.isPending || !canWrite || !selectedWorkerId}
                className="btn-primary w-full py-2.5 text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-primary-500/20"
              >
                {evaluateWorkerMutation.isPending ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Evaluating Rules Telemetry…</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck size={15} />
                    <span>EVALUATE WORKER SAFETY</span>
                  </>
                )}
              </button>
            </div>

            {/* Evaluation Results Card */}
            <div className="lg:col-span-7 space-y-4">
              {monEvaluationResult ? (
                <div className="card p-6 border border-slate-800 space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-base font-bold text-slate-100">{monEvaluationResult.worker_name}</h4>
                        <span className="text-xs font-mono text-slate-500">({monEvaluationResult.worker_id})</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Evaluated at {formatRelativeTime(monEvaluationResult.evaluated_at)} · {monEvaluationResult.detection_source}
                      </p>
                    </div>

                    {/* Overall Safety Status Badge */}
                    {(() => {
                      const st = monEvaluationResult.safety_status;
                      const badgeConfig =
                        st === 'CRITICAL'
                          ? { bg: 'bg-red-500/20 text-red-300 border-red-500/40', icon: <AlertOctagon size={16} className="animate-bounce" />, text: 'CRITICAL CONFLICT' }
                          : st === 'HIGH_RISK'
                          ? { bg: 'bg-orange-500/20 text-orange-300 border-orange-500/40', icon: <AlertTriangle size={16} />, text: 'HIGH RISK' }
                          : st === 'WARNING'
                          ? { bg: 'bg-amber-500/20 text-amber-300 border-amber-500/40', icon: <AlertTriangle size={16} />, text: 'WARNING' }
                          : { bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40', icon: <CheckCircle2 size={16} />, text: 'SAFE' };

                      return (
                        <div className={clsx('flex items-center gap-2 px-3.5 py-1.5 rounded-xl border text-xs font-bold font-mono tracking-wider', badgeConfig.bg)}>
                          {badgeConfig.icon}
                          <span>{badgeConfig.text}</span>
                        </div>
                      );
                    })()}
                  </div>

                  {/* Context Summary Chips */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="p-2 rounded bg-surface-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-500 uppercase block">Activity</span>
                      <span className="font-semibold text-slate-200 capitalize">{monEvaluationResult.current_activity.replace('_', ' ')}</span>
                    </div>
                    <div className="p-2 rounded bg-surface-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-500 uppercase block">Zone</span>
                      <span className="font-semibold text-slate-200 truncate block">{monEvaluationResult.current_zone}</span>
                    </div>
                    <div className="p-2 rounded bg-surface-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-500 uppercase block">Dwell Time</span>
                      <span className={clsx('font-mono font-semibold', monEvaluationResult.time_in_zone_minutes > 45 ? 'text-orange-400' : 'text-slate-200')}>
                        {monEvaluationResult.time_in_zone_minutes} mins
                      </span>
                    </div>
                    <div className="p-2 rounded bg-surface-950/60 border border-slate-800">
                      <span className="text-[10px] text-slate-500 uppercase block">PPE Record</span>
                      <span className="font-semibold text-slate-200 uppercase text-[11px] font-mono">{monEvaluationResult.ppe_status}</span>
                    </div>
                  </div>

                  {/* Active Findings */}
                  <div>
                    <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                      <ShieldAlert size={14} className="text-amber-400" />
                      Detected Monitoring Findings ({monEvaluationResult.findings.length})
                    </h5>

                    {monEvaluationResult.findings.length === 0 ? (
                      <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                        <CheckCircle2 size={24} className="mx-auto text-emerald-400 mb-1" />
                        <p className="text-xs font-semibold text-emerald-300">All Monitoring Rules Passed</p>
                        <p className="text-[11px] text-emerald-400/80">Worker is operating strictly within certified safety parameters.</p>
                      </div>
                    ) : (
                      <div className="space-y-2.5">
                        {monEvaluationResult.findings.map((f, i) => (
                          <div
                            key={i}
                            className="p-3 rounded-xl bg-surface-950/80 border border-slate-800 text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-bold text-slate-200">{f.rule_name}</span>
                              <span className={clsx('badge text-[10px] font-mono uppercase', RISK_BADGE_MAP[f.severity])}>
                                {RISK_LABEL_MAP[f.severity]}
                              </span>
                            </div>
                            <p className="text-slate-300">{f.description}</p>
                            <div className="p-2 rounded bg-surface-900 border border-slate-800/80 text-[11px] text-slate-400 font-mono">
                              <span className="text-slate-500 block text-[10px] uppercase">Telemetry Evidence</span>
                              {f.evidence}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Recommendations */}
                  {monEvaluationResult.recommendations.length > 0 && (
                    <div>
                      <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Wrench size={14} className="text-primary-400" />
                        Actionable Recommendations
                      </h5>
                      <div className="space-y-1.5">
                        {monEvaluationResult.recommendations.map((rec, i) => (
                          <div
                            key={i}
                            className="p-2.5 rounded-lg bg-primary-500/5 border border-primary-500/20 text-xs text-primary-200 flex items-start gap-2"
                          >
                            <Check size={14} className="text-primary-400 shrink-0 mt-0.5" />
                            <span>{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <EmptyState
                  icon={<Radio size={32} />}
                  title="No Evaluation Triggered"
                  description="Select a worker and click [ EVALUATE WORKER SAFETY ] or run one of the deterministic demo scenarios above."
                />
              )}

              {/* Live Event Stream */}
              <div className="card p-5 border border-slate-800">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Clock size={14} className="text-slate-400" />
                  Recent Monitoring Event Stream ({siteMonitoring?.recent_events?.length ?? 0})
                </h4>

                {(!siteMonitoring?.recent_events || siteMonitoring.recent_events.length === 0) ? (
                  <div className="p-4 rounded-lg bg-surface-950/40 border border-slate-800/60 text-center text-xs text-slate-500">
                    No monitoring events recorded for this site yet.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {siteMonitoring.recent_events.slice(0, 5).map(evt => (
                      <div
                        key={evt.id}
                        className="p-2.5 rounded-lg bg-surface-950/70 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className={clsx('badge text-[10px] font-mono uppercase', RISK_BADGE_MAP[evt.severity])}>
                            {evt.worker_safety_status}
                          </span>
                          <div>
                            <span className="font-semibold text-slate-200">{evt.worker_name}</span>
                            <span className="text-slate-400 ml-1.5">— {evt.event_type}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 font-mono text-[11px] text-slate-500 self-end sm:self-center">
                          <span>{evt.zone_name}</span>
                          <span>·</span>
                          <span>{formatRelativeTime(evt.created_at)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Live Video Monitoring (Platform Extension - Phase 3.1) */}
      {activeTab === 'live_video' && (
        <LiveVideoMonitoring />
      )}

      {/* Viewer read-only notice */}
      {!canWrite && (
        <div className="flex items-center gap-2 text-xs text-slate-600 px-1">
          <Eye size={13} />
          You are viewing as <strong className="text-slate-500">{user?.role}</strong> — all write actions are disabled
        </div>
      )}

      {/* Mitigate Modal */}
      {mitigateTarget && (
        <MitigateModal
          finding={mitigateTarget}
          onClose={() => setMitigateTarget(null)}
          onSubmit={notes =>
            findingUpdateMutation.mutate({
              id: mitigateTarget.id,
              data: { status: 'mitigated', mitigation_notes: notes },
            })
          }
        />
      )}
    </motion.div>
  );
}
