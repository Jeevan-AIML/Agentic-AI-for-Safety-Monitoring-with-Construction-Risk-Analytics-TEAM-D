import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, ShieldAlert, Filter, AlertTriangle, RefreshCw, Play,
  CheckCircle2, Info, ChevronRight, TrendingUp, Cpu, Sparkles,
  ArrowRight, ShieldCheck, MapPin, Eye
} from 'lucide-react';
import { hazardsApi, sitesApi, riskIntelApi } from '@/services/api';
import { EmptyState, Modal, PageLoader, RiskGauge, HazardDetailModal } from '@/components/common';
import RiskIntelligencePanel from './RiskIntelligencePanel';
import {
  HAZARD_STATUS_BADGE, HAZARD_STATUS_LABEL, HAZARD_TYPE_LABEL,
  RISK_BADGE_MAP, RISK_LABEL_MAP, formatRelativeTime, formatDate
} from '@/utils/display';
import { getRiskColor, calculateRiskScore, getRiskCategory } from '@/utils/riskScoring';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, AreaChart, Area
} from 'recharts';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { Hazard, Site, RiskScore, RiskCategory } from '@/types';

const schema = z.object({
  site_id: z.string().min(1, 'Select a site'),
  hazard_type: z.string().min(1, 'Select type'),
  description: z.string().min(5, 'Required'),
  severity: z.string(),
  probability: z.string(),
  reported_by: z.string().optional(),
  recommended_action: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

const HAZARD_TYPES = [
  'environmental', 'equipment', 'structural', 'electrical',
  'fire', 'fall', 'excavation', 'material_handling', 'other'
];

export default function RiskMonitoringPage() {
  const queryClient = useQueryClient();
  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [addOpen, setAddOpen] = useState(false);
  const [selectedHazard, setSelectedHazard] = useState<Hazard | null>(null);
  const [hazardModalOpen, setHazardModalOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [viewMode, setViewMode] = useState<'risk_intelligence' | 'site_monitoring'>('risk_intelligence');

  // Sites list
  const { data: sites } = useQuery({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  // Effective site ID: default to first site if none selected
  const activeSiteId = useMemo(() => {
    if (selectedSiteId) return selectedSiteId;
    if (sites && sites.length > 0) return sites[0].id;
    return '';
  }, [selectedSiteId, sites]);

  const activeSite = useMemo(() => {
    return sites?.find((s: Site) => s.id === activeSiteId);
  }, [sites, activeSiteId]);

  // Hazards query
  const { data: hazards, isLoading: hazardsLoading } = useQuery({
    queryKey: ['hazards', activeSiteId, statusFilter],
    queryFn: () =>
      hazardsApi.list(activeSiteId || undefined, statusFilter || undefined).then(r => r.data),
    refetchInterval: 30000,
  });

  // Risk summary query
  const { data: riskSummary, isLoading: summaryLoading } = useQuery({
    queryKey: ['risk-summary', activeSiteId],
    queryFn: () => riskIntelApi.getSiteRiskSummary(activeSiteId).then(r => r.data),
    enabled: !!activeSiteId,
  });

  // Risk history query for trend chart
  const { data: riskHistory } = useQuery({
    queryKey: ['risk-history', activeSiteId],
    queryFn: () => riskIntelApi.getSiteRiskHistory(activeSiteId, 30).then(r => r.data),
    enabled: !!activeSiteId,
  });

  // Demo scenarios catalog
  const { data: demoScenarios } = useQuery({
    queryKey: ['demo-scenarios'],
    queryFn: () => riskIntelApi.listDemoScenarios().then(r => r.data),
  });

  // Manual Hazard creation
  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { severity: '3', probability: '3' },
  });

  const severityVal = parseInt(watch('severity') || '3');
  const probabilityVal = parseInt(watch('probability') || '3');
  const previewScore = calculateRiskScore(probabilityVal, severityVal);
  const previewColor = getRiskColor(previewScore);
  const previewLabel = getRiskCategory(previewScore).toUpperCase();

  const createMutation = useMutation({
    mutationFn: (data: any) => hazardsApi.create(data),
    onSuccess: () => {
      toast.success('Hazard recorded');
      queryClient.invalidateQueries({ queryKey: ['hazards'] });
      reset();
      setAddOpen(false);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to add hazard'),
  });

  // Analyze Site Mutation (Step 14 & 15)
  const analyzeMutation = useMutation({
    mutationFn: () => riskIntelApi.analyzeSite({ site_id: activeSiteId }),
    onMutate: () => {
      setIsAnalyzing(true);
      toast.loading('Analyzing site conditions...', { id: 'risk-agent-toast' });
    },
    onSuccess: () => {
      setIsAnalyzing(false);
      toast.success('Risk analysis completed.', { id: 'risk-agent-toast' });
      queryClient.invalidateQueries({ queryKey: ['risk-summary', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['hazards'] });
      queryClient.invalidateQueries({ queryKey: ['risk-history', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['sites'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: (err: any) => {
      setIsAnalyzing(false);
      toast.error(err.response?.data?.detail || 'Analysis failed', { id: 'risk-agent-toast' });
    },
  });

  // Demo Scenario Mutation (Step 20)
  const demoMutation = useMutation({
    mutationFn: (scenarioId: number) => riskIntelApi.runDemoScenario(activeSiteId, scenarioId),
    onMutate: () => {
      toast.loading('Executing deterministic scenario...', { id: 'demo-toast' });
    },
    onSuccess: () => {
      toast.success('Demo scenario executed.', { id: 'demo-toast' });
      queryClient.invalidateQueries({ queryKey: ['risk-summary', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['hazards'] });
      queryClient.invalidateQueries({ queryKey: ['risk-history', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['sites'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Scenario failed', { id: 'demo-toast' });
    },
  });

  const onSubmit = (data: FormData) => {
    createMutation.mutate({
      ...data,
      severity: parseInt(data.severity),
      probability: parseInt(data.probability),
    });
  };

  const latestScore: RiskScore | undefined = riskSummary?.latest_score;
  const overallRiskScore = riskSummary?.current_risk_score ?? activeSite?.current_risk_score ?? 0;
  const riskCategory: RiskCategory = (riskSummary?.risk_category ?? activeSite?.risk_category ?? 'low') as RiskCategory;
  const overallColor = getRiskColor(overallRiskScore);

  // Risk trend chart data
  const chartData = useMemo(() => {
    if (!riskHistory || riskHistory.length === 0) return [];
    return [...riskHistory].reverse().map((r: RiskScore) => ({
      date: new Date(r.recorded_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
      overall: r.overall_score,
      environmental: r.environmental_risk,
      equipment: r.equipment_risk,
      activity: r.activity_risk || 0,
      site_condition: r.site_condition_risk,
      operational: r.operational_risk,
    }));
  }, [riskHistory]);

  const openHazardsCount = hazards?.filter((h: Hazard) => h.status === 'open').length ?? 0;
  const underReviewCount = hazards?.filter((h: Hazard) => h.status === 'under_review').length ?? 0;
  const criticalHazardsCount = hazards?.filter((h: Hazard) => h.risk_category === 'critical' && h.status !== 'closed').length ?? 0;
  const mitigatedCount = hazards?.filter((h: Hazard) => h.status === 'mitigated').length ?? 0;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="badge bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs font-semibold">
              Autonomous Site Risk Monitoring
            </span>
            <span className="badge bg-slate-800 border border-slate-700 text-slate-400 text-xs font-mono">
              Engine: RULE_ENGINE
            </span>
          </div>
          <h1 className="page-title">Site Risk Intelligence & Hazard Detection</h1>
          <p className="page-subtitle">
            Autonomous rule-based risk evaluation, deterministic hazard detection, multi-category scoring & actionable mitigation
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Site Selector Dropdown */}
          <div className="flex items-center gap-2 bg-surface-850 border border-slate-800 rounded-lg px-3 py-1.5">
            <MapPin size={14} className="text-primary-400" />
            <select
              value={activeSiteId}
              onChange={(e) => setSelectedSiteId(e.target.value)}
              className="bg-transparent text-sm text-slate-200 focus:outline-none cursor-pointer"
            >
              {sites?.map((s: Site) => (
                <option key={s.id} value={s.id} className="bg-surface-900 text-slate-200">
                  {s.name} ({s.site_id})
                </option>
              ))}
            </select>
          </div>

          {/* Analyze Site Risk Button */}
          <button
            id="btn-trigger-risk-agent"
            className="btn-primary text-sm flex items-center gap-2 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 shadow-lg shadow-primary-500/20"
            onClick={() => analyzeMutation.mutate()}
            disabled={isAnalyzing || !activeSiteId}
          >
            {isAnalyzing ? (
              <>
                <RefreshCw size={14} className="animate-spin text-white" />
                <span>Analyzing conditions...</span>
              </>
            ) : (
              <>
                <ShieldAlert size={14} className="text-amber-300" />
                <span>ANALYZE SITE RISK</span>
              </>
            )}
          </button>

          {/* Manual Add Hazard Button */}
          <button className="btn-secondary text-sm" onClick={() => setAddOpen(true)}>
            <Plus size={15} /> Add Hazard
          </button>
        </div>
      </div>

      {/* View Switcher: Risk Intelligence Engine (Phase 4.2) vs Site Risk Telemetry (M1) */}
      <div className="flex gap-2 p-1 rounded-lg bg-surface-900 border border-slate-800 w-fit">
        <button
          id="tab-risk-intelligence"
          onClick={() => setViewMode('risk_intelligence')}
          className={clsx(
            'px-4 py-2 rounded-md text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer',
            viewMode === 'risk_intelligence'
              ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/20'
              : 'text-slate-400 hover:text-white hover:bg-surface-800'
          )}
        >
          <Cpu size={14} />
          <span>Construction Risk Intelligence Engine</span>
          <span className="px-1.5 py-0.5 rounded bg-purple-400/20 text-purple-200 text-[10px] font-bold">
            4-Pillars
          </span>
        </button>

        <button
          id="tab-site-monitoring"
          onClick={() => setViewMode('site_monitoring')}
          className={clsx(
            'px-4 py-2 rounded-md text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer',
            viewMode === 'site_monitoring'
              ? 'bg-primary-600 text-white shadow-md shadow-primary-500/20'
              : 'text-slate-400 hover:text-white hover:bg-surface-800'
          )}
        >
          <ShieldAlert size={14} />
          <span>Site Risk Telemetry & Hazards (M1)</span>
        </button>
      </div>

      {viewMode === 'risk_intelligence' ? (
        <RiskIntelligencePanel siteId={activeSiteId} siteName={activeSite?.name} />
      ) : (
        <>
          {/* Deterministic Demo Scenarios Bar (Step 20) */}
          <div className="card p-4 bg-gradient-to-r from-surface-850 via-surface-900 to-surface-850 border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Play size={14} className="text-primary-400" />
            <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Deterministic Demo Scenarios (Rule-Engine Testing)
            </span>
          </div>
          <span className="text-[11px] text-slate-500">
            Click to run repeatable test cases with exact expected risk outcomes
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
          {[
            { id: 1, title: 'Scenario 1: Baseline', expected: 'LOW', color: '#10b981', desc: 'Clear weather + routine work' },
            { id: 2, title: 'Scenario 2: Moderate', expected: 'MEDIUM', color: '#f59e0b', desc: 'Concrete work + minor debris' },
            { id: 3, title: 'Scenario 3: Equipment', expected: 'HIGH', color: '#f97316', desc: 'Overdue crane + hot welding' },
            { id: 4, title: 'Scenario 4: Trench Flood', expected: 'CRITICAL', color: '#ef4444', desc: 'Heavy rain + excavation' },
            { id: 5, title: 'Scenario 5: Electrical', expected: 'CRITICAL', color: '#ef4444', desc: 'Water pool + active wiring' },
          ].map((sc) => (
            <button
              key={sc.id}
              onClick={() => demoMutation.mutate(sc.id)}
              disabled={demoMutation.isPending}
              className="p-2.5 rounded-lg bg-surface-900 border border-slate-800 hover:border-slate-700 text-left transition-all hover:bg-white/5 group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="text-xs font-bold text-slate-200 group-hover:text-primary-300">
                    {sc.title}
                  </span>
                  <span
                    className="text-[9px] font-bold px-1.5 py-0.2 rounded"
                    style={{ backgroundColor: sc.color + '20', color: sc.color }}
                  >
                    {sc.expected}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 line-clamp-1">{sc.desc}</p>
              </div>
              <div className="text-[10px] text-primary-400 font-medium mt-2 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                Execute →
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Step 15: OVERALL SITE RISK & Multi-Category Risk Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Overall Site Risk Hero Card */}
        <div className="lg:col-span-4 card p-6 flex flex-col justify-between relative overflow-hidden bg-gradient-to-br from-surface-850 to-surface-900 border border-slate-800">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                OVERALL SITE RISK
              </div>
              <div className="text-sm font-medium text-slate-300">
                {activeSite?.name || 'Selected Site'}
              </div>
            </div>
            <span
              className="px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider"
              style={{ backgroundColor: overallColor + '20', color: overallColor, border: `1px solid ${overallColor}40` }}
            >
              {riskCategory}
            </span>
          </div>

          {/* Central Gauge Display */}
          <div className="flex flex-col items-center justify-center my-4">
            <RiskGauge score={overallRiskScore} size={150} />
            <div className="mt-3 text-center">
              <span className="text-4xl font-extrabold tabular-nums" style={{ color: overallColor }}>
                {overallRiskScore.toFixed(0)}
              </span>
              <span className="text-slate-500 text-sm font-medium ml-1">/ 100</span>
              <div className="text-xs font-semibold text-slate-400 mt-1 uppercase tracking-wider">
                {riskCategory} RISK STATUS
              </div>
            </div>
          </div>

          {/* Auditability & Metadata */}
          <div className="pt-4 border-t border-slate-800 text-xs text-slate-500 space-y-1">
            <div className="flex justify-between">
              <span>Detection Source:</span>
              <span className="font-mono text-slate-300">RULE_ENGINE</span>
            </div>
            <div className="flex justify-between">
              <span>Last Evaluated:</span>
              <span className="text-slate-300">
                {latestScore?.recorded_at ? formatRelativeTime(latestScore.recorded_at) : 'Awaiting analysis'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Formula:</span>
              <span className="text-slate-300">(P × S / 25) × 100</span>
            </div>
          </div>
        </div>

        {/* 5 Multi-Category Risk Breakdown (Step 11 & 15) */}
        <div className="lg:col-span-8 flex flex-col justify-between gap-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              {
                title: 'Environmental Risk',
                score: latestScore?.environmental_risk ?? 0.0,
                desc: 'Precipitation, wind gusts, temperature, water pooling',
              },
              {
                title: 'Equipment Risk',
                score: latestScore?.equipment_risk ?? 0.0,
                desc: 'Overdue maintenance, inspection green-tags, machinery wear',
              },
              {
                title: 'Activity Risk',
                score: latestScore?.activity_risk ?? 0.0,
                desc: 'Excavation, hot work welding, scaffolding, rigging',
              },
              {
                title: 'Site Condition Risk',
                score: latestScore?.site_condition_risk ?? 0.0,
                desc: 'Ground saturation, slope stability, egress routes',
              },
              {
                title: 'Operational Risk',
                score: latestScore?.operational_risk ?? 0.0,
                desc: 'Workforce congestion, permit compliance, supervisor presence',
              },
            ].map((cat) => {
              const cColor = getRiskColor(cat.score);
              const cLevel = getRiskCategory(cat.score).toUpperCase();
              return (
                <div key={cat.title} className="card p-4 bg-surface-850 border border-slate-800 hover:border-slate-700 transition-all">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-300">{cat.title}</span>
                    <span className="font-bold tabular-nums" style={{ color: cColor }}>
                      {cat.score.toFixed(0)} / 100
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 mb-2">
                    <span>Level: <strong style={{ color: cColor }}>{cLevel}</strong></span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mb-2">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(5, cat.score))}%`, backgroundColor: cColor }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-500 leading-tight">{cat.desc}</p>
                </div>
              );
            })}

            {/* Quick Metrics Tile */}
            <div className="card p-4 bg-surface-850 border border-slate-800 flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Hazard Summary</span>
              <div className="grid grid-cols-2 gap-2 my-2">
                <div>
                  <div className="text-xl font-bold text-red-400 tabular-nums">{criticalHazardsCount}</div>
                  <div className="text-[10px] text-slate-500 uppercase">Critical</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-amber-400 tabular-nums">{openHazardsCount}</div>
                  <div className="text-[10px] text-slate-500 uppercase">Open</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-primary-400 tabular-nums">{underReviewCount}</div>
                  <div className="text-[10px] text-slate-500 uppercase">Reviewing</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-green-400 tabular-nums">{mitigatedCount}</div>
                  <div className="text-[10px] text-slate-500 uppercase">Mitigated</div>
                </div>
              </div>
              <div className="text-[10px] text-slate-500">Active monitored zone: {activeSite?.site_id}</div>
            </div>
          </div>

          {/* Actionable Safety Recommendations Banner (Step 12) */}
          {latestScore?.recommendations && latestScore.recommendations.length > 0 && (
            <div className="card p-4 bg-primary-950/20 border border-primary-500/30">
              <div className="flex items-center gap-2 text-xs font-semibold text-primary-400 uppercase tracking-wider mb-2">
                <CheckCircle2 size={14} />
                Site Risk Agent — Actionable Safety Recommendations
              </div>
              <ul className="space-y-1.5 text-xs text-slate-200">
                {latestScore.recommendations.slice(0, 3).map((rec, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-primary-400 font-bold">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Step 18: Risk History Trend Chart (Stored Analysis Results) */}
      <div className="card p-5 border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="section-title">Site Risk Score Trend (Stored Historical Analyses)</h3>
            <p className="text-xs text-slate-500">
              Deterministic risk history stored in database from automated agent evaluations and scenarios
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-primary-500" /> Overall Risk</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> Environmental</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Equipment</span>
          </div>
        </div>

        {chartData && chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <ReferenceLine y={75} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'CRITICAL (75)', fill: '#ef4444', fontSize: 10 }} />
              <ReferenceLine y={50} stroke="#f97316" strokeDasharray="4 4" label={{ value: 'HIGH (50)', fill: '#f97316', fontSize: 10 }} />
              <ReferenceLine y={25} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'MEDIUM (25)', fill: '#f59e0b', fontSize: 10 }} />
              <Line type="monotone" dataKey="overall" stroke="#6366f1" strokeWidth={3} dot={{ r: 3 }} name="Overall Risk" />
              <Line type="monotone" dataKey="environmental" stroke="#06b6d4" strokeWidth={1.5} strokeDasharray="2 2" dot={false} name="Environmental" />
              <Line type="monotone" dataKey="equipment" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="2 2" dot={false} name="Equipment" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState
            icon={<TrendingUp size={24} />}
            title="No stored risk history yet"
            description="Click 'ANALYZE SITE RISK' or run a demo scenario to record historical risk assessments."
          />
        )}
      </div>

      {/* Step 16: Hazard Table with Lifecycle Filtering */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border-b border-slate-800 gap-4">
          <div>
            <h3 className="section-title">Hazard Detection & Observation Table</h3>
            <p className="text-xs text-slate-500">
              Click any hazard row to inspect detection evidence, probability, severity, and manage lifecycle state
            </p>
          </div>

          {/* Status Filter Tabs */}
          <div className="flex gap-1 p-1 rounded-lg bg-surface-900 border border-slate-800 overflow-x-auto">
            {['', 'open', 'under_review', 'mitigated', 'closed'].map((s) => (
              <button
                key={s || 'all'}
                onClick={() => setStatusFilter(s)}
                className={clsx(
                  'px-3 py-1 rounded text-xs font-medium transition-all whitespace-nowrap',
                  statusFilter === s
                    ? 'bg-primary-500/20 text-primary-300 border border-primary-500/30'
                    : 'text-slate-500 hover:text-slate-300'
                )}
              >
                {s === '' ? 'All' : HAZARD_STATUS_LABEL[s as import('@/types').HazardStatus]}
              </button>
            ))}
          </div>
        </div>

        {hazardsLoading && <PageLoader />}

        {!hazardsLoading && (!hazards || hazards.length === 0) && (
          <EmptyState
            icon={<ShieldAlert size={28} />}
            title="No hazards found"
            description="No hazards match the current filter. Run 'ANALYZE SITE RISK' to execute the Site Risk Agent."
            action={
              <button className="btn-primary" onClick={() => analyzeMutation.mutate()}>
                <ShieldAlert size={15} /> Run Risk Analysis
              </button>
            }
          />
        )}

        {!hazardsLoading && hazards && hazards.length > 0 && (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Hazard ID</th>
                  <th>Type</th>
                  <th>Hazard Description</th>
                  <th className="text-center">Severity</th>
                  <th className="text-center">Probability</th>
                  <th>Risk Score</th>
                  <th>Level</th>
                  <th>Detected</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {hazards.map((hazard: Hazard) => {
                  const hColor = getRiskColor(hazard.risk_score);
                  return (
                    <tr
                      key={hazard.id}
                      className="cursor-pointer hover:bg-white/5 transition-colors"
                      onClick={() => {
                        setSelectedHazard(hazard);
                        setHazardModalOpen(true);
                      }}
                    >
                      <td className="font-mono text-xs text-slate-400 font-semibold">{hazard.hazard_id}</td>
                      <td>
                        <span className="badge badge-monitoring text-xs">
                          {HAZARD_TYPE_LABEL[hazard.hazard_type]}
                        </span>
                      </td>
                      <td className="max-w-xs">
                        <div className="text-sm font-medium text-slate-200 truncate">{hazard.description}</div>
                        <div className="text-[11px] text-slate-500 truncate">
                          Source: {hazard.detection_source || 'RULE_ENGINE'}
                        </div>
                      </td>
                      <td className="font-bold text-center" style={{ color: getRiskColor(hazard.severity * 20) }}>
                        {hazard.severity}/5
                      </td>
                      <td className="text-center font-medium">{hazard.probability}/5</td>
                      <td>
                        <span className="font-bold tabular-nums" style={{ color: hColor }}>
                          {hazard.risk_score.toFixed(0)}
                        </span>
                      </td>
                      <td>
                        <span className={clsx('badge text-[10px]', RISK_BADGE_MAP[hazard.risk_category])}>
                          {hazard.risk_category.toUpperCase()}
                        </span>
                      </td>
                      <td className="text-slate-500 text-xs">{formatRelativeTime(hazard.detected_at)}</td>
                      <td>
                        <span className={clsx('badge text-xs', HAZARD_STATUS_BADGE[hazard.status])}>
                          {HAZARD_STATUS_LABEL[hazard.status]}
                        </span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedHazard(hazard);
                            setHazardModalOpen(true);
                          }}
                        >
                          <Eye size={13} /> View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
        </>
      )}

      {/* Reusable Hazard Details Modal (Step 17) */}
      <HazardDetailModal
        hazard={selectedHazard}
        open={hazardModalOpen}
        onClose={() => setHazardModalOpen(false)}
        onUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ['hazards'] });
          queryClient.invalidateQueries({ queryKey: ['risk-summary', activeSiteId] });
        }}
      />

      {/* Manual Add Hazard Modal (Phase 1.1 preserved) */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Record Safety Hazard" size="lg">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Site *</label>
              <select {...register('site_id')} className="input">
                <option value="">Select site...</option>
                {sites?.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
              {errors.site_id && <p className="text-xs text-red-400 mt-1">{errors.site_id.message}</p>}
            </div>
            <div>
              <label className="label">Hazard Type *</label>
              <select {...register('hazard_type')} className="input">
                <option value="">Select type...</option>
                {HAZARD_TYPES.map(t => <option key={t} value={t}>{HAZARD_TYPE_LABEL[t]}</option>)}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="label">Description *</label>
              <textarea {...register('description')} className="input h-20 resize-none" placeholder="Describe observed hazard condition..." />
              {errors.description && <p className="text-xs text-red-400 mt-1">{errors.description.message}</p>}
            </div>
            <div>
              <label className="label">Severity (1–5) — {severityVal}</label>
              <input {...register('severity')} type="range" min="1" max="5" step="1" className="w-full accent-primary-500" />
              <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                <span>1: Minor</span><span>5: Catastrophic</span>
              </div>
            </div>
            <div>
              <label className="label">Probability (1–5) — {probabilityVal}</label>
              <input {...register('probability')} type="range" min="1" max="5" step="1" className="w-full accent-primary-500" />
              <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                <span>1: Rare</span><span>5: Almost Certain</span>
              </div>
            </div>

            {/* Live Formula Preview */}
            <div className="md:col-span-2 p-3 rounded-lg bg-surface-800 border border-slate-700 flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center text-lg font-bold"
                style={{ backgroundColor: previewColor + '20', color: previewColor }}
              >
                {previewScore.toFixed(0)}
              </div>
              <div>
                <div className="text-sm font-bold" style={{ color: previewColor }}>
                  {previewLabel} RISK
                </div>
                <div className="text-xs text-slate-500">
                  Formula: (Probability × Severity / 25) × 100 = ({probabilityVal} × {severityVal} / 25) × 100
                </div>
              </div>
            </div>

            <div>
              <label className="label">Reported By</label>
              <input {...register('reported_by')} className="input" placeholder="Inspector name..." />
            </div>
            <div className="md:col-span-2">
              <label className="label">Recommended Action</label>
              <textarea {...register('recommended_action')} className="input h-20 resize-none" placeholder="Describe corrective mitigation action..." />
            </div>
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={() => setAddOpen(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Saving...' : 'Add Hazard'}
            </button>
          </div>
        </form>
      </Modal>
    </motion.div>
  );
}
