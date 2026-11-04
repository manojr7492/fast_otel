/**
 * OpenTelemetry Frontend Tracing & W3C Trace Context Propagation Engine
 * Implements W3C Trace Context specification (RFC 00-{trace_id}-{span_id}-01)
 * Correlates browser API transactions with backend microservices and Jaeger UI.
 */

// Generate a random 32-hex lowercase character string (128-bit Trace ID)
export function generateTraceId() {
  const chars = '0123456789abcdef';
  let traceId = '';
  for (let i = 0; i < 32; i++) {
    traceId += chars[Math.floor(Math.random() * 16)];
  }
  return traceId;
}

// Generate a random 16-hex lowercase character string (64-bit Span ID)
export function generateSpanId() {
  const chars = '0123456789abcdef';
  let spanId = '';
  for (let i = 0; i < 16; i++) {
    spanId += chars[Math.floor(Math.random() * 16)];
  }
  return spanId;
}

// Format W3C traceparent header: 00-{trace_id}-{span_id}-01
export function createW3CTraceparent(traceId = generateTraceId(), spanId = generateSpanId()) {
  return {
    traceId,
    spanId,
    traceparent: `00-${traceId}-${spanId}-01`,
  };
}

export function getJaegerTraceUrl(traceId) {
  if (!traceId) return 'http://localhost:16686/search';
  return `http://localhost:16686/trace/${traceId}`;
}

export function getJaegerServiceUrl(serviceName = 'user-service') {
  return `http://localhost:16686/search?service=${encodeURIComponent(serviceName)}`;
}

// Real-time In-Memory Telemetry Collector for UI Observability
class ClientTelemetryHub {
  constructor() {
    this.traces = [];
    this.subscribers = new Set();
  }

  recordTrace(record) {
    const entry = {
      id: `${record.traceId}-${record.spanId}-${Date.now()}`,
      timestamp: new Date().toISOString(),
      traceId: record.traceId,
      spanId: record.spanId,
      backendTraceId: record.backendTraceId || record.traceId,
      service: record.service || 'unknown-service',
      endpoint: record.endpoint || '',
      method: (record.method || 'GET').toUpperCase(),
      status: record.status || 200,
      durationMs: record.durationMs || 0,
      success: record.status >= 200 && record.status < 400,
      error: record.error || null,
      jaegerUrl: getJaegerTraceUrl(record.backendTraceId || record.traceId),
    };

    this.traces.unshift(entry);
    if (this.traces.length > 50) {
      this.traces.pop();
    }

    this.notify();
    return entry;
  }

  getTraces() {
    return [...this.traces];
  }

  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  notify() {
    for (const callback of this.subscribers) {
      try {
        callback(this.getTraces());
      } catch (err) {
        console.error('Telemetry subscriber error:', err);
      }
    }
  }

  clear() {
    this.traces = [];
    this.notify();
  }
}

export const telemetryHub = new ClientTelemetryHub();

