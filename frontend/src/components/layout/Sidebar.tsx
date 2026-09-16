import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, FolderOpen, MapPin, ShieldAlert,
  HardHat, ClipboardCheck, FileText, Bell, Users,
  Settings, ChevronRight, Shield, AlertTriangle,
  BarChart3, Truck, Activity, X
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';
import type { UserRole } from '@/types';
import clsx from 'clsx';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  roles?: UserRole[];
  comingSoon?: boolean;
  badge?: number;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={18} /> },
  { label: 'Projects', path: '/projects', icon: <FolderOpen size={18} />, roles: ['super_admin', 'project_manager'] },
  { label: 'Sites', path: '/sites', icon: <MapPin size={18} /> },
  { label: 'Risk Monitoring', path: '/risk-monitoring', icon: <ShieldAlert size={18} /> },
  { label: 'Safety', path: '/safety', icon: <HardHat size={18} /> },
  { label: 'Compliance', path: '/compliance', icon: <ClipboardCheck size={18} /> },
  { label: 'Insurance', path: '/insurance', icon: <Shield size={18} /> },
  { label: 'Incidents', path: '/incidents', icon: <AlertTriangle size={18} />, comingSoon: true },
  { label: 'Inspections', path: '/inspections', icon: <Activity size={18} />, comingSoon: true },
  { label: 'Reports', path: '/reports', icon: <BarChart3 size={18} />, comingSoon: true },
];

const bottomNavItems: NavItem[] = [
  { label: 'Notifications', path: '/notifications', icon: <Bell size={18} /> },
  { label: 'Users', path: '/users', icon: <Users size={18} />, roles: ['super_admin'] },
  { label: 'Settings', path: '/settings', icon: <Settings size={18} />, roles: ['super_admin', 'project_manager'] },
];

export default function Sidebar() {
  const { user } = useAuthStore();
  const { sidebarOpen, setSidebarOpen } = useAppStore();
  const location = useLocation();

  const canSee = (item: NavItem) => {
    if (!item.roles) return true;
    return user ? item.roles.includes(user.role) : false;
  };

  const sidebarVariants = {
    open: { x: 0, opacity: 1 },
    closed: { x: -280, opacity: 0 },
  };

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-20 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={sidebarOpen ? 'open' : 'closed'}
        variants={sidebarVariants}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className={clsx(
          'fixed left-0 top-0 h-full w-64 z-30 flex flex-col',
          'bg-surface-900 border-r border-slate-800',
          'lg:relative lg:translate-x-0',
          !sidebarOpen && 'lg:hidden'
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-4 py-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center shadow-glow-primary">
              <Truck size={18} className="text-white" />
            </div>
            <div>
              <div className="font-bold text-sm text-slate-100 leading-none">ACRIP</div>
              <div className="text-[10px] text-slate-500 mt-0.5 leading-none">Agentic Risk Intelligence</div>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="btn-icon lg:hidden"
          >
            <X size={16} />
          </button>
        </div>

        {/* AI Status */}
        <div className="mx-3 mt-3 px-3 py-2 rounded-lg bg-green-500/5 border border-green-500/20">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
            <span className="text-[11px] text-green-400 font-medium">AI Monitoring Active</span>
          </div>
        </div>

        {/* Main Nav */}
        <nav className="flex-1 overflow-y-auto px-3 pt-4 pb-2 space-y-0.5">
          {navItems.filter(canSee).map((item) => (
            <NavItem key={item.path} item={item} currentPath={location.pathname} />
          ))}

          <div className="pt-3 pb-1">
            <div className="text-[10px] font-medium text-slate-600 uppercase tracking-widest px-3 mb-1">System</div>
          </div>

          {bottomNavItems.filter(canSee).map((item) => (
            <NavItem key={item.path} item={item} currentPath={location.pathname} />
          ))}
        </nav>

        {/* Version */}
        <div className="px-4 py-3 border-t border-slate-800">
          <div className="text-[10px] text-slate-500 font-medium">
            ACRIP v1.0 · Phase 1.3
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Site Risk Agent (Rule Engine)
          </div>
        </div>
      </motion.aside>
    </>
  );
}

function NavItem({ item, currentPath }: { item: NavItem; currentPath: string }) {
  const isActive = currentPath === item.path || currentPath.startsWith(item.path + '/');

  if (item.comingSoon) {
    return (
      <div className={clsx('nav-item opacity-40 cursor-not-allowed select-none')}>
        {item.icon}
        <span className="flex-1">{item.label}</span>
        <span className="text-[9px] bg-slate-700 text-slate-500 px-1.5 py-0.5 rounded font-medium">SOON</span>
      </div>
    );
  }

  return (
    <NavLink to={item.path}>
      {({ isActive: navActive }) => (
        <div className={clsx(navActive ? 'nav-item-active' : 'nav-item')}>
          {item.icon}
          <span className="flex-1">{item.label}</span>
          {item.badge != null && (
            <span className="w-5 h-5 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center">
              {item.badge}
            </span>
          )}
          {navActive && <ChevronRight size={14} className="opacity-60" />}
        </div>
      )}
    </NavLink>
  );
}
