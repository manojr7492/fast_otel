import React from 'react';
import {
  X,
  Activity,
  ExternalLink,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Copy,
  Radio,
  Clock,
  Layers
} from 'lucide-react';
import { useTelemetryStore } from '../store/useTelemetryStore';
import { getJaegerTraceUrl, getJaegerServiceUrl } from '../services/telemetry';

export default function TelemetryDrawer() {
  const { isOpen, close, traces, clear, activeFilter, setFilter } = useTelemetryStore();

  if (!isOpen) return null;

  const filteredTraces = activeFilter === 'all'
    ? traces
    : traces.filter((t) => t.service === activeFilter);

  const services = [
    'all',
    'user-service',
    'product-service',
    'order-service',
    'payment-service',
    'inventory-service',
    'notification-service',
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={close}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity animate-fade-in"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-6 sm:pl-10">
        <div className="w-screen max-w-xl bg-[#0A0E17] border-l border-indigo-900/40 shadow-2xl flex flex-col justify-between">
          
          {/* Header */}
          <div className="p-5 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <Activity className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>OpenTelemetry Live Traces</span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 text-[10px] font-mono border border-emerald-800/40">
                    Jaeger OTLP Active
                  </span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  W3C Trace Context correlated with Jaeger UI (localhost:16686)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={clear}
                title="Clear live traces"
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={close}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Jaeger Quick Launch Banner */}
          <div className="px-5 py-3 bg-indigo-950/30 border-b border-indigo-900/30 flex items-center justify-between text-xs">
            <span className="text-indigo-300 flex items-center gap-1.5 font-medium">
              <Radio className="w-3.5 h-3.5 text-indigo-400" />
              Jaeger Receiver: <code className="font-mono text-white">localhost:4318</code>
            </span>
            <a
              href="http://localhost:16686/search"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-200 font-semibold"
            >
              <span>Search UI</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Filter Pills */}
          <div className="px-5 py-2.5 bg-slate-900/40 border-b border-slate-800 overflow-x-auto flex gap-1.5">
            {services.map((svc) => (
              <button
                key={svc}
                onClick={() => setFilter(svc)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-mono whitespace-nowrap transition-colors ${
                  activeFilter === svc
                    ? 'bg-indigo-600 text-white font-semibold'
                    : 'bg-slate-800/70 text-slate-400 hover:text-slate-200'
                }`}
              >
                {svc === 'all' ? 'All Services' : svc.replace('-service', '')}
              </button>
            ))}
          </div>

          {/* Traces Feed */}
          <div className="flex-1 overflow-y-auto p-5 space-y-3">
            {filteredTraces.length === 0 ? (
              <div className="text-center py-16 text-slate-500 text-xs">
                <Activity className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p>No traces recorded yet for this filter.</p>
                <span className="text-[11px] text-slate-600">
                  Perform any search, add to cart, or checkout to capture distributed trace trees.
                </span>
              </div>
            ) : (
              filteredTraces.map((trace) => {
                const isSuccess = trace.status >= 200 && trace.status < 400;

                return (
                  <div
                    key={trace.id}
                    className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 transition-colors text-xs space-y-2"
                  >
                    {/* Top Row: Service & Status */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-1.5 py-0.5 rounded font-mono font-bold text-[10px] ${
                            trace.method === 'GET'
                              ? 'bg-blue-950 text-blue-300'
                              : 'bg-emerald-950 text-emerald-300'
                          }`}
                        >
                          {trace.method}
                        </span>
                        <span className="font-mono font-bold text-white text-[11px]">
                          {trace.service}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] text-slate-400 flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-500" />
                          {trace.durationMs}ms
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            isSuccess
                              ? 'bg-emerald-950 text-emerald-300'
                              : 'bg-rose-950 text-rose-300'
                          }`}
                        >
                          {trace.status}
                        </span>
                      </div>
                    </div>

                    {/* Endpoint path */}
                    <p className="font-mono text-[11px] text-slate-300 truncate">
                      {trace.endpoint}
                    </p>

                    {/* Trace ID & W3C Span */}
                    <div className="flex items-center justify-between p-2 rounded-xl bg-black/50 border border-slate-800 text-[10px] font-mono text-slate-400">
                      <div className="truncate">
                        <span className="text-slate-500">Trace: </span>
                        <span className="text-indigo-300 font-bold">
                          {trace.backendTraceId || trace.traceId}
                        </span>
                      </div>

                      {/* Direct Clickable Jaeger Trace Link */}
                      <a
                        href={getJaegerTraceUrl(trace.backendTraceId || trace.traceId)}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 px-2 py-1 rounded bg-indigo-600/80 hover:bg-indigo-600 text-white font-medium ml-2 flex-shrink-0 transition-colors"
                      >
                        <span>Open in Jaeger</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    </div>

                    {trace.error && (
                      <p className="text-[10px] text-rose-400 font-mono">
                        Error: {trace.error}
                      </p>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Footer Info */}
          <div className="p-4 border-t border-slate-800 bg-slate-950/80 text-[11px] text-slate-400 flex items-center justify-between">
            <span className="font-mono">
              W3C traceparent: <code>00-{'{trace_id}'}-{'{span_id}'}-01</code>
            </span>
            <span className="text-indigo-400 font-semibold">{filteredTraces.length} Traces</span>
          </div>

        </div>
      </div>
    </div>
  );
}

