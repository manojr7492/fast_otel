# 🛍️ E-Commerce Product & Catalog Microservice

An enterprise-grade Product & Catalog microservice built with **Python 3.11**, **FastAPI**, **SQLAlchemy 2.0 (Async)**, and **OpenTelemetry**.

This service manages categories, catalog products, pricing, and SKU lookups. It operates on port **`8002`** and connects to the dedicated MySQL database `fastapi_product_db`.

---

## 🚀 Quick Start

### 1. Run Service
```bash
cd /Users/manojkumar/Desktop/FastAPI
source .venv/bin/activate
python services/product_service/run.py
```
Server listens on **`http://localhost:8002`**.

### 2. Interactive Documentation
- **Swagger UI**: [http://localhost:8002/api/v1/docs](http://localhost:8002/api/v1/docs)
- **Health Check**: [http://localhost:8002/health](http://localhost:8002/health)

