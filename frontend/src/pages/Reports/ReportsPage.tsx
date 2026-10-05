import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText, Calendar, TrendingUp, ClipboardCheck, Activity,
  Sparkles, RefreshCw, Printer, Trash2, CheckCircle2,
  AlertTriangle, ShieldAlert, ShieldCheck, HardHat,
  ChevronRight, ExternalLink, Download, Layers, Shield, Clock,
  ArrowRight, Search, FileDown, Check, AlertOctagon
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import { reportsApi, sitesApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type {
  Site, ReportType, GeneratedReport, GeneratedReportSummary, ReportTypeInfo
} from '@/types';

const REPORT_TYPE_CONFIG: Record<ReportType, { label: string; icon: any; color: string; desc: string }> = {
  DAILY_SITE: {
    label: 'Daily Site Report',
    icon: Calendar,
    color: 'from-blue-500 to-indigo-600',
    desc: 'Daily operational site log including hazards, worker PPE violations, and prioritized daily action items.'
  },
  EXECUTIVE_SUMMARY: {
    label: 'Executive Risk Summary',
    icon: TrendingUp,
    color: 'from-purple-500 to-pink-600',
    desc: 'High-level synthesis for leadership covering multi-pillar scores, liability brackets, and executive actions.'
  },
  AUDIT_READY: {
    label: 'Audit-Ready Documentation',
    icon: ClipboardCheck,
    color: 'from-amber-500 to-orange-600',
    desc: 'Traceable compliance dossier mapping each finding to OSHA / regulatory standards, evidence, and verification.'
  },
  PROJECT_HEALTH: {
    label: 'Project Health Report',
    icon: Activity,
    color: 'from-emerald-500 to-teal-600',
    desc: '4-pillar quadrant evaluation synthesizing Site Risk, Safety, Compliance, and Insurance health grades.'
  }
};

const SEVERITY_BADGE: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: 'bg-rose-500/15', text: 'text-rose-400', border: 'border-rose-500/30' },
  HIGH: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30' },
  MEDIUM: { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30' },
  LOW: { bg: 'bg-slate-500/15', text: 'text-slate-400', border: 'border-slate-500/30' },
};

const AGENT_BADGE: Record<string, { bg: string; text: string }> = {
  site_risk: { bg: 'bg-orange-500/15 text-orange-400', text: 'Site Risk Agent' },
  safety: { bg: 'bg-yellow-500/15 text-yellow-400', text: 'Safety Agent' },
  compliance: { bg: 'bg-cyan-500/15 text-cyan-400', text: 'Compliance Agent' },
  insurance: { bg: 'bg-indigo-500/15 text-indigo-400', text: 'Insurance Agent' },
};

export default function ReportsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [selectedType, setSelectedType] = useState<ReportType>('DAILY_SITE');
  const [activeTab, setActiveTab] = useState<'view' | 'history'>('view');
  const [activeReport, setActiveReport] = useState<GeneratedReport | null>(null);
  const [auditFilter, setAuditFilter] = useState<string>('');

  // 1. Fetch available sites
  const { data: sites = [], isLoading: sitesLoading } = useQuery<Site[]>({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  useMemo(() => {
    if (sites.length > 0 && !selectedSiteId) {
      setSelectedSiteId(sites[0].id);
    }
  }, [sites, selectedSiteId]);

  // 2. Fetch report types
  const { data: reportTypesRes } = useQuery({
    queryKey: ['report-types'],
    queryFn: () => reportsApi.getTypes(),
  });
  const reportTypes: ReportTypeInfo[] = reportTypesRes?.data || [];

  // 3. Fetch past reports list
  const { data: reportsListRes, isLoading: reportsListLoading } = useQuery({
    queryKey: ['reports-list', selectedSiteId],
    queryFn: () => reportsApi.list({ site_id: selectedSiteId || undefined }),
    enabled: true,
  });
  const reportsList: GeneratedReportSummary[] = reportsListRes?.data || [];

  // 4. Generate report mutation
  const generateMutation = useMutation({
    mutationFn: (data: { site_id: string; report_type: ReportType }) =>
      reportsApi.generate(data),
    onSuccess: (res) => {
      toast.success(`${REPORT_TYPE_CONFIG[selectedType].label} generated successfully!`);
      setActiveReport(res.data);
      setActiveTab('view');
      queryClient.invalidateQueries({ queryKey: ['reports-list', selectedSiteId] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Report generation failed');
    }
  });

  // 5. Delete report mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => {
      toast.success('Report deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['reports-list', selectedSiteId] });
      if (activeReport?.id === deleteMutation.variables) {
        setActiveReport(null);
      }
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to delete report');
    }
  });

  const handleGenerate = () => {
    if (!selectedSiteId) {
      toast.error('Please select a site first.');
      return;
    }
    generateMutation.mutate({
      site_id: selectedSiteId,
      report_type: selectedType,
    });
  };

  const handleLoadPastReport = async (reportId: string) => {
    try {
      const res = await reportsApi.get(reportId);
      setActiveReport(res.data);
      setActiveTab('view');
      toast.success(`Loaded report ${res.data.report_id}`);
    } catch (e: any) {
      toast.error('Failed to load report');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const selectedSite = sites.find(s => s.id === selectedSiteId);

  return (
    <div className="space-y-6">
      {/* ── Top Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
              <FileText className="text-primary-400" size={26} />
              Reporting Intelligence
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Reporting Agent Active
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Multi-agent intelligence synthesis aggregating Site Risk, Safety, Compliance, and Insurance findings.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-2 bg-surface-900/80 p-1 rounded-xl border border-slate-800 self-start">
          <button
            onClick={() => setActiveTab('view')}
            className={clsx(
              'px-4 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2',
              activeTab === 'view'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Layers size={14} />
            Report Viewer
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={clsx(
              'px-4 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2',
              activeTab === 'history'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Clock size={14} />
            Report History ({reportsList.length})
          </button>
        </div>
      </div>

      {/* ── Report Generation Controls ─────────────────────────────────────── */}
      <div className="card p-5 border border-slate-800/80 bg-surface-900/90 shadow-xl rounded-2xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-end">
          {/* Site Selector */}
          <div className="lg:col-span-4 space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <HardHat size={14} className="text-primary-400" />
              Select Target Construction Site
            </label>
            <select
              value={selectedSiteId}
              onChange={(e) => setSelectedSiteId(e.target.value)}
              className="w-full bg-surface-800 border border-slate-700 text-slate-100 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 transition"
              disabled={sitesLoading || generateMutation.isPending}
            >
              {sites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name} — {site.site_type || 'Commercial'} ({site.city || 'Site'})
                </option>
              ))}
            </select>
          </div>

          {/* Report Type Selector Pills */}
          <div className="lg:col-span-6 space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers size={14} className="text-primary-400" />
              Select Report Type
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {(Object.keys(REPORT_TYPE_CONFIG) as ReportType[]).map((type) => {
                const config = REPORT_TYPE_CONFIG[type];
                const Icon = config.icon;
                const isSelected = selectedType === type;
                return (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setSelectedType(type)}
                    className={clsx(
                      'p-2.5 rounded-xl border text-left transition-all flex flex-col items-start gap-1.5',
                      isSelected
                        ? 'bg-primary-500/15 border-primary-500 text-primary-300 shadow-md ring-1 ring-primary-500/50'
                        : 'bg-surface-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:border-slate-600'
                    )}
                  >
                    <Icon size={16} className={isSelected ? 'text-primary-400' : 'text-slate-400'} />
                    <span className="text-[11px] font-semibold leading-tight">{config.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Generate Button */}
          <div className="lg:col-span-2">
            <button
              onClick={handleGenerate}
              disabled={generateMutation.isPending || !selectedSiteId}
              className="w-full bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white font-semibold py-2.5 px-4 rounded-xl text-sm shadow-lg shadow-primary-600/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generateMutation.isPending ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Generate Report</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Selected Type Description */}
        <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>{REPORT_TYPE_CONFIG[selectedType].desc}</span>
          <span className="text-slate-500 text-[11px]">Aggregates live findings across 4 AI agents</span>
        </div>
      </div>

      {/* ── Main Tab Content ────────────────────────────────────────────────── */}
      {activeTab === 'view' ? (
        <AnimatePresence mode="wait">
          {activeReport ? (
            <motion.div
              key={activeReport.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="space-y-6"
            >
              {/* ── Active Report Action Bar ───────────────────────────────── */}
              <div className="card p-4 border border-slate-800 bg-surface-900/90 rounded-2xl flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    'w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-white shadow-md',
                    REPORT_TYPE_CONFIG[activeReport.report_type]?.color || 'from-primary-500 to-indigo-600'
                  )}>
                    <FileText size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-bold text-slate-100">{activeReport.title}</h2>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-primary-500/15 text-primary-400 border border-primary-500/30">
                        {activeReport.report_id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Generated on {new Date(activeReport.generated_at).toLocaleString()} by {activeReport.created_by || 'ReportingAgent'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrint}
                    className="px-3 py-1.5 rounded-xl border border-slate-700 bg-surface-800 text-slate-300 hover:text-white hover:border-slate-600 text-xs font-medium flex items-center gap-1.5 transition"
                  >
                    <Printer size={14} />
                    Print / Export
                  </button>
                  <button
                    onClick={() => handleGenerate()}
                    className="px-3 py-1.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-xs font-medium flex items-center gap-1.5 transition"
                  >
                    <RefreshCw size={14} />
                    Regenerate
                  </button>
                </div>
              </div>

              {/* ── Executive Metrics Row ──────────────────────────────────── */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="card p-3.5 border border-slate-800 bg-surface-900/60 rounded-xl">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Total Risks</div>
                  <div className="text-xl font-bold text-slate-100 mt-1">{activeReport.metrics?.total_findings ?? 0}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Across all 4 agents</div>
                </div>

                <div className="card p-3.5 border border-slate-800 bg-surface-900/60 rounded-xl">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-rose-400">Critical Issues</div>
                  <div className="text-xl font-bold text-rose-400 mt-1">{activeReport.metrics?.critical_count ?? 0}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Require immediate action</div>
                </div>

                <div className="card p-3.5 border border-slate-800 bg-surface-900/60 rounded-xl">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-amber-400">High Risks</div>
                  <div className="text-xl font-bold text-amber-400 mt-1">{activeReport.metrics?.high_count ?? 0}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Supervisory remediation</div>
                </div>

                <div className="card p-3.5 border border-slate-800 bg-surface-900/60 rounded-xl">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400">Safety Score</div>
                  <div className="text-xl font-bold text-cyan-400 mt-1">
                    {activeReport.metrics?.scores?.safety_score?.toFixed(1) ?? '85.0'}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{activeReport.metrics?.scores?.safety_level || 'Good'}</div>
                </div>

                <div className="card p-3.5 border border-slate-800 bg-surface-900/60 rounded-xl">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">Compliance</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1">
                    {activeReport.metrics?.scores?.compliance_score?.toFixed(1) ?? '85.0'}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{activeReport.metrics?.scores?.compliance_status || 'Compliant'}</div>
                </div>

                <div className="card p-3.5 border border-slate-800 bg-surface-900/60 rounded-xl">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400">Liability Bracket</div>
                  <div className="text-sm font-bold text-indigo-300 mt-1 truncate">
                    {activeReport.metrics?.scores?.estimated_liability_exposure || 'LOW ($0 - $50k)'}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Underwriting estimate</div>
                </div>
              </div>

              {/* ── Specialized Report Content Layout ───────────────────────── */}
              {activeReport.report_type === 'DAILY_SITE' && (
                <DailySiteReportView report={activeReport} />
              )}

              {activeReport.report_type === 'EXECUTIVE_SUMMARY' && (
                <ExecutiveRiskSummaryView report={activeReport} />
              )}

              {activeReport.report_type === 'AUDIT_READY' && (
                <AuditReadyReportView
                  report={activeReport}
                  filter={auditFilter}
                  onFilterChange={setAuditFilter}
                />
              )}

              {activeReport.report_type === 'PROJECT_HEALTH' && (
                <ProjectHealthReportView report={activeReport} />
              )}
            </motion.div>
          ) : (
            <div className="card p-12 text-center border border-slate-800 bg-surface-900/50 rounded-2xl">
              <div className="w-16 h-16 rounded-2xl bg-primary-500/10 border border-primary-500/20 text-primary-400 flex items-center justify-center mx-auto mb-4">
                <FileText size={32} />
              </div>
              <h3 className="text-lg font-bold text-slate-200">No Report Generated Yet</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto mt-1 mb-6">
                Select your construction site and preferred report type above, then click <strong>Generate Report</strong> to trigger multi-agent risk synthesis.
              </p>
              <button
                onClick={handleGenerate}
                disabled={generateMutation.isPending || !selectedSiteId}
                className="bg-primary-600 hover:bg-primary-500 text-white font-medium px-5 py-2.5 rounded-xl text-sm transition inline-flex items-center gap-2"
              >
                <Sparkles size={16} />
                Generate Daily Site Report
              </button>
            </div>
          )}
        </AnimatePresence>
      ) : (
        /* ── Report History Tab ──────────────────────────────────────────────── */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Clock size={18} className="text-primary-400" />
              Previously Generated Reports ({reportsList.length})
            </h2>
          </div>

          {reportsListLoading ? (
            <div className="card p-8 text-center text-slate-400">
              <RefreshCw className="animate-spin mx-auto mb-2 text-primary-400" size={24} />
              Loading report history...
            </div>
          ) : reportsList.length === 0 ? (
            <div className="card p-8 text-center text-slate-400 border border-slate-800">
              No reports generated for this site yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {reportsList.map((item) => {
                const config = REPORT_TYPE_CONFIG[item.report_type] || REPORT_TYPE_CONFIG.DAILY_SITE;
                const Icon = config.icon;
                const isSelected = activeReport?.id === item.id;
                return (
                  <div
                    key={item.id}
                    className={clsx(
                      'card p-4 border rounded-2xl transition-all flex flex-col justify-between gap-3',
                      isSelected
                        ? 'border-primary-500 bg-primary-950/20'
                        : 'border-slate-800 bg-surface-900/80 hover:border-slate-700'
                    )}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase bg-surface-800 border border-slate-700 text-slate-300">
                          {config.label}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          {new Date(item.generated_at).toLocaleDateString()}
                        </span>
                      </div>

                      <h3 className="font-bold text-sm text-slate-200 mt-2 line-clamp-1">{item.title}</h3>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                        {item.summary || 'Multi-agent risk intelligence synthesis.'}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
                      <span className="text-slate-500 font-mono text-[11px]">{item.report_id}</span>
                      <div className="flex items-center gap-1.5">
                        {user?.role && ['super_admin', 'project_manager', 'site_manager'].includes(user.role) && (
                          <button
                            onClick={() => deleteMutation.mutate(item.id)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                            title="Delete Report"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                        <button
                          onClick={() => handleLoadPastReport(item.id)}
                          className="px-3 py-1 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium text-xs flex items-center gap-1 transition"
                        >
                          <span>View</span>
                          <ArrowRight size={12} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Daily Site Report Component ─────────────────────────────────────────────
function DailySiteReportView({ report }: { report: GeneratedReport }) {
  const content = report.content || {};
  const cond = content.overall_condition || {};
  const siteInfo = content.site_information || {};
  const hazards = Array.isArray(content.site_hazards?.items) ? content.site_hazards.items : [];
  const safety = Array.isArray(content.safety_violations?.items) ? content.safety_violations.items : [];
  const ppe = Array.isArray(content.ppe_findings?.items) ? content.ppe_findings.items : [];
  const compliance = Array.isArray(content.compliance_findings?.items) ? content.compliance_findings.items : [];
  const insurance = Array.isArray(content.insurance_findings?.items) ? content.insurance_findings.items : [];
  const alerts = Array.isArray(content.important_alerts?.items) ? content.important_alerts.items : [];
  const recommendations = content.recommended_actions || [];

  return (
    <div className="space-y-6">
      {/* Site Condition Banner */}
      <div className={clsx(
        'card p-4 border rounded-2xl flex items-center justify-between gap-4',
        cond.status === 'CRITICAL' ? 'bg-rose-500/10 border-rose-500/30' :
        cond.status === 'HIGH_RISK' ? 'bg-amber-500/10 border-amber-500/30' :
        cond.status === 'SATISFACTORY' ? 'bg-blue-500/10 border-blue-500/30' :
        'bg-emerald-500/10 border-emerald-500/30'
      )}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-surface-900/60">
            {cond.status === 'CRITICAL' ? <AlertOctagon className="text-rose-400" size={24} /> :
             cond.status === 'HIGH_RISK' ? <AlertTriangle className="text-amber-400" size={24} /> :
             <CheckCircle2 className="text-emerald-400" size={24} />}
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Site Operational Condition</div>
            <div className="text-sm font-semibold text-slate-100">{cond.summary}</div>
          </div>
        </div>
        <span className={clsx(
          'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border',
          cond.status === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' :
          cond.status === 'HIGH_RISK' ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' :
          'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
        )}>
          {cond.status || 'OPTIMAL'}
        </span>
      </div>

      {/* Operational Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Site Hazards (Site Risk Agent) */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <ShieldAlert size={16} className="text-orange-400" />
              Site Hazards ({hazards.length})
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
              Site Risk Agent
            </span>
          </div>
          {hazards.length === 0 ? (
            <div className="text-xs text-slate-500 py-3 text-center">No findings available</div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {hazards.map((h: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-slate-700/60 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{h.finding_id}</span>
                    <span className={clsx('px-2 py-0.2 rounded text-[10px] font-bold uppercase border', SEVERITY_BADGE[h.severity]?.border, SEVERITY_BADGE[h.severity]?.text, SEVERITY_BADGE[h.severity]?.bg)}>
                      {h.severity}
                    </span>
                  </div>
                  <p className="text-slate-300">{h.description}</p>
                  {h.recommendation && (
                    <div className="text-slate-400 text-[11px] italic">Action: {h.recommendation}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Safety & PPE Violations (Safety Agent) */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <HardHat size={16} className="text-yellow-400" />
              Safety & PPE Violations ({safety.length})
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
              Safety Agent
            </span>
          </div>
          {safety.length === 0 ? (
            <div className="text-xs text-slate-500 py-3 text-center">No findings available</div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {safety.map((s: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-slate-700/60 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{s.finding_id}</span>
                    <span className={clsx('px-2 py-0.2 rounded text-[10px] font-bold uppercase border', SEVERITY_BADGE[s.severity]?.border, SEVERITY_BADGE[s.severity]?.text, SEVERITY_BADGE[s.severity]?.bg)}>
                      {s.severity}
                    </span>
                  </div>
                  <p className="text-slate-300">{s.description}</p>
                  {s.recommendation && (
                    <div className="text-slate-400 text-[11px] italic">Action: {s.recommendation}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Regulatory Compliance (Compliance Agent) */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <ClipboardCheck size={16} className="text-cyan-400" />
              Compliance Findings ({compliance.length})
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Compliance Agent
            </span>
          </div>
          {compliance.length === 0 ? (
            <div className="text-xs text-slate-500 py-3 text-center">No findings available</div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {compliance.map((c: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-slate-700/60 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{c.finding_id}</span>
                    <span className="text-[10px] font-mono text-cyan-400">{c.metadata?.standard_ref || 'OSHA'}</span>
                  </div>
                  <p className="text-slate-300">{c.description}</p>
                  {c.recommendation && (
                    <div className="text-slate-400 text-[11px] italic">Action: {c.recommendation}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Insurance Exposures (Insurance Agent) */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield size={16} className="text-indigo-400" />
              Insurance Exposures ({insurance.length})
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Insurance Agent
            </span>
          </div>
          {insurance.length === 0 ? (
            <div className="text-xs text-slate-500 py-3 text-center">No findings available</div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {insurance.map((i: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-slate-700/60 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{i.finding_id}</span>
                    <span className={clsx('px-2 py-0.2 rounded text-[10px] font-bold uppercase border', SEVERITY_BADGE[i.severity]?.border, SEVERITY_BADGE[i.severity]?.text, SEVERITY_BADGE[i.severity]?.bg)}>
                      {i.severity}
                    </span>
                  </div>
                  <p className="text-slate-300">{i.description}</p>
                  {i.recommendation && (
                    <div className="text-slate-400 text-[11px] italic">Action: {i.recommendation}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Prioritized Daily Recommendations */}
      <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-400" />
          Recommended Actions for Site Operations
        </h3>
        <div className="space-y-2">
          {recommendations.map((rec: string, idx: number) => (
            <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-surface-800/40 border border-slate-800 text-xs text-slate-300">
              <span className="w-5 h-5 rounded-full bg-primary-500/20 text-primary-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                {idx + 1}
              </span>
              <span>{rec}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Executive Risk Summary Component ─────────────────────────────────────────
function ExecutiveRiskSummaryView({ report }: { report: GeneratedReport }) {
  const content = report.content || {};
  const scorecard = content.risk_scorecard || {};
  const narrative = content.executive_narrative || '';
  const majorHazards = Array.isArray(content.major_hazards) ? content.major_hazards : [];
  const majorSafety = Array.isArray(content.major_safety_issues) ? content.major_safety_issues : [];
  const majorCompliance = Array.isArray(content.major_compliance_issues) ? content.major_compliance_issues : [];
  const majorInsurance = Array.isArray(content.major_insurance_exposures) ? content.major_insurance_exposures : [];
  const execRecs = content.high_priority_recommendations || [];
  const trend = content.trend_information || {};

  return (
    <div className="space-y-6">
      {/* Executive Brief Callout */}
      <div className="card p-5 border border-purple-500/30 bg-purple-950/20 rounded-2xl space-y-2">
        <div className="flex items-center gap-2 text-purple-400 font-bold text-xs uppercase tracking-wider">
          <Sparkles size={16} />
          Executive Risk Brief
        </div>
        <p className="text-sm text-slate-200 leading-relaxed font-medium">
          {narrative}
        </p>
      </div>

      {/* 4 Pillars Executive Scorecard */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Site Risk */}
        <div className="card p-4 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-400">Site Risk Posture</span>
            <span className="font-bold text-orange-400">{scorecard.site_risk?.level || 'LOW'}</span>
          </div>
          <div className="text-2xl font-black text-slate-100">{scorecard.site_risk?.score?.toFixed(1) || 0}/100</div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-orange-500 h-full rounded-full" style={{ width: `${Math.min(scorecard.site_risk?.score || 0, 100)}%` }} />
          </div>
        </div>

        {/* Safety */}
        <div className="card p-4 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-400">Safety Performance</span>
            <span className="font-bold text-cyan-400">{scorecard.safety_performance?.level || 'GOOD'}</span>
          </div>
          <div className="text-2xl font-black text-slate-100">{scorecard.safety_performance?.score?.toFixed(1) || 85}%</div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${Math.min(scorecard.safety_performance?.score || 85, 100)}%` }} />
          </div>
        </div>

        {/* Compliance */}
        <div className="card p-4 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-400">Regulatory Compliance</span>
            <span className="font-bold text-emerald-400">{scorecard.compliance_status?.status || 'COMPLIANT'}</span>
          </div>
          <div className="text-2xl font-black text-slate-100">{scorecard.compliance_status?.score?.toFixed(1) || 85}%</div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${Math.min(scorecard.compliance_status?.score || 85, 100)}%` }} />
          </div>
        </div>

        {/* Insurance */}
        <div className="card p-4 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-400">Insurance Liability</span>
            <span className="font-bold text-indigo-400">{scorecard.insurance_exposure?.level || 'LOW'}</span>
          </div>
          <div className="text-lg font-black text-slate-100 truncate">{scorecard.insurance_exposure?.bracket || 'LOW ($0 - $50k)'}</div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${Math.min(scorecard.insurance_exposure?.score || 20, 100)}%` }} />
          </div>
        </div>
      </div>

      {/* Strategic Actions for Leadership */}
      <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <TrendingUp size={16} className="text-primary-400" />
          High-Priority Executive Action Items
        </h3>
        <div className="space-y-2">
          {execRecs.map((rec: string, idx: number) => (
            <div key={idx} className="p-3 rounded-xl bg-surface-800/60 border border-slate-700/60 text-xs text-slate-200 flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0" />
              <span>{rec}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Major Exposures Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="card p-4 border border-slate-800 bg-surface-900/70 rounded-xl space-y-2">
          <span className="font-bold text-slate-300">Critical Hazards & Safety</span>
          <div className="text-slate-400">
            {majorHazards.length + majorSafety.length > 0 ? (
              `${majorHazards.length} major site hazards and ${majorSafety.length} major safety violations detected.`
            ) : (
              'No high-severity hazards or safety breaches active.'
            )}
          </div>
        </div>

        <div className="card p-4 border border-slate-800 bg-surface-900/70 rounded-xl space-y-2">
          <span className="font-bold text-slate-300">Regulatory & Underwriting Posture</span>
          <div className="text-slate-400">
            {trend.ppe_compliance_trend || 'Compliance is stable.'}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Audit-Ready Documentation Component ──────────────────────────────────────
function AuditReadyReportView({
  report,
  filter,
  onFilterChange
}: {
  report: GeneratedReport;
  filter: string;
  onFilterChange: (val: string) => void;
}) {
  const content = report.content || {};
  const auditSummary = content.audit_summary || {};
  const records = Array.isArray(content.traceable_finding_records) ? content.traceable_finding_records : [];
  const attestation = content.compliance_attestation || {};

  const filteredRecords = records.filter((r: any) => {
    if (!filter) return true;
    const f = filter.toLowerCase();
    return (
      r.finding_id?.toLowerCase().includes(f) ||
      r.standard_reference?.toLowerCase().includes(f) ||
      r.source_agent?.toLowerCase().includes(f) ||
      r.description?.toLowerCase().includes(f) ||
      r.severity?.toLowerCase().includes(f)
    );
  });

  return (
    <div className="space-y-6">
      {/* Audit Dossier Header */}
      <div className="card p-5 border border-amber-500/30 bg-amber-950/20 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
            <ClipboardCheck size={16} />
            Official Compliance & Verification Dossier
          </div>
          <div className="text-base font-bold text-slate-100 mt-1">
            Dossier ID: <span className="font-mono text-amber-300">{content.audit_dossier_id || 'AUD-ACRIP-001'}</span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Auditing Period: {content.reporting_period?.start} to {content.reporting_period?.end}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right text-xs">
            <div className="font-semibold text-slate-300">{attestation.certifying_engine}</div>
            <div className="text-[11px] text-emerald-400 font-bold">{attestation.audit_status || 'CERTIFIED_VALID'}</div>
          </div>
        </div>
      </div>

      {/* Filter and Table Search */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={filter}
            onChange={(e) => onFilterChange(e.target.value)}
            placeholder="Search standard ref, finding ID, agent..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-surface-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <span className="text-xs text-slate-500">
          Showing {filteredRecords.length} of {records.length} traceable records
        </span>
      </div>

      {/* Audit Trail Table */}
      <div className="card border border-slate-800 bg-surface-900/90 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-surface-800/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3.5">#</th>
                <th className="p-3.5">Finding ID</th>
                <th className="p-3.5">Source Agent</th>
                <th className="p-3.5">Standard Ref</th>
                <th className="p-3.5">Description</th>
                <th className="p-3.5">Severity</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Remediation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-slate-500">
                    No matching audit records found.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((item: any, idx: number) => (
                  <tr key={idx} className="hover:bg-surface-800/40 transition">
                    <td className="p-3.5 text-slate-500 font-mono">{item.entry_number || idx + 1}</td>
                    <td className="p-3.5 font-mono font-semibold text-slate-200">{item.finding_id}</td>
                    <td className="p-3.5">
                      <span className={clsx('px-2 py-0.5 rounded text-[10px] font-medium', AGENT_BADGE[item.source_agent]?.bg || 'bg-slate-800 text-slate-300')}>
                        {AGENT_BADGE[item.source_agent]?.text || item.source_agent}
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-cyan-400 text-[11px]">{item.standard_reference}</td>
                    <td className="p-3.5 max-w-xs truncate" title={item.description}>{item.description}</td>
                    <td className="p-3.5">
                      <span className={clsx('px-2 py-0.5 rounded text-[10px] font-bold border', SEVERITY_BADGE[item.severity]?.border, SEVERITY_BADGE[item.severity]?.text, SEVERITY_BADGE[item.severity]?.bg)}>
                        {item.severity}
                      </span>
                    </td>
                    <td className="p-3.5">
                      <span className="text-[10px] font-bold uppercase text-slate-400">{item.status}</span>
                    </td>
                    <td className="p-3.5 max-w-xs truncate text-slate-400 italic" title={item.recommended_action}>
                      {item.recommended_action}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Project Health Report Component ──────────────────────────────────────────
function ProjectHealthReportView({ report }: { report: GeneratedReport }) {
  const content = report.content || {};
  const health = content.composite_health || {};
  const pillars = content.four_pillars || {};
  const recs = content.cross_pillar_recommendations || [];

  return (
    <div className="space-y-6">
      {/* Composite Health Grade Banner */}
      <div className="card p-6 border border-slate-800 bg-surface-900/90 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-1 text-center md:text-left">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Composite Cross-Pillar Assessment</span>
          <h2 className="text-xl font-bold text-slate-100">{health.health_grade || 'B — SATISFACTORY'}</h2>
          <p className="text-xs text-slate-400 max-w-xl">{health.summary}</p>
        </div>

        <div className="flex items-center gap-4 bg-surface-800/80 p-4 rounded-2xl border border-slate-700/80 shrink-0">
          <div className="text-center">
            <div className="text-3xl font-black text-primary-400">{health.composite_index_pct || 78}%</div>
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">Health Index</div>
          </div>
          <div className={clsx(
            'px-3 py-1.5 rounded-xl font-bold text-xs border uppercase',
            health.health_status === 'HEALTHY' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
            health.health_status === 'MODERATE' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
            'bg-amber-500/20 text-amber-400 border-amber-500/30'
          )}>
            {health.health_status || 'MODERATE'}
          </div>
        </div>
      </div>

      {/* 4 Pillars Quadrant */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Pillar 1: Site Risk */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <ShieldAlert size={16} className="text-orange-400" />
              1. Site Risk & Physical Hazards
            </h3>
            <span className={clsx(
              'px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border',
              pillars.site_risk?.status === 'PASS' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
              pillars.site_risk?.status === 'WARN' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
              'bg-rose-500/10 text-rose-400 border-rose-500/30'
            )}>
              {pillars.site_risk?.status || 'PASS'}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Score: <strong className="text-slate-200">{pillars.site_risk?.score?.toFixed(1) || 0}/100</strong></span>
            <span>Active Hazards: <strong className="text-slate-200">{pillars.site_risk?.active_hazards || 0}</strong></span>
          </div>
          <p className="text-xs text-slate-300">{pillars.site_risk?.summary}</p>
        </div>

        {/* Pillar 2: Safety */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <HardHat size={16} className="text-yellow-400" />
              2. Worker & Behavioral Safety
            </h3>
            <span className={clsx(
              'px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border',
              pillars.safety?.status === 'PASS' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
              pillars.safety?.status === 'WARN' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
              'bg-rose-500/10 text-rose-400 border-rose-500/30'
            )}>
              {pillars.safety?.status || 'PASS'}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Score: <strong className="text-slate-200">{pillars.safety?.score?.toFixed(1) || 85}%</strong></span>
            <span>PPE Compliance: <strong className="text-slate-200">{pillars.safety?.ppe_compliance_rate || '92%'}</strong></span>
          </div>
          <p className="text-xs text-slate-300">{pillars.safety?.summary}</p>
        </div>

        {/* Pillar 3: Compliance */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <ClipboardCheck size={16} className="text-cyan-400" />
              3. Regulatory Compliance
            </h3>
            <span className={clsx(
              'px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border',
              pillars.compliance?.status === 'PASS' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
              pillars.compliance?.status === 'WARN' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
              'bg-rose-500/10 text-rose-400 border-rose-500/30'
            )}>
              {pillars.compliance?.status || 'PASS'}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Score: <strong className="text-slate-200">{pillars.compliance?.score?.toFixed(1) || 85}%</strong></span>
            <span>Overdue Inspections: <strong className="text-slate-200">{pillars.compliance?.overdue_inspections || 0}</strong></span>
          </div>
          <p className="text-xs text-slate-300">{pillars.compliance?.summary}</p>
        </div>

        {/* Pillar 4: Insurance */}
        <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield size={16} className="text-indigo-400" />
              4. Insurance & Liability Exposure
            </h3>
            <span className={clsx(
              'px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border',
              pillars.insurance?.status === 'PASS' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
              pillars.insurance?.status === 'WARN' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
              'bg-rose-500/10 text-rose-400 border-rose-500/30'
            )}>
              {pillars.insurance?.status || 'PASS'}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Exposure: <strong className="text-slate-200">{pillars.insurance?.liability_exposure || 'LOW'}</strong></span>
            <span>Active Claims: <strong className="text-slate-200">{pillars.insurance?.active_claims || 0}</strong></span>
          </div>
          <p className="text-xs text-slate-300">{pillars.insurance?.summary}</p>
        </div>
      </div>

      {/* Strategic Cross-Pillar Recommendations */}
      <div className="card p-5 border border-slate-800 bg-surface-900/80 rounded-2xl space-y-3">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Activity size={16} className="text-primary-400" />
          Strategic Multi-Pillar Action Guidance
        </h3>
        <div className="space-y-2">
          {recs.map((r: string, idx: number) => (
            <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-surface-800/40 border border-slate-800 text-xs text-slate-300">
              <Check className="text-emerald-400 shrink-0 mt-0.5" size={14} />
              <span>{r}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
