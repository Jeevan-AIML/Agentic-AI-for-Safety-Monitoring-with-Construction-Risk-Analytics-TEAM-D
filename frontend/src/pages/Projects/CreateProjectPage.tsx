import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ChevronRight, ChevronLeft, Check, FolderOpen } from 'lucide-react';
import { projectsApi, authApi } from '@/services/api';
import { Spinner } from '@/components/common';
import toast from 'react-hot-toast';
import clsx from 'clsx';

const STEPS = ['Project Info', 'Location', 'Site Setup', 'Review'];

const schema = z.object({
  // Step 1
  project_id: z.string().min(1, 'Required'),
  name: z.string().min(2, 'Required'),
  client: z.string().min(1, 'Required'),
  description: z.string().optional(),
  start_date: z.string().optional(),
  expected_completion: z.string().optional(),
  budget: z.string().optional(),
  manager_id: z.string().optional(),
  // Step 2
  address: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  country: z.string().optional(),
  latitude: z.string().optional(),
  longitude: z.string().optional(),
  // Step 3
  status: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function CreateProjectPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(0);

  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: () => authApi.listUsers().then(r => r.data),
  });

  const managers = users?.filter((u: any) =>
    ['super_admin', 'project_manager'].includes(u.role)
  );

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { country: 'India', status: 'planning' },
  });

  const values = watch();

  const mutation = useMutation({
    mutationFn: (data: any) => projectsApi.create(data),
    onSuccess: (res) => {
      toast.success('Project created successfully!');
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      navigate(`/projects/${res.data.id}`);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to create project'),
  });

  const onSubmit = (data: FormData) => {
    const payload = {
      ...data,
      budget: data.budget ? parseFloat(data.budget) : undefined,
      latitude: data.latitude ? parseFloat(data.latitude) : undefined,
      longitude: data.longitude ? parseFloat(data.longitude) : undefined,
      start_date: data.start_date ? new Date(data.start_date).toISOString() : undefined,
      expected_completion: data.expected_completion ? new Date(data.expected_completion).toISOString() : undefined,
    };
    mutation.mutate(payload);
  };

  const nextStep = () => setStep(s => Math.min(s + 1, 3));
  const prevStep = () => setStep(s => Math.max(s - 1, 0));

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Create Project</h1>
          <p className="page-subtitle">Set up a new construction project</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/projects')}>
          Cancel
        </button>
      </div>

      {/* Step indicators */}
      <div className="card p-5 mb-6">
        <div className="flex items-center">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all',
                  i < step ? 'bg-primary-600 text-white' :
                  i === step ? 'bg-primary-500 text-white ring-4 ring-primary-500/20' :
                  'bg-surface-800 text-slate-500 border border-slate-700'
                )}>
                  {i < step ? <Check size={14} /> : i + 1}
                </div>
                <span className={clsx(
                  'text-[10px] mt-1 font-medium',
                  i <= step ? 'text-slate-300' : 'text-slate-600'
                )}>
                  {label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={clsx(
                  'flex-1 h-px mx-2 mb-4 transition-all',
                  i < step ? 'bg-primary-600' : 'bg-slate-800'
                )} />
              )}
            </div>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Step 1 */}
            {step === 0 && (
              <div className="card p-6 space-y-5">
                <h2 className="text-base font-semibold text-slate-200 mb-4">Project Information</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="label">Project ID *</label>
                    <input {...register('project_id')} className="input" placeholder="PRJ-005" />
                    {errors.project_id && <p className="text-xs text-red-400 mt-1">{errors.project_id.message}</p>}
                  </div>
                  <div>
                    <label className="label">Status</label>
                    <select {...register('status')} className="input">
                      <option value="planning">Planning</option>
                      <option value="active">Active</option>
                      <option value="on_hold">On Hold</option>
                      <option value="completed">Completed</option>
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="label">Project Name *</label>
                    <input {...register('name')} className="input" placeholder="Skyline Tower Construction" />
                    {errors.name && <p className="text-xs text-red-400 mt-1">{errors.name.message}</p>}
                  </div>
                  <div className="md:col-span-2">
                    <label className="label">Client Name *</label>
                    <input {...register('client')} className="input" placeholder="Client Developers Pvt. Ltd." />
                    {errors.client && <p className="text-xs text-red-400 mt-1">{errors.client.message}</p>}
                  </div>
                  <div className="md:col-span-2">
                    <label className="label">Description</label>
                    <textarea {...register('description')} className="input h-24 resize-none" placeholder="Brief project description..." />
                  </div>
                  <div>
                    <label className="label">Start Date</label>
                    <input {...register('start_date')} type="date" className="input" />
                  </div>
                  <div>
                    <label className="label">Expected Completion</label>
                    <input {...register('expected_completion')} type="date" className="input" />
                  </div>
                  <div>
                    <label className="label">Budget (₹)</label>
                    <input {...register('budget')} type="number" className="input" placeholder="850000000" />
                  </div>
                  <div>
                    <label className="label">Project Manager</label>
                    <select {...register('manager_id')} className="input">
                      <option value="">Select manager...</option>
                      {managers?.map((u: any) => (
                        <option key={u.id} value={u.id}>{u.full_name}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2 */}
            {step === 1 && (
              <div className="card p-6 space-y-5">
                <h2 className="text-base font-semibold text-slate-200 mb-4">Project Location</h2>
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
            )}

            {/* Step 3 */}
            {step === 2 && (
              <div className="card p-6">
                <h2 className="text-base font-semibold text-slate-200 mb-4">Initial Site Setup</h2>
                <p className="text-sm text-slate-500 mb-6">
                  You can add detailed site information after creating the project.
                  Sites can be added from the Project Details page.
                </p>
                <div className="p-4 rounded-lg bg-primary-500/5 border border-primary-500/20 text-sm text-primary-300">
                  After creating the project, go to <strong>Project Details → Add Site</strong> to configure construction sites.
                </div>
              </div>
            )}

            {/* Step 4 — Review */}
            {step === 3 && (
              <div className="card p-6">
                <h2 className="text-base font-semibold text-slate-200 mb-5">Review & Confirm</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  {[
                    ['Project ID', values.project_id],
                    ['Project Name', values.name],
                    ['Client', values.client],
                    ['Status', values.status],
                    ['Start Date', values.start_date],
                    ['Expected Completion', values.expected_completion],
                    ['Budget', values.budget ? `₹${parseInt(values.budget).toLocaleString('en-IN')}` : '—'],
                    ['City', values.city],
                    ['State', values.state],
                    ['Country', values.country],
                  ].map(([label, value]) => (
                    <div key={label} className="flex gap-3">
                      <span className="text-slate-500 w-36 shrink-0">{label}:</span>
                      <span className="text-slate-200 font-medium">{value || '—'}</span>
                    </div>
                  ))}
                </div>
                {values.description && (
                  <div className="mt-4 pt-4 border-t border-slate-800">
                    <div className="text-xs text-slate-500 mb-1">Description</div>
                    <p className="text-sm text-slate-300">{values.description}</p>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between mt-5">
          <button
            type="button"
            className="btn-secondary"
            onClick={prevStep}
            disabled={step === 0}
          >
            <ChevronLeft size={16} /> Back
          </button>

          {step < 3 ? (
            <button type="button" className="btn-primary" onClick={nextStep}>
              Next <ChevronRight size={16} />
            </button>
          ) : (
            <button
              type="submit"
              className="btn-primary"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? <Spinner size={16} /> : <><FolderOpen size={16} /> Save Project</>}
            </button>
          )}
        </div>
      </form>
    </motion.div>
  );
}
