# 🛍️ FastAPI E-Commerce Microservices

A distributed, production-grade e-commerce backend platform built with **Python 3.11**, **FastAPI**, **SQLAlchemy 2.0 (Async)**, **Alembic**, and dedicated **MySQL** databases per microservice.

---

## 🏗️ Architecture & Database Matrix

Each microservice operates autonomously with its own dedicated MySQL database, independent migration history, and domain-driven design:

| Microservice | Port | Database Name | Status | Documentation |
| :--- | :--- | :--- | :--- | :--- |
| **User & Auth Service** | `8001` | `fastapi_user_db` | ✅ **Complete & Verified** | [User Service README](services/user_service/README.md) |
| **Product / Catalog Service** | `8002` | `fastapi_product_db` | ✅ **Complete & Verified** | [Product Service README](services/product_service/README.md) |
| **Order Service (Saga)** | `8003` | `fastapi_order_db` | ✅ **Complete & Verified** | [Order Service README](services/order_service/README.md) |
| **Payment Service** | `8004` | `fastapi_payment_db` | ✅ **Complete & Verified** | [Payment Service README](services/payment_service/README.md) |
| **Inventory Service** | `8005` | `fastapi_inventory_db` | ✅ **Complete & Verified** | [Inventory Service README](services/inventory_service/README.md) |
| **Notification Service** | `8006` | In-Memory / Audit | ✅ **Complete & Verified** | [Notification Service README](services/notification_service/README.md) |

---

## 🚀 Quick Start: Running the Full Ecosystem

### 1. Activate Environment
```bash
source .venv/bin/activate
```

### 2. Run All 6 Microservices in Parallel
You can start any service individually using its `run.py`:
- **User Service (`:8001`)**: `python services/user_service/run.py`
- **Product Service (`:8002`)**: `python services/product_service/run.py`
- **Order Service (`:8003`)**: `python services/order_service/run.py`
- **Payment Service (`:8004`)**: `python services/payment_service/run.py`
- **Inventory Service (`:8005`)**: `python services/inventory_service/run.py`
- **Notification Service (`:8006`)**: `python services/notification_service/run.py`

*Or start everything with Docker Compose:*
```bash
docker compose up --build
```

### 3. Open Interactive Swagger UI Documentation
- **User Service**: [http://localhost:8001/api/v1/docs](http://localhost:8001/api/v1/docs)
- **Product Service**: [http://localhost:8002/api/v1/docs](http://localhost:8002/api/v1/docs)
- **Order Service**: [http://localhost:8003/api/v1/docs](http://localhost:8003/api/v1/docs)
- **Payment Service**: [http://localhost:8004/api/v1/docs](http://localhost:8004/api/v1/docs)
- **Inventory Service**: [http://localhost:8005/api/v1/docs](http://localhost:8005/api/v1/docs)
- **Notification Service**: [http://localhost:8006/api/v1/docs](http://localhost:8006/api/v1/docs)
- **Jaeger Distributed Tracing UI**: [http://localhost:16686/search](http://localhost:16686/search)

### 4. Run Full Ecosystem Verification Test Suite
```bash
python verify_all_services.py
```


---

# OpenTelemetry Observability and Distributed Tracing

## 1. Observability Fundamentals

- **OpenTelemetry (OTel)**: A vendor-neutral, open-source observability framework providing standardized APIs, SDKs, and tooling to generate, collect, and export telemetry data (traces, metrics, and logs).
- **Distributed Tracing**: The technique of recording the full execution lifecycle of a request as it traverses distributed network boundaries, microservices, and databases.
- **Span**: The fundamental building block of a trace. A span represents a single contiguous unit of work (e.g. an HTTP request, a database query, or a password hash). It contains a name, start and end timestamps, status code, parent span ID, and key-value metadata attributes.
- **Trace ID**: A globally unique 16-byte (32-hex character) identifier that links together all spans originating from the same root user request across all microservices.
- **Span ID**: A unique 8-byte (16-hex character) identifier that identifies a specific span within a trace.
- **Jaeger UI**: An open-source distributed tracing visualization platform used for monitoring, profiling, root-cause analysis, and latency breakdown of complex microservice transactions.

---

## 2. Observability Architecture & Request Flow

```
┌────────────────────────────────────────────────────────┐
│               API Gateway / HTTP Client                │
└──────────────────────────┬─────────────────────────────┘
                           │ (Incoming HTTP: POST /register)
┌──────────────────────────▼─────────────────────────────┐
│ User & Auth Service (Port 8001)                        │
│  - FastAPI Server Span                                 │
│  - Business Span: auth.register                        │
│    - Child Span: auth.hash_password                    │
│    - Child Span: MySQL INSERT users (SQLAlchemy)       │
│    - Child Span: auth.send_welcome_notification        │
│      - HTTPX Outgoing Client Span (Inject traceparent) │
└──────────────────────────┬─────────────────────────────┘
                           │ (W3C HTTP: POST /notifications/send)
                           │ Header: traceparent: 00-{trace_id}-{span_id}-01
┌──────────────────────────▼─────────────────────────────┐
│ Notification Service (Port 8006)                       │
│  - FastAPI Server Span (Adopts upstream Trace ID)      │
│  - Business Span: notification.process                 │
│    - Child Span: notification.render_template          │
│    - Child Span: notification.dispatch_channel         │
└──────────────────────────┬─────────────────────────────┘
                           │
       (Batch Asynchronous Trace Export via OTLP/HTTP)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Jaeger OTLP Receiver (:4318 HTTP / :4317 gRPC)         │
│  - Jaeger Search & Visualizer UI (:16686)              │
└────────────────────────────────────────────────────────┘
```

---

## 3. Instrumented Components & Operations

### A. User & Authentication Service (`user-service`)
- **Incoming HTTP Layer**: Instrumented via `FastAPIInstrumentor`. Captures route pattern, method, HTTP status code, client IP, and user-agent. High-frequency paths (`/health`, `/docs`, `/openapi.json`, `/redoc`) are excluded to avoid clutter.
- **Database Layer**: Instrumented via `SQLAlchemyInstrumentor` bound to the asynchronous engine (`engine.sync_engine`). Traces raw SQL queries, transaction boundaries (`BEGIN`, `COMMIT`, `ROLLBACK`), execution timing, and database errors.
- **Outgoing HTTP Client**: Instrumented via `HTTPXClientInstrumentor`. Automatically injects W3C trace context headers into downstream requests.
- **Custom Business Spans**:
  - `auth.register`: High-level registration transaction span.
  - `auth.hash_password`: Bcrypt hashing duration and algorithm metadata.
  - `auth.authenticate`: User login and credential validation span.
  - `auth.verify_password`: Constant-time password verification duration.
  - `auth.issue_jwt_tokens`: JWT access and rotating refresh token generation.
  - `auth.send_welcome_notification`: Cross-service notification dispatch.
  - `auth.refresh_token`: Refresh token rotation span.
  - `user.list_users`: Paginated directory lookups with active filter attributes.
  - `address.create`, `address.update`, `address.delete`: Address lifecycle spans.

### B. Notification Service (`notification-service`)
- **Incoming HTTP Layer**: Instrumented via `FastAPIInstrumentor`. Extracts upstream `traceparent` headers to attach downstream execution to the original trace.
- **Custom Business Spans**:
  - `notification.process`: Root processing span recording event type and recipient.
  - `notification.render_template`: Notification template formatting and subject assembly.
  - `notification.dispatch_channel`: Delivery provider execution span.
  - `notification.list_history`: In-memory audit trail queries.

---

## 4. Trace Context Propagation Across Service Boundaries

Inter-service distributed tracing relies on the **W3C Trace Context Specification**:

1. When `user-service` initiates an HTTP request to `notification-service`, the instrumented `httpx.AsyncClient` injects the `traceparent` header into the request:
   ```http
   traceparent: 00-84164301bed8a3af72c8317d9a99c8ad-2b00a550b446081c-01
   ```
   - `00`: W3C specification version.
   - `84164301bed8a3af72c8317d9a99c8ad`: Global 32-hex `trace_id`.
   - `2b00a550b446081c`: Current span ID (which becomes the parent span ID of the downstream service).
   - `01`: Trace flags (`01` indicates the trace was sampled).

2. When `notification-service` receives the request, `FastAPIInstrumentor` automatically extracts the header using `TraceContextTextMapPropagator`.
3. The new server span inside `notification-service` continues under the **same Trace ID** (`84164301bed8a3af72c8317d9a99c8ad`) with parent set to `2b00a550b446081c`.
4. In Jaeger UI, this renders as a single unified trace tree showing the execution flow across both microservices.

---

## 5. Structured Application Logging & Trace Correlation

Both services use a custom `JSONLogFormatter` (`app/core/logging.py`) that renders logs in newline-delimited JSON.

When an active span is detected in the current execution context, the formatter automatically resolves and attaches the active `trace_id` and `span_id`:

```json
{
  "timestamp": "2026-10-17T08:56:28.104231Z",
  "level": "INFO",
  "service_name": "user-service",
  "environment": "development",
  "logger": "user-service",
  "message": "Dispatched welcome notification to notification-service for user 4017bb76-d387-4076-bffe-0922533be40b [status: 200]",
  "trace_id": "84164301bed8a3af72c8317d9a99c8ad",
  "span_id": "9a38f30739ba6368",
  "process_id": 14210,
  "thread_name": "MainThread"
}
```

### Security & Credential Redaction:
The logging pipeline automatically runs `sanitize_data()` on dictionary attributes and error payloads, redacting sensitive parameters (`password`, `token`, `access_token`, `refresh_token`, `authorization`, `credit_card`) to prevent credential leakage.

---

## 6. Dependencies & Configuration Reference

### Pinned Dependencies (`requirements.txt`):
```text
opentelemetry-api>=1.45.0
opentelemetry-sdk>=1.45.0
opentelemetry-exporter-otlp>=1.45.0
opentelemetry-exporter-otlp-proto-http>=1.45.0
opentelemetry-exporter-otlp-proto-grpc>=1.45.0
opentelemetry-instrumentation-fastapi>=0.66b1
opentelemetry-instrumentation-httpx>=0.66b1
opentelemetry-instrumentation-sqlalchemy>=0.66b1
opentelemetry-instrumentation-logging>=0.66b1
```

### Environment Variables Matrix:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `OTEL_ENABLED` | `True` | Master toggle for OpenTelemetry distributed tracing |
| `OTEL_SERVICE_NAME` | `user-service` / `notification-service` | Distinguishable service identifier displayed in Jaeger UI |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318/v1/traces` | OTLP HTTP traces intake endpoint (use `http://host.docker.internal:4318/v1/traces` in Docker) |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | OTLP protocol (`http/protobuf` or `grpc`) |
| `OTEL_SAMPLING_RATIO` | `1.0` | Head sampling ratio (`1.0` = 100% of traces, `0.1` = 10% of traces) |
| `LOG_FORMAT` | `json` | Structured logging format (`json` or `text`) |
| `NOTIFICATION_SERVICE_URL` | `http://localhost:8006` | Downstream Notification microservice base URL |

---

## 7. How to Start Jaeger and the Microservices

### Step 1: Ensure Jaeger is Running
If your local Jaeger container is not running, start it using Docker:
```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```
- **Jaeger Web UI**: [http://localhost:16686](http://localhost:16686)
- **OTLP gRPC receiver**: `localhost:4317`
- **OTLP HTTP receiver**: `localhost:4318`

### Step 2: Start Microservices Locally

**Terminal 1 — Notification Service (Port 8006):**
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
python services/notification_service/run.py
```

**Terminal 2 — User & Auth Service (Port 8001):**
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
python services/user_service/run.py
```

*Alternatively, run all services using Docker Compose:*
```bash
docker compose up --build
```

---

## 8. How to Generate Requests and View Traces in Jaeger

### 1. Trigger an End-to-End Distributed Request:
Register a new customer account in `user-service`. This will automatically call `notification-service`:
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer_tracer@example.com",
    "username": "customer_tracer",
    "password": "SecurePassword@123",
    "first_name": "Distributed",
    "last_name": "Tracer"
  }'
```

### 2. View Traces in Jaeger UI:
1. Open [http://localhost:16686/search](http://localhost:16686/search) in your browser.
2. Under **Service**, select **`user-service`**.
3. Under **Operation**, select **`POST /api/v1/auth/register`** (or leave as *all*).
4. Click **Find Traces**.
5. Click on the discovered trace.
6. Observe the span timeline:
   - Span 1: `user-service: POST /api/v1/auth/register`
     - Span 2: `user-service: auth.register`
       - Span 3: `user-service: auth.hash_password`
       - Span 4: `user-service: INSERT INTO users ...` (SQLAlchemy)
       - Span 5: `user-service: auth.send_welcome_notification`
         - Span 6: `user-service: HTTP POST http://localhost:8006/api/v1/notifications/send`
           - Span 7: `notification-service: POST /api/v1/notifications/send`
             - Span 8: `notification-service: notification.process`
             - Span 9: `notification-service: notification.render_template`
             - Span 10: `notification-service: notification.dispatch_channel`

---

## 9. Troubleshooting & Diagnostics

- **Missing Traces in Jaeger**:
  - Verify OTLP collector is listening on port `4318`: `curl -v http://localhost:4318/v1/traces`.
  - Check that `OTEL_ENABLED=True` and `OTEL_SAMPLING_RATIO=1.0` in `.env`.
  - Ensure the request path is not in the excluded list (`/health`, `/docs`, `/openapi.json`).
- **Connection Refused in Docker**:
  - Docker containers cannot reach the host machine using `localhost`. Use `OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318/v1/traces` with `extra_hosts: ["host.docker.internal:host-gateway"]`.
- **Trace Context Not Propagating**:
  - Ensure outgoing HTTP requests use an instrumented `httpx.AsyncClient` or `httpx.Client`. Do not use uninstrumented low-level sockets or bare `urllib`.
- **Duplicate Spans**:
  - Ensure `setup_telemetry()` is called only once during the application `lifespan` startup, and that manual span names do not duplicate automatic instrumentation names.

---

## 10. Security, Sampling & Production Considerations

- **Sampling**: In high-throughput production environments, set `OTEL_SAMPLING_RATIO` to a fraction (e.g. `0.05` for 5% trace sampling) to minimize CPU overhead and storage cost while maintaining statistical significance.
- **Batching & Performance**: Telemetry spans are queued in memory and exported asynchronously in batches of up to 512 spans every 500ms via `BatchSpanProcessor`. Spans do not block user requests.
- **Non-Breaking Resilience**: All telemetry initialization and exporter hooks are guarded by `try/except`. If the Jaeger container goes down or network connectivity is lost, business requests continue uninterrupted without returning HTTP 500 errors to clients.
- **Secret Redaction**: Never pass plain authentication tokens, passwords, or credit card numbers in span attributes or unredacted log records.

---

## 11. Observability Limitations & Log Centralization

> [!IMPORTANT]
> **Jaeger is a distributed tracing backend, NOT a log-management system.**
>
> - **What Jaeger Stores**: Spans, parent-child relationships, operation durations, span attributes, and span events (such as recorded exceptions).
> - **What Jaeger Does NOT Store**: Standard application log streams (`logger.info`, `logger.debug`).
> - **Where Logs Live Locally**: All microservices stream structured JSON logs to standard output (`stdout`), where they can be inspected in your terminal or captured by Docker container log drivers (`docker logs`).
> - **Log Centralization in Production**: To query, search, and aggregate application logs alongside traces, an external log management backend is required (e.g., **Grafana Loki**, **Elasticsearch / OpenSearch**, or **AWS CloudWatch**), with log-to-trace navigation configured using the structured `trace_id` field.

---

# React E-Commerce Frontend with On-Screen OTP & OpenTelemetry

A modern, production-grade React 18+ Single Page Application built with Vite and Tailwind CSS that connects seamlessly to our distributed FastAPI microservices ecosystem with on-screen OTP verification and end-to-end OpenTelemetry distributed tracing.

## Architecture & Technology Stack
- **Framework**: React 18+ with Vite
- **Styling**: Tailwind CSS with dark theme aesthetic, glassmorphic cards, and custom scrollbars
- **Icons**: Lucide-React
- **State Management**: Zustand
  - `useAuthStore`: JWT token lifecycle, session persistence, on-screen demo OTP state
  - `useCartStore`: Line items, quantity steppers, subtotal/tax/shipping calculations, promo vouchers
  - `useNotificationStore`: In-app notification center alerts and toast messages
  - `useTelemetryStore`: Real-time trace inspector capturing client API requests
- **HTTP Client**: Axios with interceptors injecting W3C `traceparent` headers (`00-{trace_id}-{span_id}-01`) and `X-Request-ID`

## Microservices Integration Matrix
| Service | Local Port | Key Endpoints Used by Frontend |
|---|---|---|
| **User & Auth Service** | `:8001` | `/api/v1/auth/otp/request`, `/api/v1/auth/otp/verify`, `/api/v1/users/me`, `/api/v1/addresses/` |
| **Product / Catalog Service** | `:8002` | `/api/v1/categories/`, `/api/v1/products/`, `/api/v1/products/{sku}` |
| **Order / Saga Orchestrator** | `:8003` | `/api/v1/orders/checkout`, `/api/v1/orders/` |
| **Payment Service** | `:8004` | `/api/v1/payments/process`, `/api/v1/payments/{uuid}` |
| **Inventory Service** | `:8005` | `/api/v1/inventory/{sku}`, `/api/v1/inventory/restock` |
| **Notification Service** | `:8006` | `/api/v1/notifications/send`, `/api/v1/notifications/history` |

## On-Screen OTP Login Flow
1. User clicks **"Demo OTP Login"** and inputs an email or username (or picks a one-click preset like `customer@antigravity.io`).
2. The User Service generates a 6-digit OTP code and displays it **directly on screen** inside a prominent demo banner:
   ```
   ⚡ Demo Mode Active: Your verification code is [ 8 4 9 2 0 1 ]
   ```
3. Clicking **"One-Click Auto-Fill"** automatically populates the 6 individual verification digit boxes.
4. Smooth submission creates the customer account if new, issues authentic JWT access and refresh tokens, and binds the session.
5. (Optional) Master demo code `123456` is also accepted for instant testing.

## Frontend-to-Backend Observability
1. **W3C Traceparent Header**: Every outgoing Axios call automatically generates a 128-bit `trace_id` and 64-bit `span_id`, injecting `traceparent: 00-{trace_id}-{span_id}-01`.
2. **OpenTelemetry Inspector Drawer**: Click the **"Traces"** pill in the top navigation bar to open the live telemetry drawer showing all outgoing API calls, HTTP status, process latencies, and direct links to Jaeger.
3. **One-Click Jaeger Trace View**: When an order or payment is completed, the modal displays the exact `trace_id` with a button:
   ```
   http://localhost:16686/trace/{trace_id}
   ```
   Clicking it opens the full cross-service span tree across all 6 microservices in Jaeger UI!

## Distributed Saga Testing (Payment Failure & Inventory Rollback)
- In the Checkout modal, enable the **"⚠️ Simulate Payment Failure"** toggle.
- When placing the order, the payment gateway simulates an issuer decline (`CARD_DECLINED`).
- The Order service catches the exception, automatically rolls back reserved inventory in the Inventory service (`POST /api/v1/inventory/release`), dispatches a failure notification, and records an error span in Jaeger.

## How to Run Frontend & Microservices

### 1. Start All Microservices
```bash
# Start all 6 backend services in the background
./start_all.sh
```

### 2. Start React Frontend
```bash
# Start Vite development server
cd frontend
npm run dev
# OR from root:
./start_frontend.sh
```

The frontend will be available at:
**http://localhost:5173**

### 3. Build for Production
```bash
cd frontend
npm run build
```

### 4. Stop All Services
```bash
# Stops all 6 microservices and the React dev server
./stop_all.sh
```
