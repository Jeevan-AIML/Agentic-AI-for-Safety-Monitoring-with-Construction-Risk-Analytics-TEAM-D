import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert, AlertTriangle, CheckCircle2, Clock, MapPin,
  Cpu, FileText, ArrowRight, X, Sparkles
} from 'lucide-react';
import { hazardsApi } from '@/services/api';
import { Modal } from '@/components/common';
import {
  HAZARD_STATUS_BADGE, HAZARD_STATUS_LABEL, HAZARD_TYPE_LABEL,
  RISK_BADGE_MAP, RISK_LABEL_MAP, formatDate, formatRelativeTime
} from '@/utils/display';
import { getRiskColor, getRiskCategory } from '@/utils/riskScoring';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { Hazard } from '@/types';

interface HazardDetailModalProps {
  hazard: Hazard | null;
  open: boolean;
  onClose: () => void;
  onUpdated?: () => void;
}

const PROBABILITY_LABELS: Record<number, string> = {
  1: 'Rare (1/5)',
  2: 'Unlikely (2/5)',
  3: 'Possible (3/5)',
  4: 'Likely (4/5)',
  5: 'Almost Certain (5/5)',
};

const SEVERITY_LABELS: Record<number, string> = {
  1: 'Minor (1/5)',
  2: 'Moderate (2/5)',
  3: 'Significant (3/5)',
  4: 'Major (4/5)',
  5: 'Catastrophic (5/5)',
};

export default function HazardDetailModal({
  hazard,
  open,
  onClose,
  onUpdated,
}: HazardDetailModalProps) {
  const { user } = useAuthStore();
  const [mitigationNotes, setMitigationNotes] = useState('');
  const [showMitigateForm, setShowMitigateForm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  if (!hazard) return null;

  const color = getRiskColor(hazard.risk_score);
  const isSuperAdmin = user?.role === 'super_admin';
  const isSafetyOfficer = user?.role === 'safety_officer';
  const isManager = user?.role === 'project_manager' || user?.role === 'site_manager';
  const canModify = isSuperAdmin || isSafetyOfficer || isManager;

  const handleAcknowledge = async () => {
    try {
      setActionLoading(true);
      await hazardsApi.acknowledge(hazard.id);
      toast.success('Hazard acknowledged. Status updated to Under Review.');
      onUpdated?.();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to acknowledge hazard');
    } finally {
      setActionLoading(false);
    }
  };

  const handleMitigate = async () => {
    if (!mitigationNotes.trim()) {
      toast.error('Please provide mitigation notes detailing actions taken.');
      return;
    }
    try {
      setActionLoading(true);
      await hazardsApi.mitigate(hazard.id, mitigationNotes);
      toast.success('Hazard marked as mitigated.');
      setShowMitigateForm(false);
      setMitigationNotes('');
      onUpdated?.();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to record mitigation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCloseHazard = async () => {
    try {
      setActionLoading(true);
      await hazardsApi.close(hazard.id);
      toast.success('Hazard closed.');
      onUpdated?.();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to close hazard');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={`Hazard Details — ${hazard.hazard_id}`} size="lg">
      <div className="space-y-5">
        {/* Top Header Banner */}
        <div
          className="p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
          style={{
            backgroundColor: color + '10',
            borderColor: color + '30',
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-14 h-14 rounded-xl flex flex-col items-center justify-center shrink-0 font-bold"
              style={{ backgroundColor: color + '25', color }}
            >
              <span className="text-xl leading-none">{hazard.risk_score.toFixed(0)}</span>
              <span className="text-[9px] uppercase tracking-wider">{hazard.risk_category}</span>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="font-mono text-xs text-slate-400 font-semibold">{hazard.hazard_id}</span>
                <span className="badge badge-monitoring text-xs">
                  {HAZARD_TYPE_LABEL[hazard.hazard_type]}
                </span>
                <span className={clsx('badge text-xs', HAZARD_STATUS_BADGE[hazard.status])}>
                  {HAZARD_STATUS_LABEL[hazard.status]}
                </span>
              </div>
              <h3 className="text-base font-semibold text-slate-100">{hazard.description}</h3>
            </div>
          </div>

          <div className="shrink-0 flex sm:flex-col items-end gap-1 text-xs text-slate-400">
            <span className="badge bg-surface-800 border border-slate-700 text-slate-300 font-mono">
              Source: {hazard.detection_source || 'RULE_ENGINE'}
            </span>
            <span>{formatRelativeTime(hazard.detected_at)}</span>
          </div>
        </div>

        {/* Why it was detected / Evidence */}
        <div className="card p-4 bg-surface-850 border border-slate-800">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400 mb-2">
            <AlertTriangle size={14} />
            Why was this hazard detected? (Evidence)
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">
            {hazard.evidence ||
              `Detected through deterministic safety rule matching active site activities (${HAZARD_TYPE_LABEL[hazard.hazard_type]}) and recorded environmental/equipment conditions.`}
          </p>
        </div>

        {/* Risk Metrics Breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="card p-3 bg-surface-850">
            <span className="text-[11px] text-slate-500 uppercase tracking-wider">Probability</span>
            <div className="text-base font-bold text-slate-200 mt-0.5">
              {PROBABILITY_LABELS[hazard.probability] || `${hazard.probability} / 5`}
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="h-full bg-amber-400 rounded-full"
                style={{ width: `${(hazard.probability / 5) * 100}%` }}
              />
            </div>
          </div>

          <div className="card p-3 bg-surface-850">
            <span className="text-[11px] text-slate-500 uppercase tracking-wider">Severity</span>
            <div className="text-base font-bold text-slate-200 mt-0.5">
              {SEVERITY_LABELS[hazard.severity] || `${hazard.severity} / 5`}
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="h-full bg-red-400 rounded-full"
                style={{ width: `${(hazard.severity / 5) * 100}%` }}
              />
            </div>
          </div>

          <div className="card p-3 bg-surface-850">
            <span className="text-[11px] text-slate-500 uppercase tracking-wider">Calculated Score</span>
            <div className="text-base font-bold tabular-nums mt-0.5" style={{ color }}>
              {hazard.risk_score.toFixed(0)} / 100
            </div>
            <div className="text-[10px] text-slate-500 mt-1">
              ({hazard.probability} × {hazard.severity} / 25) × 100
            </div>
          </div>
        </div>

        {/* Recommended Action */}
        <div className="card p-4 border-l-4 border-l-primary-500 bg-primary-950/20 border-slate-800">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary-400 mb-1.5">
            <CheckCircle2 size={14} />
            Recommended Action
          </div>
          <p className="text-sm text-slate-100 font-medium leading-relaxed">
            {hazard.recommended_action || 'Inspect area immediately and apply standard risk controls.'}
          </p>
        </div>

        {/* Lifecycle Status & Metadata */}
        <div className="card p-4 bg-surface-850 space-y-2 text-xs text-slate-400">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <span className="text-slate-500 block">Site:</span>
              <span className="text-slate-200 font-medium">{hazard.site_name || hazard.site_id}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Detected:</span>
              <span className="text-slate-200 font-medium">{formatDate(hazard.detected_at)}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Reported By:</span>
              <span className="text-slate-200 font-medium">{hazard.reported_by || 'Rule Engine'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Detection Source:</span>
              <span className="text-slate-200 font-medium font-mono">{hazard.detection_source || 'RULE_ENGINE'}</span>
            </div>
          </div>

          {/* Mitigation Notes if available */}
          {hazard.mitigation_notes && (
            <div className="pt-2 mt-2 border-t border-slate-800">
              <span className="text-slate-500 block font-medium mb-0.5">Mitigation Notes:</span>
              <p className="text-slate-300 bg-surface-900 p-2.5 rounded border border-slate-800">
                {hazard.mitigation_notes}
              </p>
            </div>
          )}
        </div>

        {/* Inline Mitigate Notes Form */}
        <AnimatePresence>
          {showMitigateForm && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="card p-4 border border-green-500/30 bg-green-500/5 space-y-3"
            >
              <label className="text-xs font-semibold text-green-400 uppercase tracking-wider block">
                Record Mitigation Actions Taken:
              </label>
              <textarea
                value={mitigationNotes}
                onChange={(e) => setMitigationNotes(e.target.value)}
                placeholder="Detail the safety controls implemented (e.g., shoring installed, standing water pumped out, de-energized wiring)..."
                className="input h-20 text-xs resize-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  className="btn-secondary text-xs"
                  onClick={() => setShowMitigateForm(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn-primary text-xs bg-green-600 hover:bg-green-500 border-green-600"
                  onClick={handleMitigate}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Saving...' : 'Confirm Mitigation'}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-500">
            {canModify ? 'Authorized to perform safety lifecycle actions' : 'Viewing in read-only mode'}
          </div>

          <div className="flex items-center gap-2">
            <button type="button" className="btn-secondary text-xs" onClick={onClose}>
              Close Window
            </button>

            {canModify && hazard.status === 'open' && (
              <button
                type="button"
                className="btn-secondary text-xs text-amber-400 hover:bg-amber-500/10 border-amber-500/30"
                onClick={handleAcknowledge}
                disabled={actionLoading}
              >
                {actionLoading ? 'Processing...' : 'Acknowledge (Review)'}
              </button>
            )}

            {canModify && (hazard.status === 'open' || hazard.status === 'under_review') && !showMitigateForm && (
              <button
                type="button"
                className="btn-primary text-xs bg-green-600 hover:bg-green-500 border-green-600"
                onClick={() => setShowMitigateForm(true)}
                disabled={actionLoading}
              >
                Mitigate Hazard
              </button>
            )}

            {canModify && hazard.status !== 'closed' && (
              <button
                type="button"
                className="btn-ghost text-xs text-slate-400 hover:text-red-400 hover:bg-red-500/10"
                onClick={handleCloseHazard}
                disabled={actionLoading}
              >
                Close Hazard
              </button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
