import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, CheckCheck, Clock } from 'lucide-react';
import { notificationsApi } from '@/services/api';
import { EmptyState, PageLoader } from '@/components/common';
import { formatRelativeTime } from '@/utils/display';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import type { Notification } from '@/types';

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'border-l-red-500 bg-red-500/5',
  warning: 'border-l-amber-500 bg-amber-500/5',
  error: 'border-l-orange-500 bg-orange-500/5',
  info: 'border-l-blue-500 bg-blue-500/5',
};

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data: notifications, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list().then(r => r.data),
  });

  const markAllMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      toast.success('All marked as read');
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
    },
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const unreadCount = notifications?.filter((n: Notification) => !n.is_read).length ?? 0;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-subtitle">
            {unreadCount > 0 ? `${unreadCount} unread alerts` : 'All caught up'}
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            className="btn-secondary text-sm"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
          >
            <CheckCheck size={14} /> Mark All Read
          </button>
        )}
      </div>

      {isLoading && <PageLoader />}

      {!isLoading && (!notifications || notifications.length === 0) && (
        <EmptyState
          icon={<Bell size={28} />}
          title="No notifications"
          description="You're all caught up! Alerts and risk notifications will appear here."
        />
      )}

      {!isLoading && notifications && notifications.length > 0 && (
        <div className="space-y-3">
          {notifications.map((n: Notification, i: number) => (
            <motion.div
              key={n.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03 }}
              className={clsx(
                'card p-4 border-l-4 cursor-pointer transition-all hover:bg-white/2',
                SEVERITY_STYLES[n.severity] || SEVERITY_STYLES.info,
                !n.is_read && 'ring-1 ring-inset ring-white/5'
              )}
              onClick={() => !n.is_read && markReadMutation.mutate(n.id)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-primary-400" />
                    )}
                    <span className="text-sm font-semibold text-slate-200">{n.title}</span>
                    <span className={clsx(
                      'badge text-[10px]',
                      n.category === 'risk' ? 'badge-critical' :
                      n.category === 'safety' ? 'badge-warning' :
                      n.category === 'compliance' ? 'badge-monitoring' : 'badge-inactive'
                    )}>
                      {n.category.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400">{n.message}</p>
                </div>
                <div className="text-[11px] text-slate-600 flex items-center gap-1 shrink-0">
                  <Clock size={11} />
                  {formatRelativeTime(n.created_at)}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
