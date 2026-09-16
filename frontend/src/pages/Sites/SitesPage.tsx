import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, MapPin, Search, Eye, Edit2, Trash2 } from 'lucide-react';
import { sitesApi } from '@/services/api';
import { EmptyState, ConfirmDialog, RiskGauge, PageLoader } from '@/components/common';
import {
  SITE_STATUS_BADGE, SITE_STATUS_LABEL, formatDate
} from '@/utils/display';
import { getRiskColor } from '@/utils/riskScoring';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { Site } from '@/types';

export default function SitesPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const { data: sites, isLoading } = useQuery({
    queryKey: ['sites'],
    queryFn: () => sitesApi.list().then(r => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => sitesApi.delete(id),
    onSuccess: () => {
      toast.success('Site deleted');
      queryClient.invalidateQueries({ queryKey: ['sites'] });
      setDeleteId(null);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to delete'),
  });

  const filtered = sites?.filter((s: Site) =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.city?.toLowerCase().includes(search.toLowerCase()) ||
    s.site_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Construction Sites</h1>
          <p className="page-subtitle">Monitor and manage all active construction sites</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/sites/new')}>
          <Plus size={16} /> Add Construction Site
        </button>
      </div>

      {/* Search */}
      <div className="card p-4 mb-5">
        <div className="relative max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            className="input pl-8 text-sm"
            placeholder="Search sites..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {isLoading && <PageLoader />}

      {!isLoading && (!filtered || filtered.length === 0) && (
        <EmptyState
          icon={<MapPin size={28} />}
          title="No construction sites added yet"
          description="Add your first construction site to begin monitoring risk and safety."
          action={
            <button className="btn-primary" onClick={() => navigate('/sites/new')}>
              <Plus size={16} /> Add Construction Site
            </button>
          }
        />
      )}

      {!isLoading && filtered && filtered.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map((site: Site, i: number) => (
            <motion.div
              key={site.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card-hover p-5"
            >
              <div className="flex items-start gap-4">
                {/* Risk Gauge */}
                <RiskGauge score={site.current_risk_score} size={80} />

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-slate-600">{site.site_id}</span>
                    <span className={clsx('badge', SITE_STATUS_BADGE[site.status])}>
                      {SITE_STATUS_LABEL[site.status]}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-100 mb-0.5 truncate">{site.name}</h3>
                  <div className="text-sm text-slate-500 flex items-center gap-1 mb-3">
                    <MapPin size={11} />
                    {[site.city, site.state, site.country].filter(Boolean).join(', ')}
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <div className="text-sm font-semibold text-slate-200">{site.worker_count}</div>
                      <div className="text-[10px] text-slate-600 uppercase">Workers</div>
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">{site.equipment_count}</div>
                      <div className="text-[10px] text-slate-600 uppercase">Equipment</div>
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-300">{formatDate(site.last_inspection)}</div>
                      <div className="text-[10px] text-slate-600 uppercase">Last Insp.</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-800">
                <button
                  className="btn-primary flex-1 text-sm py-1.5"
                  onClick={() => navigate(`/sites/${site.id}`)}
                >
                  <Eye size={14} /> View Site
                </button>
                <button className="btn-icon" onClick={() => navigate(`/sites/${site.id}/edit`)}>
                  <Edit2 size={14} />
                </button>
                <button
                  className="btn-icon text-red-500/60 hover:text-red-400 hover:bg-red-500/10"
                  onClick={() => setDeleteId(site.id)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        loading={deleteMutation.isPending}
        title="Delete Site"
        message="Are you sure? All workers, equipment, activities, and risk data for this site will be removed."
      />
    </motion.div>
  );
}
