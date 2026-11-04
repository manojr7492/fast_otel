import React, { useEffect } from 'react';
import {
  X,
  Bell,
  Mail,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { useNotificationStore } from '../store/useNotificationStore';

export default function NotificationCenter() {
  const { notifications, isCenterOpen, closeCenter, fetchNotifications } = useNotificationStore();

  useEffect(() => {
    if (isCenterOpen) {
      fetchNotifications();
    }
  }, [isCenterOpen]);

  if (!isCenterOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div
        onClick={closeCenter}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-sm bg-[#0C111D] border-l border-slate-800 shadow-2xl flex flex-col justify-between">
          
          {/* Header */}
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                <Bell className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Event Audit Log</h3>
                <p className="text-[11px] text-slate-400">
                  Notification Microservice (:8006)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={fetchNotifications}
                title="Refresh notifications"
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={closeCenter}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Notifications Feed */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {notifications.length === 0 ? (
              <div className="text-center py-12 text-xs text-slate-400">
                No notification events recorded yet.
              </div>
            ) : (
              notifications.map((notif, idx) => (
                <div
                  key={notif.notification_id || idx}
                  className="p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-colors text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1 font-mono text-[10px] uppercase font-bold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded">
                      {notif.event_type}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {notif.dispatched_at ? new Date(notif.dispatched_at).toLocaleTimeString() : 'Recent'}
                    </span>
                  </div>

                  <p className="text-white font-medium text-[11px]">
                    {notif.details || `Event ${notif.event_type} dispatched.`}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/60">
                    <span className="truncate max-w-[180px]">
                      {notif.recipient_email}
                    </span>
                    <span className="text-emerald-400 font-medium">DELIVERED</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-800 bg-slate-950/60 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Dispatched via SMTP channel mock</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>

        </div>
      </div>
    </div>
  );
}

