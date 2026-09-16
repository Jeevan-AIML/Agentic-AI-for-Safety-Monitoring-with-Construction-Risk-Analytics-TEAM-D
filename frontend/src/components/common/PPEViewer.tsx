import React, { useState } from 'react';
import {
  PPEAnalysis,
  PPEDetectionItem,
  PersonPPEDetection,
  PPEComplianceStatus,
} from '../../types';
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Eye,
  Info,
  Maximize2,
  HardHat,
  Glasses,
  UserCheck,
} from 'lucide-react';

interface PPEViewerProps {
  analysis: PPEAnalysis;
  onSelectWorker?: (workerId: string) => void;
}

export const PPEViewer: React.FC<PPEViewerProps> = ({ analysis }) => {
  const [selectedDetection, setSelectedDetection] = useState<PPEDetectionItem | null>(null);
  const [hoveredDetection, setHoveredDetection] = useState<string | null>(null);
  const [filterClass, setFilterClass] = useState<string>('ALL');

  const {
    image_url,
    image_width,
    image_height,
    overall_compliance,
    compliance_score,
    total_persons_detected,
    detected_ppe,
    missing_ppe,
    detections,
    persons,
    cross_verification,
    detection_source,
    model_name,
    recommendations,
    findings,
  } = analysis;

  const isMock = detection_source === 'DEMO / MOCK';

  const getStatusBadge = (status: PPEComplianceStatus) => {
    switch (status) {
      case 'COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> COMPLIANT
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" /> NON-COMPLIANT
          </span>
        );
      case 'UNCERTAIN':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" /> UNCERTAIN / LOW CONFIDENCE
          </span>
        );
    }
  };

  const getPPEClassColor = (ppeClass: string, status: string) => {
    if (status === 'LOW_CONFIDENCE') {
      return {
        border: 'border-amber-400',
        bg: 'bg-amber-400/15',
        badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      };
    }
    switch (ppeClass) {
      case 'HARD_HAT':
        return {
          border: 'border-amber-500',
          bg: 'bg-amber-500/15',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        };
      case 'SAFETY_VEST':
        return {
          border: 'border-emerald-500',
          bg: 'bg-emerald-500/15',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
        };
      case 'SAFETY_GOGGLES':
        return {
          border: 'border-sky-500',
          bg: 'bg-sky-500/15',
          badge: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
        };
      default:
        return {
          border: 'border-indigo-500',
          bg: 'bg-indigo-500/15',
          badge: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
        };
    }
  };

  const visibleDetections = detections.filter((d) => {
    if (filterClass === 'ALL') return true;
    return d.ppe_class === filterClass;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner with Model & Integrity Declaration */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Eye className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-white">
                Computer Vision Analysis Result
              </h3>
              {isMock ? (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  DEMO / MOCK
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  REAL COMPUTER VISION
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              Engine: <span className="font-mono text-slate-300">{model_name}</span> &bull;
              Resolution: <span className="text-slate-300">{image_width} &times; {image_height}</span> &bull;
              Threshold: <span className="text-slate-300">{(analysis.confidence_threshold * 100).toFixed(0)}%</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-slate-400">Compliance Score</div>
            <div className="text-xl font-bold text-white">{compliance_score}%</div>
          </div>
          {getStatusBadge(overall_compliance)}
        </div>
      </div>

      {/* Main Analysis Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Viewer with Overlays */}
        <div className="lg:col-span-8 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Filter Gear:</span>
              {['ALL', 'HARD_HAT', 'SAFETY_VEST', 'SAFETY_GOGGLES'].map((cls) => (
                <button
                  key={cls}
                  onClick={() => setFilterClass(cls)}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    filterClass === cls
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {cls.replace('_', ' ')}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-500 font-mono">
              {visibleDetections.length} objects localized
            </span>
          </div>

          {/* Image Canvas Viewport */}
          <div className="relative w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-950 flex items-center justify-center min-h-[420px]">
            {/* Base Image */}
            <img
              src={image_url}
              alt="PPE Construction Analysis"
              className="max-h-[580px] w-full object-contain rounded-lg select-none"
            />

            {/* Bounding Boxes Layer */}
            <div className="absolute inset-0 pointer-events-none">
              {/* Person Boxes */}
              {persons &&
                persons.map((p, pIdx) => {
                  const xPct = (p.bounding_box.x / image_width) * 100;
                  const yPct = (p.bounding_box.y / image_height) * 100;
                  const wPct = (p.bounding_box.width / image_width) * 100;
                  const hPct = (p.bounding_box.height / image_height) * 100;

                  return (
                    <div
                      key={`person-${pIdx}`}
                      style={{
                        left: `${xPct}%`,
                        top: `${yPct}%`,
                        width: `${wPct}%`,
                        height: `${hPct}%`,
                      }}
                      className="absolute border border-dashed border-slate-500/40 rounded pointer-events-auto"
                    >
                      <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-slate-900/80 text-[10px] font-mono text-slate-400 border border-slate-700">
                        {p.person_id} ({p.is_compliant ? 'Compliant' : 'Deficient'})
                      </div>
                    </div>
                  );
                })}

              {/* PPE Detections */}
              {visibleDetections.map((det) => {
                const xPct = (det.bounding_box.x / image_width) * 100;
                const yPct = (det.bounding_box.y / image_height) * 100;
                const wPct = (det.bounding_box.width / image_width) * 100;
                const hPct = (det.bounding_box.height / image_height) * 100;
                const color = getPPEClassColor(det.ppe_class, det.status);
                const isHovered = hoveredDetection === det.detection_id;
                const isSelected = selectedDetection?.detection_id === det.detection_id;

                return (
                  <div
                    key={det.detection_id}
                    onClick={() => setSelectedDetection(det)}
                    onMouseEnter={() => setHoveredDetection(det.detection_id)}
                    onMouseLeave={() => setHoveredDetection(null)}
                    style={{
                      left: `${xPct}%`,
                      top: `${yPct}%`,
                      width: `${wPct}%`,
                      height: `${hPct}%`,
                    }}
                    className={`absolute border-2 rounded transition-all cursor-pointer pointer-events-auto ${color.border} ${color.bg} ${
                      isHovered || isSelected ? 'ring-2 ring-white scale-[1.01] z-20' : 'z-10'
                    }`}
                  >
                    <div
                      className={`absolute -top-6 left-0 px-2 py-0.5 rounded text-[10px] font-bold whitespace-nowrap shadow-sm border ${color.badge}`}
                    >
                      {det.ppe_class.replace('_', ' ')} &bull;{' '}
                      {(det.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Breakdown & Cross-Verification */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Compliance Breakdown Card */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <Shield className="w-4 h-4 text-indigo-400" />
              PPE Compliance Breakdown
            </h4>

            {/* Detected PPE items */}
            <div className="space-y-2">
              <div className="text-xs font-medium text-slate-400">Detected PPE Gear</div>
              {detected_ppe.length === 0 ? (
                <div className="text-xs text-slate-500 italic">No PPE gear detected</div>
              ) : (
                detected_ppe.map((item, i) => (
                  <div
                    key={`det-${i}`}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/60 border border-slate-700/50"
                  >
                    <div className="flex items-center gap-2">
                      {item.ppe_class === 'HARD_HAT' && (
                        <HardHat className="w-3.5 h-3.5 text-amber-400" />
                      )}
                      {item.ppe_class === 'SAFETY_VEST' && (
                        <Shield className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                      {item.ppe_class === 'SAFETY_GOGGLES' && (
                        <Glasses className="w-3.5 h-3.5 text-sky-400" />
                      )}
                      <span className="text-xs text-slate-200 font-medium">
                        {item.ppe_class.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[11px] font-mono font-bold ${
                          item.confidence >= 0.65 ? 'text-emerald-400' : 'text-amber-400'
                        }`}
                      >
                        {(item.confidence * 100).toFixed(0)}%
                      </span>
                      {item.status === 'LOW_CONFIDENCE' && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-amber-500/20 text-amber-300">
                          LOW CONF
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Missing PPE items */}
            <div className="space-y-2">
              <div className="text-xs font-medium text-slate-400">Missing Mandatory PPE</div>
              {missing_ppe.length === 0 ? (
                <div className="flex items-center gap-2 p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  All required PPE classes detected
                </div>
              ) : (
                missing_ppe.map((m, i) => (
                  <div
                    key={`miss-${i}`}
                    className="flex items-center justify-between p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300"
                  >
                    <div className="flex items-center gap-2">
                      <XCircle className="w-3.5 h-3.5 text-rose-400" />
                      <span className="text-xs font-medium">{m.replace('_', ' ')}</span>
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400">
                      VIOLATION
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Cross-Verification Card */}
          {cross_verification && (
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-cyan-400" />
                Cross-Verification Audit
              </h4>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800 text-slate-400">
                  <span>Registry Status:</span>
                  <span className="font-semibold text-slate-200">
                    {cross_verification.db_ppe_status?.toUpperCase() || 'UNKNOWN'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800 text-slate-400">
                  <span>CV Detection Result:</span>
                  <span
                    className={`font-semibold ${
                      cross_verification.cv_compliance === 'COMPLIANT'
                        ? 'text-emerald-400'
                        : 'text-rose-400'
                    }`}
                  >
                    {cross_verification.cv_compliance}
                  </span>
                </div>

                {cross_verification.has_discrepancy ? (
                  <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 space-y-1">
                    <div className="flex items-center gap-1.5 font-semibold text-amber-400">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      PPE STATUS DISCREPANCY
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      {cross_verification.discrepancy_details}
                    </p>
                  </div>
                ) : (
                  <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-[11px] flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    Registry and Computer Vision detection in alignment.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Safety Recommendations */}
          {recommendations && recommendations.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <Info className="w-4 h-4 text-amber-400" />
                Actionable Recommendations
              </h4>
              <ul className="space-y-1.5">
                {recommendations.map((rec, i) => (
                  <li
                    key={i}
                    className="text-xs text-slate-300 leading-relaxed pl-3 border-l-2 border-indigo-500"
                  >
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
