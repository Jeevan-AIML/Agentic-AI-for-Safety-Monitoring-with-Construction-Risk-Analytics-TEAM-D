import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { useAppStore } from '@/store/appStore';
import { notificationsApi } from '@/services/api';
import { useQuery } from '@tanstack/react-query';

export default function AppShell() {
  const { sidebarOpen, setNotificationCount } = useAppStore();

  // Poll notifications every 30 seconds
  const { data: notifications } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: () => notificationsApi.list(true).then(r => r.data),
    refetchInterval: 30000,
    staleTime: 15000,
  });

  useEffect(() => {
    if (notifications) {
      setNotificationCount(notifications.length);
    }
  }, [notifications, setNotificationCount]);

  return (
    <div className="flex h-screen overflow-hidden bg-surface-950">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto bg-grid">
          <div className="max-w-screen-2xl mx-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
