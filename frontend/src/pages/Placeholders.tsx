// Placeholder pages for Milestone 2/3 features (SafetyPage is now at pages/Safety/SafetyPage.tsx)
import { ClipboardCheck, Shield, AlertTriangle, BarChart3 } from 'lucide-react';
import { ComingSoon } from '@/components/common';
import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { ROLE_LABEL, ROLE_BADGE } from '@/utils/display';
import clsx from 'clsx';

export function CompliancePage() {
  return (
    <ComingSoon
      title="Compliance Management"
      milestone="Milestone 2"
      description="Regulatory compliance tracking against OSHA, IS standards, and project-specific safety requirements."
      icon={<ClipboardCheck size={32} />}
    />
  );
}

export function InsurancePage() {
  return (
    <ComingSoon
      title="Insurance Intelligence"
      milestone="Milestone 3"
      description="AI-driven insurance risk assessment, claim prediction, and policy optimization for construction projects."
      icon={<Shield size={32} />}
    />
  );
}

export function IncidentsPage() {
  return (
    <ComingSoon
      title="Incident Management"
      milestone="Milestone 2"
      description="Track, investigate, and analyze construction incidents with root cause analysis and corrective action tracking."
      icon={<AlertTriangle size={32} />}
    />
  );
}

export function InspectionsPage() {
  return (
    <ComingSoon
      title="Inspections"
      milestone="Milestone 2"
      description="Schedule, conduct, and track site inspections with digital checklists and automated report generation."
      icon={<ClipboardCheck size={32} />}
    />
  );
}

export function ReportsPage() {
  return (
    <ComingSoon
      title="Reports & Analytics"
      milestone="Milestone 3"
      description="Comprehensive AI-generated safety and risk reports with trend analysis and executive summaries."
      icon={<BarChart3 size={32} />}
    />
  );
}

export function SettingsPage() {
  const { user } = useAuthStore();
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Account and system preferences</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 card p-6">
          <h2 className="section-title mb-5">My Profile</h2>
          <div className="flex flex-col items-center gap-4 mb-6">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center text-2xl font-bold text-white">
              {user?.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
            </div>
            <div className="text-center">
              <div className="font-semibold text-slate-200">{user?.full_name}</div>
              <div className="text-sm text-slate-500">{user?.email}</div>
              {user && (
                <span className={clsx('badge mt-2', ROLE_BADGE[user.role])}>
                  {ROLE_LABEL[user.role]}
                </span>
              )}
            </div>
          </div>
          <div className="space-y-3 text-sm">
            {[
              ['Phone', user?.phone || '—'],
              ['Department', user?.department || '—'],
              ['Account Status', 'Active'],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between py-2 border-b border-slate-800 last:border-0">
                <span className="text-slate-500">{label}</span>
                <span className="text-slate-300 font-medium">{value}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="md:col-span-2 card p-6">
          <h2 className="section-title mb-5">System Information</h2>
          <div className="space-y-4">
            {[
              ['Application', 'ACRIP — Agentic Construction Risk Intelligence Platform'],
              ['Version', '1.0.0 (Integrated Platform)'],
              ['Build', 'Production Ready'],
              ['Site Risk Agent', 'Active (Telemetry & Environmental Rules)'],
              ['Safety Agent', 'Active (Worker Protection & Computer Vision PPE)'],
              ['Compliance Agent', 'Active (OSHA & Statutory Rule Engine)'],
              ['Insurance Agent', 'Active (Underwriting Exposure & Claims)'],
              ['Risk Intelligence Engine', 'Active (Deterministic 4-Pillar Model)'],
              ['Reporting Agent', 'Active (Multi-Agent Document Generator)'],
              ['Agent Orchestrator', 'Active (Coordinated Pipeline)'],
              ['Database', 'SQLite (Dev) / PostgreSQL (Prod)'],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between py-3 border-b border-slate-800 last:border-0 text-sm">
                <span className="text-slate-500">{label}</span>
                <span className="text-slate-300 font-medium">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// 404 Page
export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center bg-surface-950 p-8">
      <div className="text-8xl font-black text-slate-800 mb-4">404</div>
      <h1 className="text-2xl font-bold text-slate-200 mb-2">Page Not Found</h1>
      <p className="text-slate-500 mb-8">The page you're looking for doesn't exist or has been moved.</p>
      <a href="/dashboard" className="btn-primary">← Back to Dashboard</a>
    </div>
  );
}

// Unauthorized Page
export function UnauthorizedPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center bg-surface-950 p-8">
      <div className="w-20 h-20 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-6">
        <Shield size={36} className="text-red-400" />
      </div>
      <h1 className="text-2xl font-bold text-slate-200 mb-2">Access Denied</h1>
      <p className="text-slate-500 mb-8">You don't have permission to access this page. Contact your administrator.</p>
      <a href="/dashboard" className="btn-primary">← Back to Dashboard</a>
    </div>
  );
}
