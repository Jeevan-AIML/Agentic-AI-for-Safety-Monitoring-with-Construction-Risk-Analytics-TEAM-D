import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ShieldAlert, ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2,
  TrendingUp, Activity, FileText, ArrowRight, RefreshCw, Calendar,
  Clock, MapPin, HardHat, ClipboardCheck, Shield, ExternalLink,
  ChevronRight, Sparkles, Filter, Info, Eye, Layers, Zap, Truck,
  Cpu, Play, X, Radio, CheckCircle, AlertCircle, FastForward
} from 'lucide-react';
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts';
import toast from 'react-hot-toast';
import clsx from 'clsx';

import { executiveDashboardApi, sitesApi, riskIntelligenceApi, orchestrationApi } from '@/services/api';
import { KPICard, RiskGauge, PageLoader, EmptyState } from '@/components/common';
import { getRiskColor, getRiskLabel, getRiskCategory } from '@/utils/riskScoring';
import { formatDate, formatRelativeTime } from '@/utils/display';
import type {
  ExecutiveDashboardResponse,
  Site,
  OperationalRecommendation,
  RecurringPattern,
  PotentialIncidentPrediction,
  ExecutiveCriticalFinding,
  OrchestrationRunResponse,
  OrchestrationStatus,
  OrchestrationMode
} from '@/types';

export default function ExecutiveDashboardPage() {
  const queryClient = useQueryClient();
  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [recommendationHorizon, setRecommendationHorizon] = useState<'all' | 'immediate' | 'short_term' | 'strategic'>('all');
  const [criticalFindingFilter, setCriticalFindingFilter] = useState<'ALL' | 'site_risk' | 'safety' | 'compliance'>('ALL');

  // 1. Fetch available sites for the site selector
  const { data: sites = [], isLoading: sitesLoading } = useQuery<Site[]>({
    queryKey: ['sites-list'],
    queryFn: () => sitesApi.list().then((res) => res.data),
    staleTime: 60000,
  });

  // Effective site ID: user selection, or first available site
  const activeSiteId = selectedSiteId || (sites.length > 0 ? sites[0].id : '');

  // 2. Fetch executive dashboard data
  const {
    data: dashboard,
    isLoading: dashboardLoading,
    isError,
    error,
    refetch,
  } = useQuery<ExecutiveDashboardResponse>({
    queryKey: ['executive-dashboard', activeSiteId],
    queryFn: () =>
      activeSiteId
        ? executiveDashboardApi.getSiteDashboard(activeSiteId).then((res) => res.data)
        : executiveDashboardApi.getOverview().then((res) => res.data),
    enabled: true,
    staleTime: 15000,
  });

  // 3. Orchestration state & latest execution query
  const [isOrchModalOpen, setIsOrchModalOpen] = useState(false);
  const [orchMode, setOrchMode] = useState<OrchestrationMode>('FULL_ANALYSIS');
  const [selectedDomainAgents, setSelectedDomainAgents] = useState<string[]>([
    'site_risk',
    'safety',
    'compliance',
    'insurance',
  ]);
  const [generateReport, setGenerateReport] = useState<boolean>(true);
  const [activeRunResult, setActiveRunResult] = useState<OrchestrationRunResponse | null>(null);

  const { data: latestOrchestration, refetch: refetchLatestOrch } = useQuery<OrchestrationRunResponse>({
    queryKey: ['orchestration-latest', activeSiteId],
    queryFn: () => orchestrationApi.getLatest(activeSiteId).then((res) => res.data),
    enabled: !!activeSiteId,
    staleTime: 10000,
  });

  // 4. Cross-agent Orchestration run mutation
  const orchestrationMutation = useMutation({
    mutationFn: () =>
      orchestrationApi.run({
        site_id: activeSiteId,
        mode: orchMode,
        agents: orchMode === 'TARGETED_ANALYSIS' ? selectedDomainAgents : undefined,
        generate_report: generateReport,
        report_type: 'EXECUTIVE_SUMMARY',
        is_simulation: true,
      }),
    onMutate: () => {
      toast.loading('Dispatching cross-agent orchestration pipeline across domain agents...', {
        id: 'orch-run-toast',
      });
    },
    onSuccess: (res) => {
      const runData: OrchestrationRunResponse = res.data;
      setActiveRunResult(runData);
      if (runData.status === 'COMPLETED') {
        toast.success(`Orchestration completed successfully in ${runData.duration_ms}ms!`, { id: 'orch-run-toast' });
      } else if (runData.status === 'PARTIAL') {
        toast('Orchestration completed with partial agent warnings.', { id: 'orch-run-toast', icon: '⚠️' });
      } else {
        toast.error(`Orchestration failed: ${runData.errors?.[0] || 'Unknown error'}`, { id: 'orch-run-toast' });
      }
      queryClient.invalidateQueries({ queryKey: ['executive-dashboard', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['orchestration-latest', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-intelligence', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Agent orchestration failed', { id: 'orch-run-toast' });
    },
  });

  // Backward-compatible fallback reanalyze
  const reanalyzeMutation = useMutation({
    mutationFn: () =>
      riskIntelligenceApi.analyze({
        site_id: activeSiteId,
        analysis_window_days: 30,
        include_predictions: true,
        include_patterns: true,
        include_recommendations: true,
      }),
    onMutate: () => {
      toast.loading('Synthesizing cross-agent signals across Site, Safety, Compliance, and Insurance...', {
        id: 'exec-reanalyze-toast',
      });
    },
    onSuccess: () => {
      toast.success('Cross-agent intelligence analysis complete!', { id: 'exec-reanalyze-toast' });
      queryClient.invalidateQueries({ queryKey: ['executive-dashboard', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-intelligence', activeSiteId] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Analysis synthesis failed', { id: 'exec-reanalyze-toast' });
    },
  });

  if (sitesLoading || (dashboardLoading && !dashboard) || (dashboard && dashboard.site && dashboard.site.site_id !== activeSiteId && dashboardLoading)) {
    return <PageLoader />;
  }

  if (isError || !dashboard) {
    return (
      <div className="p-6">
        <EmptyState
          icon={<ShieldAlert size={36} className="text-red-400" />}
          title="Executive Dashboard Unavailable"
          description={
            (error as any)?.response?.data?.detail ||
            'Unable to load consolidated executive risk intelligence. Ensure at least one site is registered.'
          }
          action={
            <button className="btn-primary" onClick={() => refetch()}>
              <RefreshCw size={14} /> Retry Consolidation
            </button>
          }
        />
      </div>
    );
  }

  const {
    site,
    assessment,
    health,
    pillar_scores,
    critical_findings,
    recurring_patterns,
    potential_incidents,
    recommendations,
    safety_summary,
    compliance_summary,
    insurance_summary,
    recent_reports,
    history,
    last_analysis_time,
    data_freshness,
  } = dashboard;

  const overallScore = assessment.overall_risk_score;
  const overallColor = getRiskColor(overallScore);
  const overallCategory = (assessment.overall_risk_level || getRiskCategory(overallScore)).toUpperCase();

  // Helper for health status pill
  const getHealthBadge = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return <span className="badge badge-green"><CheckCircle2 size={12} /> Healthy Operations</span>;
      case 'MODERATE_RISK':
        return <span className="badge badge-yellow"><AlertTriangle size={12} /> Moderate Risk</span>;
      case 'ELEVATED':
        return <span className="badge badge-yellow"><AlertTriangle size={12} /> Elevated Exposure</span>;
      case 'CRITICAL_ACTION_REQUIRED':
      default:
        return <span className="badge badge-red animate-pulse"><AlertOctagon size={12} /> Critical Action Required</span>;
    }
  };

  // Helper for agent badge in critical findings
  const getAgentBadge = (agent: string) => {
    switch (agent.toLowerCase()) {
      case 'site_risk':
        return <span className="badge bg-blue-500/20 text-blue-300 border border-blue-500/30">Site Risk</span>;
      case 'safety':
        return <span className="badge bg-amber-500/20 text-amber-300 border border-amber-500/30">Safety Agent</span>;
      case 'compliance':
        return <span className="badge bg-purple-500/20 text-purple-300 border border-purple-500/30">Compliance</span>;
      default:
        return <span className="badge bg-slate-700 text-slate-300">{agent}</span>;
    }
  };

  // Filter critical findings
  const filteredFindings = critical_findings.filter((f) => {
    if (criticalFindingFilter === 'ALL') return true;
    return f.source_agent.toLowerCase() === criticalFindingFilter.toLowerCase();
  });

  // Filter recommendations by horizon
  const filteredRecommendations = recommendations.filter((rec) => {
    if (recommendationHorizon === 'all') return true;
    if (recommendationHorizon === 'immediate') return rec.timeframe.toLowerCase().includes('24') || rec.timeframe.toLowerCase().includes('immediate');
    if (recommendationHorizon === 'short_term') return rec.timeframe.toLowerCase().includes('7') || rec.timeframe.toLowerCase().includes('short');
    if (recommendationHorizon === 'strategic') return rec.timeframe.toLowerCase().includes('30') || rec.timeframe.toLowerCase().includes('strategic');
    return true;
  });

  // Pillar scores extraction
  const getScoreData = (key: string) => {
    const raw = pillar_scores[key];
    if (typeof raw === 'object' && raw !== null) {
      return {
        score: Number(raw.score ?? 0),
        level: String(raw.level ?? 'LOW'),
        weight: Number(raw.weight_pct ?? 25),
        contribution: Number(raw.contribution_pct ?? 25),
      };
    }
    const scoreVal = Number(pillar_scores[`${key}_score`] ?? 0);
    const weightVal = Number((pillar_scores.weights ?? {})[key] ?? 0.25) * 100;
    return {
      score: scoreVal,
      level: getRiskCategory(scoreVal).toUpperCase(),
      weight: weightVal,
      contribution: (scoreVal * (weightVal / 100)),
    };
  };

  const sitePillar = getScoreData('site_risk');
  const safetyPillar = getScoreData('safety_risk');
  const compliancePillar = getScoreData('compliance_risk');
  const insurancePillar = getScoreData('insurance_risk');

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 pb-12"
    >
      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION A: PROJECT OVERVIEW BANNER                                  */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="card p-6 bg-gradient-to-r from-surface-900 via-surface-900/90 to-surface-850 border border-slate-800 relative overflow-hidden">
        {/* Glow accent */}
        <div
          className="absolute -right-12 -top-12 w-64 h-64 rounded-full opacity-10 blur-3xl pointer-events-none"
          style={{ backgroundColor: overallColor }}
        />

        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
          {/* Site Title & Selector */}
          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="badge bg-primary-500/20 text-primary-300 border border-primary-500/30">
                Executive Risk Intelligence
              </span>
              {latestOrchestration && (
                <button
                  type="button"
                  onClick={() => {
                    setActiveRunResult(latestOrchestration);
                    setIsOrchModalOpen(true);
                  }}
                  className={clsx(
                    'badge border cursor-pointer transition-all hover:scale-105 flex items-center gap-1',
                    latestOrchestration.status === 'COMPLETED'
                      ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
                      : latestOrchestration.status === 'PARTIAL'
                      ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
                      : 'bg-red-500/10 text-red-300 border-red-500/30 hover:bg-red-500/20'
                  )}
                  title="Click to view latest multi-agent orchestration run breakdown"
                >
                  <Cpu size={11} />
                  <span>Orchestration: {latestOrchestration.status}</span>
                  <span className="opacity-75 text-[10px]">({latestOrchestration.duration_ms}ms)</span>
                </button>
              )}
              {getHealthBadge(health.health_status)}
              <span className="badge bg-slate-800 text-slate-400 border border-slate-700">
                <Clock size={11} className="mr-1" />
                Updated {formatRelativeTime(last_analysis_time)}
              </span>
            </div>

            <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 flex items-center gap-3">
              <span>{site.site_name}</span>
              <span className="text-xs font-mono font-normal text-slate-500 bg-surface-800 px-2 py-0.5 rounded border border-slate-700">
                {site.site_code || site.site_id.substring(0, 8).toUpperCase()}
              </span>
            </h1>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1.5">
                <MapPin size={13} className="text-slate-500" />
                {site.location || 'Metro Project Zone'}
              </span>
              <span>•</span>
              <span>Project: <strong className="text-slate-300">{site.project_name || 'Infrastructure Alpha'}</strong></span>
              <span>•</span>
              <span>Manager: <strong className="text-slate-300">{site.manager || 'Site Operations'}</strong></span>
            </div>
          </div>

          {/* Controls: Site Selector & Run Agent Orchestration */}
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-start lg:justify-end">
            <div className="flex items-center gap-2">
              <label htmlFor="site-select" className="text-xs text-slate-400 font-medium">
                Site:
              </label>
              <select
                id="site-select"
                value={activeSiteId}
                onChange={(e) => setSelectedSiteId(e.target.value)}
                className="input text-xs py-1.5 px-3 bg-surface-800 border-slate-700 text-slate-200 rounded-lg max-w-[200px]"
              >
                {sites.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setIsOrchModalOpen(true)}
              disabled={orchestrationMutation.isPending}
              className="btn-primary text-xs flex items-center gap-2 bg-gradient-to-r from-primary-600 via-indigo-600 to-primary-700 hover:from-primary-500 hover:to-indigo-500 text-white shadow-lg shadow-primary-500/25 border-primary-500/40"
              title="Launch Agent Orchestrator to coordinate domain agents, risk intelligence, and reporting"
            >
              <Cpu size={14} className={clsx(orchestrationMutation.isPending && 'animate-spin text-primary-200')} />
              <span>{orchestrationMutation.isPending ? 'Orchestrating Agents...' : 'Agent Orchestrator'}</span>
            </button>
          </div>
        </div>

        {/* Engine-computed Risk Gauge Summary Sub-bar */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-5">
            <RiskGauge
              score={overallScore}
              size={92}
              label={overallCategory}
              displayValue={overallScore % 1 !== 0 ? overallScore.toFixed(1) : overallScore}
            />
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                Unified Risk Index
              </div>
              <div className="text-2xl font-bold tracking-tight" style={{ color: overallColor }}>
                {overallScore % 1 !== 0 ? overallScore.toFixed(1) : overallScore}{' '}
                <span className="text-sm font-medium uppercase text-slate-400">/ 100</span>
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Deterministic 4-Pillar Model: <span className="font-semibold text-slate-200">{overallCategory} Risk Tier</span>
              </div>
            </div>
          </div>

          {assessment.scoring_explanation && (
            <div className="flex-1 max-w-xl text-xs text-slate-400 bg-surface-800/60 p-3 rounded-lg border border-slate-800">
              <span className="font-semibold text-slate-300 block mb-0.5">Engine Assessment:</span>
              <p className="line-clamp-2">{assessment.scoring_explanation}</p>
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION B: FOUR-PILLAR RISK BREAKDOWN CARDS                         */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Four-Pillar Risk Breakdown
            </h2>
            <p className="text-xs text-slate-500">
              Deterministic weights applied by Construction Risk Intelligence Engine
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {/* Pillar 1: Site Risk */}
          <div className="card-hover p-4 relative overflow-hidden">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Site Conditions</span>
                <div className="text-xl font-bold text-slate-100 mt-1">
                  {sitePillar.score.toFixed(1)}
                  <span className="text-xs text-slate-500 font-normal ml-1">/ 100</span>
                </div>
              </div>
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: `${getRiskColor(sitePillar.score)}20`, color: getRiskColor(sitePillar.score) }}
              >
                <MapPin size={16} />
              </div>
            </div>
            {/* Progress Bar */}
            <div className="w-full bg-surface-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, sitePillar.score)}%`, backgroundColor: getRiskColor(sitePillar.score) }}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
              <span>Weight: {sitePillar.weight.toFixed(0)}%</span>
              <span className="font-medium" style={{ color: getRiskColor(sitePillar.score) }}>
                {sitePillar.level}
              </span>
            </div>
            <Link
              to="/risk-monitoring"
              className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs text-primary-400 hover:text-primary-300 font-medium"
            >
              <span>Site Risk Agent</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          {/* Pillar 2: Safety Risk */}
          <div className="card-hover p-4 relative overflow-hidden">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Worker Safety</span>
                <div className="text-xl font-bold text-slate-100 mt-1">
                  {safetyPillar.score.toFixed(1)}
                  <span className="text-xs text-slate-500 font-normal ml-1">/ 100</span>
                </div>
              </div>
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: `${getRiskColor(safetyPillar.score)}20`, color: getRiskColor(safetyPillar.score) }}
              >
                <HardHat size={16} />
              </div>
            </div>
            <div className="w-full bg-surface-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, safetyPillar.score)}%`, backgroundColor: getRiskColor(safetyPillar.score) }}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
              <span>Weight: {safetyPillar.weight.toFixed(0)}%</span>
              <span className="font-medium" style={{ color: getRiskColor(safetyPillar.score) }}>
                {safetyPillar.level}
              </span>
            </div>
            <Link
              to="/safety"
              className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs text-primary-400 hover:text-primary-300 font-medium"
            >
              <span>Safety Agent</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          {/* Pillar 3: Compliance Risk */}
          <div className="card-hover p-4 relative overflow-hidden">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Regulatory Compliance</span>
                <div className="text-xl font-bold text-slate-100 mt-1">
                  {compliancePillar.score.toFixed(1)}
                  <span className="text-xs text-slate-500 font-normal ml-1">/ 100</span>
                </div>
              </div>
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: `${getRiskColor(compliancePillar.score)}20`, color: getRiskColor(compliancePillar.score) }}
              >
                <ClipboardCheck size={16} />
              </div>
            </div>
            <div className="w-full bg-surface-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, compliancePillar.score)}%`, backgroundColor: getRiskColor(compliancePillar.score) }}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
              <span>Weight: {compliancePillar.weight.toFixed(0)}%</span>
              <span className="font-medium" style={{ color: getRiskColor(compliancePillar.score) }}>
                {compliancePillar.level}
              </span>
            </div>
            <Link
              to="/compliance"
              className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs text-primary-400 hover:text-primary-300 font-medium"
            >
              <span>Compliance Agent</span>
              <ArrowRight size={12} />
            </Link>
          </div>

          {/* Pillar 4: Insurance Risk */}
          <div className="card-hover p-4 relative overflow-hidden">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase">Insurance Underwriting</span>
                <div className="text-xl font-bold text-slate-100 mt-1">
                  {insurancePillar.score.toFixed(1)}
                  <span className="text-xs text-slate-500 font-normal ml-1">/ 100</span>
                </div>
              </div>
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: `${getRiskColor(insurancePillar.score)}20`, color: getRiskColor(insurancePillar.score) }}
              >
                <Shield size={16} />
              </div>
            </div>
            <div className="w-full bg-surface-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, insurancePillar.score)}%`, backgroundColor: getRiskColor(insurancePillar.score) }}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
              <span>Weight: {insurancePillar.weight.toFixed(0)}%</span>
              <span className="font-medium" style={{ color: getRiskColor(insurancePillar.score) }}>
                {insurancePillar.level}
              </span>
            </div>
            <Link
              to="/insurance"
              className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs text-primary-400 hover:text-primary-300 font-medium"
            >
              <span>Insurance Agent</span>
              <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION C: PROJECT HEALTH KPIS                                      */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KPICard
          title="Active Findings"
          value={health.total_active_findings}
          subtitle="Across all agents"
          icon={<AlertTriangle size={16} />}
          accent="from-amber-500/10"
        />
        <KPICard
          title="Critical Issues"
          value={health.critical_findings_count}
          subtitle="Immediate hazard"
          icon={<AlertOctagon size={16} />}
          accent={health.critical_findings_count > 0 ? "from-red-500/20" : "from-green-500/10"}
          riskScore={health.critical_findings_count > 0 ? 80 : 10}
        />
        <KPICard
          title="Safety Alerts"
          value={health.active_safety_alerts_count}
          subtitle="Real-time triggers"
          icon={<HardHat size={16} />}
          accent="from-amber-500/10"
        />
        <KPICard
          title="Compliance Breaches"
          value={health.compliance_violations_count}
          subtitle="Rule violations"
          icon={<ClipboardCheck size={16} />}
          accent="from-purple-500/10"
        />
        <KPICard
          title="Overdue Inspections"
          value={health.overdue_inspections_count}
          subtitle="Statutory requirement"
          icon={<Activity size={16} />}
          accent={health.overdue_inspections_count > 0 ? "from-red-500/15" : "from-slate-700/10"}
        />
        <KPICard
          title="Exposure Index"
          value={`${health.insurance_exposure_index.toFixed(2)}x`}
          subtitle="Baseline premium mult."
          icon={<Shield size={16} />}
          accent="from-blue-500/10"
        />
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION D: PRIORITIZED CRITICAL ISSUES FEED                         */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <AlertTriangle size={18} className="text-amber-400" />
              Prioritized Critical Issues Feed
            </h2>
            <p className="text-xs text-slate-400">
              Cross-agent findings ordered deterministically by risk severity
            </p>
          </div>

          {/* Filter tabs */}
          <div className="flex items-center gap-1.5 bg-surface-800 p-1 rounded-lg border border-slate-700/80 text-xs">
            {(['ALL', 'site_risk', 'safety', 'compliance'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setCriticalFindingFilter(tab)}
                className={clsx(
                  'px-2.5 py-1 rounded-md transition-colors capitalize font-medium',
                  criticalFindingFilter === tab
                    ? 'bg-surface-700 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                {tab === 'ALL' ? 'All Sources' : tab.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {filteredFindings.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs">
            <CheckCircle2 size={24} className="mx-auto mb-2 text-emerald-400 opacity-60" />
            No open critical findings detected for the selected filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider font-semibold">
                  <th className="py-2.5 px-3">Finding ID</th>
                  <th className="py-2.5 px-3">Source Agent</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Issue Description</th>
                  <th className="py-2.5 px-3">Mitigation Recommendation</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredFindings.map((finding) => (
                  <tr key={finding.id} className="hover:bg-surface-800/40 transition-colors">
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-300 font-medium whitespace-nowrap">
                      {finding.finding_id}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      {getAgentBadge(finding.source_agent)}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span
                        className={clsx(
                          'badge text-[10px]',
                          finding.severity === 'CRITICAL' && 'badge-red',
                          finding.severity === 'HIGH' && 'badge-yellow',
                          finding.severity === 'MEDIUM' && 'bg-slate-800 text-slate-300'
                        )}
                      >
                        {finding.severity}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold tabular-nums" style={{ color: getRiskColor(finding.risk_score) }}>
                      {finding.risk_score.toFixed(0)}
                    </td>
                    <td className="py-3 px-3 max-w-xs">
                      <div className="font-medium text-slate-200 truncate">{finding.title}</div>
                      <div className="text-slate-400 text-[11px] line-clamp-1">{finding.description}</div>
                    </td>
                    <td className="py-3 px-3 max-w-xs text-slate-300 text-[11px]">
                      {finding.evidence ? (
                        <span className="line-clamp-1">{finding.evidence}</span>
                      ) : (
                        <span className="text-slate-500 italic">Immediate supervisor inspection</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      <Link
                        to={finding.navigation_url}
                        className="btn-ghost text-xs px-2 py-1 text-primary-400 hover:text-primary-300 inline-flex items-center gap-1"
                      >
                        <span>View</span>
                        <ChevronRight size={12} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION E & F: PATTERNS & POTENTIAL INCIDENTS GRID                  */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SECTION E: RECURRING PATTERNS */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Layers size={18} className="text-blue-400" />
                Detected Recurring Risk Patterns
              </h2>
              <p className="text-xs text-slate-400">
                Cross-agent temporal clusters identified across surveillance & logs
              </p>
            </div>
            <span className="badge bg-blue-500/10 text-blue-300 border border-blue-500/20 text-xs">
              {recurring_patterns.length} Active
            </span>
          </div>

          {recurring_patterns.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              <CheckCircle2 size={24} className="mx-auto mb-2 text-slate-600" />
              No recurring hazard patterns detected in the current analysis window.
            </div>
          ) : (
            <div className="space-y-3">
              {recurring_patterns.slice(0, 4).map((p, idx) => (
                <div key={p.pattern_id || idx} className="p-3 bg-surface-800/60 rounded-lg border border-slate-800">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="font-semibold text-xs text-slate-200">
                      {p.pattern_description || 'Persistent Environmental/Safety Pattern'}
                    </span>
                    <span className={clsx('badge text-[10px]', p.severity === 'HIGH' ? 'badge-red' : 'badge-yellow')}>
                      {p.velocity || 'STEADY'}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 line-clamp-2 mb-2">
                    Observed {p.occurrence_count} times over {Math.round((p.time_window_hours || 720) / 24)} days.
                    {p.locations && p.locations.length > 0 && ` Affecting: ${p.locations.join(', ')}.`}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                    <span>Pattern ID: {p.pattern_id}</span>
                    <span>Category: {p.category}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SECTION F: POTENTIAL INCIDENTS (EARLY WARNING) */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Zap size={18} className="text-amber-400" />
                Incident Predictions & Early Warnings
              </h2>
              <p className="text-xs text-slate-400">
                Deterministic leading indicator causal analysis (Risk Intelligence Engine)
              </p>
            </div>
            <span className="badge bg-amber-500/10 text-amber-300 border border-amber-500/20 text-xs">
              Early Warning
            </span>
          </div>

          {potential_incidents.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              <ShieldCheck size={24} className="mx-auto mb-2 text-slate-600" />
              No high-probability incident pathways detected at this time.
            </div>
          ) : (
            <div className="space-y-3">
              {potential_incidents.slice(0, 4).map((inc, idx) => (
                <div key={inc.prediction_id || idx} className="p-3 bg-surface-800/60 rounded-lg border border-slate-800">
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div>
                      <div className="font-semibold text-xs text-slate-200">{inc.incident_type}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Timeframe: <strong className="text-slate-300">{inc.predicted_timeframe}</strong>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold text-amber-400">
                        {Math.round((inc.probability_score || 0) * 100)}% Probability
                      </div>
                      <span className="badge badge-yellow text-[9px] mt-0.5">
                        {inc.severity_potential} POTENTIAL
                      </span>
                    </div>
                  </div>

                  {/* Leading indicators */}
                  {inc.leading_indicators && inc.leading_indicators.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                      <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1">
                        Leading Indicators:
                      </span>
                      <ul className="list-disc list-inside space-y-0.5">
                        {inc.leading_indicators.slice(0, 2).map((ind, i) => (
                          <li key={i} className="line-clamp-1">
                            {ind.indicator} ({ind.observed_value})
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION G: OPERATIONAL RECOMMENDATIONS (3 HORIZONS)                 */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Sparkles size={18} className="text-primary-400" />
              Prioritized Operational Recommendations
            </h2>
            <p className="text-xs text-slate-400">
              Prescriptive interventions partitioned across 3 operational horizons
            </p>
          </div>

          {/* Horizon tabs */}
          <div className="flex items-center gap-1.5 bg-surface-800 p-1 rounded-lg border border-slate-700/80 text-xs">
            {[
              { id: 'all', label: 'All Horizons' },
              { id: 'immediate', label: '0-24h Immediate' },
              { id: 'short_term', label: '1-7d Short-Term' },
              { id: 'strategic', label: '7-30d Strategic' },
            ].map((h) => (
              <button
                key={h.id}
                onClick={() => setRecommendationHorizon(h.id as any)}
                className={clsx(
                  'px-2.5 py-1 rounded-md transition-colors font-medium',
                  recommendationHorizon === h.id
                    ? 'bg-surface-700 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                {h.label}
              </button>
            ))}
          </div>
        </div>

        {filteredRecommendations.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            <CheckCircle2 size={24} className="mx-auto mb-2 text-slate-600" />
            No specific recommendations generated for this horizon.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRecommendations.map((rec, idx) => (
              <div
                key={rec.recommendation_id || idx}
                className="p-4 bg-surface-850/80 rounded-xl border border-slate-800 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span
                      className={clsx(
                        'badge text-[10px]',
                        rec.priority === 'HIGH' || rec.priority === 'CRITICAL' ? 'badge-red' : 'badge-blue'
                      )}
                    >
                      {rec.priority} PRIORITY
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">{rec.timeframe}</span>
                  </div>

                  <h3 className="font-semibold text-sm text-slate-100 mb-2">{rec.title}</h3>

                  {rec.action_items && rec.action_items.length > 0 && (
                    <ul className="space-y-1.5 mb-4">
                      {rec.action_items.map((item, i) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                          <span className="text-primary-400 font-bold mt-0.5">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Reduction: <strong className="text-emerald-400">{rec.expected_risk_reduction}</strong></span>
                  <span>Cost Impact: <strong className="text-slate-200">{rec.cost_impact_level}</strong></span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION H: DOMAIN SNAPSHOT TRIAD                                    */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Domain 1: Safety Snapshot */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-300 flex items-center justify-center">
                <HardHat size={16} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-100">Safety Snapshot</h3>
                <span className="text-[11px] text-slate-500">Worker Protection Subsystems</span>
              </div>
            </div>
            <Link to="/safety" className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
              <span>View</span>
              <ChevronRight size={12} />
            </Link>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Safety Score:</span>
              <strong className="text-slate-100">{safety_summary.safety_score.toFixed(1)} / 100</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">PPE Compliance Rate:</span>
              <strong className="text-emerald-400">{safety_summary.ppe_compliance_rate.toFixed(1)}%</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Active Workers Tracked:</span>
              <strong className="text-slate-200">{safety_summary.active_workers_count}</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Active Safety Alerts:</span>
              <strong className={safety_summary.active_alerts_count > 0 ? 'text-amber-400' : 'text-slate-200'}>
                {safety_summary.active_alerts_count}
              </strong>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Critical Observations:</span>
              <strong className={safety_summary.critical_findings_count > 0 ? 'text-red-400' : 'text-slate-200'}>
                {safety_summary.critical_findings_count}
              </strong>
            </div>
          </div>
        </div>

        {/* Domain 2: Compliance Snapshot */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-300 flex items-center justify-center">
                <ClipboardCheck size={16} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-100">Compliance Snapshot</h3>
                <span className="text-[11px] text-slate-500">Regulatory Intelligence</span>
              </div>
            </div>
            <Link to="/compliance" className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
              <span>View</span>
              <ChevronRight size={12} />
            </Link>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Compliance Score:</span>
              <strong className="text-slate-100">{compliance_summary.compliance_score.toFixed(1)}%</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Statutory Status:</span>
              <span className="badge badge-green text-[10px]">{compliance_summary.compliance_status}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Overdue Inspections:</span>
              <strong className={compliance_summary.overdue_inspections_count > 0 ? 'text-red-400' : 'text-slate-200'}>
                {compliance_summary.overdue_inspections_count}
              </strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Active Rule Violations:</span>
              <strong className="text-slate-200">{compliance_summary.active_violations_count}</strong>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Total Rules Evaluated:</span>
              <strong className="text-slate-200">{compliance_summary.total_rules_evaluated} Rules</strong>
            </div>
          </div>
        </div>

        {/* Domain 3: Insurance Snapshot */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-300 flex items-center justify-center">
                <Shield size={16} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-100">Insurance Snapshot</h3>
                <span className="text-[11px] text-slate-500">Underwriting & Actuarial</span>
              </div>
            </div>
            <Link to="/insurance" className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
              <span>View</span>
              <ChevronRight size={12} />
            </Link>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Underwriting Risk Score:</span>
              <strong className="text-slate-100">{insurance_summary.insurance_risk_score.toFixed(1)} / 100</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Exposure Multiplier:</span>
              <strong className="text-amber-400">{insurance_summary.exposure_index.toFixed(2)}x</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Est. Liability Exposure:</span>
              <strong className="text-slate-200">{insurance_summary.estimated_liability_exposure}</strong>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Unresolved Underwriting Items:</span>
              <strong className="text-slate-200">{insurance_summary.unresolved_findings_count}</strong>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Active Open Claims:</span>
              <strong className="text-slate-200">{insurance_summary.active_claims_count}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION I: RECENT GENERATED REPORTS                                 */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <FileText size={18} className="text-emerald-400" />
              Recent Generated Reports
            </h2>
            <p className="text-xs text-slate-400">
              Ingested directly from Reporting Agent
            </p>
          </div>
          <Link to="/reports" className="btn-secondary text-xs flex items-center gap-1.5">
            <span>View All Reports</span>
            <ExternalLink size={12} />
          </Link>
        </div>

        {recent_reports.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs">
            <FileText size={24} className="mx-auto mb-2 text-slate-600" />
            No generated reports found for this site yet. Generate one in the Reports portal.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {recent_reports.slice(0, 4).map((report) => (
              <div
                key={report.id}
                className="p-3.5 bg-surface-850 rounded-xl border border-slate-800 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-1 mb-2">
                    <span className="badge bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px]">
                      {report.report_type.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-500">{formatRelativeTime(report.generated_at)}</span>
                  </div>
                  <h4 className="font-medium text-xs text-slate-200 mb-1 line-clamp-1">{report.title}</h4>
                  <p className="text-[11px] text-slate-400 line-clamp-2">
                    {report.summary || 'Comprehensive multi-source platform documentation.'}
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-[10px] font-mono text-slate-500">{report.report_id}</span>
                  <Link
                    to={`/reports?report_id=${report.report_id}`}
                    className="text-primary-400 hover:text-primary-300 font-medium inline-flex items-center gap-1 text-[11px]"
                  >
                    <span>Read</span>
                    <ArrowRight size={11} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* SECTION J: RISK TREND / HISTORY VISUALIZER                          */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <TrendingUp size={18} className="text-primary-400" />
              Risk Trend & Historical Evolution
            </h2>
            <p className="text-xs text-slate-400">
              Deterministic 4-pillar risk trajectories over time
            </p>
          </div>
        </div>

        {history.length < 2 ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            <Activity size={24} className="mx-auto mb-2 text-slate-600" />
            Insufficient historical risk assessments. New datapoints will automatically populate this trendline.
          </div>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={[...history].reverse()} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorOverall" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorSite" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis
                  dataKey="generated_at"
                  stroke="#64748b"
                  fontSize={11}
                  tickFormatter={(val) => (val ? formatDate(val).substring(0, 6) : '')}
                />
                <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Critical (70)', fill: '#ef4444', fontSize: 10 }} />
                <ReferenceLine y={40} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Elevated (40)', fill: '#f59e0b', fontSize: 10 }} />
                <Area
                  type="monotone"
                  dataKey="overall_risk_score"
                  name="Overall Risk"
                  stroke="#ef4444"
                  fillOpacity={1}
                  fill="url(#colorOverall)"
                  strokeWidth={2}
                />
                <Line type="monotone" dataKey="site_risk" name="Site Risk" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="safety_risk" name="Safety Risk" stroke="#f59e0b" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="compliance_risk" name="Compliance Risk" stroke="#a855f7" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="insurance_risk" name="Insurance Risk" stroke="#06b6d4" strokeWidth={1.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* AGENT ORCHESTRATION CENTER MODAL (Phase 4.4)                        */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {isOrchModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-surface-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl p-6 shadow-2xl relative space-y-6 my-8 max-h-[90vh] overflow-y-auto"
            >
              {/* Modal Header */}
              <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-primary-500/20">
                    <Cpu size={22} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                      Agent Orchestration Center
                      <span className="text-[11px] font-normal px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-300 border border-primary-500/20">
                        Enterprise Orchestration
                      </span>
                    </h2>
                    <p className="text-xs text-slate-400">
                      Coordinated execution across Level 1 Domain Agents, Level 2 Risk Intelligence Engine, and Level 3 Reporting Agent
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setIsOrchModalOpen(false)}
                  className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Execution Controls & Mode Selection */}
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
                    Execution Mode
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
                    {[
                      {
                        mode: 'FULL_ANALYSIS' as OrchestrationMode,
                        title: 'Full Pipeline',
                        desc: 'Domain Agents → Risk Engine → Reporting',
                        badge: 'Recommended',
                      },
                      {
                        mode: 'TARGETED_ANALYSIS' as OrchestrationMode,
                        title: 'Targeted Analysis',
                        desc: 'Execute selected domain agents only',
                        badge: 'Custom',
                      },
                      {
                        mode: 'REFRESH' as OrchestrationMode,
                        title: 'Engine Refresh',
                        desc: 'Re-synthesize signals without domain run',
                        badge: 'Fast',
                      },
                      {
                        mode: 'REPORT_REFRESH' as OrchestrationMode,
                        title: 'Report Refresh',
                        desc: 'Generate fresh audit documentation',
                        badge: 'Reports',
                      },
                    ].map((item) => (
                      <button
                        key={item.mode}
                        type="button"
                        onClick={() => setOrchMode(item.mode)}
                        className={clsx(
                          'p-3 rounded-xl border text-left transition-all',
                          orchMode === item.mode
                            ? 'bg-primary-500/10 border-primary-500/60 ring-1 ring-primary-500/40 text-slate-100 shadow-md'
                            : 'bg-surface-850/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                        )}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-slate-200">{item.title}</span>
                          <span className={clsx(
                            'text-[10px] px-1.5 py-0.5 rounded font-medium',
                            orchMode === item.mode ? 'bg-primary-500/20 text-primary-300' : 'bg-slate-800 text-slate-500'
                          )}>
                            {item.badge}
                          </span>
                        </div>
                        <p className="text-[11px] leading-tight opacity-80">{item.desc}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Targeted Domain Agents Checkboxes */}
                {orchMode === 'TARGETED_ANALYSIS' && (
                  <div className="p-3.5 bg-surface-850 border border-slate-800 rounded-xl space-y-2.5">
                    <span className="text-xs font-semibold text-slate-300">Select Domain Agents to Execute:</span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {[
                        { id: 'site_risk', label: 'Site Risk Agent', icon: '🛰️' },
                        { id: 'safety', label: 'Safety Agent', icon: '🦺' },
                        { id: 'compliance', label: 'Compliance Agent', icon: '📋' },
                        { id: 'insurance', label: 'Insurance Agent', icon: '🛡️' },
                      ].map((ag) => {
                        const isChecked = selectedDomainAgents.includes(ag.id);
                        return (
                          <label
                            key={ag.id}
                            className={clsx(
                              'flex items-center gap-2 p-2 rounded-lg border text-xs cursor-pointer select-none transition-colors',
                              isChecked
                                ? 'bg-primary-500/15 border-primary-500/50 text-slate-200'
                                : 'bg-surface-800 border-slate-700/60 text-slate-400 hover:bg-surface-750'
                            )}
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedDomainAgents([...selectedDomainAgents, ag.id]);
                                } else {
                                  setSelectedDomainAgents(selectedDomainAgents.filter((a) => a !== ag.id));
                                }
                              }}
                              className="rounded border-slate-700 text-primary-600 focus:ring-0"
                            />
                            <span>{ag.icon}</span>
                            <span className="font-medium truncate">{ag.label}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Additional Options & Execution Button */}
                <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
                  <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={generateReport}
                      onChange={(e) => setGenerateReport(e.target.checked)}
                      className="rounded border-slate-700 text-primary-600 focus:ring-0"
                    />
                    <span>Automatically trigger <strong>Reporting Agent</strong> (Audit-Ready Executive Summary)</span>
                  </label>

                  <button
                    type="button"
                    onClick={() => orchestrationMutation.mutate()}
                    disabled={orchestrationMutation.isPending || (orchMode === 'TARGETED_ANALYSIS' && selectedDomainAgents.length === 0)}
                    className="btn-primary text-xs px-5 py-2.5 flex items-center gap-2 bg-gradient-to-r from-primary-600 via-indigo-600 to-primary-700 hover:from-primary-500 hover:to-indigo-500 shadow-lg shadow-primary-500/25 disabled:opacity-50"
                  >
                    {orchestrationMutation.isPending ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        <span>Orchestrating Workflow...</span>
                      </>
                    ) : (
                      <>
                        <Play size={14} className="fill-current" />
                        <span>Execute Pipeline Now</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Live Pipeline Visualizer / Run Status */}
              {(activeRunResult || latestOrchestration) && (
                <div className="space-y-4 pt-4 border-t border-slate-800">
                  {(() => {
                    const run = activeRunResult || latestOrchestration!;
                    return (
                      <div className="space-y-4">
                        {/* Run Status Banner */}
                        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-surface-850 border border-slate-800 text-xs">
                          <div className="flex items-center gap-2.5">
                            <span className="font-mono text-slate-400 font-semibold">{run.execution_id}</span>
                            <span
                              className={clsx(
                                'badge font-bold uppercase text-[10px]',
                                run.status === 'COMPLETED'
                                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                  : run.status === 'PARTIAL'
                                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                  : 'bg-red-500/20 text-red-300 border border-red-500/30'
                              )}
                            >
                              {run.status}
                            </span>
                            <span className="text-slate-400">Mode: <strong>{run.execution_mode}</strong></span>
                          </div>

                          <div className="flex items-center gap-3 text-slate-400">
                            <span>Duration: <strong className="text-slate-200">{run.duration_ms} ms</strong></span>
                            <span>•</span>
                            <span>Started: <strong className="text-slate-200">{formatRelativeTime(run.started_at)}</strong></span>
                          </div>
                        </div>

                        {/* Pipeline Stages Breakdown */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {/* Stage 1: Domain Agents */}
                          <div className="p-3.5 bg-surface-850/80 border border-slate-800 rounded-xl space-y-2.5">
                            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                <span className="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-mono">1</span>
                                Domain Agents
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">Parallel</span>
                            </div>

                            <div className="space-y-1.5">
                              {['site_risk', 'safety', 'compliance', 'insurance'].map((name) => {
                                const st = run.agent_statuses?.[name];
                                if (!st) return null;
                                return (
                                  <div
                                    key={name}
                                    className="p-2 bg-surface-800/90 border border-slate-700/60 rounded-lg text-xs space-y-1"
                                  >
                                    <div className="flex items-center justify-between">
                                      <span className="font-semibold text-slate-200 capitalize">
                                        {name.replace('_', ' ')}
                                      </span>
                                      <span
                                        className={clsx(
                                          'text-[10px] px-1.5 py-0.5 rounded font-bold uppercase',
                                          st.status === 'COMPLETED'
                                            ? 'bg-emerald-500/15 text-emerald-300'
                                            : st.status === 'RUNNING'
                                            ? 'bg-blue-500/15 text-blue-300'
                                            : st.status === 'FAILED'
                                            ? 'bg-red-500/15 text-red-300'
                                            : 'bg-slate-700 text-slate-400'
                                        )}
                                      >
                                        {st.status} ({st.duration_ms}ms)
                                      </span>
                                    </div>
                                    {st.message && (
                                      <p className="text-[11px] text-slate-400 leading-tight truncate" title={st.message}>
                                        {st.message}
                                      </p>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                          {/* Stage 2: Risk Intelligence Engine */}
                          <div className="p-3.5 bg-surface-850/80 border border-slate-800 rounded-xl space-y-2.5">
                            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                <span className="w-4 h-4 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-[10px] font-mono">2</span>
                                Risk Intelligence
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">Synthesis</span>
                            </div>

                            {run.agent_statuses?.['risk_intelligence'] ? (
                              <div className="p-2.5 bg-surface-800/90 border border-slate-700/60 rounded-lg text-xs space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold text-slate-200">Synthesis Engine</span>
                                  <span
                                    className={clsx(
                                      'text-[10px] px-1.5 py-0.5 rounded font-bold uppercase',
                                      run.agent_statuses['risk_intelligence'].status === 'COMPLETED'
                                        ? 'bg-emerald-500/15 text-emerald-300'
                                        : 'bg-slate-700 text-slate-400'
                                    )}
                                  >
                                    {run.agent_statuses['risk_intelligence'].status}
                                  </span>
                                </div>
                                {run.risk_intelligence_id && (
                                  <div className="text-[11px] font-mono text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20 truncate">
                                    ID: {run.risk_intelligence_id}
                                  </div>
                                )}
                                {run.agent_statuses['risk_intelligence'].message && (
                                  <p className="text-[11px] text-slate-400 leading-tight">
                                    {run.agent_statuses['risk_intelligence'].message}
                                  </p>
                                )}
                              </div>
                            ) : (
                              <div className="p-4 text-center text-slate-500 text-xs">
                                Stage not scheduled in this mode
                              </div>
                            )}
                          </div>

                          {/* Stage 3: Reporting Intelligence */}
                          <div className="p-3.5 bg-surface-850/80 border border-slate-800 rounded-xl space-y-2.5">
                            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-mono">3</span>
                                Reporting Agent
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">Audit Doc</span>
                            </div>

                            {run.agent_statuses?.['reporting'] ? (
                              <div className="p-2.5 bg-surface-800/90 border border-slate-700/60 rounded-lg text-xs space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold text-slate-200">Executive Summary</span>
                                  <span
                                    className={clsx(
                                      'text-[10px] px-1.5 py-0.5 rounded font-bold uppercase',
                                      run.agent_statuses['reporting'].status === 'COMPLETED'
                                        ? 'bg-emerald-500/15 text-emerald-300'
                                        : 'bg-slate-700 text-slate-400'
                                    )}
                                  >
                                    {run.agent_statuses['reporting'].status}
                                  </span>
                                </div>
                                {run.report_id && (
                                  <div className="flex items-center justify-between">
                                    <span className="text-[11px] font-mono text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 truncate">
                                      ID: {run.report_id}
                                    </span>
                                    <Link
                                      to="/reports"
                                      onClick={() => setIsOrchModalOpen(false)}
                                      className="text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1"
                                    >
                                      View <ExternalLink size={10} />
                                    </Link>
                                  </div>
                                )}
                                {run.agent_statuses['reporting'].message && (
                                  <p className="text-[11px] text-slate-400 leading-tight">
                                    {run.agent_statuses['reporting'].message}
                                  </p>
                                )}
                              </div>
                            ) : (
                              <div className="p-4 text-center text-slate-500 text-xs">
                                Reporting was not requested
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Partial Success Warnings / Errors alert if present */}
                        {run.warnings && run.warnings.length > 0 && (
                          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300 space-y-1">
                            <div className="font-semibold flex items-center gap-1.5">
                              <AlertTriangle size={14} /> Pipeline Warnings:
                            </div>
                            <ul className="list-disc list-inside space-y-0.5 text-amber-200/90 text-[11px]">
                              {run.warnings.map((w, idx) => (
                                <li key={idx}>{w}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
