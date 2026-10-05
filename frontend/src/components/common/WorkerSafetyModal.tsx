import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HardHat, ShieldAlert, ShieldCheck, AlertTriangle, Zap,
  CheckCircle2, Clock, User as UserIcon, Phone, Calendar,
  Building2, RefreshCw, X, Wrench, Lock, ArrowRight, Sparkles,
  Shield, Layers, Camera
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { safetyApi, ppeApi } from '@/services/api';
import { Modal } from '@/components/common';
import {
  WORKER_ROLE_LABEL, TRAINING_STATUS_BADGE, TRAINING_STATUS_LABEL,
  PPE_STATUS_BADGE, RISK_BADGE_MAP, RISK_LABEL_MAP,
  formatDate, formatRelativeTime
} from '@/utils/display';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { Worker, SafetyFinding, SafetyAnalysisResponse, PPEAnalysis } from '@/types';

interface WorkerSafetyModalProps {
  worker: Worker | null;
  open: boolean;
  onClose: () => void;
  onUpdated?: () => void;
}

const WRITE_ROLES = ['super_admin', 'project_manager', 'site_manager', 'safety_officer', 'viewer'];

const STANDARD_PPE_ITEMS = [
  { name: 'Helmet', icon: '🪖', required: true },
  { name: 'Safety Vest', icon: '🦺', required: true },
  { name: 'Gloves', icon: '🧤', required: true },
  { name: 'Safety Shoes', icon: '🥾', required: true },
  { name: 'Eye Protection', icon: '🥽', required: false },
  { name: 'Hearing Protection', icon: '🎧', required: false },
  { name: 'Safety Harness', icon: '🪢', required: false },
  { name: 'Respiratory Protection', icon: '😷', required: false },
];

const FINDING_TYPE_LABEL: Record<string, string> = {
  ppe_violation: 'PPE Violation',
  expired_training: 'Expired Training',
  missing_training: 'Missing Training',
  unsafe_equipment_operation: 'Unsafe Equipment',
  high_risk_activity: 'High-Risk Activity',
  high_risk_zone_exposure: 'Zone Exposure',
};

const FINDING_STATUS_BADGE: Record<string, string> = {
  open: 'badge-critical',
  acknowledged: 'badge-warning',
  mitigated: 'badge-monitoring',
  closed: 'badge-active',
};

export default function WorkerSafetyModal({
  worker,
  open,
  onClose,
  onUpdated,
}: WorkerSafetyModalProps) {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const canWrite = WRITE_ROLES.includes(user?.role ?? '');

  const [mitigateTarget, setMitigateTarget] = useState<SafetyFinding | null>(null);
  const [mitigationNotes, setMitigationNotes] = useState('');
  const [analysisResult, setAnalysisResult] = useState<SafetyAnalysisResponse | null>(null);

  // Fetch worker specific safety findings
  const { data: findings, isLoading: findingsLoading, refetch: refetchFindings } = useQuery<SafetyFinding[]>({
    queryKey: ['worker-safety-findings', worker?.id],
    queryFn: () => safetyApi.getWorkerFindings(worker!.id).then(r => r.data),
    enabled: !!worker?.id && open,
  });

  // Fetch worker specific CV PPE analyses (Phase 2.2)
  const { data: ppeAnalyses, isLoading: ppeLoading } = useQuery<PPEAnalysis[]>({
    queryKey: ['worker-ppe-analyses', worker?.id],
    queryFn: () => ppeApi.getWorkerAnalyses(worker!.id).then(r => r.data),
    enabled: !!worker?.id && open,
  });

  // Mutation: Analyze Worker Safety via Safety Agent
  const analyzeMutation = useMutation({
    mutationFn: () => safetyApi.analyzeWorker(worker!.id),
    onSuccess: r => {
      setAnalysisResult(r.data);
      refetchFindings();
      queryClient.invalidateQueries({ queryKey: ['safety-findings'] });
      queryClient.invalidateQueries({ queryKey: ['safety-summary'] });
      toast.success(
        `Worker safety analysis completed: ${r.data.summary.violation_count} finding(s) detected`,
        { id: 'worker-safety-toast' }
      );
      onUpdated?.();
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Worker safety analysis failed', { id: 'worker-safety-toast' });
    },
  });

  // Mutation: Finding Lifecycle Updates
  const updateFindingMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: object }) =>
      safetyApi.updateFinding(id, data),
    onSuccess: () => {
      refetchFindings();
      setMitigateTarget(null);
      setMitigationNotes('');
      toast.success('Finding status updated successfully');
      onUpdated?.();
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to update finding');
    },
  });

  if (!worker) return null;

  const isCompliant = worker.ppe_status === 'compliant' && worker.safety_training === 'certified';

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`${worker.name} (${worker.worker_id}) — Worker Safety Intelligence`}
      size="xl"
    >
      <div className="space-y-6">
        {/* Worker Overview Card */}
        <div className="p-5 rounded-xl bg-surface-900 border border-slate-800/80">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block mb-1">Role</span>
              <span className="font-semibold text-slate-200 text-sm">
                {WORKER_ROLE_LABEL[worker.role] || worker.role}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1">Department</span>
              <span className="text-slate-300 font-medium">{worker.department || 'General Construction'}</span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1">Training Certification</span>
              <span className={clsx('badge text-xs', TRAINING_STATUS_BADGE[worker.safety_training])}>
                {TRAINING_STATUS_LABEL[worker.safety_training]}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1">PPE Foundation</span>
              <span className={clsx('badge text-xs', PPE_STATUS_BADGE[worker.ppe_status])}>
                {worker.ppe_status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1 flex items-center gap-1">
                <Building2 size={12} /> Assigned Site
              </span>
              <span className="text-slate-300">{worker.site_name || 'Assigned to Site'}</span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1 flex items-center gap-1">
                <Phone size={12} /> Contact
              </span>
              <span className="text-slate-300 font-mono">{worker.contact || '—'}</span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1 flex items-center gap-1">
                <Calendar size={12} /> Joined
              </span>
              <span className="text-slate-300">{formatDate(worker.joining_date)}</span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1">Overall Status</span>
              <span className={clsx(
                'badge text-xs',
                isCompliant ? 'badge-active' : 'badge-critical'
              )}>
                {isCompliant ? 'COMPLIANT' : 'REQUIRES REVIEW'}
              </span>
            </div>
          </div>
        </div>

        {/* PPE Foundation Equipment Strip */}
        <div className="p-4 rounded-xl bg-surface-900 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck size={13} className="text-emerald-400" />
              PPE Safety Compliance Standards
            </span>
            <span className="text-[11px] text-slate-500 font-mono">
              Status: {worker.ppe_status.toUpperCase()}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {STANDARD_PPE_ITEMS.map(item => {
              const isWorn = worker.ppe_status === 'compliant' || (worker.ppe_status === 'partial' && item.required);
              return (
                <div
                  key={item.name}
                  className={clsx(
                    'p-2 rounded-lg border text-xs flex items-center justify-between transition-colors',
                    isWorn
                      ? 'bg-emerald-500/5 border-emerald-500/20 text-slate-200'
                      : 'bg-red-500/5 border-red-500/20 text-slate-400'
                  )}
                >
                  <span className="flex items-center gap-1.5">
                    <span>{item.icon}</span>
                    <span>{item.name}</span>
                  </span>
                  <span className={clsx(
                    'text-[10px] font-bold px-1.5 py-0.5 rounded',
                    isWorn ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                  )}>
                    {isWorn ? 'Worn' : 'Missing'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Phase 2.2: Computer Vision PPE Analysis History */}
        <div className="p-4 rounded-xl bg-surface-900 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Camera size={14} className="text-primary-400" />
              Computer Vision PPE History ({ppeAnalyses?.length ?? 0})
            </h4>
            <span className="text-[10px] font-mono text-primary-400/80 bg-primary-500/10 px-2 py-0.5 rounded border border-primary-500/20">
              PHASE 2.2 CV
            </span>
          </div>

          {ppeLoading ? (
            <div className="text-center py-4 text-slate-500 text-xs">Loading CV PPE records…</div>
          ) : !ppeAnalyses || ppeAnalyses.length === 0 ? (
            <div className="p-4 rounded-lg bg-surface-950/60 border border-slate-800/80 text-center">
              <p className="text-xs text-slate-400 font-medium">No CV PPE Scans on Record</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Upload a site image in the Safety &gt; PPE Detection tab to run visual compliance detection.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {ppeAnalyses.slice(0, 3).map((analysis) => {
                const isCompliant = analysis.overall_compliance === 'COMPLIANT';
                const isUncertain = analysis.overall_compliance === 'UNCERTAIN';
                const badgeCls = isCompliant
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                  : isUncertain
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                    : 'bg-red-500/20 text-red-300 border-red-500/30';

                return (
                  <div
                    key={analysis.id}
                    className="p-3 rounded-lg bg-surface-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={clsx('text-[11px] font-bold px-2 py-0.5 rounded border font-mono', badgeCls)}>
                        {analysis.overall_compliance}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-200">
                            {analysis.image_filename}
                          </span>
                          <span className="text-[10px] font-mono text-slate-500">
                            {formatRelativeTime(analysis.created_at)}
                          </span>
                        </div>
                        {analysis.missing_ppe && analysis.missing_ppe.length > 0 ? (
                          <p className="text-[11px] text-red-400 mt-0.5">
                            Missing: {analysis.missing_ppe.map(p => p.replace('_', ' ')).join(', ')}
                          </p>
                        ) : (
                          <p className="text-[11px] text-emerald-400 mt-0.5">
                            All required PPE detected
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded">
                        {analysis.detection_source}
                      </span>
                      {analysis.cross_verification?.has_discrepancy && (
                        <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">
                          DISCREPANCY
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Action: ANALYZE WORKER SAFETY */}
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 rounded-xl bg-gradient-to-r from-primary-900/30 via-surface-900 to-indigo-950/30 border border-primary-500/30 gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center text-primary-300 shrink-0">
              <ShieldAlert size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-slate-200">Safety Agent Compliance Check</span>
                <span className="text-[10px] bg-primary-500/20 text-primary-300 font-mono px-1.5 py-0.5 rounded border border-primary-500/30">
                  RULE_ENGINE
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates PPE status, role-specific certifications, activity hazards, and equipment permissions.
              </p>
            </div>
          </div>

          <button
            id="btn-analyze-worker-safety-action"
            className={clsx(
              'btn-primary text-xs font-semibold py-2.5 px-4 flex items-center gap-2 whitespace-nowrap shadow-lg shadow-primary-500/20',
              !canWrite && 'opacity-50 cursor-not-allowed'
            )}
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending || !canWrite}
          >
            {analyzeMutation.isPending ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Analyzing Worker…</span>
              </>
            ) : (
              <>
                <Sparkles size={14} className="text-amber-300" />
                <span>ANALYZE WORKER SAFETY</span>
              </>
            )}
          </button>
        </div>

        {/* Latest Analysis Result Banner */}
        <AnimatePresence>
          {analysisResult && (() => {
            const score = analysisResult.overall_safety_score ?? analysisResult.summary?.overall_safety_score ?? 0;
            const level = analysisResult.safety_level ?? analysisResult.summary?.safety_level ?? 'low';
            const violCount = analysisResult.violation_count ?? analysisResult.summary?.violation_count ?? 0;
            const critCount = analysisResult.critical_count ?? analysisResult.summary?.critical_count ?? 0;
            const highCount = analysisResult.high_count ?? analysisResult.summary?.high_count ?? 0;

            return (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className={clsx(
                  'p-4 rounded-xl border text-sm',
                  level === 'low'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
                    : level === 'medium'
                      ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                      : 'bg-red-500/10 border-red-500/30 text-red-200'
                )}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold flex items-center gap-1.5">
                    <CheckCircle2 size={16} /> Analysis Score: {score}/100
                  </span>
                  <span className="text-xs uppercase font-bold tracking-wider font-mono">
                    Level: {level}
                  </span>
                </div>
                <p className="text-xs opacity-90">
                  {violCount === 0
                    ? 'Worker has met all current PPE and safety certification requirements.'
                    : `${violCount} safety finding(s) detected (${critCount} CRITICAL, ${highCount} HIGH). Check recommended actions below.`}
                </p>
              </motion.div>
            );
          })()}
        </AnimatePresence>

        {/* Safety Findings List */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert size={14} className="text-amber-400" />
              Safety Findings ({findings?.length ?? 0})
            </h4>
            {findings && findings.length > 0 && (
              <span className="text-xs text-slate-500">
                {findings.filter(f => f.status === 'open').length} Open
              </span>
            )}
          </div>

          {findingsLoading ? (
            <div className="text-center py-8 text-slate-500 text-xs">Loading safety findings…</div>
          ) : !findings || findings.length === 0 ? (
            <div className="p-6 rounded-xl bg-surface-900 border border-slate-800/80 text-center">
              <ShieldCheck size={28} className="mx-auto text-emerald-400 mb-2 opacity-80" />
              <p className="text-sm text-slate-300 font-medium">No Safety Violations Detected</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Worker is in good standing. Click [ ANALYZE WORKER SAFETY ] to perform a fresh audit.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {findings.map(finding => (
                <div
                  key={finding.id}
                  className="p-4 rounded-xl bg-surface-900 border border-slate-800 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-slate-400 font-bold">
                        {finding.finding_id}
                      </span>
                      <span className={clsx('badge text-xs uppercase', RISK_BADGE_MAP[finding.severity])}>
                        {RISK_LABEL_MAP[finding.severity]}
                      </span>
                      <span className="text-xs font-semibold text-slate-200">
                        {FINDING_TYPE_LABEL[finding.finding_type] || finding.finding_type}
                      </span>
                    </div>

                    <span className={clsx('badge text-xs', FINDING_STATUS_BADGE[finding.status])}>
                      {finding.status.toUpperCase()}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 font-medium mb-2">{finding.description}</p>

                  {finding.evidence && (
                    <div className="text-xs bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 text-slate-400 mb-2">
                      <span className="text-slate-500 font-semibold block mb-0.5 uppercase tracking-wider text-[10px]">
                        Evidence
                      </span>
                      {finding.evidence}
                    </div>
                  )}

                  {finding.recommendation && (
                    <div className="text-xs bg-amber-500/5 p-2.5 rounded-lg border border-amber-500/20 text-amber-200 mb-3">
                      <span className="text-amber-400 font-semibold block mb-0.5 uppercase tracking-wider text-[10px]">
                        Recommended Action
                      </span>
                      {finding.recommendation}
                    </div>
                  )}

                  {finding.mitigation_notes && (
                    <div className="text-xs bg-emerald-500/5 p-2 rounded-lg border border-emerald-500/20 text-emerald-300 mb-3">
                      <span className="text-emerald-400 font-semibold block mb-0.5 text-[10px] uppercase">
                        Mitigation Notes
                      </span>
                      {finding.mitigation_notes}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px] text-slate-500">
                    <span className="font-mono text-[10px] text-primary-400 bg-primary-500/10 px-1.5 py-0.5 rounded">
                      {finding.detection_source}
                    </span>

                    <div className="flex gap-2">
                      {finding.status === 'open' && canWrite && (
                        <button
                          className="btn-ghost text-xs py-1 px-2.5"
                          onClick={() => updateFindingMutation.mutate({
                            id: finding.id,
                            data: { status: 'acknowledged' }
                          })}
                          disabled={updateFindingMutation.isPending}
                        >
                          Acknowledge
                        </button>
                      )}
                      {finding.status === 'acknowledged' && canWrite && (
                        <button
                          className="btn-ghost text-xs py-1 px-2.5 text-emerald-400 border-emerald-500/20"
                          onClick={() => setMitigateTarget(finding)}
                        >
                          Mitigate
                        </button>
                      )}
                      {finding.status === 'mitigated' && canWrite && (
                        <button
                          className="btn-ghost text-xs py-1 px-2.5 text-slate-400"
                          onClick={() => updateFindingMutation.mutate({
                            id: finding.id,
                            data: { status: 'closed' }
                          })}
                          disabled={updateFindingMutation.isPending}
                        >
                          Close
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Mitigate Note Modal */}
        <AnimatePresence>
          {mitigateTarget && (
            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="card w-full max-w-md p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Wrench size={16} className="text-emerald-400" />
                    <h3 className="font-semibold text-slate-200">Mitigate Finding</h3>
                  </div>
                  <button onClick={() => setMitigateTarget(null)} className="btn-ghost p-1">
                    <X size={16} />
                  </button>
                </div>
                <p className="text-xs text-slate-400 mb-3">{mitigateTarget.description}</p>
                <textarea
                  value={mitigationNotes}
                  onChange={e => setMitigationNotes(e.target.value)}
                  placeholder="Detail corrective actions implemented (e.g., provided certified helmet, reassigned task)…"
                  rows={3}
                  className="input w-full text-xs resize-none mb-4"
                />
                <div className="flex gap-2 justify-end">
                  <button className="btn-ghost text-xs" onClick={() => setMitigateTarget(null)}>
                    Cancel
                  </button>
                  <button
                    className="btn-primary text-xs"
                    disabled={!mitigationNotes.trim() || updateFindingMutation.isPending}
                    onClick={() => updateFindingMutation.mutate({
                      id: mitigateTarget.id,
                      data: { status: 'mitigated', mitigation_notes: mitigationNotes.trim() }
                    })}
                  >
                    Confirm Mitigation
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </Modal>
  );
}
