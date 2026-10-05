import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getRiskColor, getRiskLabel, getRiskCategory } from '@/utils/riskScoring';
import clsx from 'clsx';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: number;
  isRisk?: boolean;
  riskScore?: number;
  accent?: string;
  loading?: boolean;
  delay?: number;
}

export function KPICard({
  title, value, subtitle, icon, trend, isRisk, riskScore, accent = 'from-primary-500/10', loading, delay = 0
}: KPICardProps) {
  const riskColor = riskScore != null ? getRiskColor(riskScore) : undefined;
  const riskLabel = riskScore != null ? getRiskLabel(riskScore) : undefined;

  if (loading) {
    return (
      <div className="card p-5">
        <div className="skeleton h-4 w-24 mb-3" />
        <div className="skeleton h-9 w-16 mb-2" />
        <div className="skeleton h-3 w-20" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={clsx(
        'card-hover p-5 overflow-hidden relative',
        'bg-gradient-to-br', accent
      )}
    >
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-white/3 blur-xl" />

      <div className="flex items-start justify-between mb-4">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</div>
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-400"
          style={riskColor ? { color: riskColor, backgroundColor: riskColor + '20' } : {}}
        >
          {icon}
        </div>
      </div>

      <div className="flex items-end gap-3">
        <div className="tabular-nums">
          <span
            className="text-3xl font-bold text-slate-100"
            style={riskColor ? { color: riskColor } : {}}
          >
            {value}
          </span>
          {riskScore != null && (
            <span className="ml-1 text-sm font-medium" style={{ color: riskColor }}>
              / 100
            </span>
          )}
        </div>
      </div>

      {riskLabel && (
        <div
          className="inline-flex items-center gap-1.5 mt-1 px-2 py-0.5 rounded text-xs font-bold"
          style={{ color: riskColor, backgroundColor: riskColor + '20' }}
        >
          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: riskColor }} />
          {riskLabel}
        </div>
      )}

      {subtitle && !riskLabel && (
        <div className="text-sm text-slate-500 mt-1">{subtitle}</div>
      )}

      {trend != null && (
        <div className={clsx(
          'flex items-center gap-1 mt-2 text-xs font-medium',
          trend > 0 ? 'text-red-400' : trend < 0 ? 'text-green-400' : 'text-slate-500'
        )}>
          {trend > 0 ? <TrendingUp size={12} /> : trend < 0 ? <TrendingDown size={12} /> : <Minus size={12} />}
          {Math.abs(trend)}% from last week
        </div>
      )}
    </motion.div>
  );
}

// ── Risk Gauge ─────────────────────────────────────────────────────────────

interface RiskGaugeProps {
  score: number;
  size?: number;
  label?: string;
  displayValue?: string | number;
}

export function RiskGauge({ score, size = 120, label: customLabel, displayValue }: RiskGaugeProps) {
  const color = getRiskColor(score);
  const label = customLabel || getRiskLabel(score);
  const r = 45;
  const cx = 60;
  const cy = 60;
  const circumference = 2 * Math.PI * r;
  // 270 degrees of arc (start -225deg end 45deg)
  const arcLength = circumference * 0.75;
  const fillLength = arcLength * (Math.min(100, Math.max(0, score)) / 100);

  const formattedScore = displayValue !== undefined
    ? displayValue
    : (Number.isInteger(score) ? score : score.toFixed(1));

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox="0 0 120 120">
        {/* Background arc */}
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke="#1e293b"
          strokeWidth={10}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform="rotate(135 60 60)"
        />
        {/* Filled arc */}
        <motion.circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeDasharray={`${fillLength} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform="rotate(135 60 60)"
          initial={{ strokeDasharray: `0 ${circumference}` }}
          animate={{ strokeDasharray: `${fillLength} ${circumference}` }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
        {/* Score text */}
        <text x={cx} y={cy - 4} textAnchor="middle" className="tabular-nums" fill={color} fontSize="20" fontWeight="700">
          {formattedScore}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fill="#64748b" fontSize="9" fontWeight="600">
          {label}
        </text>
      </svg>
    </div>
  );
}

// ── Empty State ────────────────────────────────────────────────────────────

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      <div className="w-16 h-16 rounded-2xl bg-surface-800 border border-slate-700 flex items-center justify-center text-slate-500 mb-4">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-slate-300 mb-1">{title}</h3>
      {description && <p className="text-sm text-slate-600 max-w-sm mb-5">{description}</p>}
      {action}
    </div>
  );
}

// ── Loading Spinner ────────────────────────────────────────────────────────

export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      style={{ width: size, height: size }}
      className="border-2 border-slate-700 border-t-primary-500 rounded-full"
    />
  );
}

// ── Page loader ────────────────────────────────────────────────────────────

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-64">
      <Spinner size={32} />
    </div>
  );
}

// ── Coming Soon ────────────────────────────────────────────────────────────

interface ComingSoonProps {
  title: string;
  milestone: string;
  description?: string;
  icon: React.ReactNode;
}

export function ComingSoon({ title, milestone, description, icon }: ComingSoonProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-24 px-8 text-center"
    >
      <div className="w-20 h-20 rounded-2xl bg-surface-800 border border-slate-700/50 flex items-center justify-center text-slate-500 mb-6">
        {icon}
      </div>
      <div className="badge badge-monitoring mb-3">{milestone}</div>
      <h2 className="text-xl font-bold text-slate-200 mb-2">{title}</h2>
      <p className="text-sm text-slate-500 max-w-md mb-6">
        {description || `This module will be available in ${milestone}. The data architecture is already prepared for integration.`}
      </p>
      <div className="flex items-center gap-2 text-xs text-slate-600">
        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
        Data layer ready · Agent integration pending
      </div>
    </motion.div>
  );
}

// ── Modal ──────────────────────────────────────────────────────────────────

import { AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export function Modal({ open, onClose, title, children, size = 'md' }: ModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.2 }}
            className={clsx('relative card w-full', sizeClasses[size])}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
              <h2 className="text-base font-semibold text-slate-100">{title}</h2>
              <button onClick={onClose} className="btn-icon">
                <X size={16} />
              </button>
            </div>
            <div className="px-6 py-5">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

// ── Confirm Dialog ─────────────────────────────────────────────────────────

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  loading?: boolean;
}

export function ConfirmDialog({ open, onClose, onConfirm, title, message, confirmLabel = 'Delete', loading }: ConfirmDialogProps) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className="text-sm text-slate-400 mb-6">{message}</p>
      <div className="flex gap-3 justify-end">
        <button className="btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn-danger" onClick={onConfirm} disabled={loading}>
          {loading ? <Spinner size={14} /> : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}

export { default as HazardDetailModal } from './HazardDetailModal';
export { default as WorkerSafetyModal } from './WorkerSafetyModal';

