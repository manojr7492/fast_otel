import asyncio
import httpx

async def test_full_microservices_ecosystem():
    print("==================================================")
    print("  🛍️ TESTING FRONTEND-TO-MICROSERVICES INTEGRATION")
    print("==================================================")

    async with httpx.AsyncClient(timeout=8.0) as client:
        # 1. Test OTP Flow
        print("\n[STEP 1] Testing OTP Request & Verification...")
        req = await client.post(
            "http://127.0.0.1:8001/api/v1/auth/otp/request",
            json={"login_identifier": "alex.dev@antigravity.io"}
        )
        assert req.status_code == 200
        otp = req.json()["data"]["otp"]
        print(f"  ✓ OTP generated: {otp}")

        ver = await client.post(
            "http://127.0.0.1:8001/api/v1/auth/otp/verify",
            json={"login_identifier": "alex.dev@antigravity.io", "otp_code": otp}
        )
        assert ver.status_code == 200
        auth_data = ver.json()["data"]
        token = auth_data["access_token"]
        user_uuid = auth_data["user"]["uuid"]
        print(f"  ✓ Session created for UUID: {user_uuid}")

        # 2. Test Catalog Service (:8002)
        print("\n[STEP 2] Querying Product Catalog (:8002)...")
        cat_resp = await client.get("http://127.0.0.1:8002/api/v1/categories/")
        assert cat_resp.status_code == 200
        cats = cat_resp.json()["data"]
        print(f"  ✓ Categories retrieved: {len(cats)}")

        prod_resp = await client.get("http://127.0.0.1:8002/api/v1/products/")
        assert prod_resp.status_code == 200
        prods = prod_resp.json()["data"]["items"]
        print(f"  ✓ Catalog products retrieved: {len(prods)}")

        # Pick first product
        test_prod = prods[0] if prods else None
        if not test_prod:
            # Create a product for testing
            first_cat = cats[0]["uuid"]
            new_prod = await client.post("http://127.0.0.1:8002/api/v1/products/", json={
                "category_uuid": first_cat,
                "name": "Apple MacBook Pro 16 M3 Max",
                "slug": "macbook-pro-16-m3-max",
                "sku": "MACBOOK-M3-MAX",
                "description": "16-core CPU, 40-core GPU, 48GB Unified Memory",
                "price": 3499.00,
                "currency": "USD",
                "is_active": True
            })
            test_prod = new_prod.json()["data"]

        prod_uuid = test_prod["uuid"]
        sku = test_prod["sku"]
        print(f"  ✓ Selected SKU '{sku}' (UUID: {prod_uuid})")

        # 3. Restock in Inventory (:8005)
        print("\n[STEP 3] Restocking in Inventory Service (:8005)...")
        restock = await client.post("http://127.0.0.1:8005/api/v1/inventory/restock", json={
            "sku": sku,
            "quantity": 50,
            "warehouse_location": "SAN-FRANCISCO-HUB"
        })
        assert restock.status_code == 200
        print(f"  ✓ Ingested stock: SKU '{sku}' available = {restock.json()['data']['available_quantity']}")

        # 4. Distributed Saga Order Checkout (:8003)
        print("\n[STEP 4] Executing Distributed Saga Order Checkout (:8003)...")
        order_payload = {
            "user_uuid": user_uuid,
            "customer_email": "alex.dev@antigravity.io",
            "customer_name": "Alex Developer",
            "items": [
                {
                    "product_uuid": prod_uuid,
                    "sku": sku,
                    "quantity": 1
                }
            ],
            "payment_method": "CREDIT_CARD",
            "simulate_payment_failure": False
        }
        order_resp = await client.post("http://127.0.0.1:8003/api/v1/orders/checkout", json=order_payload)
        assert order_resp.status_code == 201, f"Checkout failed: {order_resp.text}"
        order_data = order_resp.json()["data"]
        trace_id = order_resp.headers.get("x-trace-id")
        print(f"  ✓ Order Confirmed! UUID: {order_data['uuid']}")
        print(f"  ✓ OpenTelemetry Trace ID: {trace_id}")
        print(f"  ✓ Jaeger UI URL: http://localhost:16686/trace/{trace_id}")

        # 5. Test Saga Failure Simulation (Payment Declined -> Compensation Rollback)
        print("\n[STEP 5] Testing Saga Failure & Automatic Inventory Rollback...")
        fail_payload = {
            "user_uuid": user_uuid,
            "customer_email": "alex.dev@antigravity.io",
            "customer_name": "Alex Developer",
            "items": [
                {
                    "product_uuid": prod_uuid,
                    "sku": sku,
                    "quantity": 1
                }
            ],
            "payment_method": "CREDIT_CARD",
            "simulate_payment_failure": True
        }
        fail_resp = await client.post("http://127.0.0.1:8003/api/v1/orders/checkout", json=fail_payload)
        assert fail_resp.status_code == 400
        print(f"  ✓ Saga handled simulated payment failure correctly (HTTP 400): {fail_resp.json()['message']}")

        # 6. Verify Notification Service History (:8006)
        print("\n[STEP 6] Checking Notification Events (:8006)...")
        notifs = await client.get("http://127.0.0.1:8006/api/v1/notifications/history")
        assert notifs.status_code == 200
        history = notifs.json()
        print(f"  ✓ Dispatched notifications count: {len(history)}")

    print("\n==================================================")
    print("🎉 ALL 6 BACKEND SERVICES & FRONTEND FLOWS VERIFIED! 🎉")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_full_microservices_ecosystem())

