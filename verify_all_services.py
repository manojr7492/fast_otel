import asyncio
import os
import subprocess
import sys
import time
from typing import Dict, List

from httpx import AsyncClient


SERVICES_CONFIG = [
    {
        "name": "Notification Service",
        "service_id": "notification-service",
        "port": 8006,
        "entry": "services/notification_service/run.py",
        "health_url": "http://localhost:8006/health",
    },
    {
        "name": "Product Service",
        "service_id": "product-service",
        "port": 8002,
        "entry": "services/product_service/run.py",
        "health_url": "http://localhost:8002/health",
    },
    {
        "name": "Inventory Service",
        "service_id": "inventory-service",
        "port": 8005,
        "entry": "services/inventory_service/run.py",
        "health_url": "http://localhost:8005/health",
    },
    {
        "name": "Payment Service",
        "service_id": "payment-service",
        "port": 8004,
        "entry": "services/payment_service/run.py",
        "health_url": "http://localhost:8004/health",
    },
    {
        "name": "Order Service",
        "service_id": "order-service",
        "port": 8003,
        "entry": "services/order_service/run.py",
        "health_url": "http://localhost:8003/health",
    },
    {
        "name": "User Service",
        "service_id": "user-service",
        "port": 8001,
        "entry": "services/user_service/run.py",
        "health_url": "http://localhost:8001/health",
    },
]


async def run_all_services_verification():
    print("==================================================================")
    print("  🛍️ FULL E-COMMERCE MICROSERVICES ECOSYSTEM VERIFICATION        ")
    print("  Distributed Tracing, Saga Orchestration & OpenTelemetry Check   ")
    print("==================================================================")

    project_root = os.path.abspath(os.path.dirname(__file__))
    py_bin = sys.executable
    processes: List[subprocess.Popen] = []

    try:
        # 1. Start all 6 microservices
        print("\n[PHASE 1] Starting All 6 Microservices...")
        for svc in SERVICES_CONFIG:
            print(f"  → Launching {svc['name']} on port {svc['port']}...")
            proc = subprocess.Popen(
                [py_bin, svc["entry"]],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(proc)

        # 2. Wait for health checks
        print("\n[PHASE 2] Waiting for Liveness & Health Probes...")
        async with AsyncClient(timeout=4.0) as client:
            for svc in SERVICES_CONFIG:
                ready = False
                for _ in range(25):
                    await asyncio.sleep(0.4)
                    try:
                        r = await client.get(svc["health_url"])
                        if r.status_code == 200:
                            data = r.json()
                            print(f"  ✓ {svc['name']} is ready on :{svc['port']} (Status: {data.get('status')}, Tracing: {data.get('tracing')})")
                            ready = True
                            break
                    except Exception:
                        pass
                assert ready, f"Service {svc['name']} failed to become healthy on port {svc['port']}"

            # -----------------------------------------------------------------
            # Phase 3: User Registration & Notification
            # -----------------------------------------------------------------
            print("\n[PHASE 3] User Registration & Inter-Service Welcome Notification...")
            ts = int(time.time())
            test_email = f"customer_{ts}@antigravity.io"
            user_reg = {
                "email": test_email,
                "username": f"customer_{ts}",
                "password": "SecurePassword@123",
                "first_name": "Satya",
                "last_name": "Nadella",
            }
            u_resp = await client.post("http://localhost:8001/api/v1/auth/register", json=user_reg)
            assert u_resp.status_code == 201, f"User registration failed: {u_resp.text}"
            user_data = u_resp.json()["data"]
            user_uuid = user_data["uuid"]
            print(f"  ✓ User registered: UUID={user_uuid} [Trace: {u_resp.headers.get('X-Trace-ID')}]")

            # -----------------------------------------------------------------
            # Phase 4: Product Catalog Creation
            # -----------------------------------------------------------------
            print("\n[PHASE 4] Catalog Management in Product Service...")
            cat_payload = {
                "name": f"Laptops & Tech {ts}",
                "slug": f"laptops-tech-{ts}",
                "description": "High performance computing hardware",
            }
            cat_resp = await client.post("http://localhost:8002/api/v1/categories/", json=cat_payload)
            assert cat_resp.status_code == 201
            category_uuid = cat_resp.json()["data"]["uuid"]
            print(f"  ✓ Category created: {cat_payload['name']} (UUID: {category_uuid})")

            test_sku = f"MACBOOK-M3-{ts}"
            prod_payload = {
                "category_uuid": category_uuid,
                "name": "Apple MacBook Pro 16-inch M3 Max",
                "slug": f"macbook-pro-16-m3-max-{ts}",
                "sku": test_sku,
                "description": "16-core CPU, 40-core GPU, 48GB Unified Memory",
                "price": 3499.00,
                "currency": "USD",
                "is_active": True,
            }
            prod_resp = await client.post("http://localhost:8002/api/v1/products/", json=prod_payload)
            assert prod_resp.status_code == 201
            prod_data = prod_resp.json()["data"]
            prod_uuid = prod_data["uuid"]
            print(f"  ✓ Product created: {prod_data['name']} [SKU: {test_sku}, Price: ${prod_data['price']}]")

            # -----------------------------------------------------------------
            # Phase 5: Stock Ingestion in Inventory Service
            # -----------------------------------------------------------------
            print("\n[PHASE 5] Stock Ingestion in Inventory Service...")
            restock_payload = {
                "sku": test_sku,
                "quantity": 100,
                "warehouse_location": "SAN-FRANCISCO-HUB",
            }
            inv_resp = await client.post("http://localhost:8005/api/v1/inventory/restock", json=restock_payload)
            assert inv_resp.status_code == 200
            inv_data = inv_resp.json()["data"]
            assert inv_data["available_quantity"] == 100
            print(f"  ✓ Ingested stock: SKU '{test_sku}' available quantity = {inv_data['available_quantity']}")

            # -----------------------------------------------------------------
            # Phase 6: Distributed Saga Checkout
            # (Order -> Product -> Inventory -> Payment -> Notification)
            # -----------------------------------------------------------------
            print("\n[PHASE 6] Executing Distributed Saga Order Checkout...")
            checkout_payload = {
                "user_uuid": user_uuid,
                "customer_email": test_email,
                "customer_name": "Satya Nadella",
                "items": [
                    {
                        "product_uuid": prod_uuid,
                        "sku": test_sku,
                        "quantity": 2,
                    }
                ],
                "payment_method": "CREDIT_CARD",
                "simulate_payment_failure": False,
            }
            order_resp = await client.post("http://localhost:8003/api/v1/orders/checkout", json=checkout_payload)
            assert order_resp.status_code == 201, f"Checkout failed: {order_resp.text}"
            order_data = order_resp.json()["data"]
            order_uuid = order_data["uuid"]

            assert order_data["status"] == "CONFIRMED"
            assert Decimal(str(order_data["total_amount"])) == Decimal("6998.00")
            print(f"  ✓ Order Checkout Successful: UUID={order_uuid}, Status={order_data['status']}, Total=${order_data['total_amount']}")
            print(f"  ✓ End-to-End Distributed Trace ID: {order_resp.headers.get('X-Trace-ID')}")
            print(f"  ✓ Process Latency: {order_resp.headers.get('X-Process-Time-Ms')}ms")

            # Verify remaining inventory was committed (100 - 2 = 98)
            check_stock = await client.get(f"http://localhost:8005/api/v1/inventory/{test_sku}")
            stock_data = check_stock.json()["data"]
            assert stock_data["quantity"] == 98
            print(f"  ✓ Verified inventory reduction: remaining available = {stock_data['quantity']}")

            # Verify notification audit history
            notif_history = await client.get("http://localhost:8006/api/v1/notifications/history")
            confirmed_notifs = [n for n in notif_history.json() if n["recipient_email"] == test_email]
            assert len(confirmed_notifs) >= 2  # WELCOME_USER and ORDER_CONFIRMATION
            print(f"  ✓ Notification Service successfully received and processed events for {test_email}")

            # -----------------------------------------------------------------
            # Phase 7: Saga Compensation Test (Simulated Payment Failure)
            # -----------------------------------------------------------------
            print("\n[PHASE 7] Testing Saga Compensation & Automatic Rollback...")
            fail_checkout_payload = {
                "user_uuid": user_uuid,
                "customer_email": test_email,
                "customer_name": "Satya Nadella",
                "items": [{"product_uuid": prod_uuid, "sku": test_sku, "quantity": 1}],
                "payment_method": "CREDIT_CARD",
                "simulate_payment_failure": True,
            }
            fail_resp = await client.post("http://localhost:8003/api/v1/orders/checkout", json=fail_checkout_payload)
            assert fail_resp.status_code == 400
            err_data = fail_resp.json()
            assert err_data["error_code"] == "ORDER_CHECKOUT_FAILED"
            print("  ✓ Payment declined simulated successfully.")

            # Verify inventory was NOT deducted (still 98) due to compensation rollback
            stock_after_rollback = await client.get(f"http://localhost:8005/api/v1/inventory/{test_sku}")
            assert stock_after_rollback.json()["data"]["quantity"] == 98
            assert stock_after_rollback.json()["data"]["reserved_quantity"] == 0
            print("  ✓ Saga compensation verified: Reserved inventory was cleanly released back to available pool.")

            # -----------------------------------------------------------------
            # Phase 8: Jaeger UI Check
            # -----------------------------------------------------------------
            print("\n[PHASE 8] Querying Jaeger Tracing Backend...")
            try:
                j_ui = await client.get("http://localhost:16686/search")
                if j_ui.status_code == 200:
                    print("  ✓ Jaeger UI accessible at http://localhost:16686/search")
                svc_resp = await client.get("http://localhost:16686/api/services")
                if svc_resp.status_code == 200:
                    registered_svcs = svc_resp.json().get("data", [])
                    print(f"  ✓ Jaeger Registered Services: {registered_svcs}")
            except Exception as j_err:
                print(f"  ℹ Jaeger connection check: {j_err}")

    finally:
        print("\n[CLEANUP] Terminating All Microservices...")
        for p in processes:
            p.terminate()
        for p in processes:
            try:
                p.wait(timeout=2)
            except Exception:
                p.kill()
        print("  ✓ All 6 microservice processes cleanly stopped.")

    print("\n==================================================================")
    print("🎉 ALL 6 ENTERPRISE MICROSERVICES VERIFIED SUCCESSFULLY! 🎉      ")
    print("==================================================================")


if __name__ == "__main__":
    from decimal import Decimal
    asyncio.run(run_all_services_verification())

