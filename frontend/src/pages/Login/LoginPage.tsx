import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Shield, Truck, Lock, AlertCircle, ChevronRight, Activity } from 'lucide-react';
import { authApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import { Spinner } from '@/components/common';
import type { User } from '@/types';

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
  remember: z.boolean().optional(),
});

type FormData = z.infer<typeof schema>;

const DEMO_USERS = [
  { label: 'Super Admin', email: 'admin@acriplatform.com', password: 'Admin@123' },
  { label: 'Project Manager', email: 'manager@acriplatform.com', password: 'Manager@123' },
  { label: 'Site Manager', email: 'site.manager@acriplatform.com', password: 'SiteManager@123' },
  { label: 'Safety Officer', email: 'safety@acriplatform.com', password: 'Safety@123' },
  { label: 'Viewer', email: 'viewer@acriplatform.com', password: 'Viewer@123' },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    setError('');
    try {
      const res = await authApi.login(data.email, data.password);
      const { access_token, user } = res.data;
      setAuth(user as User, access_token);
      toast.success(`Welcome back, ${user.full_name}!`);
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid credentials. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (email: string, password: string) => {
    setValue('email', email);
    setValue('password', password);
  };

  return (
    <div className="min-h-screen flex bg-surface-950">
      {/* Left Side — Branding */}
      <motion.div
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
        className="hidden lg:flex flex-1 flex-col justify-between p-12 relative overflow-hidden bg-gradient-to-br from-surface-950 via-surface-900 to-primary-950/30"
      >
        {/* Grid pattern */}
        <div className="absolute inset-0 bg-grid opacity-50" />
        {/* Glow */}
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-20 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl" />

        <div className="relative z-10">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center shadow-glow-primary">
              <Truck size={22} className="text-white" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-100">ACRIP</div>
              <div className="text-xs text-slate-500">Agentic Risk Intelligence</div>
            </div>
          </div>

          <h1 className="text-4xl font-bold text-slate-100 leading-tight mb-4">
            Intelligent Risk
            <br />
            <span className="text-gradient">Monitoring Platform</span>
          </h1>
          <p className="text-slate-400 text-base leading-relaxed max-w-sm">
            AI-powered construction safety intelligence. Monitor site conditions, detect hazards, and manage risk across all your construction projects.
          </p>
        </div>

        {/* Feature highlights */}
        <div className="relative z-10 space-y-4">
          {[
            { icon: <Shield size={18} />, title: 'Site Risk Agent', desc: 'Automated hazard detection & risk scoring' },
            { icon: <Activity size={18} />, title: 'Real-time Monitoring', desc: 'Live site condition tracking across all sites' },
            { icon: <ChevronRight size={18} />, title: 'Compliance Ready', desc: 'OSHA & IS standards built-in' },
          ].map((f) => (
            <div key={f.title} className="flex items-start gap-3 glass-card p-3">
              <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center text-primary-400 shrink-0">
                {f.icon}
              </div>
              <div>
                <div className="text-sm font-medium text-slate-200">{f.title}</div>
                <div className="text-xs text-slate-500">{f.desc}</div>
              </div>
            </div>
          ))}
        </div>

        {/* AI Status */}
        <div className="relative z-10 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
          <span className="text-xs text-green-400 font-medium">AI Monitoring System Online</span>
        </div>
      </motion.div>

      {/* Right Side — Login Form */}
      <motion.div
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="flex-1 lg:max-w-md flex flex-col justify-center px-8 py-12 lg:px-12"
      >
        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-3 mb-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center">
            <Truck size={20} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-100">ACRIP</div>
            <div className="text-xs text-slate-500">Agentic Risk Intelligence</div>
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-100 mb-1">Welcome back</h2>
          <p className="text-sm text-slate-500">Sign in to your ACRIP account</p>
        </div>

        {/* Security Message */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-primary-500/5 border border-primary-500/20 mb-6">
          <Lock size={14} className="text-primary-400" />
          <span className="text-xs text-primary-400">Secure access to construction risk intelligence.</span>
        </div>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 mb-5"
          >
            <AlertCircle size={14} className="text-red-400" />
            <span className="text-xs text-red-400">{error}</span>
          </motion.div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div>
            <label className="label">Email Address</label>
            <input
              {...register('email')}
              type="email"
              placeholder="you@acriplatform.com"
              className={`input ${errors.email ? 'input-error' : ''}`}
              autoComplete="email"
            />
            {errors.email && (
              <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="label">Password</label>
            <div className="relative">
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                className={`input pr-10 ${errors.password ? 'input-error' : ''}`}
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.password && (
              <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                {...register('remember')}
                type="checkbox"
                className="w-3.5 h-3.5 rounded accent-primary-500"
              />
              <span className="text-sm text-slate-400">Remember me</span>
            </label>
            <button type="button" className="text-sm text-primary-400 hover:text-primary-300">
              Forgot password?
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3 text-base"
          >
            {loading ? <Spinner size={18} /> : 'Sign In'}
            {!loading && <ChevronRight size={16} />}
          </button>
        </form>

        {/* Demo credentials */}
        <div className="mt-8">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full divider" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-3 text-xs text-slate-600 bg-surface-950">Demo Accounts</span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-2">
            {DEMO_USERS.map((u) => (
              <button
                key={u.email}
                type="button"
                onClick={() => fillDemo(u.email, u.password)}
                className="flex items-center justify-between px-3 py-2 rounded-lg bg-surface-900 border border-slate-800 hover:border-slate-700 transition-all text-left group"
              >
                <div>
                  <div className="text-xs font-medium text-slate-300">{u.label}</div>
                  <div className="text-[10px] text-slate-600">{u.email}</div>
                </div>
                <ChevronRight size={12} className="text-slate-600 group-hover:text-primary-400 transition-colors" />
              </button>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
