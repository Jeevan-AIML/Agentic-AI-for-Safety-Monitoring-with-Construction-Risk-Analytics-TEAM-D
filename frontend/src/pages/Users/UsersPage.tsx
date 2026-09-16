import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Users, Trash2 } from 'lucide-react';
import { authApi } from '@/services/api';
import { EmptyState, PageLoader, Modal } from '@/components/common';
import { ROLE_BADGE, ROLE_LABEL, formatDate } from '@/utils/display';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { User } from '@/types';

const schema = z.object({
  full_name: z.string().min(2, 'Required'),
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
  role: z.string(),
  phone: z.string().optional(),
  department: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => authApi.listUsers().then(r => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => authApi.createUser(data),
    onSuccess: () => {
      toast.success('User created');
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setAddOpen(false);
      reset();
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => authApi.deleteUser(id),
    onSuccess: () => {
      toast.success('User deleted');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Cannot delete'),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'viewer' },
  });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Users</h1>
          <p className="page-subtitle">Manage platform users and their roles</p>
        </div>
        <button className="btn-primary" onClick={() => setAddOpen(true)}>
          <Plus size={16} /> Add User
        </button>
      </div>

      {isLoading && <PageLoader />}

      {!isLoading && (!users || users.length === 0) && (
        <EmptyState icon={<Users size={28} />} title="No users found" />
      )}

      {!isLoading && users && users.length > 0 && (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th>Last Login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user: User) => (
                  <tr key={user.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
                          {user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                        </div>
                        <span className="font-medium text-slate-200">{user.full_name}</span>
                      </div>
                    </td>
                    <td className="text-slate-400">{user.email}</td>
                    <td>
                      <span className={clsx('badge', ROLE_BADGE[user.role])}>
                        {ROLE_LABEL[user.role]}
                      </span>
                    </td>
                    <td className="text-slate-500">{user.department || '—'}</td>
                    <td>
                      <span className={clsx('badge', user.is_active ? 'badge-active' : 'badge-inactive')}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="text-slate-500">{formatDate(user.last_login)}</td>
                    <td>
                      <button
                        className="btn-icon text-red-500/60 hover:text-red-400 hover:bg-red-500/10"
                        onClick={() => deleteMutation.mutate(user.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Create User">
        <form onSubmit={handleSubmit(data => createMutation.mutate(data))} className="space-y-4">
          <div>
            <label className="label">Full Name *</label>
            <input {...register('full_name')} className="input" placeholder="John Doe" />
            {errors.full_name && <p className="text-xs text-red-400 mt-1">{errors.full_name.message}</p>}
          </div>
          <div>
            <label className="label">Email *</label>
            <input {...register('email')} type="email" className="input" placeholder="john@company.com" />
            {errors.email && <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>}
          </div>
          <div>
            <label className="label">Password *</label>
            <input {...register('password')} type="password" className="input" placeholder="Min 8 chars" />
            {errors.password && <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>}
          </div>
          <div>
            <label className="label">Role</label>
            <select {...register('role')} className="input">
              <option value="viewer">Viewer</option>
              <option value="safety_officer">Safety Officer</option>
              <option value="site_manager">Site Manager</option>
              <option value="project_manager">Project Manager</option>
              <option value="super_admin">Super Admin</option>
            </select>
          </div>
          <div>
            <label className="label">Department</label>
            <input {...register('department')} className="input" placeholder="Engineering" />
          </div>
          <div>
            <label className="label">Phone</label>
            <input {...register('phone')} className="input" placeholder="+91-9000000000" />
          </div>
          <div className="flex gap-3 justify-end">
            <button type="button" className="btn-secondary" onClick={() => setAddOpen(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </Modal>
    </motion.div>
  );
}
