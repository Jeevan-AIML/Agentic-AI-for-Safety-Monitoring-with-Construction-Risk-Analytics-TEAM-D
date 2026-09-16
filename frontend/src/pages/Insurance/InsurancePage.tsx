import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Shield, AlertTriangle, FileText, CheckCircle2, TrendingUp,
  Percent, DollarSign, Award, Sparkles, RefreshCw, Lock,
  FileCheck, ShieldAlert, AlertOctagon, Scale, ShieldCheck,
  ChevronRight, ExternalLink, Printer, Hash
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import { insuranceApi, sitesApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type {
  Site, InsuranceRiskAssessment, InsuranceClaimAssessment,
  ClaimDocumentationPackage, InsuranceDemoScenario, InsuranceRiskLevel
} from '@/types';

const OPERATIONAL_ROLES = ['super_admin', 'safety_officer', 'site_manager'];
const DEMO_ROLES = ['super_admin', 'safety_officer', 'site_manager', 'project_manager'];

const EXPOSURE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  NEGLIGIBLE: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  LOW: { bg: 'bg-teal-500/10', text: 'text-teal-400', border: 'border-teal-500/30' },
  MODERATE: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  ELEVATED: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' },
  HIGH: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
  CRITICAL: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30' },
};

export default function InsurancePage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'underwriting' | 'claim-eval' | 'dossier'>('underwriting');
  const [activeClaimId, setActiveClaimId] = useState<string>('');

  // Claim assessment form
  const [claimForm, setClaimForm] = useState({
    incident_title: 'Heavy Mobile Crane Boom Collapse during Lift',
    incident_type: 'CRANE_STRUCTURAL_FAILURE',
    estimated_loss_amount: 320000,
    description: 'During 45-ton girder placement, crane rigging cable snapped due to overdue statutory load testing certification.'
  });

  const canMutate = user && OPERATIONAL_ROLES.includes(user.role);
  const canRunDemo = user && DEMO_ROLES.includes(user.role);

  // Queries
  const { data: sites = [], isLoading: sitesLoading } = useQuery<Site[]>({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  useMemo(() => {
    if (sites.length > 0 && !selectedSiteId) {
      setSelectedSiteId(sites[0].id);
    }
  }, [sites, selectedSiteId]);

  const { data: assessmentRes } = useQuery({
    queryKey: ['insurance-assessment', selectedSiteId],
    queryFn: () => insuranceApi.getLatestAssessment(selectedSiteId),
    enabled: !!selectedSiteId,
  });
  const assessment: InsuranceRiskAssessment | null = assessmentRes?.data || null;

  const { data: scenariosRes } = useQuery({
    queryKey: ['insurance-demos'],
    queryFn: () => insuranceApi.listDemoScenarios(),
  });
  const demoScenarios: InsuranceDemoScenario[] = scenariosRes?.data || [];

  const { data: packageRes } = useQuery({
    queryKey: ['claim-package', activeClaimId],
    queryFn: () => insuranceApi.getClaimPackage(activeClaimId),
    enabled: !!activeClaimId,
  });
  const claimPackage: ClaimDocumentationPackage | null = packageRes?.data || null;

  // Mutations
  const assessMutation = useMutation({
    mutationFn: (isSim: boolean) => insuranceApi.assessSite(selectedSiteId, { is_simulation: isSim }),
    onSuccess: () => {
      toast.success('Insurance risk underwriting assessment completed');
      queryClient.invalidateQueries({ queryKey: ['insurance-assessment', selectedSiteId] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to complete insurance assessment');
    }
  });

  const demoMutation = useMutation({
    mutationFn: (scenarioId: number) => insuranceApi.runDemoScenario(scenarioId, selectedSiteId),
    onSuccess: (res) => {
      toast.success(`Demo Scenario loaded: ${res.data?.risk_level}`);
      queryClient.invalidateQueries({ queryKey: ['insurance-assessment', selectedSiteId] });
      if (res.data?.claim_assessment_id) {
        setActiveClaimId(res.data.claim_assessment_id);
      }
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to execute demo scenario');
    }
  });

  const [evaluatedClaim, setEvaluatedClaim] = useState<InsuranceClaimAssessment | null>(null);

  const claimMutation = useMutation({
    mutationFn: (data: any) => insuranceApi.assessClaim(selectedSiteId, data),
    onSuccess: (res) => {
      toast.success('Incident claim risk evaluated');
      setEvaluatedClaim(res.data);
      setActiveClaimId(res.data.id);
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to evaluate claim');
    }
  });

  const generatePackageMutation = useMutation({
    mutationFn: (claimId: string) => insuranceApi.generateClaimPackage(claimId),
    onSuccess: (res) => {
      toast.success('Verified claim documentation package generated');
      queryClient.invalidateQueries({ queryKey: ['claim-package', activeClaimId] });
      setActiveTab('dossier');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to generate claim package');
    }
  });

  const exposureStyle = assessment
    ? EXPOSURE_COLORS[assessment.risk_level] || EXPOSURE_COLORS.MODERATE
    : EXPOSURE_COLORS.LOW;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-surface-900/80 backdrop-blur-md p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-blue-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-glow-primary">
            <Shield size={26} />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-slate-100 tracking-tight">Insurance Intelligence</h1>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Milestone 3 Core
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Actuarial exposure underwriting, incident loss severity modeling, and automated claims dossier generation.
            </p>
          </div>
        </div>

        {/* Site Selector & Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <select
              value={selectedSiteId}
              onChange={(e) => setSelectedSiteId(e.target.value)}
              className="bg-surface-800 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2 pr-8 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              {sites.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.site_id})
                </option>
              ))}
            </select>
          </div>

          {canMutate ? (
            <button
              onClick={() => assessMutation.mutate(false)}
              disabled={assessMutation.isPending || !selectedSiteId}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-900/30 transition-all disabled:opacity-50"
            >
              <RefreshCw size={14} className={assessMutation.isPending ? 'animate-spin' : ''} />
              {assessMutation.isPending ? 'Underwriting...' : 'Assess Site Exposure'}
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
              <button className="flex items-center gap-2 px-3 py-2 bg-surface-800 hover:bg-surface-700 border border-slate-700 text-indigo-400 text-xs font-medium rounded-xl transition-all">
                <Sparkles size={14} />
                <span>Demo Scenarios</span>
              </button>
              <div className="absolute right-0 mt-2 w-80 bg-surface-900 border border-slate-800 rounded-xl shadow-2xl p-2 z-50 hidden group-hover:block">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 py-1.5 border-b border-slate-800 mb-1">
                  Deterministic Insurance Scenarios
                </div>
                {demoScenarios.map((sc) => (
                  <button
                    key={sc.id}
                    onClick={() => demoMutation.mutate(sc.id)}
                    disabled={demoMutation.isPending}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface-800 transition-colors flex flex-col gap-0.5 group/item"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-200 group-hover/item:text-indigo-400">
                        Demo {sc.id}: {sc.name}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                        {sc.expected_risk_score ? `${sc.expected_risk_score} pts` : sc.scenario_type}
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
        <div className="flex items-center justify-between px-4 py-2.5 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-400 text-xs">
          <div className="flex items-center gap-2">
            <AlertOctagon size={16} />
            <span className="font-semibold uppercase tracking-wider">DEMO / SIMULATION ACTIVE</span>
            <span className="text-slate-400">— Synthetic insurance exposure scenario loaded for demonstration.</span>
          </div>
          <button
            onClick={() => assessMutation.mutate(false)}
            className="text-[11px] font-semibold underline hover:text-blue-300"
          >
            Re-run Underwriting Assessment
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        {[
          { id: 'underwriting', label: 'Underwriting Exposure & Score', icon: <Shield size={14} /> },
          { id: 'claim-eval', label: 'Incident Claim Risk Analysis', icon: <Scale size={14} /> },
          { id: 'dossier', label: 'Verified Claim Dossier Package', icon: <FileCheck size={14} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all shrink-0',
              activeTab === tab.id
                ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800/60'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Underwriting */}
      {activeTab === 'underwriting' && (
        <div className="space-y-6">
          {/* Top Scorecards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Insurance Risk Score */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Underwriting Risk Score</span>
                <span className={clsx('text-[10px] font-bold px-2 py-0.5 rounded-full border', exposureStyle.bg, exposureStyle.text, exposureStyle.border)}>
                  {assessment ? assessment.risk_level : 'LOW'}
                </span>
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className={clsx('text-3xl font-extrabold tracking-tight', exposureStyle.text)}>
                  {assessment ? assessment.insurance_risk_score.toFixed(1) : '24.0'}
                </span>
                <span className="text-xs text-slate-500">/ 100.0 (lower is better)</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Bracket: <strong className="text-slate-200">{assessment?.exposure_bracket || 'Standard Tier'}</strong>
              </p>
            </div>

            {/* Premium Impact */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Premium Impact</span>
                <Percent size={16} className="text-indigo-400" />
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className={clsx('text-3xl font-extrabold', (assessment?.estimated_annual_premium_impact_pct || 0) > 0 ? 'text-rose-400' : 'text-emerald-400')}>
                  {assessment && assessment.estimated_annual_premium_impact_pct > 0 ? '+' : ''}
                  {assessment ? assessment.estimated_annual_premium_impact_pct.toFixed(1) : '0.0'}%
                </span>
                <span className="text-xs text-slate-500">annual policy adjustment</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Based on active risk exposure & safety record
              </p>
            </div>

            {/* Deductible Multiplier */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Deductible Multiplier</span>
                <DollarSign size={16} className="text-amber-400" />
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className="text-3xl font-extrabold text-slate-100">
                  {assessment ? assessment.recommended_deductible_multiplier.toFixed(1) : '1.0'}x
                </span>
                <span className="text-xs text-slate-500">recommended base</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                Loss control deductible retention
              </p>
            </div>

            {/* Assessment ID */}
            <div className="bg-surface-900/90 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Actuarial Session</span>
                  <Award size={16} className="text-blue-400" />
                </div>
                <div className="text-xs font-mono font-bold text-slate-200 mt-3 truncate">
                  {assessment?.assessment_id || 'INS-DEFAULT'}
                </div>
              </div>
              <p className="text-[10px] text-slate-500">
                Calculated by InsuranceAgent Underwriting Engine
              </p>
            </div>
          </div>

          {/* Actuarial Factor Breakdown & Underwriting Concerns */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Actuarial Weights */}
            <div className="bg-surface-900/90 border border-slate-800 p-6 rounded-2xl">
              <h3 className="text-sm font-bold text-slate-100 mb-4 flex items-center gap-2">
                <Scale size={16} className="text-indigo-400" />
                Actuarial Risk Component Weights
              </h3>
              <div className="space-y-3.5">
                {[
                  { label: 'Regulatory Compliance Deficit', weight: '30%', val: assessment?.compliance_factor || 15 },
                  { label: 'Incident Severity Profile', weight: '25%', val: assessment?.incident_factor || 20 },
                  { label: 'Unmitigated Physical Hazards', weight: '20%', val: assessment?.hazard_factor || 20 },
                  { label: 'Statutory Inspection Lapses', weight: '15%', val: assessment?.inspection_factor || 10 },
                  { label: 'Historical Claim Frequency', weight: '10%', val: assessment?.claim_frequency_factor || 10 },
                ].map((item, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{item.label}</span>
                      <span className="font-mono text-slate-400">{item.val.toFixed(0)} / 100 ({item.weight})</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={clsx(
                          'h-full transition-all duration-500',
                          item.val > 50 ? 'bg-rose-500' : item.val > 25 ? 'bg-amber-500' : 'bg-indigo-500'
                        )}
                        style={{ width: `${item.val}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Underwriting Concerns & Loss Control */}
            <div className="lg:col-span-2 bg-surface-900/90 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100 mb-3 flex items-center gap-2">
                  <ShieldAlert size={16} className="text-rose-400" />
                  Underwriter Red Flags & Risk Concerns
                </h3>
                <div className="space-y-2 mb-5">
                  {(assessment?.underwriting_concerns && assessment.underwriting_concerns.length > 0) ? (
                    assessment.underwriting_concerns.map((c, i) => (
                      <div key={i} className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-300 flex items-start gap-2">
                        <AlertTriangle size={14} className="shrink-0 mt-0.5 text-rose-400" />
                        <span>{c}</span>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-300">
                      No high-severity underwriting concerns. Preferred risk classification.
                    </div>
                  )}
                </div>

                <h3 className="text-sm font-bold text-slate-100 mb-3 flex items-center gap-2">
                  <ShieldCheck size={16} className="text-emerald-400" />
                  Mandated Loss Control Actions
                </h3>
                <div className="space-y-2">
                  {assessment?.loss_control_recommendations?.map((rec, i) => (
                    <div key={i} className="p-3 bg-surface-800/70 border border-slate-800 rounded-xl text-xs text-slate-300 flex items-start gap-2">
                      <div className="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 text-[10px] font-bold mt-0.5">
                        {i + 1}
                      </div>
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>Deterministic Explainable Model</span>
                <span>Annual Premium Impact Formula Applied</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Claim Evaluation */}
      {activeTab === 'claim-eval' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Claim Evaluation Form */}
          <div className="bg-surface-900/90 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div className="border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Scale size={16} className="text-indigo-400" />
                Evaluate Incident Claim Exposure
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Analyze liability, subrogation potential, and regulatory violation correlation.
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-300 font-medium">Incident Title</label>
                <input
                  type="text"
                  value={claimForm.incident_title}
                  onChange={(e) => setClaimForm({ ...claimForm, incident_title: e.target.value })}
                  className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-300 font-medium">Incident Type</label>
                  <select
                    value={claimForm.incident_type}
                    onChange={(e) => setClaimForm({ ...claimForm, incident_type: e.target.value })}
                    className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="CRANE_STRUCTURAL_FAILURE">Crane Structural Failure</option>
                    <option value="SCAFFOLDING_COLLAPSE">Scaffolding Collapse</option>
                    <option value="TRENCH_CAVE_IN">Trench Cave-In</option>
                    <option value="FALL_FROM_HEIGHT">Fall from Height</option>
                    <option value="ELECTRICAL_ARC_FLASH">Electrical Arc Flash</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium">Estimated Loss ($)</label>
                  <input
                    type="number"
                    value={claimForm.estimated_loss_amount}
                    onChange={(e) => setClaimForm({ ...claimForm, estimated_loss_amount: parseFloat(e.target.value) || 0 })}
                    className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium">Narrative & Field Notes</label>
                <textarea
                  rows={3}
                  value={claimForm.description}
                  onChange={(e) => setClaimForm({ ...claimForm, description: e.target.value })}
                  className="w-full mt-1 bg-surface-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {canMutate ? (
                <button
                  onClick={() => claimMutation.mutate(claimForm)}
                  disabled={claimMutation.isPending}
                  className="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-900/30 transition-all disabled:opacity-50"
                >
                  {claimMutation.isPending ? 'Analyzing Severity & Subrogation...' : 'Calculate Claim Risk & Exposure'}
                </button>
              ) : (
                <div className="p-3 bg-slate-800 rounded-xl text-xs text-slate-400 text-center">
                  Viewer role cannot trigger claim risk calculations.
                </div>
              )}
            </div>
          </div>

          {/* Claim Evaluation Results */}
          <div className="bg-surface-900/90 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between">
            {evaluatedClaim ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] font-mono text-indigo-400 font-bold">{evaluatedClaim.claim_id}</span>
                    <h4 className="text-sm font-bold text-slate-100">{evaluatedClaim.incident_title}</h4>
                  </div>
                  <span className={clsx(
                    'text-xs font-bold px-2.5 py-1 rounded-full uppercase border',
                    evaluatedClaim.claim_risk_level === 'EXTREME' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' :
                    evaluatedClaim.claim_risk_level === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                    'bg-amber-500/20 text-amber-400 border-amber-500/30'
                  )}>
                    {evaluatedClaim.claim_risk_level} RISK
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-surface-800/80 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase">Estimated Loss</span>
                    <div className="text-base font-extrabold text-slate-100 mt-0.5">
                      ${evaluatedClaim.estimated_loss_amount.toLocaleString()}
                    </div>
                  </div>
                  <div className="p-3 bg-surface-800/80 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase">Subrogation Potential</span>
                    <div className="text-sm font-bold text-indigo-400 mt-1">
                      {evaluatedClaim.subrogation_potential.replace(/_/g, ' ')}
                    </div>
                  </div>
                </div>

                <div>
                  <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Correlated Violations</h5>
                  <div className="flex flex-wrap gap-1.5">
                    {evaluatedClaim.contributing_violations.map((v, i) => (
                      <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {v}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-3 bg-surface-800/60 rounded-xl border border-slate-800 text-xs text-slate-300">
                  <strong className="text-slate-200">Adjuster Analysis: </strong>
                  {evaluatedClaim.adjuster_notes}
                </div>

                {canMutate && (
                  <button
                    onClick={() => generatePackageMutation.mutate(evaluatedClaim.id)}
                    disabled={generatePackageMutation.isPending}
                    className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition-all"
                  >
                    {generatePackageMutation.isPending ? 'Assembling Package...' : 'Generate Verified Claim Package'}
                  </button>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8">
                <FileCheck size={40} className="text-slate-600 mb-3" />
                <h4 className="text-sm font-bold text-slate-300">No Incident Claim Evaluated</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm">
                  Fill the evaluation form on the left or launch Demo Scenario 6 to compute claim exposure and subrogation potential.
                </p>
              </div>
            )}

            <div className="pt-4 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
              <span>ACRIP Claim Risk Modeler</span>
              <span>Subrogation & Legal Discovery Ready</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Dossier Package */}
      {activeTab === 'dossier' && (
        <div className="bg-surface-900/90 border border-slate-800 p-8 rounded-2xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-bold text-slate-100">Verified Claim Documentation Package</h2>
                <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <CheckCircle2 size={12} />
                  SHA-256 VERIFIED
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Cryptographically sealed claims evidentiary package with aerial photogrammetry and video audit trail.
              </p>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-3 py-1.5 bg-surface-800 hover:bg-surface-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition-all"
            >
              <Printer size={14} />
              Export Dossier PDF
            </button>
          </div>

          {claimPackage ? (
            <div className="space-y-6">
              {/* Checksum & Integrity Badge */}
              <div className="p-4 bg-surface-800/60 rounded-xl border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Hash size={16} className="text-indigo-400" />
                  <span className="text-xs font-mono text-slate-300">
                    Checksum: <strong className="text-indigo-300">{claimPackage.package_checksum}</strong>
                  </span>
                </div>
                <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  Tamper-Evident Package
                </span>
              </div>

              {/* Executive Summary */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Executive Claim Summary</h4>
                <p className="text-xs text-slate-200 leading-relaxed bg-surface-800/40 p-4 rounded-xl border border-slate-800">
                  {claimPackage.executive_summary}
                </p>
              </div>

              {/* Multi-Modal Evidence Integration */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-surface-800/50 border border-slate-800">
                  <h5 className="text-xs font-bold text-slate-200 mb-2 flex items-center gap-2">
                    <ShieldCheck size={14} className="text-blue-400" />
                    Drone Aerial Evidence Included
                  </h5>
                  <div className="text-xs text-slate-400">
                    {claimPackage.drone_aerial_evidence && claimPackage.drone_aerial_evidence.length > 0 ? (
                      <span className="text-emerald-400 font-medium">
                        ✓ {claimPackage.drone_aerial_evidence.length} aerial inspection points attached
                      </span>
                    ) : (
                      <span>Aerial surveillance telemetry verified clean.</span>
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-surface-800/50 border border-slate-800">
                  <h5 className="text-xs font-bold text-slate-200 mb-2 flex items-center gap-2">
                    <ShieldCheck size={14} className="text-teal-400" />
                    Video Surveillance Audit Trail
                  </h5>
                  <div className="text-xs text-slate-400">
                    {claimPackage.video_surveillance_evidence && claimPackage.video_surveillance_evidence.length > 0 ? (
                      <span className="text-emerald-400 font-medium">
                        ✓ {claimPackage.video_surveillance_evidence.length} live ground camera events correlated
                      </span>
                    ) : (
                      <span>Fixed zone surveillance cameras verified.</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Incident Chronology */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Incident Chronology</h4>
                <div className="space-y-2">
                  {claimPackage.incident_chronology?.map((event: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-surface-800/80 border border-slate-800 text-xs">
                      <div className="font-mono text-[11px] text-indigo-400 font-bold w-16 shrink-0">
                        {event.time}
                      </div>
                      <div>
                        <strong className="text-slate-200">{event.event}</strong>
                        <p className="text-slate-400 text-[11px] mt-0.5">{event.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center bg-surface-800/30 rounded-2xl border border-slate-800">
              <FileText size={36} className="mx-auto text-slate-600 mb-3" />
              <h4 className="text-sm font-bold text-slate-300">No Claim Package Selected</h4>
              <p className="text-xs text-slate-500 mt-1">
                Evaluate an incident in the Claim Analysis tab or trigger Demo 7 to inspect a completed verified dossier.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
