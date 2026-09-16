import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ClipboardCheck, ShieldAlert, AlertTriangle, CheckCircle2,
  Calendar, FileText, Play, RefreshCw, Plus, Filter,
  ExternalLink, Search, Clock, Lock, Sparkles, BookOpen,
  DollarSign, CheckCircle, XCircle, AlertOctagon, Printer
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import { complianceApi, sitesApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { EmptyState } from '@/components/common';
import type {
  Site, ComplianceAssessment, ComplianceRule,
  InspectionRequirement, ComplianceFinding, ComplianceReport,
  ComplianceDemoScenario, ComplianceStatus
} from '@/types';

const OPERATIONAL_ROLES = ['super_admin', 'safety_officer', 'site_manager'];
const DEMO_ROLES = ['super_admin', 'safety_officer', 'site_manager', 'project_manager'];

const STATUS_CONFIG: Record<string, { label: string; badge: string; color: string; border: string }> = {
  COMPLIANT: {
    label: 'Fully Compliant',
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    color: 'text-emerald-400',
    border: 'border-emerald-500/30'
  },
  PARTIALLY_COMPLIANT: {
    label: 'Partially Compliant',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    color: 'text-amber-400',
    border: 'border-amber-500/30'
  },
  NON_COMPLIANT: {
    label: 'Non-Compliant',
    badge: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    color: 'text-orange-400',
    border: 'border-orange-500/30'
  },
  CRITICAL_NON_COMPLIANT: {
    label: 'Critical Non-Compliant',
    badge: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    color: 'text-rose-400',
    border: 'border-rose-500/30'
  }
};

export default function CompliancePage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'findings' | 'inspections' | 'rules' | 'report'>('overview');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState<boolean>(false);

  // New Inspection Form State
  const [newInspection, setNewInspection] = useState({
    title: '',
    inspection_type: 'Statutory Weekly',
    regulatory_reference: 'OSHA 1926.451',
    responsible_role: 'safety_officer',
    due_date: new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0],
    notes: ''
  });

  const canMutate = user && OPERATIONAL_ROLES.includes(user.role);
  const canRunDemo = user && DEMO_ROLES.includes(user.role);

  // Queries
  const { data: sites = [], isLoading: sitesLoading } = useQuery<Site[]>({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  // Set default selected site
  useMemo(() => {
    if (sites.length > 0 && !selectedSiteId) {
      setSelectedSiteId(sites[0].id);
    }
  }, [sites, selectedSiteId]);

  const { data: assessmentRes, isLoading: assessmentLoading } = useQuery({
    queryKey: ['compliance-assessment', selectedSiteId],
    queryFn: () => complianceApi.getLatestAssessment(selectedSiteId),
    enabled: !!selectedSiteId,
  });
  const assessment: ComplianceAssessment | null = assessmentRes?.data || null;

  const { data: findingsRes, isLoading: findingsLoading } = useQuery({
    queryKey: ['compliance-findings', selectedSiteId],
    queryFn: () => complianceApi.listFindings(selectedSiteId),
    enabled: !!selectedSiteId,
  });
  const findings: ComplianceFinding[] = findingsRes?.data || [];

  const { data: inspectionsRes, isLoading: inspectionsLoading } = useQuery({
    queryKey: ['compliance-inspections', selectedSiteId],
    queryFn: () => complianceApi.listInspections(selectedSiteId),
    enabled: !!selectedSiteId,
  });
  const inspections: InspectionRequirement[] = inspectionsRes?.data || [];

  const { data: rulesRes } = useQuery({
    queryKey: ['compliance-rules', categoryFilter],
    queryFn: () => complianceApi.listRules(categoryFilter !== 'all' ? categoryFilter : undefined),
  });
  const rules: ComplianceRule[] = rulesRes?.data || [];

  const { data: scenariosRes } = useQuery({
    queryKey: ['compliance-demos'],
    queryFn: () => complianceApi.listDemoScenarios(),
  });
  const demoScenarios: ComplianceDemoScenario[] = scenariosRes?.data || [];

  const { data: reportRes, refetch: refetchReport } = useQuery({
    queryKey: ['compliance-report', selectedSiteId],
    queryFn: () => complianceApi.getComplianceReport(selectedSiteId),
    enabled: !!selectedSiteId && activeTab === 'report',
  });
  const report: ComplianceReport | null = reportRes?.data || null;

  // Mutations
  const auditMutation = useMutation({
    mutationFn: (isSim: boolean) => complianceApi.analyzeSite(selectedSiteId, { is_simulation: isSim }),
    onSuccess: () => {
      toast.success('Site compliance audit completed successfully');
      queryClient.invalidateQueries({ queryKey: ['compliance-assessment', selectedSiteId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-findings', selectedSiteId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-inspections', selectedSiteId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-report', selectedSiteId] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to complete compliance audit');
    }
  });

  const demoMutation = useMutation({
    mutationFn: (scenarioId: number) => complianceApi.runDemoScenario(scenarioId, selectedSiteId),
    onSuccess: (res) => {
      toast.success(`Demo Scenario loaded: ${res.data?.compliance_status}`);
      queryClient.invalidateQueries({ queryKey: ['compliance-assessment', selectedSiteId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-findings', selectedSiteId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-inspections', selectedSiteId] });
      queryClient.invalidateQueries({ queryKey: ['compliance-report', selectedSiteId] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to execute demo scenario');
    }
  });

  const createInspectionMutation = useMutation({
    mutationFn: (data: any) => complianceApi.createInspection(selectedSiteId, data),
    onSuccess: () => {
      toast.success('Statutory inspection scheduled');
      setIsScheduleModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['compliance-inspections', selectedSiteId] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to schedule inspection');
    }
  });

  // Filtered findings
  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (severityFilter !== 'all' && f.severity?.toLowerCase() !== severityFilter.toLowerCase()) {
        return false;
      }
      return true;
    });
  }, [findings, severityFilter]);

  const statusInfo = assessment
    ? STATUS_CONFIG[assessment.compliance_status] || STATUS_CONFIG.PARTIALLY_COMPLIANT
    : STATUS_CONFIG.COMPLIANT;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-surface-900/80 backdrop-blur-md p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500/20 to-emerald-500/20 border border-teal-500/30 flex items-center justify-center text-teal-400 shadow-glow-primary">
            <ClipboardCheck size={26} />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-slate-100 tracking-tight">Compliance Intelligence</h1>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
                Milestone 3 Core
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Autonomous regulatory validation, OSHA 1926 / IS 4081 / ISO 45001 monitoring, and statutory tracking.
            </p>
          </div>
        </div>

        {/* Site Selector & Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <select
              value={selectedSiteId}
              onChange={(e) => setSelectedSiteId(e.target.value)}
              className="bg-surface-800 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2 pr-8 focus:outline-none focus:border-teal-500 transition-colors"
            >
              {sites.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.site_id})
                </option>
              ))}
            </select>
          </div>

          {/* Audit Site Button */}
          {canMutate ? (
            <button
              onClick={() => auditMutation.mutate(false)}
              disabled={auditMutation.isPending || !selectedSiteId}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-teal-900/30 transition-all disabled:opacity-50"
            >
              <RefreshCw size={14} className={auditMutation.isPending ? 'animate-spin' : ''} />
              {auditMutation.isPending ? 'Auditing...' : 'Run Compliance Audit'}
            </button>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-slate-400">
              <Lock size={12} />
              <span>Read-Only</span>
            </div>
          )}

          {/* Demos Dropdown */}
          {canRunDemo && (
            <div className="relative group">
              <button className="flex items-center gap-2 px-3 py-2 bg-surface-800 hover:bg-surface-700 border border-slate-700 text-teal-400 text-xs font-medium rounded-xl transition-all">
                <Sparkles size={14} />
                <span>Demo Scenarios</span>
              </button>
              <div className="absolute right-0 mt-2 w-72 bg-surface-900 border border-slate-800 rounded-xl shadow-2xl p-2 z-50 hidden group-hover:block">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 py-1.5 border-b border-slate-800 mb-1">
                  Deterministic Compliance Scenarios
                </div>
                {demoScenarios.map((sc) => (
                  <button
                    key={sc.id}
                    onClick={() => demoMutation.mutate(sc.id)}
                    disabled={demoMutation.isPending}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface-800 transition-colors flex flex-col gap-0.5 group/item"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-200 group-hover/item:text-teal-400">
                        Demo {sc.id}: {sc.name}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                        {sc.expected_score}%
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 line-clamp-1">{sc.description}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Simulation Banner */}
      {assessment?.is_simulation && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-400 text-xs">
          <div className="flex items-center gap-2">
            <AlertOctagon size={16} />
            <span className="font-semibold uppercase tracking-wider">DEMO / SIMULATION ACTIVE</span>
            <span className="text-slate-400">— Synthetic regulatory scenario loaded for demonstration.</span>
          </div>
          <button
            onClick={() => auditMutation.mutate(false)}
            className="text-[11px] font-semibold underline hover:text-amber-300"
          >
            Re-run Live Audit
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        {[
          { id: 'overview', label: 'Executive Overview', icon: <ClipboardCheck size={14} /> },
          { id: 'findings', label: `Violations & Findings (${findings.length})`, icon: <AlertTriangle size={14} /> },
          { id: 'inspections', label: `Statutory Inspections (${inspections.length})`, icon: <Calendar size={14} /> },
          { id: 'rules', label: `Rule Repository (${rules.length})`, icon: <BookOpen size={14} /> },
          { id: 'report', label: 'Executive Report', icon: <FileText size={14} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all shrink-0',
              activeTab === tab.id
                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800/60'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Compliance Score */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Compliance Score</span>
                <span className={clsx('text-[10px] font-bold px-2 py-0.5 rounded-full border', statusInfo.badge)}>
                  {statusInfo.label}
                </span>
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className={clsx('text-3xl font-extrabold tracking-tight', statusInfo.color)}>
                  {assessment ? assessment.compliance_score.toFixed(1) : '100.0'}
                </span>
                <span className="text-xs text-slate-500">/ 100.0</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
                <div
                  className={clsx(
                    'h-full transition-all duration-500',
                    (assessment?.compliance_score || 100) >= 80 ? 'bg-emerald-500' :
                    (assessment?.compliance_score || 100) >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                  )}
                  style={{ width: `${assessment?.compliance_score || 100}%` }}
                />
              </div>
            </div>

            {/* Rules Passed */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Rules Evaluated</span>
                <CheckCircle2 size={16} className="text-emerald-400" />
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className="text-3xl font-extrabold text-slate-100">
                  {assessment ? assessment.rules_passed : rules.length}
                </span>
                <span className="text-xs text-slate-500">
                  / {assessment ? assessment.total_rules_evaluated : rules.length} passed
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                {assessment?.rules_failed || 0} statutory non-compliances detected
              </p>
            </div>

            {/* Critical & High Violations */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Critical Violations</span>
                <AlertTriangle size={16} className="text-rose-400" />
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className={clsx('text-3xl font-extrabold', (assessment?.critical_violations || 0) > 0 ? 'text-rose-400' : 'text-slate-100')}>
                  {assessment?.critical_violations || 0}
                </span>
                <span className="text-xs text-slate-500">
                  + {assessment?.high_violations || 0} high
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Triggers SafetyAlert dispatched to Safety Officer
              </p>
            </div>

            {/* Overdue Statutory Inspections */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Overdue Inspections</span>
                <Clock size={16} className="text-amber-400" />
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className={clsx('text-3xl font-extrabold', (assessment?.overdue_inspections || 0) > 0 ? 'text-amber-400' : 'text-slate-100')}>
                  {assessment?.overdue_inspections || 0}
                </span>
                <span className="text-xs text-slate-500">statutory deadlines missed</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Mandated under IS 3696 / OSHA 1926
              </p>
            </div>
          </div>

          {/* Category Scores & Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Category Scores */}
            <div className="bg-surface-900/90 border border-slate-800 p-6 rounded-2xl">
              <h3 className="text-sm font-bold text-slate-100 mb-4 flex items-center gap-2">
                <BookOpen size={16} className="text-teal-400" />
                Category Performance
              </h3>
              <div className="space-y-3.5">
                {Object.entries(assessment?.category_scores || {
                  PPE: 100,
                  SCAFFOLDING: 100,
                  EXCAVATION: 100,
                  ELECTRICAL: 100,
                  FALL_PROTECTION: 100,
                  STATUTORY_INSPECTION: 100,
                  TRAINING_CERTIFICATION: 100
                }).map(([cat, score]) => (
                  <div key={cat} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300 font-medium">{cat.replace(/_/g, ' ')}</span>
                      <span className={clsx('font-mono font-semibold', score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : 'text-rose-400')}>
                        {score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={clsx(
                          'h-full transition-all duration-500',
                          score >= 80 ? 'bg-emerald-500' : score >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                        )}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations & Action Plan */}
            <div className="lg:col-span-2 bg-surface-900/90 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100 mb-4 flex items-center gap-2">
                  <Sparkles size={16} className="text-teal-400" />
                  Agentic Compliance Action Plan
                </h3>
                <div className="space-y-2.5">
                  {(assessment?.recommendations && assessment.recommendations.length > 0) ? (
                    assessment.recommendations.map((rec, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-3 p-3 rounded-xl bg-surface-800/70 border border-slate-800"
                      >
                        <div className="w-5 h-5 rounded-full bg-teal-500/10 text-teal-400 flex items-center justify-center shrink-0 text-xs font-bold mt-0.5">
                          {idx + 1}
                        </div>
                        <p className="text-xs text-slate-200 leading-relaxed">{rec}</p>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
                      <CheckCircle2 size={18} />
                      <span>All regulatory checks passed. Maintain current audit schedules and daily toolbox talks.</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>Evaluated by ComplianceAgent v1.0</span>
                <span>Assessment ID: {assessment?.assessment_id || 'CMP-DEFAULT'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Findings */}
      {activeTab === 'findings' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Severity:</span>
              {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
                <button
                  key={sev}
                  onClick={() => setSeverityFilter(sev)}
                  className={clsx(
                    'px-3 py-1 rounded-lg text-xs font-medium capitalize transition-colors',
                    severityFilter === sev
                      ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                      : 'bg-surface-800 text-slate-400 hover:text-slate-200'
                  )}
                >
                  {sev}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-400">{filteredFindings.length} violations found</span>
          </div>

          {filteredFindings.length === 0 ? (
            <div className="bg-surface-900/60 border border-slate-800 rounded-2xl p-12 text-center">
              <CheckCircle2 size={40} className="mx-auto text-emerald-400 mb-3" />
              <h4 className="text-sm font-bold text-slate-200">No Regulatory Violations Detected</h4>
              <p className="text-xs text-slate-400 mt-1">This site complies with all active OSHA, IS, and ISO standards.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {filteredFindings.map((finding) => (
                <div
                  key={finding.finding_id}
                  className="bg-surface-900/90 border border-slate-800 hover:border-slate-700 p-5 rounded-2xl transition-all"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-3">
                      <span className={clsx(
                        'text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider',
                        finding.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                        finding.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                        'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      )}>
                        {finding.severity}
                      </span>
                      <span className="text-xs font-mono font-semibold text-teal-400">
                        {finding.standard_ref}
                      </span>
                      <span className="text-xs font-bold text-slate-200">
                        {finding.violation_type.replace(/_/g, ' ')}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs">
                      {finding.fine_exposure_estimate > 0 && (
                        <span className="font-mono text-rose-400 flex items-center gap-1 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                          <DollarSign size={12} />
                          Est. Fine: ${finding.fine_exposure_estimate.toLocaleString()}
                        </span>
                      )}
                      <span className="text-slate-500 font-mono text-[11px]">{finding.finding_id}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed mb-3">{finding.description}</p>

                  <div className="p-3 bg-surface-800/80 rounded-xl border border-slate-800/80 flex items-start gap-2">
                    <CheckCircle size={14} className="text-teal-400 shrink-0 mt-0.5" />
                    <div className="text-[11px] text-slate-300">
                      <strong className="text-teal-400">Required Mitigation: </strong>
                      {finding.recommendation}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab: Statutory Inspections */}
      {activeTab === 'inspections' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">Mandatory Statutory Inspections</h3>
              <p className="text-xs text-slate-400">Legal tracking under OSHA 1926 & IS 3696</p>
            </div>
            {canMutate && (
              <button
                onClick={() => setIsScheduleModalOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium rounded-xl transition-all"
              >
                <Plus size={14} />
                Schedule Inspection
              </button>
            )}
          </div>

          <div className="overflow-x-auto bg-surface-900/80 border border-slate-800 rounded-2xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-800 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Inspection ID / Title</th>
                  <th className="px-4 py-3">Regulatory Reference</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Responsible Role</th>
                  <th className="px-4 py-3">Due Date</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {inspections.map((insp) => (
                  <tr key={insp.requirement_id} className="hover:bg-surface-800/40 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-200">{insp.title}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{insp.requirement_id}</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-teal-400">{insp.regulatory_reference}</td>
                    <td className="px-4 py-3 text-slate-300">{insp.inspection_type}</td>
                    <td className="px-4 py-3 text-slate-300 capitalize">{insp.responsible_role.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {new Date(insp.due_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx(
                        'text-[10px] font-bold px-2 py-0.5 rounded-full border',
                        insp.is_overdue || insp.status === 'OVERDUE' ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' :
                        insp.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                        'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      )}>
                        {insp.is_overdue ? 'OVERDUE' : insp.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Rule Repository */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Category:</span>
              {['all', 'PPE', 'SCAFFOLDING', 'EXCAVATION', 'ELECTRICAL', 'FALL_PROTECTION', 'STATUTORY_INSPECTION'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={clsx(
                    'px-2.5 py-1 rounded-lg text-xs font-medium transition-colors',
                    categoryFilter === cat
                      ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                      : 'bg-surface-800 text-slate-400 hover:text-slate-200'
                  )}
                >
                  {cat.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-400">{rules.length} active standards</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rules.map((rule) => (
              <div
                key={rule.rule_id}
                className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-bold text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">
                      {rule.standard_code}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                      {rule.category}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-100 mb-1">{rule.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{rule.description}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500">
                  <span>Standard: {rule.standard_name}</span>
                  <span>Jurisdiction: {rule.jurisdiction}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Report */}
      {activeTab === 'report' && (
        <div className="bg-surface-900/90 border border-slate-800 p-8 rounded-2xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-100">Executive Statutory Compliance Report</h2>
              <p className="text-xs text-slate-400">ACRIP Compliance Intelligence Engine • OSHA 1926 / IS 4081 / ISO 45001</p>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-3 py-1.5 bg-surface-800 hover:bg-surface-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition-all"
            >
              <Printer size={14} />
              Print Report
            </button>
          </div>

          {report && (
            <div className="space-y-6">
              {/* Executive Summary Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl bg-surface-800/50 border border-slate-800">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Audit Score</span>
                  <div className="text-xl font-extrabold text-teal-400 mt-0.5">{report.compliance_score.toFixed(1)} / 100</div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Status</span>
                  <div className="text-sm font-bold text-slate-200 mt-1">{report.compliance_status}</div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Rules Passed</span>
                  <div className="text-sm font-bold text-slate-200 mt-1">{report.rules_passed} / {report.total_rules_evaluated}</div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Critical Violations</span>
                  <div className="text-sm font-bold text-rose-400 mt-1">{report.critical_violations_count}</div>
                </div>
              </div>

              {/* Actionable Findings */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Regulatory Deficiencies</h4>
                <div className="space-y-2">
                  {report.findings.map((f, i) => (
                    <div key={i} className="p-3 bg-surface-800/80 rounded-xl border border-slate-800 text-xs flex flex-col gap-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-200">{f.standard_ref} — {f.violation_type}</span>
                        <span className="text-[10px] font-bold text-rose-400 uppercase">{f.severity}</span>
                      </div>
                      <p className="text-slate-400">{f.description}</p>
                      <div className="text-teal-400 text-[11px] mt-1 font-medium">Fix: {f.recommendation}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-800 text-[11px] text-slate-400 italic">
                {report.disclaimer}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Schedule Inspection Modal */}
      {isScheduleModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Calendar size={16} className="text-teal-400" />
                Schedule Statutory Inspection
              </h3>
              <button
                onClick={() => setIsScheduleModalOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-300 font-medium">Title</label>
                <input
                  type="text"
                  value={newInspection.title}
                  onChange={(e) => setNewInspection({ ...newInspection, title: e.target.value })}
                  placeholder="e.g. Scaffolding Weekly Load Inspection"
                  className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium">Standard Reference</label>
                <input
                  type="text"
                  value={newInspection.regulatory_reference}
                  onChange={(e) => setNewInspection({ ...newInspection, regulatory_reference: e.target.value })}
                  placeholder="e.g. OSHA 1926.451 / IS 3696"
                  className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-300 font-medium">Type</label>
                  <select
                    value={newInspection.inspection_type}
                    onChange={(e) => setNewInspection({ ...newInspection, inspection_type: e.target.value })}
                    className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                  >
                    <option value="Statutory Weekly">Statutory Weekly</option>
                    <option value="Statutory Monthly">Statutory Monthly</option>
                    <option value="Equipment Pre-Use">Equipment Pre-Use</option>
                    <option value="Excavation Daily">Excavation Daily</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium">Due Date</label>
                  <input
                    type="date"
                    value={newInspection.due_date}
                    onChange={(e) => setNewInspection({ ...newInspection, due_date: e.target.value })}
                    className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium">Responsible Role</label>
                <select
                  value={newInspection.responsible_role}
                  onChange={(e) => setNewInspection({ ...newInspection, responsible_role: e.target.value })}
                  className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                >
                  <option value="safety_officer">Safety Officer</option>
                  <option value="site_manager">Site Manager</option>
                  <option value="certified_inspector">Certified External Inspector</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setIsScheduleModalOpen(false)}
                className="px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={() => createInspectionMutation.mutate(newInspection)}
                disabled={createInspectionMutation.isPending || !newInspection.title}
                className="px-4 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-xl disabled:opacity-50 transition-all"
              >
                {createInspectionMutation.isPending ? 'Scheduling...' : 'Save Inspection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
