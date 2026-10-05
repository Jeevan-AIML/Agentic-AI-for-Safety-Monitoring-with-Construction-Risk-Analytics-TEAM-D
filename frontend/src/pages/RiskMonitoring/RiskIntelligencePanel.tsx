import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ShieldAlert, RefreshCw, AlertTriangle, TrendingUp, CheckCircle2,
  Clock, ArrowRight, ShieldCheck, Cpu, Zap, Layers, AlertOctagon,
  Target, BarChart3, ChevronRight, Activity, Calendar
} from 'lucide-react';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import { riskIntelligenceApi } from '@/services/api';
import { EmptyState, PageLoader, RiskGauge } from '@/components/common';
import { getRiskColor, getRiskCategory } from '@/utils/riskScoring';
import { formatRelativeTime, formatDate } from '@/utils/display';
import type {
  RiskIntelligenceAssessment,
  RecurringPattern,
  PotentialIncidentPrediction,
  OperationalRecommendation
} from '@/types';

interface RiskIntelligencePanelProps {
  siteId: string;
  siteName?: string;
}

export default function RiskIntelligencePanel({ siteId, siteName }: RiskIntelligencePanelProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'overview' | 'patterns' | 'predictions' | 'recommendations'>('overview');

  // Fetch latest risk intelligence assessment
  const {
    data: assessment,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['risk-intelligence', siteId],
    queryFn: () => riskIntelligenceApi.getLatest(siteId).then((r) => r.data as RiskIntelligenceAssessment),
    enabled: !!siteId,
  });

  // Mutation to trigger fresh multi-agent analysis
  const analyzeMutation = useMutation({
    mutationFn: () =>
      riskIntelligenceApi.analyze({
        site_id: siteId,
        analysis_window_days: 30,
        include_predictions: true,
        include_patterns: true,
        include_recommendations: true,
      }),
    onMutate: () => {
      toast.loading('Consolidating multi-agent risk signals...', { id: 'risk-intel-toast' });
    },
    onSuccess: (res) => {
      toast.success('Risk intelligence assessment refreshed!', { id: 'risk-intel-toast' });
      queryClient.setQueryData(['risk-intelligence', siteId], res.data);
      queryClient.invalidateQueries({ queryKey: ['risk-summary', siteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-intelligence-history', siteId] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Assessment failed', { id: 'risk-intel-toast' });
    },
  });

  if (!siteId) {
    return (
      <EmptyState
        icon={<ShieldAlert size={32} />}
        title="No Site Selected"
        description="Please select an active site to view its Construction Risk Intelligence assessment."
      />
    );
  }

  if (isLoading) {
    return <PageLoader />;
  }

  const overallScore = assessment?.overall_risk_score ?? 0;
  const overallColor = getRiskColor(overallScore);
  const riskTier = assessment?.risk_level || getRiskCategory(overallScore).toUpperCase();

  const rawCatScores = (assessment?.category_scores || {}) as any;
  const extractScore = (key: 'site_risk' | 'safety_risk' | 'compliance_risk' | 'insurance_risk'): number => {
    if (typeof rawCatScores[`${key}_score`] === 'number') return rawCatScores[`${key}_score`];
    if (typeof rawCatScores[key] === 'number') return rawCatScores[key];
    if (rawCatScores[key] && typeof rawCatScores[key].score === 'number') return rawCatScores[key].score;
    return 0;
  };

  const categoryScores = {
    site_risk_score: extractScore('site_risk'),
    safety_risk_score: extractScore('safety_risk'),
    compliance_risk_score: extractScore('compliance_risk'),
    insurance_risk_score: extractScore('insurance_risk'),
    weights: rawCatScores.weights || { site_risk: 0.3, safety_risk: 0.3, compliance_risk: 0.2, insurance_risk: 0.2 },
  };

  const patterns: RecurringPattern[] = assessment?.recurring_patterns || [];
  const predictions: PotentialIncidentPrediction[] = assessment?.predicted_incidents || [];
  const recommendations: OperationalRecommendation[] = assessment?.recommendations || [];

  return (
    <div className="space-y-6">
      {/* Top Banner / Assessment Meta */}
      <div className="card p-5 bg-gradient-to-r from-surface-850 via-surface-900 to-surface-850 border border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="badge bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold flex items-center gap-1">
                <Cpu size={12} />
                Risk Intelligence Engine
              </span>
              <span className="badge bg-slate-800 border border-slate-700 text-slate-400 text-xs font-mono">
                Engine: MULTI_AGENT_RISK_SYNTHESIS
              </span>
              {assessment?.assessment_id && (
                <span className="text-xs text-slate-500 font-mono">
                  ID: {assessment.assessment_id}
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              Construction Risk Intelligence Engine
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Synthesis of Site Risk, Safety, Compliance, and Insurance agent telemetry with deterministic causal incident prediction
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              id="btn-reanalyze-intelligence"
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="btn-primary text-sm flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-lg shadow-purple-500/20"
            >
              <RefreshCw size={14} className={clsx(analyzeMutation.isPending && 'animate-spin')} />
              <span>{analyzeMutation.isPending ? 'Synthesizing...' : 'Run Intelligence Synthesis'}</span>
            </button>
          </div>
        </div>

        {/* Sub-tab Navigation */}
        <div className="flex gap-2 mt-5 pt-4 border-t border-slate-800/80 overflow-x-auto">
          {[
            { id: 'overview', label: 'Score & 4-Pillars', icon: <BarChart3 size={14} />, badge: null },
            { id: 'patterns', label: 'Recurring Patterns', icon: <Layers size={14} />, badge: patterns.length },
            { id: 'predictions', label: 'Incident Predictions', icon: <Zap size={14} />, badge: predictions.length },
            { id: 'recommendations', label: 'Operational Actions', icon: <Target size={14} />, badge: recommendations.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                'flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap',
                activeTab === tab.id
                  ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800 border border-transparent'
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge !== null && tab.badge > 0 && (
                <span className={clsx(
                  'px-1.5 py-0.2 rounded-full text-[10px] font-bold',
                  activeTab === tab.id ? 'bg-purple-500 text-white' : 'bg-slate-700 text-slate-300'
                )}>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* TAB 1: OVERVIEW & 4-PILLAR BREAKDOWN */}
      {activeTab === 'overview' && (
        <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Unified Project Risk Score Card */}
            <div className="lg:col-span-4 card p-6 flex flex-col justify-between bg-gradient-to-br from-surface-850 to-surface-900 border border-slate-800">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Consolidated Project Risk
                    </span>
                    <h3 className="text-base font-semibold text-white mt-0.5">{siteName || 'Site ' + siteId}</h3>
                  </div>
                  <span
                    className="px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider"
                    style={{ backgroundColor: `${overallColor}20`, color: overallColor, border: `1px solid ${overallColor}40` }}
                  >
                    {riskTier}
                  </span>
                </div>

                <div className="flex flex-col items-center justify-center my-4">
                  <RiskGauge score={overallScore} size={150} />
                  <div className="mt-3 text-center">
                    <span className="text-4xl font-extrabold tabular-nums" style={{ color: overallColor }}>
                      {overallScore != null ? overallScore.toFixed(1) : '—'}
                    </span>
                    <span className="text-slate-500 text-sm font-medium ml-1">/ 100</span>
                    <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                      Composite Risk Index
                    </p>
                  </div>
                </div>
              </div>

              {/* Assessment Stats */}
              <div className="pt-4 border-t border-slate-800 text-xs text-slate-400 space-y-2">
                <div className="flex justify-between">
                  <span>Synthesized Findings:</span>
                  <span className="font-bold text-white">{assessment?.findings_count ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Critical / High Severity:</span>
                  <span className="font-bold text-red-400">
                    {assessment?.critical_findings_count ?? 0} Crit · {assessment?.high_findings_count ?? 0} High
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Last Evaluated:</span>
                  <span className="text-slate-300">
                    {assessment?.assessed_at ? formatRelativeTime(assessment.assessed_at) : 'Just now'}
                  </span>
                </div>
              </div>
            </div>

            {/* 4 Pillars Grid */}
            <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Pillar 1: Site Risk */}
              <div className="card p-5 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        <Activity size={16} />
                      </span>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Site Physical Risk</h4>
                        <span className="text-[10px] text-slate-400">Weight: 30% · M1 Telemetry</span>
                      </div>
                    </div>
                    <span
                      className="text-lg font-bold tabular-nums"
                      style={{ color: getRiskColor(categoryScores.site_risk_score) }}
                    >
                      {categoryScores.site_risk_score != null ? categoryScores.site_risk_score.toFixed(1) : '—'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden my-3">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, Math.max(5, categoryScores.site_risk_score ?? 0))}%`,
                        backgroundColor: getRiskColor(categoryScores.site_risk_score),
                      }}
                    />
                  </div>
                  <p className="text-xs text-slate-400">
                    Environmental conditions, equipment hazards, structural integrity, and drone inspection findings.
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-500">
                  <span>Status:</span>
                  <span className="font-semibold text-slate-300 uppercase">
                    {getRiskCategory(categoryScores.site_risk_score)}
                  </span>
                </div>
              </div>

              {/* Pillar 2: Safety Intelligence */}
              <div className="card p-5 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                        <ShieldAlert size={16} />
                      </span>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Worker Safety Risk</h4>
                        <span className="text-[10px] text-slate-400">Weight: 30% · M2 Telemetry</span>
                      </div>
                    </div>
                    <span
                      className="text-lg font-bold tabular-nums"
                      style={{ color: getRiskColor(categoryScores.safety_risk_score) }}
                    >
                      {categoryScores.safety_risk_score != null ? categoryScores.safety_risk_score.toFixed(1) : '—'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden my-3">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, Math.max(5, categoryScores.safety_risk_score ?? 0))}%`,
                        backgroundColor: getRiskColor(categoryScores.safety_risk_score),
                      }}
                    />
                  </div>
                  <p className="text-xs text-slate-400">
                    PPE compliance deficits, zone breaches, lone worker alerts, and active safety observations.
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-500">
                  <span>Status:</span>
                  <span className="font-semibold text-slate-300 uppercase">
                    {getRiskCategory(categoryScores.safety_risk_score)}
                  </span>
                </div>
              </div>

              {/* Pillar 3: Compliance Risk */}
              <div className="card p-5 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        <ShieldCheck size={16} />
                      </span>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Regulatory Compliance Risk</h4>
                        <span className="text-[10px] text-slate-400">Weight: 20% · M3 Telemetry</span>
                      </div>
                    </div>
                    <span
                      className="text-lg font-bold tabular-nums"
                      style={{ color: getRiskColor(categoryScores.compliance_risk_score) }}
                    >
                      {categoryScores.compliance_risk_score != null ? categoryScores.compliance_risk_score.toFixed(1) : '—'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden my-3">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, Math.max(5, categoryScores.compliance_risk_score ?? 0))}%`,
                        backgroundColor: getRiskColor(categoryScores.compliance_risk_score),
                      }}
                    />
                  </div>
                  <p className="text-xs text-slate-400">
                    Statutory rule non-compliance, OSHA standard breaches, and overdue safety inspections.
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-500">
                  <span>Status:</span>
                  <span className="font-semibold text-slate-300 uppercase">
                    {getRiskCategory(categoryScores.compliance_risk_score)}
                  </span>
                </div>
              </div>

              {/* Pillar 4: Insurance Exposure */}
              <div className="card p-5 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        <TrendingUp size={16} />
                      </span>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Insurance & Financial Exposure</h4>
                        <span className="text-[10px] text-slate-400">Weight: 20% · M3 Telemetry</span>
                      </div>
                    </div>
                    <span
                      className="text-lg font-bold tabular-nums"
                      style={{ color: getRiskColor(categoryScores.insurance_risk_score) }}
                    >
                      {categoryScores.insurance_risk_score != null ? categoryScores.insurance_risk_score.toFixed(1) : '—'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden my-3">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, Math.max(5, categoryScores.insurance_risk_score ?? 0))}%`,
                        backgroundColor: getRiskColor(categoryScores.insurance_risk_score),
                      }}
                    />
                  </div>
                  <p className="text-xs text-slate-400">
                    Underwriting loss exposure, unmitigated claim indicators, and premium impact risk.
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-500">
                  <span>Status:</span>
                  <span className="font-semibold text-slate-300 uppercase">
                    {getRiskCategory(categoryScores.insurance_risk_score)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* TAB 2: RECURRING RISK PATTERNS */}
      {activeTab === 'patterns' && (
        <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-base font-semibold text-white">Detected Recurring Risk Patterns</h3>
              <p className="text-xs text-slate-400">
                Identifies hazard and violation patterns recurring $\ge 2$ times across time windows (24h, 7d, 30d).
              </p>
            </div>
            <span className="badge bg-slate-800 border border-slate-700 text-slate-300 text-xs">
              {patterns.length} Active Pattern{patterns.length === 1 ? '' : 's'}
            </span>
          </div>

          {patterns.length === 0 ? (
            <div className="card p-8 border border-slate-800 text-center">
              <CheckCircle2 size={36} className="mx-auto text-emerald-400 mb-2" />
              <h4 className="text-base font-semibold text-slate-200">No Recurring Risk Patterns Detected</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                Findings are either isolated incidents or within baseline variance. Patterns require $\ge 2$ identical observations within the 30-day window.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {patterns.map((pattern) => (
                <div
                  key={pattern.pattern_id}
                  className="card p-5 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className={clsx(
                          'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                          pattern.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                          pattern.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                          'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        )}>
                          {pattern.severity}
                        </span>
                        <span className="text-xs font-semibold text-slate-300">
                          {pattern.category}
                        </span>
                      </div>
                      <span className="badge bg-purple-500/20 border border-purple-500/30 text-purple-300 text-xs font-bold">
                        {pattern.occurrence_count} Occurrences
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-white mb-2">
                      {pattern.pattern_description}
                    </h4>

                    <div className="flex flex-wrap gap-2 text-[11px] text-slate-400 mb-3">
                      <span className="flex items-center gap-1 bg-surface-900 px-2 py-0.5 rounded border border-slate-800">
                        <Clock size={11} /> {pattern.time_window_hours}h window
                      </span>
                      <span className="flex items-center gap-1 bg-surface-900 px-2 py-0.5 rounded border border-slate-800">
                        <TrendingUp size={11} /> Velocity: <strong className="text-slate-200">{pattern.velocity}</strong>
                      </span>
                    </div>

                    {pattern.locations && pattern.locations.length > 0 && (
                      <div className="text-[11px] text-slate-400 mb-2">
                        <span className="text-slate-500">Observed Zones:</span>{' '}
                        {pattern.locations.join(', ')}
                      </div>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                    <span>Type: {pattern.pattern_type}</span>
                    <span className="font-mono text-[10px] text-slate-400">{pattern.pattern_id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* TAB 3: POTENTIAL INCIDENT PREDICTIONS */}
      {activeTab === 'predictions' && (
        <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-base font-semibold text-white">Predictive Incident Intelligence</h3>
              <p className="text-xs text-slate-400">
                Explainable causal risk chains mapping leading indicators to potential high-severity safety incidents.
              </p>
            </div>
            <span className="badge bg-slate-800 border border-slate-700 text-slate-300 text-xs">
              {predictions.length} Causal Chain{predictions.length === 1 ? '' : 's'}
            </span>
          </div>

          {predictions.length === 0 ? (
            <div className="card p-8 border border-slate-800 text-center">
              <ShieldCheck size={36} className="mx-auto text-emerald-400 mb-2" />
              <h4 className="text-base font-semibold text-slate-200">No Imminent Incident Chains Identified</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                Current site leading indicators do not meet composite threshold conditions for high-severity predictive events.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {predictions.map((pred) => (
                <div
                  key={pred.prediction_id}
                  className="card p-5 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all space-y-4"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                      <span className={clsx(
                        'p-2 rounded-lg border',
                        pred.severity_potential === 'CRITICAL'
                          ? 'bg-red-500/10 text-red-400 border-red-500/30'
                          : 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                      )}>
                        <AlertOctagon size={20} />
                      </span>
                      <div>
                        <h4 className="text-base font-bold text-white">{pred.incident_type}</h4>
                        <span className="text-xs text-slate-400">
                          Primary Driver: <strong className="text-slate-200">{pred.primary_driver}</strong>
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-xs text-slate-500 font-medium">Estimated Probability</div>
                        <div className="text-lg font-extrabold text-amber-400 tabular-nums">
                          {pred.probability_score != null ? pred.probability_score.toFixed(0) : '—'}%
                        </div>
                      </div>
                      <span className={clsx(
                        'px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider border',
                        pred.severity_potential === 'CRITICAL'
                          ? 'bg-red-500/20 text-red-400 border-red-500/30'
                          : 'bg-orange-500/20 text-orange-400 border-orange-500/30'
                      )}>
                        {pred.predicted_timeframe}
                      </span>
                    </div>
                  </div>

                  {/* Causal Chain Visualization */}
                  {pred.causal_chain && pred.causal_chain.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Zap size={12} className="text-amber-400" />
                        Explainable Causal Risk Chain
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
                        {pred.causal_chain.map((step, idx) => (
                          <div
                            key={idx}
                            className="bg-surface-900 border border-slate-800 p-2.5 rounded-lg text-xs relative flex flex-col justify-between"
                          >
                            <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                              <span className="font-bold text-purple-400">STEP 0{idx + 1}</span>
                              {idx < pred.causal_chain.length - 1 && (
                                <ArrowRight size={12} className="text-slate-600 hidden md:block" />
                              )}
                            </div>
                            <p className="text-slate-300 leading-snug">{step}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Leading Indicators & Interventions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    {pred.leading_indicators && pred.leading_indicators.length > 0 && (
                      <div className="bg-surface-900/60 border border-slate-800/80 p-3 rounded-lg">
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                          Active Leading Indicators
                        </div>
                        <ul className="space-y-1.5 text-xs">
                          {pred.leading_indicators.map((ind, i) => (
                            <li key={i} className="flex items-start gap-2 text-slate-300">
                              <span className="text-amber-400 font-bold">•</span>
                              <div>
                                <span className="font-medium text-white">{ind.indicator}:</span>{' '}
                                <span className="text-slate-400">{ind.observed_value}</span>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {pred.recommended_interventions && pred.recommended_interventions.length > 0 && (
                      <div className="bg-emerald-950/20 border border-emerald-500/20 p-3 rounded-lg">
                        <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                          <CheckCircle2 size={13} />
                          Targeted Preventative Interventions
                        </div>
                        <ul className="space-y-1.5 text-xs text-slate-300">
                          {pred.recommended_interventions.map((action, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-emerald-400 font-bold">✓</span>
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* TAB 4: OPERATIONAL RECOMMENDATIONS */}
      {activeTab === 'recommendations' && (
        <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-base font-semibold text-white">Prioritized Operational Recommendations</h3>
              <p className="text-xs text-slate-400">
                Ranked actionable interventions across immediate (0-24h), short-term (1-7d), and systemic (7-30d) horizons.
              </p>
            </div>
            <span className="badge bg-slate-800 border border-slate-700 text-slate-300 text-xs">
              {recommendations.length} Recommendation{recommendations.length === 1 ? '' : 's'}
            </span>
          </div>

          {recommendations.length === 0 ? (
            <div className="card p-8 border border-slate-800 text-center">
              <CheckCircle2 size={36} className="mx-auto text-emerald-400 mb-2" />
              <h4 className="text-base font-semibold text-slate-200">All Operations Optimal</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                No outstanding high-priority operational remediations required for this site.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendations.map((rec) => (
                <div
                  key={rec.recommendation_id}
                  className="card p-5 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                        rec.priority === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        rec.priority === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                        'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      )}>
                        {rec.priority} PRIORITY
                      </span>
                      <span className="badge bg-surface-900 border border-slate-700 text-slate-300 text-xs font-semibold">
                        {rec.timeframe} HORIZON
                      </span>
                      <span className="text-xs text-slate-400 font-medium">
                        {rec.category}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span>Expected Risk Reduction: <strong className="text-emerald-400">{rec.expected_risk_reduction}</strong></span>
                      <span>Impact Level: <strong className="text-slate-200">{rec.cost_impact_level}</strong></span>
                    </div>
                  </div>

                  <h4 className="text-sm font-bold text-white">{rec.title}</h4>

                  {rec.action_items && rec.action_items.length > 0 && (
                    <div className="bg-surface-900/70 p-3 rounded-lg border border-slate-800/80">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        Required Action Items
                      </div>
                      <ul className="space-y-1.5 text-xs text-slate-300">
                        {rec.action_items.map((item, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-primary-400 font-bold">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {rec.target_hazard_types && rec.target_hazard_types.length > 0 && (
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <span>Target Hazards:</span>
                      <div className="flex flex-wrap gap-1">
                        {rec.target_hazard_types.map((h, i) => (
                          <span key={i} className="bg-surface-900 px-1.5 py-0.5 rounded border border-slate-800 text-slate-400 font-mono text-[10px]">
                            {h}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
