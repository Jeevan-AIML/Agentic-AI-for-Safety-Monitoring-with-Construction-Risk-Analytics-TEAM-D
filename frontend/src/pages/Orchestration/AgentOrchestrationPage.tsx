import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Cpu, Play, RefreshCw, AlertTriangle, ExternalLink,
  Clock, Shield, HardHat, ClipboardCheck, FileText, CheckCircle2,
  Layers, ArrowRight, Zap, CheckCircle, AlertOctagon, FastForward
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import { orchestrationApi, sitesApi } from '@/services/api';
import { PageLoader, EmptyState } from '@/components/common';
import { formatRelativeTime } from '@/utils/display';
import type {
  Site,
  OrchestrationRunResponse,
  OrchestrationMode
} from '@/types';

export default function AgentOrchestrationPage() {
  const queryClient = useQueryClient();
  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [orchMode, setOrchMode] = useState<OrchestrationMode>('FULL_ANALYSIS');
  const [selectedDomainAgents, setSelectedDomainAgents] = useState<string[]>([
    'site_risk',
    'safety',
    'compliance',
    'insurance',
  ]);
  const [generateReport, setGenerateReport] = useState<boolean>(true);
  const [activeRunResult, setActiveRunResult] = useState<OrchestrationRunResponse | null>(null);

  // Fetch available sites
  const { data: sites = [], isLoading: sitesLoading } = useQuery<Site[]>({
    queryKey: ['sites-list'],
    queryFn: () => sitesApi.list().then((res) => res.data),
    staleTime: 60000,
  });

  const activeSiteId = selectedSiteId || (sites.length > 0 ? sites[0].id : '');

  // Fetch latest orchestration run for active site
  const { data: latestOrchestration, isLoading: orchLoading, refetch: refetchLatest } = useQuery<OrchestrationRunResponse>({
    queryKey: ['orchestration-latest', activeSiteId],
    queryFn: () => orchestrationApi.getLatest(activeSiteId).then((res) => res.data),
    enabled: !!activeSiteId,
    staleTime: 10000,
  });

  // Orchestration run mutation
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
        id: 'orch-page-run-toast',
      });
    },
    onSuccess: (res) => {
      const runData: OrchestrationRunResponse = res.data;
      setActiveRunResult(runData);
      if (runData.status === 'COMPLETED') {
        toast.success(`Orchestration completed successfully in ${runData.duration_ms}ms!`, { id: 'orch-page-run-toast' });
      } else if (runData.status === 'PARTIAL') {
        toast('Orchestration completed with partial agent warnings.', { id: 'orch-page-run-toast', icon: '⚠️' });
      } else {
        toast.error(`Orchestration failed: ${runData.errors?.[0] || 'Unknown error'}`, { id: 'orch-page-run-toast' });
      }
      queryClient.invalidateQueries({ queryKey: ['executive-dashboard', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['orchestration-latest', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['risk-intelligence', activeSiteId] });
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Agent orchestration failed', { id: 'orch-page-run-toast' });
    },
  });

  if (sitesLoading) {
    return <PageLoader />;
  }

  const currentRun = activeRunResult || latestOrchestration;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 pb-12">
      {/* Header */}
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="badge bg-primary-500/20 text-primary-300 border border-primary-500/30">
              Autonomous Multi-Agent System
            </span>
            <span className="badge bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Live Engine
            </span>
          </div>
          <h1 className="page-title flex items-center gap-2.5">
            <Cpu className="text-primary-400" size={24} />
            Agent Orchestration Center
          </h1>
          <p className="page-subtitle">
            Coordinated pipeline execution across Level 1 Domain Agents, Level 2 Risk Intelligence Engine, and Level 3 Reporting Agent
          </p>
        </div>

        {/* Site Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="orch-site-select" className="text-xs text-slate-400 font-medium">
            Target Site:
          </label>
          <select
            id="orch-site-select"
            value={activeSiteId}
            onChange={(e) => {
              setSelectedSiteId(e.target.value);
              setActiveRunResult(null);
            }}
            className="input text-xs py-1.5 px-3 bg-surface-800 border-slate-700 text-slate-200 rounded-lg min-w-[200px]"
          >
            {sites.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Execution Controls Card */}
      <div className="card p-6 bg-surface-900 border border-slate-800 space-y-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
          <span>Pipeline Configuration</span>
          <span className="text-xs font-normal text-slate-500 font-mono">Sequential Multi-Stage Execution</span>
        </h2>

        {/* Execution Mode Selection */}
        <div>
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
            Execution Mode
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
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
                  'p-4 rounded-xl border text-left transition-all',
                  orchMode === item.mode
                    ? 'bg-primary-500/10 border-primary-500/60 ring-1 ring-primary-500/40 text-slate-100 shadow-md'
                    : 'bg-surface-850/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                )}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-bold text-slate-200">{item.title}</span>
                  <span
                    className={clsx(
                      'text-[10px] px-1.5 py-0.5 rounded font-medium',
                      orchMode === item.mode ? 'bg-primary-500/20 text-primary-300' : 'bg-slate-800 text-slate-500'
                    )}
                  >
                    {item.badge}
                  </span>
                </div>
                <p className="text-xs leading-relaxed opacity-80">{item.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Targeted Domain Agents Checkboxes */}
        {orchMode === 'TARGETED_ANALYSIS' && (
          <div className="p-4 bg-surface-850 border border-slate-800 rounded-xl space-y-2.5">
            <span className="text-xs font-semibold text-slate-300">Select Domain Agents to Execute:</span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
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
                      'flex items-center gap-2.5 p-3 rounded-lg border text-xs cursor-pointer select-none transition-colors',
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

        {/* Options & Execute Action */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800/80">
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
            className="btn-primary text-sm px-6 py-2.5 flex items-center gap-2 bg-gradient-to-r from-primary-600 via-indigo-600 to-primary-700 hover:from-primary-500 hover:to-indigo-500 shadow-lg shadow-primary-500/25 disabled:opacity-50"
          >
            {orchestrationMutation.isPending ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                <span>Orchestrating Workflow...</span>
              </>
            ) : (
              <>
                <Play size={16} className="fill-current" />
                <span>Execute Pipeline Now</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live Pipeline Visualizer / Run Status */}
      {currentRun ? (
        <div className="card p-6 bg-surface-900 border border-slate-800 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <span className="font-mono text-slate-300 text-sm font-semibold">{currentRun.execution_id}</span>
              <span
                className={clsx(
                  'badge font-bold uppercase text-[10px]',
                  currentRun.status === 'COMPLETED'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : currentRun.status === 'PARTIAL'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-red-500/20 text-red-300 border border-red-500/30'
                )}
              >
                {currentRun.status}
              </span>
              <span className="text-xs text-slate-400">Mode: <strong className="text-slate-200">{currentRun.execution_mode}</strong></span>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span>Duration: <strong className="text-slate-200">{currentRun.duration_ms} ms</strong></span>
              <span>•</span>
              <span>Started: <strong className="text-slate-200">{formatRelativeTime(currentRun.started_at)}</strong></span>
            </div>
          </div>

          {/* 3 Stages Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Level 1: Domain Agents */}
            <div className="p-4 bg-surface-850 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-mono font-bold">1</span>
                  Level 1: Domain Agents
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Parallel</span>
              </div>

              <div className="space-y-2">
                {['site_risk', 'safety', 'compliance', 'insurance'].map((name) => {
                  const st = currentRun.agent_statuses?.[name];
                  if (!st) return null;
                  return (
                    <div
                      key={name}
                      className="p-2.5 bg-surface-800/90 border border-slate-700/60 rounded-lg text-xs space-y-1.5"
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
                        <p className="text-[11px] text-slate-400 leading-tight" title={st.message}>
                          {st.message}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Level 2: Risk Intelligence Engine */}
            <div className="p-4 bg-surface-850 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-mono font-bold">2</span>
                  Level 2: Risk Intelligence
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Synthesis</span>
              </div>

              {currentRun.agent_statuses?.['risk_intelligence'] ? (
                <div className="p-3 bg-surface-800/90 border border-slate-700/60 rounded-lg text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">Synthesis Engine</span>
                    <span
                      className={clsx(
                        'text-[10px] px-1.5 py-0.5 rounded font-bold uppercase',
                        currentRun.agent_statuses['risk_intelligence'].status === 'COMPLETED'
                          ? 'bg-emerald-500/15 text-emerald-300'
                          : 'bg-slate-700 text-slate-400'
                      )}
                    >
                      {currentRun.agent_statuses['risk_intelligence'].status}
                    </span>
                  </div>
                  {currentRun.risk_intelligence_id && (
                    <div className="text-[11px] font-mono text-purple-300 bg-purple-500/10 px-2 py-1 rounded border border-purple-500/20 truncate">
                      ID: {currentRun.risk_intelligence_id}
                    </div>
                  )}
                  {currentRun.agent_statuses['risk_intelligence'].message && (
                    <p className="text-[11px] text-slate-400 leading-tight">
                      {currentRun.agent_statuses['risk_intelligence'].message}
                    </p>
                  )}
                  <Link
                    to="/executive-dashboard"
                    className="inline-flex items-center gap-1 text-primary-400 hover:text-primary-300 font-medium text-xs pt-1"
                  >
                    View Executive Dashboard <ArrowRight size={12} />
                  </Link>
                </div>
              ) : (
                <div className="p-6 text-center text-slate-500 text-xs">
                  Stage not scheduled in this mode
                </div>
              )}
            </div>

            {/* Level 3: Reporting Intelligence */}
            <div className="p-4 bg-surface-850 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-mono font-bold">3</span>
                  Level 3: Reporting Agent
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Audit Doc</span>
              </div>

              {currentRun.agent_statuses?.['reporting'] ? (
                <div className="p-3 bg-surface-800/90 border border-slate-700/60 rounded-lg text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">Executive Summary</span>
                    <span
                      className={clsx(
                        'text-[10px] px-1.5 py-0.5 rounded font-bold uppercase',
                        currentRun.agent_statuses['reporting'].status === 'COMPLETED'
                          ? 'bg-emerald-500/15 text-emerald-300'
                          : 'bg-slate-700 text-slate-400'
                      )}
                    >
                      {currentRun.agent_statuses['reporting'].status}
                    </span>
                  </div>
                  {currentRun.report_id && (
                    <div className="flex items-center justify-between bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
                      <span className="text-[11px] font-mono text-emerald-300 truncate">
                        ID: {currentRun.report_id}
                      </span>
                      <Link
                        to="/reports"
                        className="text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium ml-2 shrink-0"
                      >
                        View <ExternalLink size={11} />
                      </Link>
                    </div>
                  )}
                  {currentRun.agent_statuses['reporting'].message && (
                    <p className="text-[11px] text-slate-400 leading-tight">
                      {currentRun.agent_statuses['reporting'].message}
                    </p>
                  )}
                </div>
              ) : (
                <div className="p-6 text-center text-slate-500 text-xs">
                  Reporting was not requested
                </div>
              )}
            </div>
          </div>

          {/* Warnings & Errors */}
          {currentRun.warnings && currentRun.warnings.length > 0 && (
            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300 space-y-1.5">
              <div className="font-semibold flex items-center gap-2 text-amber-200">
                <AlertTriangle size={15} /> Pipeline Warnings:
              </div>
              <ul className="list-disc list-inside space-y-1 text-amber-200/90 text-xs">
                {currentRun.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <EmptyState
          icon={<Cpu size={36} className="text-slate-500" />}
          title="No Recent Orchestration Run"
          description="Click 'Execute Pipeline Now' above to coordinate all agents for the active site."
        />
      )}
    </motion.div>
  );
}
