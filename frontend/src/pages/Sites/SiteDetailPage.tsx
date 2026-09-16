import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft, MapPin, Users, Truck, Activity as ActivityIcon, ShieldAlert,
  ClipboardCheck, Clock, TrendingUp, Plus, Settings, Play, Sparkles, AlertTriangle,
  CheckCircle2, Info, ChevronRight, RefreshCw, Layers, X, Camera
} from 'lucide-react';

import { sitesApi, workersApi, equipmentApi, activitiesApi, hazardsApi, riskIntelApi, safetyApi, ppeApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { RiskGauge, PageLoader, EmptyState, Modal, HazardDetailModal, WorkerSafetyModal } from '@/components/common';
import {
  SITE_STATUS_BADGE, SITE_STATUS_LABEL, RISK_BADGE_MAP, RISK_LABEL_MAP,
  HAZARD_STATUS_BADGE, HAZARD_STATUS_LABEL, HAZARD_TYPE_LABEL, ACTIVITY_TYPE_LABEL,
  WORKER_ROLE_LABEL, TRAINING_STATUS_BADGE, TRAINING_STATUS_LABEL,
  PPE_STATUS_BADGE, EQUIPMENT_STATUS_BADGE, EQUIPMENT_STATUS_LABEL,
  formatDate, formatRelativeTime
} from '@/utils/display';
import { getRiskColor, getRiskCategory } from '@/utils/riskScoring';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { Worker, Equipment, Activity, Hazard, RiskScore, SiteStatus, RiskCategory, SiteRiskAnalysisResponse, SafetyFinding, SafetyAnalysisResponse, PPEAnalysis } from '@/types';

type Tab = 'overview' | 'workers' | 'equipment' | 'activities' | 'hazards' | 'inspections' | 'risk-history';

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'overview', label: 'Overview', icon: <ActivityIcon size={14} /> },
  { key: 'workers', label: 'Workers', icon: <Users size={14} /> },
  { key: 'equipment', label: 'Equipment', icon: <Truck size={14} /> },
  { key: 'activities', label: 'Activities', icon: <ClipboardCheck size={14} /> },
  { key: 'hazards', label: 'Hazards', icon: <ShieldAlert size={14} /> },
  { key: 'inspections', label: 'Inspections', icon: <ClipboardCheck size={14} /> },
  { key: 'risk-history', label: 'Risk History', icon: <TrendingUp size={14} /> },
];

const WRITE_ROLES = ['super_admin', 'project_manager', 'site_manager', 'safety_officer'];

export default function SiteDetailPage() {
  const { siteId } = useParams<{ siteId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const canWrite = WRITE_ROLES.includes(user?.role ?? '');
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  // Phase 1.2 State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<SiteRiskAnalysisResponse | null>(null);
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const [demoModalOpen, setDemoModalOpen] = useState(false);
  const [selectedHazard, setSelectedHazard] = useState<Hazard | null>(null);
  const [hazardModalOpen, setHazardModalOpen] = useState(false);

  // Phase 2.1 Safety State
  const [safetyAnalysisResult, setSafetyAnalysisResult] = useState<SafetyAnalysisResponse | null>(null);
  const [safetyFindingsOpen, setSafetyFindingsOpen] = useState(false);
  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null);
  const [workerSafetyModalOpen, setWorkerSafetyModalOpen] = useState(false);

  const { data: site, isLoading } = useQuery({
    queryKey: ['site', siteId],
    queryFn: () => sitesApi.get(siteId!).then(r => r.data),
    enabled: !!siteId,
  });

  const { data: riskSummary } = useQuery({
    queryKey: ['risk-summary', siteId],
    queryFn: () => riskIntelApi.getSiteRiskSummary(siteId!).then(r => r.data),
    enabled: !!siteId,
  });

  const { data: workers } = useQuery({
    queryKey: ['workers', siteId],
    queryFn: () => workersApi.list(siteId).then(r => r.data),
    enabled: !!siteId && activeTab === 'workers',
  });

  const { data: equipment } = useQuery({
    queryKey: ['equipment', siteId],
    queryFn: () => equipmentApi.list(siteId).then(r => r.data),
    enabled: !!siteId && activeTab === 'equipment',
  });

  const { data: activities } = useQuery({
    queryKey: ['activities', siteId],
    queryFn: () => activitiesApi.list(siteId).then(r => r.data),
    enabled: !!siteId && activeTab === 'activities',
  });

  const { data: hazards } = useQuery({
    queryKey: ['hazards', siteId],
    queryFn: () => hazardsApi.list(siteId).then(r => r.data),
    enabled: !!siteId && (activeTab === 'hazards' || activeTab === 'overview'),
  });

  const { data: riskHistory } = useQuery({
    queryKey: ['risk-history', siteId],
    queryFn: () => sitesApi.getRiskHistory(siteId!).then(r => r.data),
    enabled: !!siteId && (activeTab === 'risk-history' || activeTab === 'overview'),
  });

  const { data: demoScenarios } = useQuery({
    queryKey: ['demo-scenarios'],
    queryFn: () => riskIntelApi.listDemoScenarios().then(r => r.data),
  });

  // Phase 2.1: Safety summary + findings for workers tab
  const { data: safetySummary, refetch: refetchSafetySummary } = useQuery({
    queryKey: ['safety-summary', siteId],
    queryFn: () => safetyApi.getSiteSummary(siteId!).then(r => r.data),
    enabled: !!siteId && activeTab === 'workers',
  });

  const { data: safetyFindings, refetch: refetchSafetyFindings } = useQuery<SafetyFinding[]>({
    queryKey: ['safety-findings-site', siteId],
    queryFn: () => safetyApi.getSiteFindings(siteId!).then(r => r.data),
    enabled: !!siteId && safetyFindingsOpen,
  });

  // Phase 2.2: CV PPE analyses for this site
  const { data: ppeAnalyses } = useQuery<PPEAnalysis[]>({
    queryKey: ['ppe-analyses-site', siteId],
    queryFn: () => ppeApi.getSiteAnalyses(siteId!).then(r => r.data),
    enabled: !!siteId,
  });

  // Analyze Site Risk Mutation
  const analyzeMutation = useMutation({
    mutationFn: (data?: any) => riskIntelApi.analyzeSite({ site_id: siteId!, ...(data || {}) }),
    onMutate: () => {
      setIsAnalyzing(true);
      toast.loading('Analyzing site conditions...', { id: 'analyze-toast' });
    },
    onSuccess: (res) => {
      setIsAnalyzing(false);
      toast.success('Risk analysis completed.', { id: 'analyze-toast' });
      setAnalysisResult(res.data);
      setAnalysisModalOpen(true);
      queryClient.invalidateQueries({ queryKey: ['site', siteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-summary', siteId] });
      queryClient.invalidateQueries({ queryKey: ['hazards', siteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-history', siteId] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: (err: any) => {
      setIsAnalyzing(false);
      toast.error(err.response?.data?.detail || 'Risk analysis failed', { id: 'analyze-toast' });
    },
  });

  // Phase 2.1: Analyze Worker Safety Mutation
  const safetyAnalyzeMutation = useMutation({
    mutationFn: () => safetyApi.analyzeSite(siteId!),
    onSuccess: r => {
      setSafetyAnalysisResult(r.data);
      setSafetyFindingsOpen(true);
      refetchSafetySummary();
      refetchSafetyFindings();
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast.success(`Safety analysis: ${r.data.summary.violation_count} finding(s) detected`);
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Safety analysis failed');
    },
  });

  // Run Demo Scenario Mutation
  const demoMutation = useMutation({
    mutationFn: (scenarioId: number) => riskIntelApi.runDemoScenario(siteId!, scenarioId),
    onMutate: () => {
      toast.loading('Executing demo scenario...', { id: 'demo-toast' });
    },
    onSuccess: (res) => {
      toast.success('Demo scenario executed successfully.', { id: 'demo-toast' });
      setAnalysisResult(res.data);
      setDemoModalOpen(false);
      setAnalysisModalOpen(true);
      queryClient.invalidateQueries({ queryKey: ['site', siteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-summary', siteId] });
      queryClient.invalidateQueries({ queryKey: ['hazards', siteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-history', siteId] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Demo scenario execution failed', { id: 'demo-toast' });
    },
  });

  if (isLoading) return <PageLoader />;
  if (!site) return <div className="text-center py-16 text-slate-500">Site not found</div>;

  const chartData = riskHistory?.map((r: RiskScore) => ({
    date: new Date(r.recorded_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
    score: r.overall_score,
  })).reverse();

  const latestScore = riskSummary?.latest_score;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {/* Header */}
      <div className="mb-6">
        <button onClick={() => navigate('/sites')} className="btn-ghost text-sm mb-4 -ml-2">
          <ArrowLeft size={14} /> Back to Sites
        </button>

        <div className="card p-6">
          <div className="flex flex-col md:flex-row md:items-start gap-6">
            {/* Gauge */}
            <div className="flex flex-col items-center gap-2">
              <RiskGauge score={site.current_risk_score} size={120} />
              <span className="text-xs text-slate-500">Overall Site Risk</span>
            </div>

            {/* Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <span className="text-xs font-mono text-slate-500">{site.site_id}</span>
                <span className={clsx('badge', SITE_STATUS_BADGE[site.status as SiteStatus])}>
                  {SITE_STATUS_LABEL[site.status as SiteStatus]}
                </span>
                <span className={clsx('badge', RISK_BADGE_MAP[site.risk_category as RiskCategory])}>
                  {RISK_LABEL_MAP[site.risk_category as RiskCategory]} RISK
                </span>
                <span className="badge bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs">
                  Agent: Site Risk Agent (Phase 1.3 Verified)
                </span>
              </div>
              <h1 className="text-2xl font-bold text-slate-100 mb-1">{site.name}</h1>
              {site.project_name && (
                <p className="text-sm text-slate-500 mb-4">Project: {site.project_name}</p>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <InfoBlock icon={<MapPin size={14} />} label="Location" value={[site.city, site.state].filter(Boolean).join(', ') || '—'} />
                <InfoBlock icon={<Users size={14} />} label="Manager" value={site.manager_name || '—'} />
                <InfoBlock icon={<Users size={14} />} label="Workers" value={`${site.worker_count}`} />
                <InfoBlock icon={<Truck size={14} />} label="Equipment" value={`${site.equipment_count}`} />
                <InfoBlock icon={<Clock size={14} />} label="Last Inspection" value={formatDate(site.last_inspection)} />
                <InfoBlock icon={<MapPin size={14} />} label="Site Type" value={site.site_type || '—'} />
              </div>
            </div>

            {/* Actions: Step 14 - ANALYZE SITE RISK */}
            <div className="flex flex-col gap-2.5 shrink-0 sm:w-52">
              <button
                id="btn-analyze-site-risk"
                className="btn-primary text-sm flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 shadow-lg shadow-primary-500/20"
                onClick={() => analyzeMutation.mutate()}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw size={15} className="animate-spin text-white" />
                    <span>Analyzing site...</span>
                  </>
                ) : (
                  <>
                    <ShieldAlert size={15} className="text-amber-300" />
                    <span className="font-semibold">ANALYZE SITE RISK</span>
                  </>
                )}
              </button>

              <button
                id="btn-run-demo-scenario"
                className="btn-secondary text-xs flex items-center justify-center gap-1.5 py-2 text-slate-300"
                onClick={() => setDemoModalOpen(true)}
              >
                <Play size={13} className="text-primary-400" />
                <span>Deterministic Scenarios</span>
              </button>

              <button className="btn-ghost text-xs text-slate-400 flex items-center justify-center gap-1" onClick={() => navigate(`/sites/${siteId}/activities/new`)}>
                <Plus size={13} /> Log Activity
              </button>
            </div>
          </div>

          {/* Sub-category Risk Scores Strip */}
          {latestScore && (
            <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-5 gap-3">
              {[
                { label: 'Environmental', score: latestScore.environmental_risk },
                { label: 'Equipment', score: latestScore.equipment_risk },
                { label: 'Activity', score: latestScore.activity_risk || 0 },
                { label: 'Site Condition', score: latestScore.site_condition_risk },
                { label: 'Operational', score: latestScore.operational_risk },
              ].map((cat) => {
                const cColor = getRiskColor(cat.score);
                return (
                  <div key={cat.label} className="p-2.5 rounded-lg bg-surface-900 border border-slate-800">
                    <div className="flex items-center justify-between text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                      <span>{cat.label}</span>
                      <span className="font-bold tabular-nums" style={{ color: cColor }}>
                        {cat.score.toFixed(0)}
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${cat.score}%`, backgroundColor: cColor }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-xl bg-surface-900 border border-slate-800 mb-5 overflow-x-auto">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap',
              activeTab === tab.key
                ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20'
                : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* Overview */}
        {activeTab === 'overview' && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="card p-5">
                <h3 className="section-title mb-4">Active Hazards</h3>
                <div className="space-y-3">
                    {hazards?.filter((h: Hazard) => h.status === 'open').slice(0, 4).map((h: Hazard) => (
                    <HazardRow
                      key={h.id}
                      hazard={h}
                      onClick={() => {
                        setSelectedHazard(h);
                        setHazardModalOpen(true);
                      }}
                    />
                  ))}
                  {(!hazards || hazards.filter((h: Hazard) => h.status === 'open').length === 0) && (
                    <p className="text-sm text-slate-600 py-4 text-center">No open hazards 🎉</p>
                  )}
                </div>
              </div>
              <div className="card p-5">
                <h3 className="section-title mb-4">Site Details</h3>
                <div className="space-y-3 text-sm">
                  {[
                    ['Site ID', site.site_id],
                    ['Project', site.project_name || '—'],
                    ['Type', site.site_type || '—'],
                    ['Address', site.address || '—'],
                    ['City', site.city || '—'],
                    ['State', site.state || '—'],
                    ['Country', site.country || '—'],
                    ['Created', formatDate(site.created_at)],
                  ].map(([label, value]) => (
                    <div key={label} className="flex gap-3 py-2 border-b border-slate-800 last:border-0">
                      <span className="text-slate-500 w-28 shrink-0">{label}</span>
                      <span className="text-slate-300 font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Phase 2.2: Site Computer Vision PPE Summary */}
            {(() => {
              const totalAnalyses = ppeAnalyses?.length ?? 0;
              const compliantCount = ppeAnalyses?.filter(a => a.overall_compliance === 'COMPLIANT').length ?? 0;
              const nonCompliantCount = ppeAnalyses?.filter(a => a.overall_compliance === 'NON_COMPLIANT').length ?? 0;
              const uncertainCount = ppeAnalyses?.filter(a => a.overall_compliance === 'UNCERTAIN').length ?? 0;
              const recentViolations = ppeAnalyses?.filter(a => a.overall_compliance === 'NON_COMPLIANT' || (a.missing_ppe && a.missing_ppe.length > 0)).slice(0, 3) ?? [];
              const workersAnalyzed = new Set(ppeAnalyses?.filter(a => a.worker_id).map(a => a.worker_id)).size;

              return (
                <div className="card p-5 border border-primary-500/20 bg-gradient-to-r from-surface-900 via-surface-900 to-primary-950/20">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400">
                        <Camera size={16} />
                      </div>
                      <div>
                        <h3 className="section-title text-sm flex items-center gap-2">
                          Computer Vision PPE Compliance
                          <span className="text-[10px] font-mono font-semibold bg-primary-500/20 text-primary-300 border border-primary-500/30 px-1.5 py-0.5 rounded">
                            PHASE 2.2
                          </span>
                        </h3>
                        <p className="text-xs text-slate-400">Visual detection records and site worker compliance</p>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate('/safety')}
                      className="btn-ghost text-xs py-1.5 px-3 flex items-center gap-1.5 text-primary-400 hover:text-primary-300 border border-primary-500/20 self-start sm:self-auto"
                    >
                      <span>Open CV Detector</span>
                      <ChevronRight size={14} />
                    </button>
                  </div>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                    <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                      <span className="text-[11px] text-slate-400 block mb-1">Workers Analyzed</span>
                      <span className="text-xl font-bold font-mono text-slate-200">{workersAnalyzed}</span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">{totalAnalyses} visual scan(s)</span>
                    </div>
                    <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                      <span className="text-[11px] text-emerald-400 block mb-1">PPE Compliant</span>
                      <span className="text-xl font-bold font-mono text-emerald-400">{compliantCount}</span>
                      <span className="text-[10px] text-emerald-500/80 block mt-0.5">Full PPE verified</span>
                    </div>
                    <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                      <span className="text-[11px] text-red-400 block mb-1">PPE Non-Compliant</span>
                      <span className="text-xl font-bold font-mono text-red-400">{nonCompliantCount}</span>
                      <span className="text-[10px] text-red-500/80 block mt-0.5">Missing gear detected</span>
                    </div>
                    <div className="p-3 rounded-lg bg-surface-950/80 border border-slate-800">
                      <span className="text-[11px] text-amber-400 block mb-1">Uncertain Detections</span>
                      <span className="text-xl font-bold font-mono text-amber-400">{uncertainCount}</span>
                      <span className="text-[10px] text-amber-500/80 block mt-0.5">Below threshold</span>
                    </div>
                  </div>

                  {/* Recent PPE Violations / Analyses */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Recent PPE Violations
                    </h4>
                    {recentViolations.length === 0 ? (
                      <div className="p-3 rounded-lg bg-surface-950/40 border border-slate-800/60 text-xs text-slate-500 text-center">
                        No active PPE violations logged for this site.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {recentViolations.map((v) => (
                          <div
                            key={v.id}
                            className="p-2.5 rounded-lg bg-surface-950/80 border border-slate-800 flex items-center justify-between text-xs"
                          >
                            <div className="flex items-center gap-2">
                              <span className="badge badge-critical text-[10px] font-mono">NON-COMPLIANT</span>
                              <span className="text-slate-300 font-medium">
                                Missing: {v.missing_ppe.map(p => p.replace('_', ' ')).join(', ')}
                              </span>
                            </div>
                            <span className="text-[10px] font-mono text-slate-500">
                              {formatRelativeTime(v.created_at)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* Workers */}
        {activeTab === 'workers' && (
          <div className="card">
            {/* Safety findings panel */}
            {safetyFindingsOpen && (
              <div className="border-b border-slate-800 bg-surface-800/40 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <ShieldAlert size={16} className="text-amber-400" />
                    <h4 className="font-semibold text-slate-200 text-sm">
                      Safety Findings
                      {safetyFindings && safetyFindings.length > 0 && (
                        <span className="ml-2 badge badge-critical text-xs">{safetyFindings.filter(f => f.status === 'open').length} open</span>
                      )}
                    </h4>
                    {safetyAnalysisResult && (
                      <span className={clsx(
                        'badge text-xs',
                        safetyAnalysisResult.summary.safety_level === 'low' ? 'badge-active'
                        : safetyAnalysisResult.summary.safety_level === 'medium' ? 'badge-warning'
                        : 'badge-critical'
                      )}>
                        {safetyAnalysisResult.summary.safety_level?.toUpperCase()} · Score {safetyAnalysisResult.summary.overall_safety_score.toFixed(0)}/100
                      </span>
                    )}
                  </div>
                  <button className="btn-ghost p-1.5" onClick={() => setSafetyFindingsOpen(false)}>
                    <X size={14} />
                  </button>
                </div>
                {(!safetyFindings || safetyFindings.length === 0) ? (
                  <p className="text-sm text-slate-500">No safety findings detected on this site.</p>
                ) : (
                  <div className="table-container">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Type</th>
                          <th>Worker</th>
                          <th>Severity</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {safetyFindings.slice(0, 8).map(f => (
                          <tr key={f.id}>
                            <td className="font-mono text-xs text-slate-500">{f.finding_id}</td>
                            <td className="text-xs text-slate-300">
                              {f.finding_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                            </td>
                            <td className="text-sm text-slate-200">{f.worker_name || 'Site-wide'}</td>
                            <td>
                              <span className={clsx('badge text-xs uppercase', RISK_BADGE_MAP[f.severity])}>
                                {RISK_LABEL_MAP[f.severity]}
                              </span>
                            </td>
                            <td>
                              <span className={clsx('badge text-xs', {
                                'badge-critical': f.status === 'open',
                                'badge-warning': f.status === 'acknowledged',
                                'badge-monitoring': f.status === 'mitigated',
                                'badge-active': f.status === 'closed',
                              })}>
                                {f.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {safetyFindings.length > 8 && (
                      <p className="text-xs text-slate-600 px-4 py-2">
                        +{safetyFindings.length - 8} more findings — <a href="/safety" className="text-primary-400 hover:underline">View on Safety page</a>
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <div>
                <h3 className="section-title">Site Workers ({workers?.length ?? 0})</h3>
                {safetySummary && safetySummary.open_findings_count > 0 && (
                  <p className="text-xs text-amber-400 mt-0.5 flex items-center gap-1">
                    <AlertTriangle size={11} />
                    {safetySummary.open_findings_count} open safety finding(s) · {safetySummary.critical_findings_count} critical
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  id="btn-analyze-worker-safety"
                  className={clsx(
                    'btn-ghost text-sm gap-1.5',
                    !canWrite && 'opacity-50 cursor-not-allowed'
                  )}
                  disabled={!canWrite || safetyAnalyzeMutation.isPending}
                  onClick={() => safetyAnalyzeMutation.mutate()}
                  title={!canWrite ? 'Insufficient permissions' : 'Analyze worker safety compliance'}
                >
                  {safetyAnalyzeMutation.isPending ? (
                    <RefreshCw size={13} className="animate-spin" />
                  ) : (
                    <ShieldAlert size={13} />
                  )}
                  {safetyAnalyzeMutation.isPending ? 'Analyzing…' : 'Analyze Safety'}
                  {safetySummary && safetySummary.open_findings_count > 0 && (
                    <span className="badge badge-critical text-[10px] py-0">{safetySummary.open_findings_count}</span>
                  )}
                </button>
                <button className="btn-primary text-sm" onClick={() => navigate(`/sites/${siteId}/workers/new`)}>
                  <Plus size={14} /> Add Worker
                </button>
              </div>
            </div>
            {(!workers || workers.length === 0) ? (
              <EmptyState icon={<Users size={24} />} title="No workers assigned" />
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Role</th>
                      <th>Department</th>
                      <th>Safety Training</th>
                      <th>PPE</th>
                      <th>Contact</th>
                      <th className="text-right">Safety Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workers.map((w: Worker) => (
                      <tr
                        key={w.id}
                        className="cursor-pointer hover:bg-white/[0.02] transition-colors"
                        onClick={() => {
                          setSelectedWorker(w);
                          setWorkerSafetyModalOpen(true);
                        }}
                      >
                        <td className="font-mono text-xs text-slate-500">{w.worker_id}</td>
                        <td className="font-medium text-slate-200">{w.name}</td>
                        <td>{WORKER_ROLE_LABEL[w.role]}</td>
                        <td className="text-slate-500">{w.department || '—'}</td>
                        <td>
                          <span className={clsx('badge text-xs', TRAINING_STATUS_BADGE[w.safety_training])}>
                            {TRAINING_STATUS_LABEL[w.safety_training]}
                          </span>
                        </td>
                        <td>
                          <span className={clsx('badge text-xs', PPE_STATUS_BADGE[w.ppe_status])}>
                            {w.ppe_status.replace('_', ' ').toUpperCase()}
                          </span>
                        </td>
                        <td className="text-slate-500">{w.contact || '—'}</td>
                        <td className="text-right" onClick={e => e.stopPropagation()}>
                          <button
                            id={`btn-worker-safety-${w.worker_id}`}
                            className="btn-ghost text-xs py-1 px-2.5 text-primary-400 hover:text-primary-300 inline-flex items-center gap-1.5 border border-primary-500/20 bg-primary-500/5 hover:bg-primary-500/15"
                            onClick={() => {
                              setSelectedWorker(w);
                              setWorkerSafetyModalOpen(true);
                            }}
                          >
                            <ShieldAlert size={12} className="text-amber-400" />
                            <span>Safety Profile</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Equipment */}
        {activeTab === 'equipment' && (
          <div className="card">
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <h3 className="section-title">Equipment ({equipment?.length ?? 0})</h3>
              <button className="btn-primary text-sm" onClick={() => navigate(`/sites/${siteId}/equipment/new`)}>
                <Plus size={14} /> Add Equipment
              </button>
            </div>
            {(!equipment || equipment.length === 0) ? (
              <EmptyState icon={<Truck size={24} />} title="No equipment added" />
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Manufacturer</th>
                      <th>Operator</th>
                      <th>Status</th>
                      <th>Last Inspection</th>
                      <th>Maintenance Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {equipment.map((e: Equipment) => (
                      <tr key={e.id}>
                        <td className="font-mono text-xs text-slate-500">{e.equipment_id}</td>
                        <td className="font-medium text-slate-200">{e.name}</td>
                        <td className="text-slate-400">{e.equipment_type}</td>
                        <td className="text-slate-500">{e.manufacturer || '—'}</td>
                        <td className="text-slate-400">{e.operator_name || '—'}</td>
                        <td>
                          <span className={clsx('badge text-xs', EQUIPMENT_STATUS_BADGE[e.status])}>
                            {EQUIPMENT_STATUS_LABEL[e.status]}
                          </span>
                        </td>
                        <td className="text-slate-500">{formatDate(e.last_inspection)}</td>
                        <td className="text-slate-500">{formatDate(e.maintenance_due)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Activities */}
        {activeTab === 'activities' && (
          <div className="card">
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <h3 className="section-title">Activities ({activities?.length ?? 0})</h3>
              <button className="btn-primary text-sm" onClick={() => navigate(`/sites/${siteId}/activities/new`)}>
                <Plus size={14} /> Log Activity
              </button>
            </div>
            {(!activities || activities.length === 0) ? (
              <EmptyState icon={<ActivityIcon size={24} />} title="No activities recorded" />
            ) : (
              <div className="space-y-3 p-5">
                {activities.map((a: Activity) => (
                  <div key={a.id} className="flex items-start gap-4 p-4 rounded-lg bg-surface-800 border border-slate-700">
                    <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center text-primary-400 shrink-0">
                      <ActivityIcon size={14} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="badge badge-monitoring text-xs">
                          {ACTIVITY_TYPE_LABEL[a.activity_type]}
                        </span>
                        <span className="text-xs text-slate-500">{formatDate(a.date)}</span>
                      </div>
                      <p className="text-sm text-slate-300">{a.description || 'No description'}</p>
                      <div className="flex gap-4 mt-2 text-xs text-slate-500">
                        <span>{a.workers_involved} workers</span>
                        {a.start_time && <span>{a.start_time} – {a.end_time}</span>}
                        {a.environmental_conditions && <span>{a.environmental_conditions}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Hazards */}
        {activeTab === 'hazards' && (
          <div className="card">
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <div>
                <h3 className="section-title">Detected Hazards ({hazards?.length ?? 0})</h3>
                <p className="text-xs text-slate-500 mt-0.5">Click any hazard to review evidence, probability, severity, and take action</p>
              </div>
              <button className="btn-primary text-sm" onClick={() => navigate(`/risk-monitoring?site=${siteId}`)}>
                <Plus size={14} /> Add Hazard
              </button>
            </div>
            {(!hazards || hazards.length === 0) ? (
              <EmptyState icon={<ShieldAlert size={24} />} title="No hazards recorded" />
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Type</th>
                      <th>Description</th>
                      <th>Severity</th>
                      <th>Probability</th>
                      <th>Risk Score</th>
                      <th>Level</th>
                      <th>Status</th>
                      <th>Detected</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {hazards.map((h: Hazard) => (
                      <tr
                        key={h.id}
                        className="cursor-pointer hover:bg-white/5 transition-colors"
                        onClick={() => {
                          setSelectedHazard(h);
                          setHazardModalOpen(true);
                        }}
                      >
                        <td className="font-mono text-xs text-slate-500 font-semibold">{h.hazard_id}</td>
                        <td>
                          <span className="badge badge-monitoring text-xs">
                            {HAZARD_TYPE_LABEL[h.hazard_type]}
                          </span>
                        </td>
                        <td className="max-w-xs truncate text-slate-200 font-medium">{h.description}</td>
                        <td className="font-bold text-center" style={{ color: getRiskColor(h.severity * 20) }}>
                          {h.severity}/5
                        </td>
                        <td className="text-center font-medium">{h.probability}/5</td>
                        <td>
                          <span className="font-bold tabular-nums" style={{ color: getRiskColor(h.risk_score) }}>
                            {h.risk_score.toFixed(0)}
                          </span>
                        </td>
                        <td>
                          <span className={clsx('badge text-[10px]', RISK_BADGE_MAP[h.risk_category])}>
                            {h.risk_category.toUpperCase()}
                          </span>
                        </td>
                        <td>
                          <span className={clsx('badge text-xs', HAZARD_STATUS_BADGE[h.status])}>
                            {HAZARD_STATUS_LABEL[h.status]}
                          </span>
                        </td>
                        <td className="text-slate-500 text-xs">{formatRelativeTime(h.detected_at)}</td>
                        <td>
                          <button
                            type="button"
                            className="btn-ghost text-xs text-primary-400 hover:text-primary-300"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedHazard(h);
                              setHazardModalOpen(true);
                            }}
                          >
                            Details →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Inspections */}
        {activeTab === 'inspections' && (
          <EmptyState
            icon={<ClipboardCheck size={28} />}
            title="No inspections recorded"
            description="Inspection records will appear here once logged."
          />
        )}

        {/* Risk History */}
        {activeTab === 'risk-history' && (
          <div className="card p-5">
            <h3 className="section-title mb-5">Site Risk Score History (Stored Analysis Records)</h3>
            {chartData && chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }}
                    labelStyle={{ color: '#94a3b8' }}
                    itemStyle={{ color: '#6366f1' }}
                  />
                  <ReferenceLine y={75} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'CRITICAL (75-100)', fill: '#ef4444', fontSize: 10 }} />
                  <ReferenceLine y={50} stroke="#f97316" strokeDasharray="4 4" label={{ value: 'HIGH (50-74)', fill: '#f97316', fontSize: 10 }} />
                  <ReferenceLine y={25} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'MEDIUM (25-49)', fill: '#f59e0b', fontSize: 10 }} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    dot={{ fill: '#6366f1', r: 3 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={<TrendingUp size={24} />} title="No risk history available" />
            )}
          </div>
        )}
      </motion.div>

      {/* Hazard Detail Modal */}
      <HazardDetailModal
        hazard={selectedHazard}
        open={hazardModalOpen}
        onClose={() => setHazardModalOpen(false)}
        onUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ['hazards', siteId] });
          queryClient.invalidateQueries({ queryKey: ['site', siteId] });
          queryClient.invalidateQueries({ queryKey: ['risk-summary', siteId] });
        }}
      />

      {/* Demo Scenarios Modal */}
      <Modal open={demoModalOpen} onClose={() => setDemoModalOpen(false)} title="Deterministic Construction Risk Demo Scenarios" size="lg">
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            Select a deterministic scenario to test the Site Risk Agent rule engine. Results are 100% reproducible based on exact empirical construction parameters.
          </p>

          <div className="space-y-3">
            {demoScenarios?.map((sc: any) => {
              const lvlColor = sc.expected_level === 'CRITICAL' ? '#ef4444' : sc.expected_level === 'HIGH' ? '#f97316' : sc.expected_level === 'MEDIUM' ? '#f59e0b' : '#10b981';
              return (
                <div
                  key={sc.id}
                  className="p-4 rounded-xl bg-surface-850 border border-slate-800 hover:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-sm text-slate-100">{sc.name}</span>
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-bold"
                        style={{ backgroundColor: lvlColor + '20', color: lvlColor }}
                      >
                        Expected: {sc.expected_level}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{sc.description}</p>
                  </div>

                  <button
                    className="btn-primary text-xs shrink-0 self-start sm:self-auto"
                    onClick={() => demoMutation.mutate(sc.id)}
                    disabled={demoMutation.isPending}
                  >
                    Run Scenario {sc.id}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </Modal>

      {/* Analysis Result Modal */}
      {analysisResult && (
        <Modal open={analysisModalOpen} onClose={() => setAnalysisModalOpen(false)} title="Site Risk Intelligence Analysis Report" size="lg">
          <div className="space-y-5">
            {/* Overall result banner */}
            <div
              className="p-4 rounded-xl border flex items-center justify-between gap-4"
              style={{
                backgroundColor: getRiskColor(analysisResult.overall_risk_score) + '15',
                borderColor: getRiskColor(analysisResult.overall_risk_score) + '40',
              }}
            >
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Analysis Engine: {analysisResult.detection_source}
                </div>
                <div className="text-2xl font-bold text-slate-100 mt-0.5">
                  Overall Score: {analysisResult.overall_risk_score.toFixed(0)} / 100
                </div>
                <span
                  className="inline-block mt-1 px-2.5 py-0.5 rounded text-xs font-bold"
                  style={{
                    backgroundColor: getRiskColor(analysisResult.overall_risk_score) + '30',
                    color: getRiskColor(analysisResult.overall_risk_score),
                  }}
                >
                  {analysisResult.risk_level.toUpperCase()} RISK
                </span>
              </div>

              <div className="text-right text-xs text-slate-400 space-y-1">
                <div>Active Hazards: <strong className="text-slate-200">{analysisResult.active_hazards_count}</strong></div>
                <div>Critical Hazards: <strong className="text-red-400">{analysisResult.critical_hazards_count}</strong></div>
                <div>Highest Single Factor: <strong className="text-amber-400">{analysisResult.highest_hazard_score.toFixed(0)}/100</strong></div>
              </div>
            </div>

            {/* Category breakdown */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                Multi-Category Risk Breakdown
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(analysisResult.categories).map(([key, cat]) => {
                  const catCol = getRiskColor(cat.score);
                  return (
                    <div key={key} className="p-3 rounded-lg bg-surface-850 border border-slate-800">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-semibold text-slate-300 capitalize">{key.replace('_', ' ')} Risk</span>
                        <span className="font-bold tabular-nums" style={{ color: catCol }}>
                          {cat.score.toFixed(0)} / 100 ({cat.level.toUpperCase()})
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden mb-2">
                        <div className="h-full rounded-full" style={{ width: `${cat.score}%`, backgroundColor: catCol }} />
                      </div>
                      <p className="text-[11px] text-slate-500 leading-tight">{cat.explanation}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Actionable Recommendations */}
            {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
              <div className="card p-4 bg-primary-950/20 border-primary-500/20">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-primary-400 mb-2 flex items-center gap-1.5">
                  <CheckCircle2 size={14} /> Actionable Safety Recommendations
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-200">
                  {analysisResult.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-primary-400 font-bold">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                className="btn-primary text-xs"
                onClick={() => setAnalysisModalOpen(false)}
              >
                Close Report
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Worker Safety Detail Modal */}
      <WorkerSafetyModal
        worker={selectedWorker}
        open={workerSafetyModalOpen}
        onClose={() => {
          setWorkerSafetyModalOpen(false);
          setSelectedWorker(null);
        }}
        onUpdated={() => {
          queryClient.invalidateQueries({ queryKey: ['workers', siteId] });
          queryClient.invalidateQueries({ queryKey: ['safety-findings', siteId] });
          queryClient.invalidateQueries({ queryKey: ['safety-summary', siteId] });
        }}
      />
    </motion.div>
  );
}

function InfoBlock({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-slate-500 mt-0.5 shrink-0">{icon}</span>
      <div>
        <div className="text-[10px] text-slate-600 uppercase tracking-wider">{label}</div>
        <div className="text-sm font-medium text-slate-300">{value}</div>
      </div>
    </div>
  );
}

function HazardRow({ hazard, onClick }: { hazard: Hazard; onClick?: () => void }) {
  return (
    <div
      onClick={onClick}
      className="flex items-start gap-3 p-3 rounded-lg bg-surface-800 border border-slate-700 hover:border-slate-600 cursor-pointer transition-colors"
    >
      <div
        className="w-8 h-8 rounded shrink-0 flex items-center justify-center text-xs font-bold"
        style={{ backgroundColor: getRiskColor(hazard.risk_score) + '20', color: getRiskColor(hazard.risk_score) }}
      >
        {hazard.risk_score.toFixed(0)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-200 truncate">{hazard.description}</div>
        <div className="text-xs text-slate-500 mt-0.5">
          {HAZARD_TYPE_LABEL[hazard.hazard_type]} · {formatRelativeTime(hazard.detected_at)}
        </div>
      </div>
      <span className={clsx('badge text-xs shrink-0', HAZARD_STATUS_BADGE[hazard.status])}>
        {HAZARD_STATUS_LABEL[hazard.status]}
      </span>
    </div>
  );
}

