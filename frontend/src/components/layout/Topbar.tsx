import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu, Bell, Search, ChevronDown, LogOut, User,
  Settings, Activity, Wifi, AlertCircle
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';
import { ROLE_LABEL, ROLE_BADGE } from '@/utils/display';
import { authApi } from '@/services/api';
import toast from 'react-hot-toast';
import clsx from 'clsx';

export default function Topbar() {
  const { user, clearAuth } = useAuthStore();
  const { toggleSidebar, notificationCount } = useAppStore();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (_) {}
    clearAuth();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const initials = user?.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || 'U';

  return (
    <header className="h-14 flex items-center gap-3 px-4 bg-surface-900 border-b border-slate-800 sticky top-0 z-10">
      {/* Sidebar Toggle */}
      <button onClick={toggleSidebar} className="btn-icon shrink-0">
        <Menu size={18} />
      </button>

      {/* Search */}
      <div className="flex-1 max-w-md relative">
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-800 border border-slate-700 cursor-pointer hover:border-slate-600 transition-colors"
          onClick={() => setSearchOpen(true)}
        >
          <Search size={14} className="text-slate-500" />
          <span className="text-sm text-slate-500">Search projects, sites...</span>
          <kbd className="ml-auto text-[10px] text-slate-600 bg-surface-900 px-1.5 py-0.5 rounded border border-slate-700">
            ⌘K
          </kbd>
        </div>
      </div>

      <div className="flex-1" />

      {/* AI Status */}
      <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/5 border border-green-500/20">
        <Wifi size={12} className="text-green-400" />
        <span className="text-[11px] text-green-400 font-medium">Monitoring Online</span>
      </div>

      {/* Notifications */}
      <button
        className="btn-icon relative"
        onClick={() => navigate('/notifications')}
      >
        <Bell size={18} />
        {notificationCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] flex items-center justify-center font-bold">
            {notificationCount > 9 ? '9+' : notificationCount}
          </span>
        )}
      </button>

      {/* Profile */}
      <div ref={profileRef} className="relative">
        <button
          onClick={() => setProfileOpen(!profileOpen)}
          className="flex items-center gap-2.5 pl-1 pr-2 py-1 rounded-lg hover:bg-white/5 transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white">
            {initials}
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-medium text-slate-200 leading-none">{user?.full_name}</div>
            <div className="text-[10px] text-slate-500 mt-0.5 leading-none">
              {user ? ROLE_LABEL[user.role] : ''}
            </div>
          </div>
          <ChevronDown size={14} className="text-slate-500" />
        </button>

        <AnimatePresence>
          {profileOpen && (
            <motion.div
              initial={{ opacity: 0, y: 8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-2 w-56 card shadow-card-hover z-50 overflow-hidden"
            >
              {/* User Info */}
              <div className="px-4 py-3 border-b border-slate-800">
                <div className="font-medium text-sm text-slate-200">{user?.full_name}</div>
                <div className="text-xs text-slate-500 mt-0.5">{user?.email}</div>
                {user && (
                  <span className={clsx('badge mt-2', ROLE_BADGE[user.role])}>
                    {ROLE_LABEL[user.role]}
                  </span>
                )}
              </div>

              {/* Menu Items */}
              <div className="py-1">
                <MenuItem icon={<User size={14} />} label="Profile" onClick={() => { navigate('/settings'); setProfileOpen(false); }} />
                <MenuItem icon={<Activity size={14} />} label="Activity" onClick={() => { navigate('/notifications'); setProfileOpen(false); }} />
                <MenuItem icon={<Settings size={14} />} label="Preferences" onClick={() => { navigate('/settings'); setProfileOpen(false); }} />
              </div>

              <div className="border-t border-slate-800 py-1">
                <MenuItem
                  icon={<LogOut size={14} />}
                  label="Sign Out"
                  onClick={handleLogout}
                  danger
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}

function MenuItem({
  icon, label, onClick, danger = false
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center gap-3 w-full px-4 py-2.5 text-sm transition-colors',
        danger
          ? 'text-red-400 hover:bg-red-500/10'
          : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
      )}
    >
      {icon}
      {label}
    </button>
  );
}
