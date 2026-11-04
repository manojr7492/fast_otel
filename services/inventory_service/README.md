# 📦 E-Commerce Inventory Microservice

An enterprise-grade Inventory microservice built with **Python 3.11**, **FastAPI**, **SQLAlchemy 2.0 (Async)**, and **OpenTelemetry**.

This service manages warehouse stock levels, stock reservations, order commits, and release locks. It operates on port **`8005`** and connects to the dedicated MySQL database `fastapi_inventory_db`.

---

## 🚀 Quick Start

### 1. Run Service
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
python services/inventory_service/run.py
```
Server listens on **`http://localhost:8005`**.

### 2. Interactive Documentation
- **Swagger UI**: [http://localhost:8005/api/v1/docs](http://localhost:8005/api/v1/docs)
- **Health Check**: [http://localhost:8005/health](http://localhost:8005/health)

