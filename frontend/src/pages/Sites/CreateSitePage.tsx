import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, MapPin } from 'lucide-react';
import { sitesApi, authApi, projectsApi } from '@/services/api';
import { Spinner } from '@/components/common';
import toast from 'react-hot-toast';

const schema = z.object({
  site_id: z.string().min(1, 'Required'),
  name: z.string().min(2, 'Required'),
  site_type: z.string().optional(),
  project_id: z.string().optional(),
  manager_id: z.string().optional(),
  status: z.string().optional(),
  address: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  country: z.string().optional(),
  latitude: z.string().optional(),
  longitude: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

const SITE_TYPES = ['High-Rise Construction', 'Underground Construction', 'Bridge Construction', 'Road Construction', 'Rail Infrastructure', 'Industrial Construction', 'Residential Construction', 'Commercial Construction'];

export default function CreateSitePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: projects } = useQuery({ queryKey: ['projects'], queryFn: () => projectsApi.list().then(r => r.data) });
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: () => authApi.listUsers().then(r => r.data) });

  const managers = users?.filter((u: any) => ['super_admin', 'project_manager', 'site_manager'].includes(u.role));

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { status: 'active', country: 'India' },
  });

  const mutation = useMutation({
    mutationFn: (data: any) => sitesApi.create(data),
    onSuccess: (res) => {
      toast.success('Site created successfully!');
      queryClient.invalidateQueries({ queryKey: ['sites'] });
      navigate(`/sites/${res.data.id}`);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to create site'),
  });

  const onSubmit = (data: FormData) => {
    mutation.mutate({
      ...data,
      latitude: data.latitude ? parseFloat(data.latitude) : undefined,
      longitude: data.longitude ? parseFloat(data.longitude) : undefined,
    });
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <button onClick={() => navigate('/sites')} className="btn-ghost text-sm mb-4 -ml-2">
        <ArrowLeft size={14} /> Back to Sites
      </button>
      <div className="page-header">
        <div>
          <h1 className="page-title">Add Construction Site</h1>
          <p className="page-subtitle">Register a new construction site to start monitoring</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-5">
          <div className="card p-6">
            <h2 className="text-base font-semibold text-slate-200 mb-5">Site Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="label">Site ID *</label>
                <input {...register('site_id')} className="input" placeholder="SITE-005" />
                {errors.site_id && <p className="text-xs text-red-400 mt-1">{errors.site_id.message}</p>}
              </div>
              <div>
                <label className="label">Status</label>
                <select {...register('status')} className="input">
                  <option value="active">Active</option>
                  <option value="monitoring">Monitoring</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="label">Site Name *</label>
                <input {...register('name')} className="input" placeholder="Skyline Tower — Hyderabad" />
                {errors.name && <p className="text-xs text-red-400 mt-1">{errors.name.message}</p>}
              </div>
              <div>
                <label className="label">Site Type</label>
                <select {...register('site_type')} className="input">
                  <option value="">Select type...</option>
                  {SITE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Project</label>
                <select {...register('project_id')} className="input">
                  <option value="">Select project...</option>
                  {projects?.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Site Manager</label>
                <select {...register('manager_id')} className="input">
                  <option value="">Select manager...</option>
                  {managers?.map((u: any) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
                </select>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-base font-semibold text-slate-200 mb-5 flex items-center gap-2">
              <MapPin size={16} className="text-primary-400" /> Location Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="md:col-span-2">
                <label className="label">Address</label>
                <input {...register('address')} className="input" placeholder="Plot No. 42, Hitech City" />
              </div>
              <div>
                <label className="label">City</label>
                <input {...register('city')} className="input" placeholder="Hyderabad" />
              </div>
              <div>
                <label className="label">State</label>
                <input {...register('state')} className="input" placeholder="Telangana" />
              </div>
              <div>
                <label className="label">Country</label>
                <input {...register('country')} className="input" placeholder="India" />
              </div>
              <div />
              <div>
                <label className="label">Latitude</label>
                <input {...register('latitude')} className="input" placeholder="17.4435" />
              </div>
              <div>
                <label className="label">Longitude</label>
                <input {...register('longitude')} className="input" placeholder="78.3772" />
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-5">
          <button type="button" className="btn-secondary" onClick={() => navigate('/sites')}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? <><Spinner size={16} /> Saving...</> : 'Create Site'}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
