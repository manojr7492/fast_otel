# 🛒 E-Commerce Order Microservice

An enterprise-grade Order microservice built with **Python 3.11**, **FastAPI**, **SQLAlchemy 2.0 (Async)**, and **OpenTelemetry**.

This service serves as the core checkout and saga orchestrator across Product, Inventory, Payment, and Notification microservices. It operates on port **`8003`** and connects to the dedicated MySQL database `fastapi_order_db`.

---

## 🚀 Quick Start

### 1. Run Service
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
python services/order_service/run.py
```
Server listens on **`http://localhost:8003`**.

### 2. Interactive Documentation
- **Swagger UI**: [http://localhost:8003/api/v1/docs](http://localhost:8003/api/v1/docs)
- **Health Check**: [http://localhost:8003/health](http://localhost:8003/health)

