import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, FolderOpen, MapPin, ShieldAlert,
  HardHat, ClipboardCheck, FileText, Bell, Users,
  Settings, ChevronRight, Shield, AlertTriangle,
  BarChart3, Truck, Activity, X, Briefcase, Video, Cpu
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';
import { APP_FOOTER_TITLE, APP_FOOTER_SUBTITLE } from '@/utils/constants';
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

interface NavSection {
  title: string;
  items: NavItem[];
}

const coreNavItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={18} /> },
  { label: 'Executive Dashboard', path: '/executive-dashboard', icon: <Briefcase size={18} /> },
  { label: 'Projects', path: '/projects', icon: <FolderOpen size={18} />, roles: ['super_admin', 'project_manager'] },
  { label: 'Sites', path: '/sites', icon: <MapPin size={18} /> },
];

const intelligenceNavItems: NavItem[] = [
  { label: 'Risk Monitoring', path: '/risk-monitoring', icon: <ShieldAlert size={18} /> },
  { label: 'Safety', path: '/safety', icon: <HardHat size={18} /> },
  { label: 'Compliance', path: '/compliance', icon: <ClipboardCheck size={18} /> },
  { label: 'Insurance', path: '/insurance', icon: <Shield size={18} /> },
  { label: 'Reports', path: '/reports', icon: <BarChart3 size={18} /> },
];

const advancedNavItems: NavItem[] = [
  { label: 'Video Surveillance', path: '/video-surveillance', icon: <Video size={18} /> },
];

const systemNavItems: NavItem[] = [
  { label: 'Agent Orchestrator', path: '/orchestration', icon: <Cpu size={18} /> },
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
        <nav className="flex-1 overflow-y-auto px-3 pt-3 pb-2 space-y-4">
          {/* Core */}
          <div>
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-3 mb-1.5">Core</div>
            <div className="space-y-0.5">
              {coreNavItems.filter(canSee).map((item) => (
                <NavItem key={item.path} item={item} currentPath={location.pathname} />
              ))}
            </div>
          </div>

          {/* Intelligence */}
          <div>
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-3 mb-1.5">Intelligence</div>
            <div className="space-y-0.5">
              {intelligenceNavItems.filter(canSee).map((item) => (
                <NavItem key={item.path} item={item} currentPath={location.pathname} />
              ))}
            </div>
          </div>

          {/* Advanced Intelligence */}
          {advancedNavItems.filter(canSee).length > 0 && (
            <div>
              <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-3 mb-1.5">Advanced Intelligence</div>
              <div className="space-y-0.5">
                {advancedNavItems.filter(canSee).map((item) => (
                  <NavItem key={item.path} item={item} currentPath={location.pathname} />
                ))}
              </div>
            </div>
          )}

          {/* System */}
          <div>
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-3 mb-1.5">System</div>
            <div className="space-y-0.5">
              {systemNavItems.filter(canSee).map((item) => (
                <NavItem key={item.path} item={item} currentPath={location.pathname} />
              ))}
            </div>
          </div>
        </nav>

        {/* Platform Footer */}
        <div className="px-4 py-3 border-t border-slate-800 bg-surface-950/40">
          <div className="text-[10px] text-slate-300 font-medium truncate">
            {APP_FOOTER_TITLE}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {APP_FOOTER_SUBTITLE}
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
