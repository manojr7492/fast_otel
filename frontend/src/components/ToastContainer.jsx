import React from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Info,
  X,
  Activity,
  ExternalLink
} from 'lucide-react';
import { useNotificationStore } from '../store/useNotificationStore';
import { getJaegerTraceUrl } from '../services/telemetry';

export default function ToastContainer() {
  const { toasts, removeToast } = useNotificationStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => {
        const isSuccess = toast.type === 'success';
        const isError = toast.type === 'error';

        return (
          <div
            key={toast.id}
            className="pointer-events-auto flex items-start gap-3 p-4 rounded-2xl glass-dropdown border border-slate-700/80 shadow-2xl animate-slide-up"
          >
            {/* Icon */}
            <div className="mt-0.5 flex-shrink-0">
              {isSuccess ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              ) : isError ? (
                <AlertCircle className="w-5 h-5 text-rose-400" />
              ) : (
                <Info className="w-5 h-5 text-indigo-400" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <h4 className="text-xs font-bold text-white mb-0.5">
                {toast.title}
              </h4>
              <p className="text-[11px] text-slate-300 leading-snug">
                {toast.message}
              </p>

              {/* Optional Jaeger Trace Link */}
              {toast.traceId && (
                <a
                  href={getJaegerTraceUrl(toast.traceId)}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-indigo-300 hover:text-white bg-indigo-950/70 border border-indigo-700/60 px-2 py-0.5 rounded-lg transition-colors"
                >
                  <Activity className="w-3 h-3 text-indigo-400" />
                  <span>Inspect in Jaeger</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              )}
            </div>

            {/* Dismiss Button */}
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-500 hover:text-white transition-colors p-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

