import { create } from 'zustand';

interface AppStore {
  sidebarOpen: boolean;
  selectedProjectId: string | null;
  selectedSiteId: string | null;
  notificationCount: number;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSelectedProject: (id: string | null) => void;
  setSelectedSite: (id: string | null) => void;
  setNotificationCount: (count: number) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  sidebarOpen: true,
  selectedProjectId: null,
  selectedSiteId: null,
  notificationCount: 0,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setSelectedProject: (id) => set({ selectedProjectId: id }),
  setSelectedSite: (id) => set({ selectedSiteId: id }),
  setNotificationCount: (count) => set({ notificationCount: count }),
}));
