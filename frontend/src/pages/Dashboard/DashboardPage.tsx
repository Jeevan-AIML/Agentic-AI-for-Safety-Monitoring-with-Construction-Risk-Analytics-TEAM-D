import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  ShieldAlert, AlertTriangle, ClipboardCheck, Activity,
  MapPin, CheckCircle2, TrendingUp, Users, Truck,
  Clock, RefreshCw, BarChart3
} from 'lucide-react';
import { dashboardApi, notificationsApi, sitesApi } from '@/services/api';
import { KPICard, RiskGauge, PageLoader } from '@/components/common';
import { RISK_BADGE_MAP, RISK_LABEL_MAP, SITE_STATUS_BADGE, SITE_STATUS_LABEL, formatRelativeTime } from '@/utils/display';
import { getRiskColor } from '@/utils/riskScoring';
import { useAuthStore } from '@/store/authStore';
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine
} from 'recharts';
import clsx from 'clsx';
import type { Site, Notification, RiskBreakdown } from '@/types';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const now = new Date();

  const { data: kpi, isLoading: kpiLoading } = useQuery({
    queryKey: ['dashboard-kpi'],
    queryFn: () => dashboardApi.getKPI().then(r => r.data),
    refetchInterval: 30000,
  });

  const { data: riskBreakdown } = useQuery({
    queryKey: ['risk-breakdown'],
    queryFn: () => dashboardApi.getRiskBreakdown().then(r => r.data),
  });

  const { data: sites } = useQuery({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list().then(r => r.data),
  });

  const radarData = riskBreakdown ? [
    { subject: 'Environmental', score: riskBreakdown.environmental_risk },
    { subject: 'Equipment', score: riskBreakdown.equipment_risk },
    { subject: 'Site Condition', score: riskBreakdown.site_condition_risk },
    { subject: 'Operational', score: riskBreakdown.operational_risk },
  ] : [];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Construction Risk Overview</h1>
          <p className="page-subtitle">
            Monitor site conditions, hazards and operational risk from one intelligent platform.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <div className="text-sm font-medium text-slate-300">
              {now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </div>
            <div className="text-xs text-slate-500">
              {now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} · IST
            </div>
          </div>
          <button
            className="btn-secondary text-xs"
            onClick={() => window.location.reload()}
          >
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        <KPICard
          title="Overall Risk Score"
          value={kpi?.overall_risk_score ?? '—'}
          riskScore={kpi?.overall_risk_score}
          icon={<ShieldAlert size={18} />}
          loading={kpiLoading}
          delay={0}
          accent="from-surface-900"
        />
        <KPICard
          title="Active Hazards"
          value={kpi?.active_hazards ?? '—'}
          subtitle="Requires attention"
          icon={<AlertTriangle size={18} />}
          loading={kpiLoading}
          delay={0.05}
          accent="from-red-500/5"
        />
        <KPICard
          title="Safety Observations"
          value={kpi?.safety_observations ?? '—'}
          subtitle="This period"
          icon={<ClipboardCheck size={18} />}
          loading={kpiLoading}
          delay={0.1}
          accent="from-amber-500/5"
        />
        <KPICard
          title="Open Incidents"
          value={kpi?.open_incidents ?? '—'}
          subtitle="Under review"
          icon={<AlertTriangle size={18} />}
          loading={kpiLoading}
          delay={0.15}
          accent="from-orange-500/5"
        />
        <KPICard
          title="Compliance Status"
          value={kpi ? `${kpi.compliance_status}%` : '—'}
          subtitle="Regulatory compliance"
          icon={<CheckCircle2 size={18} />}
          loading={kpiLoading}
          delay={0.2}
          accent="from-green-500/5"
        />
        <KPICard
          title="Site Monitoring"
          value={kpi?.site_monitoring ?? '—'}
          subtitle={`${kpi?.total_sites ?? 0} sites active`}
          icon={<Activity size={18} />}
          loading={kpiLoading}
          delay={0.25}
          accent="from-primary-500/5"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">

        {/* Risk Breakdown Radar */}
        <div className="card p-5 xl:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="section-title">Risk Overview</h2>
              <p className="section-subtitle">Multi-dimensional risk analysis across all sites</p>
            </div>
            {riskBreakdown && (
              <div className="text-right">
                <div className="text-2xl font-bold tabular-nums" style={{ color: getRiskColor(riskBreakdown.overall_risk) }}>
                  {riskBreakdown.overall_risk.toFixed(0)}
                </div>
                <div className="text-xs" style={{ color: getRiskColor(riskBreakdown.overall_risk) }}>
                  {RISK_LABEL_MAP[riskBreakdown.category as import('@/types').RiskCategory]} RISK
                </div>
              </div>
            )}
          </div>

          {/* Risk breakdown bars */}
          <div className="grid grid-cols-2 gap-4 mb-5">
            {riskBreakdown && [
              { label: 'Environmental Risk', score: riskBreakdown.environmental_risk },
              { label: 'Equipment Risk', score: riskBreakdown.equipment_risk },
              { label: 'Site Condition', score: riskBreakdown.site_condition_risk },
              { label: 'Operational Risk', score: riskBreakdown.operational_risk },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-slate-400">{item.label}</span>
                  <span className="text-xs font-bold tabular-nums" style={{ color: getRiskColor(item.score) }}>
                    {item.score.toFixed(0)}
                  </span>
                </div>
                <div className="h-2 bg-surface-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${item.score}%` }}
                    transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: getRiskColor(item.score) }}
                  />
                </div>
              </div>
            ))}
          </div>

          {radarData.length > 0 && (
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 11 }} />
                <Radar
                  name="Risk"
                  dataKey="score"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.15}
                  dot={{ fill: '#6366f1', r: 3 }}
                />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Site Status */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Sites</h2>
            <span className="text-xs text-slate-500">{sites?.length ?? 0} total</span>
          </div>
          <div className="space-y-3">
            {sites?.slice(0, 5).map((site: Site) => (
              <SiteRow key={site.id} site={site} />
            ))}
            {(!sites || sites.length === 0) && (
              <div className="text-center py-6 text-sm text-slate-600">No sites configured</div>
            )}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <div className="text-lg font-bold text-slate-200">{kpi?.total_workers ?? '—'}</div>
                <div className="text-[10px] text-slate-600 flex items-center justify-center gap-1 mt-0.5">
                  <Users size={10} /> Workers
                </div>
              </div>
              <div>
                <div className="text-lg font-bold text-slate-200">{kpi?.total_equipment ?? '—'}</div>
                <div className="text-[10px] text-slate-600 flex items-center justify-center gap-1 mt-0.5">
                  <Truck size={10} /> Equipment
                </div>
              </div>
              <div>
                <div className="text-lg font-bold text-slate-200">{kpi?.total_projects ?? '—'}</div>
                <div className="text-[10px] text-slate-600 flex items-center justify-center gap-1 mt-0.5">
                  <BarChart3 size={10} /> Projects
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Recent Alerts</h2>
          <a href="/notifications" className="text-xs text-primary-400 hover:text-primary-300">View all →</a>
        </div>
        <div className="space-y-3">
          {notifications?.slice(0, 5).map((n: Notification) => (
            <NotificationRow key={n.id} n={n} />
          ))}
          {(!notifications || notifications.length === 0) && (
            <div className="text-center py-6 text-sm text-slate-600">No notifications</div>
          )}
        </div>
      </div>

      {/* Platform status banner */}
      <div className="mt-6 p-4 rounded-xl border border-primary-500/20 bg-primary-500/5 flex items-center gap-3">
        <Activity size={16} className="text-primary-400 shrink-0" />
        <div>
          <span className="text-sm font-medium text-primary-300">Integrated Risk Intelligence Platform</span>
          <span className="text-sm text-slate-400 ml-2">· Autonomous multi-agent coordination active across Site Risk, Worker Safety, Compliance, Insurance Exposure, and Enterprise Reporting.</span>
        </div>
      </div>
    </motion.div>
  );
}

function SiteRow({ site }: { site: Site }) {
  return (
    <a href={`/sites/${site.id}`} className="flex items-center gap-3 group">
      <div className="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center shrink-0">
        <MapPin size={14} className="text-slate-500 group-hover:text-primary-400 transition-colors" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-300 truncate group-hover:text-slate-100 transition-colors">
          {site.name}
        </div>
        <div className="text-xs text-slate-600">{site.city} · {site.worker_count}W / {site.equipment_count}E</div>
      </div>
      <div className="flex flex-col items-end gap-1 shrink-0">
        <span className={clsx('badge text-[10px]', SITE_STATUS_BADGE[site.status])}>
          {SITE_STATUS_LABEL[site.status]}
        </span>
        <span
          className="text-xs font-bold tabular-nums"
          style={{ color: getRiskColor(site.current_risk_score) }}
        >
          {site.current_risk_score.toFixed(0)}
        </span>
      </div>
    </a>
  );
}

function NotificationRow({ n }: { n: Notification }) {
  const severityColors: Record<string, string> = {
    critical: 'text-red-400 bg-red-500/10 border-red-500/20',
    warning: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    error: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    info: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  };
  return (
    <div className={clsx(
      'flex items-start gap-3 p-3 rounded-lg border',
      severityColors[n.severity] || severityColors.info,
      !n.is_read && 'ring-1 ring-inset ring-current ring-opacity-20'
    )}>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{n.title}</div>
        <div className="text-xs opacity-70 mt-0.5">{n.message}</div>
      </div>
      <div className="text-[10px] opacity-60 shrink-0 flex items-center gap-1">
        <Clock size={10} />
        {formatRelativeTime(n.created_at)}
      </div>
    </div>
  );
}
