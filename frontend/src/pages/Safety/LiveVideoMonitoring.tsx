import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Video, Play, Square, RefreshCw, AlertOctagon, ShieldAlert,
  HardHat, ShieldCheck, Shield, Activity, Users, Eye, CheckCircle2,
  AlertTriangle, Clock, Layers, Sparkles, Radio, Check, Lock, ChevronRight
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import { videoApi, sitesApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { EmptyState } from '@/components/common';
import { formatRelativeTime } from '@/utils/display';
import type {
  Site, VideoStream, VideoEvent, CameraZone, VideoLiveStatus, VideoDemoScenario
} from '@/types';

const WRITE_ROLES = ['super_admin', 'safety_officer', 'site_manager'];

const ZONE_COLOR_MAP: Record<string, { border: string; bg: string; text: string; badge: string }> = {
  safe_area: { border: 'border-emerald-500/40', bg: 'bg-emerald-500/10', text: 'text-emerald-400', badge: 'bg-emerald-500/20 text-emerald-300' },
  excavation: { border: 'border-amber-500/50', bg: 'bg-amber-500/15', text: 'text-amber-400', badge: 'bg-amber-500/20 text-amber-300' },
  heavy_equipment: { border: 'border-red-500/50', bg: 'bg-red-500/15', text: 'text-red-400', badge: 'bg-red-500/20 text-red-300' },
  restricted: { border: 'border-purple-500/50', bg: 'bg-purple-500/15', text: 'text-purple-400', badge: 'bg-purple-500/20 text-purple-300' },
  electrical: { border: 'border-yellow-500/50', bg: 'bg-yellow-500/15', text: 'text-yellow-400', badge: 'bg-yellow-500/20 text-yellow-300' },
  general: { border: 'border-slate-500/40', bg: 'bg-slate-500/10', text: 'text-slate-400', badge: 'bg-slate-500/20 text-slate-300' },
};

export function LiveVideoMonitoring() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const canControl = WRITE_ROLES.includes(user?.role ?? '');

  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [selectedStreamId, setSelectedStreamId] = useState<string>('');
  const [runningScenario, setRunningScenario] = useState<number | null>(null);
  const [activeFrameCount, setActiveFrameCount] = useState<number>(0);

  // Fetch Sites
  const { data: sites } = useQuery<Site[]>({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  // Set default selected site
  useEffect(() => {
    if (sites && sites.length > 0 && !selectedSiteId) {
      setSelectedSiteId(sites[0].id);
    }
  }, [sites, selectedSiteId]);

  // Fetch Live Status for Selected Site
  const { data: liveStatus, refetch: refetchLiveStatus } = useQuery<VideoLiveStatus>({
    queryKey: ['video-live-status', selectedSiteId],
    queryFn: () => videoApi.getSiteLiveStatus(selectedSiteId).then(r => r.data),
    enabled: !!selectedSiteId,
    refetchInterval: 5000,
  });

  // Fetch Streams for Selected Site
  const { data: streams, refetch: refetchStreams } = useQuery<VideoStream[]>({
    queryKey: ['video-streams', selectedSiteId],
    queryFn: () => videoApi.getSiteStreams(selectedSiteId).then(r => r.data),
    enabled: !!selectedSiteId,
  });

  // Auto-select active stream or first stream
  useEffect(() => {
    if (streams && streams.length > 0) {
      const active = streams.find(s => s.status === 'active');
      setSelectedStreamId(active ? active.stream_id : streams[0].stream_id);
    } else {
      setSelectedStreamId('');
    }
  }, [streams]);

  const activeStream = streams?.find(s => s.stream_id === selectedStreamId || s.id === selectedStreamId);
  const isStreamLive = activeStream?.status === 'active';

  // Fetch Stream Events
  const { data: streamEvents, refetch: refetchEvents } = useQuery<VideoEvent[]>({
    queryKey: ['video-stream-events', selectedStreamId],
    queryFn: () => videoApi.getStreamEvents(selectedStreamId, 30).then(r => r.data),
    enabled: !!selectedStreamId,
    refetchInterval: isStreamLive ? 4000 : false,
  });

  // Fetch Demo Scenarios
  const { data: demoScenarios } = useQuery<VideoDemoScenario[]>({
    queryKey: ['video-demo-scenarios'],
    queryFn: () => videoApi.listDemoScenarios().then(r => r.data),
  });

  // Simulated frame heartbeat
  useEffect(() => {
    if (!isStreamLive) return;
    const timer = setInterval(() => {
      setActiveFrameCount(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [isStreamLive]);

  // Mutations
  const startStreamMutation = useMutation({
    mutationFn: () =>
      videoApi.startStream({
        site_id: selectedSiteId,
        camera_name: `Surveillance Cam — ${(sites?.find(s => s.id === selectedSiteId)?.name) || 'Site'}`,
        source_type: 'demo',
        fps: 15.0,
      }),
    onSuccess: (res) => {
      refetchStreams();
      refetchLiveStatus();
      setSelectedStreamId(res.data.stream_id);
      toast.success('Live video monitoring stream started');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to start stream');
    },
  });

  const stopStreamMutation = useMutation({
    mutationFn: (streamId: string) => videoApi.stopStream(streamId),
    onSuccess: () => {
      refetchStreams();
      refetchLiveStatus();
      toast.success('Stream stopped successfully');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to stop stream');
    },
  });

  const runScenarioMutation = useMutation({
    mutationFn: ({ scenarioId }: { scenarioId: number }) =>
      videoApi.runDemoScenario(scenarioId, selectedSiteId),
    onSuccess: (res) => {
      refetchStreams();
      refetchLiveStatus();
      refetchEvents();
      queryClient.invalidateQueries({ queryKey: ['video-stream-events'] });
      setRunningScenario(null);
      toast.success(`Demo Scenario ${res.data.scenario?.id || ''} executed`);
    },
    onError: (err: any) => {
      setRunningScenario(null);
      toast.error(err.response?.data?.detail || 'Demo scenario execution failed');
    },
  });

  const handleRunScenario = (scenId: number) => {
    if (!selectedSiteId) {
      toast.error('Please select a construction site first');
      return;
    }
    setRunningScenario(scenId);
    runScenarioMutation.mutate({ scenarioId: scenId });
  };

  const currentScenarioId = runningScenario || (activeStream?.is_simulation ? 1 : null);

  return (
    <div className="space-y-6">
      {/* Stream Controls Header Bar */}
      <div className="card p-5">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            {/* Site Selector */}
            <div className="flex items-center gap-2">
              <Activity size={16} className="text-slate-500" />
              <span className="text-xs font-medium text-slate-400">Site:</span>
              <select
                id="select-video-site"
                className="input text-xs py-1.5 px-3 min-w-[200px]"
                value={selectedSiteId}
                onChange={(e) => setSelectedSiteId(e.target.value)}
              >
                <option value="">— Select Site —</option>
                {sites?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.site_id})
                  </option>
                ))}
              </select>
            </div>

            {/* Camera / Stream Selector */}
            <div className="flex items-center gap-2">
              <Video size={16} className="text-slate-500" />
              <span className="text-xs font-medium text-slate-400">Camera:</span>
              <select
                id="select-video-stream"
                className="input text-xs py-1.5 px-3 min-w-[220px]"
                value={selectedStreamId}
                onChange={(e) => setSelectedStreamId(e.target.value)}
                disabled={!streams || streams.length === 0}
              >
                {(!streams || streams.length === 0) ? (
                  <option value="">No streams available</option>
                ) : (
                  streams.map((st) => (
                    <option key={st.stream_id} value={st.stream_id}>
                      {st.camera_name} ({st.status.toUpperCase()})
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Live Indicator Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-950 border border-slate-800">
              <div className="relative flex items-center justify-center">
                {isStreamLive && (
                  <span className="absolute w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping opacity-60" />
                )}
                <span className={clsx('w-2 h-2 rounded-full', isStreamLive ? 'bg-emerald-400' : 'bg-slate-600')} />
              </div>
              <span className={clsx('text-xs font-mono font-bold tracking-wider', isStreamLive ? 'text-emerald-400' : 'text-slate-500')}>
                {isStreamLive ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>

            {/* Explicit Source Labeling */}
            {activeStream && (
              <span className={clsx(
                'px-2 py-1 rounded text-[11px] font-mono font-bold uppercase tracking-wider',
                activeStream.is_simulation
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
              )}>
                {activeStream.is_simulation ? 'DEMO / SIMULATION' : 'COMPUTER_VISION'}
              </span>
            )}
          </div>

          {/* Stream Action Buttons */}
          <div className="flex items-center gap-2.5 shrink-0">
            {!isStreamLive ? (
              <button
                id="btn-start-stream"
                className="btn-primary text-xs gap-1.5 px-4 py-2"
                disabled={!selectedSiteId || startStreamMutation.isPending || !canControl}
                onClick={() => startStreamMutation.mutate()}
              >
                {startStreamMutation.isPending ? (
                  <RefreshCw size={13} className="animate-spin" />
                ) : (
                  <Play size={13} />
                )}
                START STREAM
              </button>
            ) : (
              <button
                id="btn-stop-stream"
                className="btn-danger text-xs gap-1.5 px-4 py-2"
                disabled={stopStreamMutation.isPending || !canControl}
                onClick={() => activeStream && stopStreamMutation.mutate(activeStream.stream_id)}
              >
                {stopStreamMutation.isPending ? (
                  <RefreshCw size={13} className="animate-spin" />
                ) : (
                  <Square size={13} />
                )}
                STOP STREAM
              </button>
            )}

            {!canControl && (
              <span className="flex items-center gap-1 text-[11px] text-slate-500">
                <Lock size={11} /> Viewer — Read Only
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Processed Frames</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-xl font-mono font-bold text-slate-100">
              {(activeStream?.processed_frames_count ?? 0) + activeFrameCount}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              Drops: {activeStream?.dropped_frames_count ?? 0}
            </span>
          </div>
        </div>

        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Detected Personnel</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-xl font-mono font-bold text-primary-400 flex items-center gap-1.5">
              <Users size={18} />
              {liveStatus?.detected_personnel_count ?? 0}
            </span>
            <span className="text-[10px] text-slate-400">On-scene</span>
          </div>
        </div>

        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">PPE Compliance</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className={clsx(
              'text-xl font-mono font-bold flex items-center gap-1.5',
              (liveStatus?.ppe_compliance_rate ?? 100) >= 85 ? 'text-emerald-400' : 'text-amber-400'
            )}>
              <ShieldCheck size={18} />
              {liveStatus?.ppe_compliance_rate ?? 100}%
            </span>
            <span className="text-[10px] text-slate-400">
              {liveStatus?.compliant_workers_count ?? 0} Compliant
            </span>
          </div>
        </div>

        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active HIGH Alerts</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-xl font-mono font-bold text-amber-400 flex items-center gap-1.5">
              <AlertTriangle size={18} />
              {liveStatus?.active_high_alerts_count ?? 0}
            </span>
            <span className="text-[10px] text-amber-500/80 font-mono">Pending</span>
          </div>
        </div>

        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active CRITICAL Alerts</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-xl font-mono font-bold text-red-400 flex items-center gap-1.5">
              <AlertOctagon size={18} />
              {liveStatus?.active_critical_alerts_count ?? 0}
            </span>
            <span className="text-[10px] text-red-500/80 font-mono">Immediate</span>
          </div>
        </div>
      </div>

      {/* Main Surveillance Area: Video Feed Visualizer + Side Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-Time Video Scene Preview (2 cols) */}
        <div className="lg:col-span-2 card p-5 flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Video className="w-4 h-4 text-primary-400" />
              <h3 className="text-sm font-bold text-slate-200">
                {activeStream ? activeStream.camera_name : 'Surveillance Feed Canvas'}
              </h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <span>{activeStream?.fps ?? 15} FPS</span>
              <span>·</span>
              <span>{activeStream ? `${activeStream.resolution_width}x${activeStream.resolution_height}` : '1280x720'}</span>
            </div>
          </div>

          {/* Interactive Scene Canvas */}
          <div className="relative w-full aspect-video bg-surface-950/90 rounded-xl border border-slate-800 overflow-hidden shadow-2xl flex items-center justify-center">
            {/* Grid background simulation */}
            <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:24px_24px]" />

            {/* Video overlay watermark & stream metadata */}
            <div className="absolute top-3 left-3 z-20 flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-black/70 backdrop-blur-md text-[10px] font-mono text-emerald-400 font-bold border border-emerald-500/30 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                CAM_01 · LIVE STREAM
              </span>
              <span className="px-2 py-0.5 rounded bg-black/70 backdrop-blur-md text-[10px] font-mono text-purple-300 font-bold border border-purple-500/30">
                {activeStream?.is_simulation ? 'DEMO / SIMULATION' : 'COMPUTER_VISION'}
              </span>
            </div>

            {/* Camera timestamp HUD */}
            <div className="absolute top-3 right-3 z-20 px-2 py-0.5 rounded bg-black/70 backdrop-blur-md text-[10px] font-mono text-slate-400 border border-slate-800">
              REC {new Date().toLocaleTimeString()}
            </div>

            {/* Simulated Scene Elements / Zones Overlay */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 1280 720">
              {/* Safe Laydown Zone */}
              <rect x="50" y="50" width="380" height="280" rx="8" fill="rgba(16, 185, 129, 0.08)" stroke="#10b981" strokeWidth="2" strokeDasharray="4 4" />
              <text x="65" y="80" fill="#10b981" fontSize="14" fontWeight="bold" fontFamily="monospace">ZONE A: Safe Laydown Area [Capacity: 10]</text>

              {/* Excavation Zone */}
              <rect x="470" y="50" width="410" height="340" rx="8" fill="rgba(245, 158, 11, 0.08)" stroke="#f59e0b" strokeWidth="2" strokeDasharray="4 4" />
              <text x="485" y="80" fill="#f59e0b" fontSize="14" fontWeight="bold" fontFamily="monospace">ZONE B: Excavation Trench [HIGH RISK]</text>

              {/* Heavy Equipment Zone */}
              <rect x="470" y="420" width="410" height="260" rx="8" fill="rgba(239, 68, 68, 0.1)" stroke="#ef4444" strokeWidth="2" strokeDasharray="4 4" />
              <text x="485" y="450" fill="#ef4444" fontSize="14" fontWeight="bold" fontFamily="monospace">ZONE C: Heavy Machinery Operating Zone [CRITICAL]</text>

              {/* Restricted / Electrical Zone */}
              <rect x="910" y="50" width="320" height="630" rx="8" fill="rgba(168, 85, 247, 0.08)" stroke="#a855f7" strokeWidth="2" strokeDasharray="4 4" />
              <text x="925" y="80" fill="#a855f7" fontSize="14" fontWeight="bold" fontFamily="monospace">ZONE D: Restricted / Electrical</text>

              {/* Simulated Detected Person 1 */}
              <g transform="translate(180, 110)">
                <rect x="0" y="0" width="95" height="180" rx="4" fill="rgba(56, 189, 248, 0.15)" stroke="#38bdf8" strokeWidth="2" />
                {/* HUD Label */}
                <rect x="0" y="-22" width="95" height="20" fill="#0284c7" rx="3" />
                <text x="5" y="-8" fill="#ffffff" fontSize="10" fontWeight="bold" fontFamily="monospace">P1: Marcus (0.94)</text>
                {/* PPE status badges */}
                <rect x="0" y="185" width="95" height="32" fill="rgba(15, 23, 42, 0.9)" rx="3" stroke="#334155" strokeWidth="1" />
                <text x="5" y="198" fill="#10b981" fontSize="9" fontWeight="bold">✓ Hard Hat</text>
                <text x="5" y="210" fill="#10b981" fontSize="9" fontWeight="bold">✓ Vest</text>
              </g>

              {/* Simulated Detected Person 2 (Violator in Excavation / Equipment zone if scenario 2/3/4/5) */}
              {(currentScenarioId && currentScenarioId >= 2) && (
                <g transform="translate(560, 140)">
                  <rect x="0" y="0" width="105" height="190" rx="4" fill="rgba(239, 68, 68, 0.2)" stroke="#ef4444" strokeWidth="2.5" />
                  {/* Warning HUD Label */}
                  <rect x="0" y="-22" width="105" height="20" fill="#dc2626" rx="3" />
                  <text x="5" y="-8" fill="#ffffff" fontSize="10" fontWeight="bold" fontFamily="monospace">P2: VIOLATION (0.91)</text>
                  {/* Missing PPE badge */}
                  <rect x="0" y="195" width="105" height="32" fill="rgba(15, 23, 42, 0.95)" rx="3" stroke="#dc2626" strokeWidth="1" />
                  <text x="5" y="208" fill="#ef4444" fontSize="9" fontWeight="bold">✗ Missing Hard Hat</text>
                  <text x="5" y="220" fill="#f59e0b" fontSize="9" fontWeight="bold">⚠ High Risk Zone</text>
                </g>
              )}
            </svg>

            {/* Overlay Scene Status Badge */}
            <div className="absolute bottom-3 left-3 z-20 flex items-center gap-2">
              <span className="px-2.5 py-1 rounded bg-black/80 backdrop-blur-md text-[11px] font-mono text-slate-300 border border-slate-700">
                Camera Active · Optical Flow: Normal · Inference: ~24ms
              </span>
            </div>
          </div>

          {/* Zones Summary Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
            {liveStatus?.active_zones.slice(0, 4).map((z) => {
              const styling = ZONE_COLOR_MAP[z.zone_type] || ZONE_COLOR_MAP.general;
              return (
                <div key={z.id} className={clsx('p-2.5 rounded-lg border text-xs', styling.bg, styling.border)}>
                  <span className={clsx('font-bold block truncate', styling.text)}>{z.name}</span>
                  <div className="flex justify-between items-center text-[10px] text-slate-400 mt-1">
                    <span>Limit: {z.max_capacity}</span>
                    <span className={clsx('px-1.5 py-0.2 rounded uppercase font-mono font-bold', styling.badge)}>
                      {z.risk_level}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side Panel: Deterministic Demo Scenarios + Live Event Feed */}
        <div className="space-y-6">
          {/* Deterministic Demo Scenarios Runner Card */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-slate-200">Surveillance Demo Scenarios</h3>
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 font-bold ml-auto font-mono">
                DEMO / SIMULATION
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Trigger deterministic surveillance safety scenarios to test person detection, PPE compliance, restricted zones, and alert escalation.
            </p>

            <div className="space-y-2">
              {demoScenarios?.map((scen) => (
                <button
                  key={scen.id}
                  id={`btn-demo-scenario-${scen.id}`}
                  onClick={() => handleRunScenario(scen.id)}
                  disabled={runScenarioMutation.isPending || !canControl}
                  className={clsx(
                    'w-full text-left p-3 rounded-lg border transition-all flex items-start justify-between gap-2 group',
                    runningScenario === scen.id
                      ? 'bg-purple-500/20 border-purple-500/50'
                      : 'bg-surface-950/60 border-slate-800 hover:border-slate-700 hover:bg-surface-900/60'
                  )}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-200 group-hover:text-primary-400 transition-colors">
                        {scen.name}
                      </span>
                      {scen.expected_violations > 0 && (
                        <span className="badge-critical text-[9px] uppercase font-mono">
                          {scen.expected_violations} Violations
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {scen.description}
                    </p>
                  </div>
                  <ChevronRight size={14} className="text-slate-600 group-hover:text-slate-300 shrink-0 mt-0.5 transition-colors" />
                </button>
              ))}
            </div>
          </div>

          {/* Real-time Safety Events Feed Card */}
          <div className="card p-5 flex flex-col h-[400px]">
            <div className="flex items-center justify-between mb-3 shrink-0">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-slate-200">Live Safety Event Feed</h3>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                {streamEvents?.length ?? 0} Recorded
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 text-xs">
              {(!streamEvents || streamEvents.length === 0) ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-4">
                  <ShieldCheck size={32} className="text-slate-600 mb-2" />
                  <p className="text-xs text-slate-400">No safety events recorded yet.</p>
                  <p className="text-[11px] text-slate-600 mt-1">Start a stream or run a demo scenario.</p>
                </div>
              ) : (
                streamEvents.map((evt) => (
                  <div
                    key={evt.id}
                    className={clsx(
                      'p-2.5 rounded-lg border text-xs flex flex-col space-y-1',
                      evt.severity === 'critical' ? 'bg-red-500/10 border-red-500/30 text-red-300' :
                      evt.severity === 'high' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                      'bg-surface-950/80 border-slate-800/80 text-slate-300'
                    )}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="font-mono text-[10px] font-bold text-slate-400">{evt.event_id}</span>
                      <span className={clsx(
                        'badge text-[9px] uppercase font-mono',
                        evt.severity === 'critical' ? 'badge-critical' :
                        evt.severity === 'high' ? 'badge-warning' : 'badge-monitoring'
                      )}>
                        {evt.severity}
                      </span>
                    </div>
                    <span className="font-semibold text-slate-200">{evt.event_type.replace(/_/g, ' ').toUpperCase()}</span>
                    <p className="text-[11px] text-slate-400 leading-snug">{evt.description}</p>
                    {evt.evidence && (
                      <span className="text-[10px] text-slate-500 font-mono truncate">{evt.evidence}</span>
                    )}
                    <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500">
                      <span>{evt.zone_name || 'General Site'}</span>
                      <span>{formatRelativeTime(evt.timestamp || evt.created_at)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
