import { create } from 'zustand';
import { api } from '../services/api';

export const useNotificationStore = create((set, get) => ({
  notifications: [
    {
      notification_id: 'notif-welcome-init',
      recipient_email: 'demo@antigravity.io',
      event_type: 'SYSTEM_STARTUP',
      details: 'All 6 FastAPI microservices linked with OpenTelemetry & Jaeger.',
      dispatched_at: new Date().toISOString(),
      read: false,
    },
  ],
  unreadCount: 1,
  isCenterOpen: false,
  toasts: [],

  toggleCenter: () => {
    const nextState = !get().isCenterOpen;
    set({ isCenterOpen: nextState });
    if (nextState) {
      get().markAllRead();
    }
  },

  closeCenter: () => set({ isCenterOpen: false }),

  addToast: (title, message, type = 'info', traceId = null) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const newToast = { id, title, message, type, traceId, createdAt: Date.now() };

    set((state) => ({ toasts: [...state.toasts, newToast] }));

    // Auto dismiss after 5.5 seconds
    setTimeout(() => {
      get().removeToast(id);
    }, 5500);

    return id;
  },

  removeToast: (id) => {
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
  },

  fetchNotifications: async () => {
    try {
      const history = await api.notification.getHistory();
      if (Array.isArray(history) && history.length > 0) {
        set({
          notifications: history,
          unreadCount: history.length,
        });
      }
    } catch (err) {
      console.warn('Notification history fetch fallback:', err.message);
    }
  },

  markAllRead: () => {
    set({ unreadCount: 0 });
  },
}));

