# OpenTelemetry & Jaeger Distributed Tracing Guide

This comprehensive guide explains **OpenTelemetry (OTel)** and **Jaeger** from foundational concepts to end-to-end installation, architectural design, client-to-backend context propagation, and real-world debugging.

---

## Table of Contents
1. [What is OpenTelemetry?](#1-what-is-opentelemetry)
2. [What is Jaeger?](#2-what-is-jaeger)
3. [Why Use OpenTelemetry & Jaeger?](#3-why-use-opentelemetry--jaeger)
4. [Core Concepts: Spans, Traces & Context Propagation](#4-core-concepts-spans-traces--context-propagation)
5. [Where Does It Live in this E-Commerce Platform?](#5-where-does-it-live-in-this-e-commerce-platform)
6. [When to Use Tracing vs Logging vs Metrics](#6-when-to-use-tracing-vs-logging-vs-metrics)
7. [Installation & Setup from Scratch](#7-installation--setup-from-scratch)
   - [A. Running Jaeger with Docker](#a-running-jaeger-with-docker)
   - [B. Python FastAPI Microservices Setup](#b-python-fastapi-microservices-setup)
   - [C. React Frontend W3C Context Propagation Setup](#c-react-frontend-w3c-context-propagation-setup)
8. [How Distributed Tracing Works End-to-End](#8-how-distributed-tracing-works-end-to-end)
9. [How to Use the Jaeger UI for Troubleshooting](#9-how-to-use-the-jaeger-ui-for-troubleshooting)
10. [Testing Distributed Saga Rollback & Error Spans](#10-testing-distributed-saga-rollback--error-spans)
11. [Production Best Practices & Checklist](#11-production-best-practices--checklist)

---

## 1. What is OpenTelemetry?

**OpenTelemetry (OTel)** is a vendor-neutral, open-source observability framework hosted by the **Cloud Native Computing Foundation (CNCF)**. It provides a standardized set of APIs, SDKs, and tooling to generate, collect, and export telemetry data:
- **Traces**: The distributed path and timing of a request across services.
- **Metrics**: Quantitative numerical measurements (CPU, error counts, latency histograms).
- **Logs**: Structured event records emitted by services.

### Key Philosophy: Standardization Without Lock-In
Before OpenTelemetry, instrumenting code for Datadog, New Relic, Dynatrace, or AWS X-Ray required proprietary SDKs. Switching vendors meant rewriting application code. 

With OpenTelemetry:
- You instrument your code **once** using the universal OTel API.
- You change your telemetry destination (Jaeger, Tempo, Datadog, etc.) simply by modifying an environment variable (`OTEL_EXPORTER_OTLP_ENDPOINT`).

---

## 2. What is Jaeger?

**Jaeger** is an open-source, end-to-end distributed tracing system originally developed by Uber Technologies and graduated by the CNCF.

While **OpenTelemetry is the collector and instrumentation library inside your code**, **Jaeger is the backend server and web visualizer** that ingests those traces, indexes them, and displays interactive timeline flamegraphs.

```
┌────────────────────────────────┐
│   OpenTelemetry SDK in App     │  (Generates Spans & Trace IDs)
└───────────────┬────────────────┘
                │ OTLP Export (Port 4318 HTTP / 4317 gRPC)
                ▼
┌────────────────────────────────┐
│        Jaeger Collector        │  (Validates, Buffers, Indexes Spans)
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│   Storage (Memory / DB)        │  (Stores Trace DAGs)
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│      Jaeger Web UI (:16686)    │  (Interactive Waterfall Flamegraphs)
└────────────────────────────────┘
```

### Jaeger Default Port Reference
| Port | Protocol | Purpose |
|---|---|---|
| **`16686`** | HTTP | **Jaeger Web UI & Search API** (`http://localhost:16686`) |
| **`4317`** | gRPC | **OTLP gRPC Receiver** for high-throughput span ingestion |
| **`4318`** | HTTP | **OTLP HTTP Receiver** (`/v1/traces`) used by Python & web clients |
| **`14268`** | HTTP | Legacy Jaeger thrift collector (deprecated in favor of OTLP) |

---

## 3. Why Use OpenTelemetry & Jaeger?

In monolithic architectures, a single error log or stack trace is usually enough to diagnose a bug. 

In a distributed microservice ecosystem:
1. A single user click on **"Confirm Order"** touches **6 distinct services** (`order_service`, `product_service`, `inventory_service`, `payment_service`, `notification_service`, and `user_service`).
2. Without distributed tracing, if an order takes 4.5 seconds or fails with HTTP 500:
   - You have to open logs across 6 different server instances.
   - You cannot determine which service started first, which downstream call hung, or which database query caused a lock.
3. **With OpenTelemetry + Jaeger**:
   - One globally unique **Trace ID** travels across every single network boundary.
   - Jaeger renders an interactive flamegraph showing every service, every database query, every latency duration, and any exception stack traces in a single view.

---

## 4. Core Concepts: Spans, Traces & Context Propagation

### 1. Span (The Atom of Tracing)
A **Span** represents a single contiguous unit of work. For example:
- Handling an incoming HTTP request (`GET /api/v1/products`)
- Executing a database query (`SELECT * FROM inventory WHERE sku = 'MACBOOK-M3'`)
- Encrypting a password with bcrypt
- Dispatching an event over HTTP or message queue

Every Span contains:
- **Name**: Operation description (e.g., `orders.checkout`, `inventory.reserve_stock`).
- **Span ID**: 64-bit hex string (e.g., `00f067aa0ba902b7`).
- **Trace ID**: 128-bit hex string shared by all spans in this transaction.
- **Parent Span ID**: Points to the caller span (forming a tree hierarchy).
- **Start & End Timestamps**: Measures exact microsecond duration.
- **Attributes**: Key-value context metadata (e.g. `http.status_code: 200`, `sku: "MACBOOK-M3"`, `user.uuid: "usr-42"`).
- **Status**: `UNSET`, `OK`, or `ERROR`.
- **Events**: In-span milestones (e.g., recorded Python exceptions with stack traces).

### 2. Trace (The Complete Journey)
A **Trace** is a Directed Acyclic Graph (DAG) of spans representing an entire end-to-end user transaction:

```
[Browser: User clicks "Confirm Order"] (Root Span)
  │
  ├── [order-service: POST /api/v1/orders/checkout] (Duration: 185ms)
  │     │
  │     ├── [order-service: db.execute SELECT * FROM orders] (Duration: 8ms)
  │     │
  │     ├── [inventory-service: POST /api/v1/inventory/reserve] (Duration: 42ms)
  │     │     └── [inventory-service: db.execute UPDATE inventory SET reserved=...] (Duration: 12ms)
  │     │
  │     ├── [payment-service: POST /api/v1/payments/process] (Duration: 65ms)
  │     │     └── [payment-service: bank_gateway_authorization] (Duration: 55ms)
  │     │
  │     └── [notification-service: POST /api/v1/notifications/send] (Duration: 28ms)
```

### 3. W3C Trace Context Standard (`traceparent`)
To propagate context across network boundaries, OpenTelemetry uses the universal **W3C Trace Context** specification. This is passed as an HTTP request header:

```http
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              │  │                                │                │
      Version ┘  └────────── Trace ID ────────────┘ Span ID ───────┴─ Flags (01 = sampled)
```

1. **Version** (`00`): W3C specification version.
2. **Trace ID** (`32 hex digits`): Universal transaction ID.
3. **Parent Span ID** (`16 hex digits`): ID of the calling span.
4. **Trace Flags** (`01`): Bitmask (where `01` means "record and export this trace").

---

## 5. Where Does It Live in this E-Commerce Platform?

### In the React Frontend (`/frontend`)
1. **[`src/services/telemetry.js`](file:///Users/manojkumar/Desktop/FastAPI/frontend/src/services/telemetry.js)**:
   - Generates W3C `traceparent` headers for outgoing user transactions.
   - Collects live trace records into an in-memory client telemetry hub.
   - Builds direct one-click links to Jaeger UI: `http://localhost:16686/trace/{traceId}`.
2. **[`src/services/api.js`](file:///Users/manojkumar/Desktop/FastAPI/frontend/src/services/api.js)**:
   - **Axios Request Interceptor**: Automatically generates and injects `traceparent` and `X-Request-ID` into every HTTP call.
   - **Axios Response Interceptor**: Reads backend `X-Trace-ID` and latency headers, logging the correlated span.
3. **[`src/components/TelemetryDrawer.jsx`](file:///Users/manojkumar/Desktop/FastAPI/frontend/src/components/TelemetryDrawer.jsx)**:
   - Slides out from the top-bar **"Traces"** pill to display real-time client API calls, HTTP status codes, and direct links to Jaeger.
4. **[`src/components/CheckoutModal.jsx`](file:///Users/manojkumar/Desktop/FastAPI/frontend/src/components/CheckoutModal.jsx)**:
   - Captures the backend transaction's Trace ID and displays a prominent **"Open Full Trace in Jaeger UI"** button.

### In the FastAPI Backend (`/services`)
1. **`app/core/telemetry.py`** (Present in all 6 microservices):
   - Sets up `TracerProvider`, `Resource(service_name=...)`, and `OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")`.
   - Automatically instruments FastAPI HTTP endpoints, SQLAlchemy database sessions, and HTTPX inter-service clients.
2. **`app/main.py`**:
   - `CORSMiddleware`: Exposes `X-Trace-ID`, `X-Span-ID`, `X-Request-ID`, and `X-Process-Time-Ms` to browser JavaScript.
   - Timing and correlation middleware extracts active span context and attaches it to response headers.

---

## 6. When to Use Tracing vs Logging vs Metrics

| Feature | Traces (OpenTelemetry + Jaeger) | Structured Logs (JSON stdout) | Metrics (Prometheus) |
|---|---|---|---|
| **Primary Question** | *"Where in the distributed call chain did latency or failure occur?"* | *"What exact debug details happened inside this specific service?"* | *"What is the overall system health, error rate, and throughput?"* |
| **Data Structure** | Directed Acyclic Graph (DAG) of Spans | Timestamped text/JSON log lines with `trace_id` | Aggregated counters, gauges, histograms |
| **Best Used For** | Microservice-to-microservice latency bottlenecks, saga rollbacks | Debugging internal functions, stack traces, variable values | Real-time alerting (CPU > 90%, 5xx rate > 1%) |
| **Storage Cost** | Moderate (governed by sampling ratio) | High (every debug line stored) | Low (pre-aggregated numerical time series) |

---

## 7. Installation & Setup from Scratch

### A. Running Jaeger with Docker

The fastest, standard way to run Jaeger locally is using the official all-in-one Docker image:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Or within [`docker-compose.yml`](file:///Users/manojkumar/Desktop/FastAPI/docker-compose.yml):

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686" # Web UI
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    restart: unless-stopped
```

Verify Jaeger is up:
- Open your browser to: `http://localhost:16686`

---

### B. Python FastAPI Microservices Setup

#### 1. Install Dependencies
```bash
pip install \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp-proto-http \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-instrumentation-httpx \
  opentelemetry-instrumentation-sqlalchemy \
  opentelemetry-instrumentation-logging
```

#### 2. Configure Telemetry (`telemetry.py`)
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

def setup_telemetry(app, service_name: str, otlp_endpoint: str = "http://localhost:4318/v1/traces"):
    # 1. Define identity of this microservice
    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": "development"
    })

    # 2. Configure Tracer Provider with 100% sampling
    provider = TracerProvider(
        resource=resource,
        sampler=TraceIdRatioBased(1.0)
    )

    # 3. Configure asynchronous OTLP HTTP Exporter
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, timeout=5.0)
    processor = BatchSpanProcessor(exporter, max_queue_size=2048, schedule_delay_millis=500)
    provider.add_span_processor(processor)

    # 4. Set as global default
    trace.set_tracer_provider(provider)

    # 5. Automatically instrument incoming FastAPI calls and outgoing HTTPX calls
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    HTTPXClientInstrumentor().instrument()
```

---

### C. React Frontend W3C Context Propagation Setup

In the React frontend, Axios injects the `traceparent` header into every request:

#### 1. Generating W3C Traceparent Header (`telemetry.js`)
```javascript
export function generateTraceId() {
  const chars = '0123456789abcdef';
  let traceId = '';
  for (let i = 0; i < 32; i++) {
    traceId += chars[Math.floor(Math.random() * 16)];
  }
  return traceId;
}

export function generateSpanId() {
  const chars = '0123456789abcdef';
  let spanId = '';
  for (let i = 0; i < 16; i++) {
    spanId += chars[Math.floor(Math.random() * 16)];
  }
  return spanId;
}

export function createW3CTraceparent() {
  const traceId = generateTraceId();
  const spanId = generateSpanId();
  return {
    traceId,
    spanId,
    traceparent: `00-${traceId}-${spanId}-01`,
  };
}
```

#### 2. Axios Request Interceptor (`api.js`)
```javascript
import axios from 'axios';
import { createW3CTraceparent } from './telemetry';

const client = axios.create({ baseURL: 'http://localhost:8003' });

client.interceptors.request.use((config) => {
  const { traceId, spanId, traceparent } = createW3CTraceparent();
  
  // Inject standard W3C header
  config.headers['traceparent'] = traceparent;
  config.headers['X-Request-ID'] = `req-${Date.now()}`;
  
  // Preserve for latency computation
  config.metadata = { startTime: performance.now(), traceId, spanId };
  return config;
});

client.interceptors.response.use((response) => {
  const duration = Math.round(performance.now() - response.config.metadata.startTime);
  const backendTraceId = response.headers['x-trace-id'] || response.config.metadata.traceId;
  
  console.log(`[Trace: ${backendTraceId}] Completed in ${duration}ms`);
  return response;
});
```

---

## 8. How Distributed Tracing Works End-to-End

Here is the exact step-by-step lifecycle of an order checkout in this project:

1. **User Action**: User clicks **"Place & Confirm Order"** on `http://localhost:5173`.
2. **Client Header Injection**: The frontend's Axios interceptor creates:
   `traceparent: 00-cc0f8450a5d6cb7de94cb460bd19412e-1a2b3c4d5e6f7a8b-01`
3. **Service 1 Entry (`order_service :8003`)**:
   - `FastAPIInstrumentor` detects the `traceparent` header.
   - Instead of creating a new trace ID, it **adopts `cc0f8450a5d6cb7de94cb460bd19412e`** as the active Trace ID.
   - It starts an internal span: `order.checkout`.
4. **Service 2 Downstream (`inventory_service :8005`)**:
   - `order_service` calls `POST http://localhost:8005/api/v1/inventory/reserve`.
   - `HTTPXClientInstrumentor` injects a new `traceparent` header with the **same Trace ID**, but setting `order_service`'s current span as the parent.
   - `inventory_service` receives the request and records its database update span under the same tree.
5. **Service 3 Downstream (`payment_service :8004`)**:
   - `order_service` calls `POST http://localhost:8004/api/v1/payments/process`.
   - `payment_service` authorizes the payment and returns.
6. **Service 4 Downstream (`notification_service :8006`)**:
   - `order_service` dispatches a welcome/order confirmation event to `notification_service`.
7. **Trace Export**:
   - Each microservice's `BatchSpanProcessor` asynchronously flushes spans to Jaeger at `http://localhost:4318/v1/traces`.
8. **UI Correlation**:
   - `order_service` returns HTTP 201 with header: `X-Trace-ID: cc0f8450a5d6cb7de94cb460bd19412e`.
   - The React UI displays the Order Confirmation modal with a direct link to Jaeger:
     `http://localhost:16686/trace/cc0f8450a5d6cb7de94cb460bd19412e`.

---

## 9. How to Use the Jaeger UI for Troubleshooting

### 1. Finding Traces
1. Open **`http://localhost:16686/search`** in your browser.
2. In the left panel:
   - **Service**: Select `order-service` (or any of the 6 microservices).
   - **Operation**: Select `all` or a specific route like `POST /api/v1/orders/checkout`.
   - **Tags**: Filter by specific attributes (e.g. `http.status_code=400` or `error=true`).
3. Click **"Find Traces"**.

### 2. Inspecting the Timeline Waterfall
Clicking on any trace in the search results opens the **Trace Timeline View**:
- **Depth & Hierarchy**: Indented child bars show nested downstream calls.
- **Latency Bars**: The horizontal length of each bar represents its duration. If an order took 2,000ms, you can instantly see which bar takes up 90% of the timeline width.
- **Span Detail Drawer**: Clicking any span displays:
  - Exact SQL query executed
  - Client IP and HTTP User Agent
  - HTTP method, route, and status code
  - Process ID and service version

---

## 10. Testing Distributed Saga Rollback & Error Spans

To observe how OpenTelemetry and Jaeger capture system failures and compensation sagas:

1. Open the React frontend at **`http://localhost:5173`**.
2. Add any hardware item to your cart and proceed to Checkout.
3. Enable the **"⚠️ Simulate Payment Failure"** toggle.
4. Click **"Place Order"**.

### What Happens Behind the Scenes:
1. `order_service` drafts the order and reserves stock in `inventory_service`.
2. `payment_service` simulates an issuer card decline (`CARD_DECLINED`).
3. `order_service` catches the `PaymentFailedException`.
4. The distributed saga executes **Compensation**:
   - Calls `POST /api/v1/inventory/release` to cleanly return reserved inventory to the warehouse pool.
   - Marks the order as `CANCELLED`.
5. OpenTelemetry records:
   - Span status: `ERROR` (colored **RED** in Jaeger).
   - An event attached to the span containing the full exception traceback.
6. Click **"Open Full Trace in Jaeger UI"** on screen to view the red error span and verify that the saga compensation executed successfully!

---

## 11. Production Best Practices & Checklist

1. **Configurable Sampling**:
   - In local dev: `OTEL_SAMPLING_RATIO=1.0` (100% of traces captured).
   - In high-throughput production (10,000+ RPS): `OTEL_SAMPLING_RATIO=0.05` (5% sample) to avoid saturating storage while capturing statistically significant performance profiles.
2. **Use BatchSpanProcessor**:
   - Never use `SimpleSpanProcessor` in production. Always use `BatchSpanProcessor` so traces are exported asynchronously in the background and never block user requests.
3. **Resilient Failure Handling**:
   - If the Jaeger container crashes or the network blips, OpenTelemetry gracefully drops spans in memory. It must **never** cause customer business requests to fail with HTTP 500.
4. **PII and Secret Redaction**:
   - Never record credit card CVVs, plain passwords, or secret JWT signing keys inside span attributes or span events.
5. **CORS Expose Headers**:
   - Ensure backend CORS middleware includes `expose_headers=["*"]` (or explicitly `X-Trace-ID`, `X-Span-ID`, `X-Request-ID`), allowing frontend browsers to read the Trace ID from responses.

