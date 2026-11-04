# 💳 E-Commerce Payment Microservice

An enterprise-grade Payment microservice built with **Python 3.11**, **FastAPI**, **SQLAlchemy 2.0 (Async)**, and **OpenTelemetry**.

This service manages payment processing, gateway authorizations, transaction lifecycle tracking, and refunds. It operates on port **`8004`** and connects to the dedicated MySQL database `fastapi_payment_db`.

---

## 🚀 Quick Start

### 1. Run Service
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
python services/payment_service/run.py
```
Server listens on **`http://localhost:8004`**.

### 2. Interactive Documentation
- **Swagger UI**: [http://localhost:8004/api/v1/docs](http://localhost:8004/api/v1/docs)
- **Health Check**: [http://localhost:8004/health](http://localhost:8004/health)

