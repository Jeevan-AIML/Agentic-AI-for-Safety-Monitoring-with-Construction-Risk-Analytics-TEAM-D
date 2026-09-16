import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, FolderOpen, Search, Filter, Eye, Edit2, Trash2, MapPin } from 'lucide-react';
import { projectsApi } from '@/services/api';
import { EmptyState, ConfirmDialog, PageLoader } from '@/components/common';
import {
  PROJECT_STATUS_BADGE, PROJECT_STATUS_LABEL, formatDate, formatCurrency
} from '@/utils/display';
import { getRiskColor } from '@/utils/riskScoring';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { Project } from '@/types';

export default function ProjectsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list().then(r => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      toast.success('Project deleted');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setDeleteId(null);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to delete'),
  });

  const filtered = projects?.filter((p: Project) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.client.toLowerCase().includes(search.toLowerCase()) ||
    p.project_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Projects</h1>
          <p className="page-subtitle">Manage construction projects and their sites</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/projects/new')}>
          <Plus size={16} /> Create Project
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-5">
        <div className="flex gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              className="input pl-8 text-sm"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button className="btn-secondary text-sm">
            <Filter size={14} /> Filter
          </button>
        </div>
      </div>

      {isLoading && <PageLoader />}

      {!isLoading && (!filtered || filtered.length === 0) && (
        <EmptyState
          icon={<FolderOpen size={28} />}
          title="No projects found"
          description={search ? 'Try a different search term.' : 'Get started by creating your first construction project.'}
          action={
            !search && (
              <button className="btn-primary" onClick={() => navigate('/projects/new')}>
                <Plus size={16} /> Create Project
              </button>
            )
          }
        />
      )}

      {!isLoading && filtered && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((project: Project, i: number) => (
            <motion.div
              key={project.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="card-hover p-5"
            >
              <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                {/* Left */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-xs font-mono text-slate-600">{project.project_id}</span>
                    <span className={clsx('badge', PROJECT_STATUS_BADGE[project.status])}>
                      {PROJECT_STATUS_LABEL[project.status]}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-100 mb-0.5">{project.name}</h3>
                  <div className="text-sm text-slate-500">
                    {project.client}
                    {project.city && (
                      <span className="ml-3 inline-flex items-center gap-1">
                        <MapPin size={11} /> {project.city}, {project.country}
                      </span>
                    )}
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-6 text-center shrink-0">
                  <div>
                    <div className="text-lg font-bold text-slate-200">{project.site_count}</div>
                    <div className="text-[10px] text-slate-600 uppercase">Sites</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-slate-300">{project.manager_name || '—'}</div>
                    <div className="text-[10px] text-slate-600 uppercase">Manager</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-slate-300">{formatDate(project.start_date)}</div>
                    <div className="text-[10px] text-slate-600 uppercase">Started</div>
                  </div>
                  {project.budget && (
                    <div>
                      <div className="text-sm font-medium text-slate-300">{formatCurrency(project.budget)}</div>
                      <div className="text-[10px] text-slate-600 uppercase">Budget</div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    className="btn-ghost text-xs"
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    <Eye size={14} /> View
                  </button>
                  <button
                    className="btn-ghost text-xs"
                    onClick={() => navigate(`/projects/${project.id}/edit`)}
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    className="btn-icon text-red-500/60 hover:text-red-400 hover:bg-red-500/10"
                    onClick={() => setDeleteId(project.id)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
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
        title="Delete Project"
        message="Are you sure you want to delete this project? All associated sites and data will be permanently removed."
      />
    </motion.div>
  );
}
