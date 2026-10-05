import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Shield, Truck, Lock, AlertCircle, ChevronRight, Activity, User, Mail, CheckCircle2 } from 'lucide-react';
import { authApi } from '@/services/api';
import toast from 'react-hot-toast';
import { Spinner } from '@/components/common';

const schema = z.object({
  full_name: z.string().trim().min(2, 'Full name must be at least 2 characters'),
  email: z.string().trim().email('Enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirm_password: z.string().min(1, 'Please confirm your password'),
  role: z.string().optional(),
}).refine((data) => data.password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'site_manager' },
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    setError('');
    try {
      await authApi.register({
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        confirm_password: data.confirm_password,
        role: data.role || 'site_manager',
      });
      toast.success('Account created successfully! Please sign in.');
      navigate('/login', { state: { email: data.email, registered: true } });
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Please check your information and try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
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
            Autonomous Safety &amp;
            <br />
            <span className="text-gradient">Risk Monitoring</span>
          </h1>
          <p className="text-slate-400 text-base leading-relaxed max-w-sm">
            Join construction safety leaders. Monitor active sites, identify hazards proactively, and track compliance metrics with agentic AI intelligence.
          </p>
        </div>

        {/* Feature highlights */}
        <div className="relative z-10 space-y-4">
          {[
            { icon: <Shield size={18} />, title: 'Proactive Hazard Detection', desc: 'Continuous hazard and risk condition tracking' },
            { icon: <Activity size={18} />, title: 'Real-Time Risk Scoring', desc: 'Dynamic site risk indices and matrix assessments' },
            { icon: <CheckCircle2 size={18} />, title: 'Secure Instant Access', desc: 'Default Viewer access to project safety telemetry' },
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

      {/* Right Side — Register Form */}
      <motion.div
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="flex-1 lg:max-w-md flex flex-col justify-center px-8 py-10 lg:px-12"
      >
        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center">
            <Truck size={20} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-100">ACRIP</div>
            <div className="text-xs text-slate-500">Agentic Risk Intelligence</div>
          </div>
        </div>

        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-100 mb-1">Create Account</h2>
          <p className="text-sm text-slate-500">Sign up for your ACRIP platform account</p>
        </div>

        {/* Security Message */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-primary-500/5 border border-primary-500/20 mb-5">
          <Lock size={14} className="text-primary-400 shrink-0" />
          <span className="text-xs text-primary-400">Enterprise security. New accounts receive Viewer access by default.</span>
        </div>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 mb-5"
          >
            <AlertCircle size={14} className="text-red-400 shrink-0" />
            <span className="text-xs text-red-400">{error}</span>
          </motion.div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="label">Full Name</label>
            <div className="relative">
              <input
                {...register('full_name')}
                type="text"
                placeholder="e.g. Sarah Connor"
                className={`input pl-9 ${errors.full_name ? 'input-error' : ''}`}
                autoComplete="name"
              />
              <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            </div>
            {errors.full_name && (
              <p className="text-xs text-red-400 mt-1">{errors.full_name.message}</p>
            )}
          </div>

          <div>
            <label className="label">Email Address</label>
            <div className="relative">
              <input
                {...register('email')}
                type="email"
                placeholder="you@acriplatform.com"
                className={`input pl-9 ${errors.email ? 'input-error' : ''}`}
                autoComplete="email"
              />
              <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            </div>
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
                placeholder="At least 6 characters"
                className={`input pr-10 ${errors.password ? 'input-error' : ''}`}
                autoComplete="new-password"
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

          <div>
            <label className="label">Confirm Password</label>
            <div className="relative">
              <input
                {...register('confirm_password')}
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Repeat password"
                className={`input pr-10 ${errors.confirm_password ? 'input-error' : ''}`}
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.confirm_password && (
              <p className="text-xs text-red-400 mt-1">{errors.confirm_password.message}</p>
            )}
          </div>

          <div>
            <label className="label">Account Role</label>
            <select {...register('role')} className="input text-xs w-full">
              <option value="site_manager">Site Manager (Manage sites, hazards & operations)</option>
              <option value="safety_officer">Safety Officer (PPE Computer Vision & safety inspections)</option>
              <option value="viewer">Viewer (Read-only auditor & dashboards)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3 text-base mt-2"
          >
            {loading ? <Spinner size={18} /> : 'Sign Up'}
            {!loading && <ChevronRight size={16} />}
          </button>
        </form>

        {/* Link to Sign In */}
        <div className="mt-6 text-center">
          <p className="text-sm text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
              Sign In
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
