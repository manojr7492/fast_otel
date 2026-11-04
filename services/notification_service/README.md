# 🔔 E-Commerce Notification Microservice

An enterprise-grade, lightweight event-driven Notification microservice built with **Python 3.11**, **FastAPI**, and **OpenTelemetry**.

This service receives notification events (e.g. `WELCOME_USER`, `PASSWORD_RESET`, `ORDER_CONFIRMATION`), renders message templates, dispatches notifications, and maintains an in-memory audit trail.

It operates on port **`8006`** and integrates directly with **Jaeger UI** (`http://localhost:16686`) for end-to-end distributed tracing across microservices.

---

## 🚀 Quick Start

### 1. Activate Environment
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
```

### 2. Start Service
```bash
python services/notification_service/run.py
```
The service will listen on `http://localhost:8006`.

### 3. API Documentation
- **Swagger UI**: [http://localhost:8006/api/v1/docs](http://localhost:8006/api/v1/docs)
- **Health Check**: [http://localhost:8006/health](http://localhost:8006/health)

