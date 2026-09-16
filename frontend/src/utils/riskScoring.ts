/**
 * Risk Scoring Utility (Frontend)
 * ================================
 * Mirrors the backend risk_scoring.py for client-side display.
 * Single source of truth for risk thresholds.
 *
 * NOTE: In Phase 1.2, risk scores will come directly from the
 * Site Risk Agent API. These functions remain useful for display
 * formatting and local validation.
 */

import type { RiskCategory } from '@/types';

// ── Configurable thresholds ────────────────────────────────────────────────
export const RISK_THRESHOLDS = {
  low: { min: 0, max: 24, label: 'LOW', color: '#22c55e', bg: 'bg-green-500/15', text: 'text-green-400', border: 'border-green-500/20' },
  medium: { min: 25, max: 49, label: 'MEDIUM', color: '#f59e0b', bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/20' },
  high: { min: 50, max: 74, label: 'HIGH', color: '#f97316', bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/20' },
  critical: { min: 75, max: 100, label: 'CRITICAL', color: '#ef4444', bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/20' },
} as const;

export function calculateRiskScore(probability: number, severity: number): number {
  const raw = probability * severity; // max 25
  return Math.round((raw / 25) * 100 * 100) / 100;
}

export function getRiskCategory(score: number): RiskCategory {
  if (score >= 75) return 'critical';
  if (score >= 50) return 'high';
  if (score >= 25) return 'medium';
  return 'low';
}

export function getRiskThreshold(category: RiskCategory) {
  return RISK_THRESHOLDS[category];
}

export function getRiskColor(score: number): string {
  return getRiskThreshold(getRiskCategory(score)).color;
}

export function getRiskLabel(score: number): string {
  return getRiskThreshold(getRiskCategory(score)).label;
}

export function getRiskClasses(category: RiskCategory) {
  const t = RISK_THRESHOLDS[category];
  return `${t.bg} ${t.text} ${t.border}`;
}

// Gauge arc calculation for circular risk indicator
export function getRiskArcPath(score: number, radius = 60): { d: string; color: string } {
  const angle = (score / 100) * 270 - 135;
  const rad = (angle * Math.PI) / 180;
  const x = 80 + radius * Math.cos(rad);
  const y = 80 + radius * Math.sin(rad);
  return { d: `M ${x} ${y}`, color: getRiskColor(score) };
}
