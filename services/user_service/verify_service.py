import asyncio
import sys
import os

# Add service directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from httpx import AsyncClient, ASGITransport
from app.main import app


async def run_tests():
    print("==================================================")
    print("Starting Enterprise User Service Verification Tests")
    print("==================================================")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health Check
        print("\n[TEST 1] Testing /health endpoint...")
        resp = await client.get("/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["status"] == "healthy", f"Service not healthy: {data}"
        print(f"  ✓ Service status: {data['status']}, DB: {data['database']}")

        # 2. Register New User
        print("\n[TEST 2] Testing User Registration...")
        test_email = "testuser_enterprise@example.com"
        test_username = "test_enterprise_user"
        test_password = "SecurePassword@123"

        reg_payload = {
            "email": test_email,
            "username": test_username,
            "password": test_password,
            "first_name": "Antigravity",
            "last_name": "Engineer",
            "phone_number": "+919876543210",
        }
        resp = await client.post("/api/v1/auth/register", json=reg_payload)
        # Note: If user was previously registered, status could be 409
        if resp.status_code == 409:
            print("  ℹ User already exists from previous run, proceeding to login.")
        else:
            assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
            res_data = resp.json()
            assert res_data["success"] is True
            assert res_data["data"]["email"] == test_email
            print(f"  ✓ User registered successfully with UUID: {res_data['data']['uuid']}")

        # 3. Test Duplicate Registration Conflict Handling
        print("\n[TEST 3] Testing Duplicate Registration Error Handling (409 Conflict)...")
        resp_dup = await client.post("/api/v1/auth/register", json=reg_payload)
        assert resp_dup.status_code == 409, f"Expected 409, got {resp_dup.status_code}"
        assert resp_dup.json()["error_code"] == "ENTITY_ALREADY_EXISTS"
        print("  ✓ Duplicate registration correctly rejected with 409 ENTITY_ALREADY_EXISTS")

        # 4. Test Password Strength Validation
        print("\n[TEST 4] Testing Weak Password Validation (422 Unprocessable Entity)...")
        weak_payload = dict(reg_payload, email="weak_pwd@test.com", username="weak_pwd_user", password="weak")
        resp_weak = await client.post("/api/v1/auth/register", json=weak_payload)
        assert resp_weak.status_code == 422, f"Expected 422, got {resp_weak.status_code}"
        print("  ✓ Weak password correctly rejected with 422 VALIDATION_ERROR")

        # 5. Test Login (Dual-token generation)
        print("\n[TEST 5] Testing User Authentication & JWT Issuance...")
        login_payload = {
            "login_identifier": test_email,
            "password": test_password,
        }
        resp_login = await client.post("/api/v1/auth/login", json=login_payload)
        assert resp_login.status_code == 200, f"Expected 200, got {resp_login.status_code}: {resp_login.text}"
        tokens = resp_login.json()["data"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        assert access_token and refresh_token
        print("  ✓ Successfully received JWT Access and Refresh tokens")

        # 6. Test Token Refresh (Rotation)
        print("\n[TEST 6] Testing Token Refresh & Rotation...")
        resp_refresh = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp_refresh.status_code == 200, f"Expected 200, got {resp_refresh.status_code}: {resp_refresh.text}"
        refreshed_tokens = resp_refresh.json()["data"]
        new_access_token = refreshed_tokens["access_token"]
        assert new_access_token
        print("  ✓ Refresh token successfully rotated and new access token issued")

        headers = {"Authorization": f"Bearer {new_access_token}"}

        # 7. Test Get Profile (/me)
        print("\n[TEST 7] Testing Get Profile (/api/v1/users/me)...")
        resp_me = await client.get("/api/v1/users/me", headers=headers)
        assert resp_me.status_code == 200, f"Expected 200, got {resp_me.status_code}: {resp_me.text}"
        user_profile = resp_me.json()["data"]
        assert user_profile["email"] == test_email
        print(f"  ✓ Profile retrieved for user: {user_profile['full_name']} (Role: {user_profile['role']})")

        # 8. Test RBAC Guard: Normal CUSTOMER cannot access Admin user listing
        print("\n[TEST 8] Testing RBAC Authorization Guard (Customer accessing Admin endpoint)...")
        resp_admin = await client.get("/api/v1/users/", headers=headers)
        assert resp_admin.status_code == 403, f"Expected 403, got {resp_admin.status_code}: {resp_admin.text}"
        assert resp_admin.json()["error_code"] == "FORBIDDEN"
        print("  ✓ RBAC guard successfully blocked non-admin user with 403 FORBIDDEN")

        # 9. Test Add Customer Address
        print("\n[TEST 9] Testing Address Creation (/api/v1/addresses/)...")
        addr_payload = {
            "address_type": "SHIPPING",
            "street_address": "42 Tech Boulevard, Silicon Towers",
            "apartment": "Suite 502",
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India",
            "postal_code": "560001",
            "is_default": True,
        }
        resp_addr = await client.post("/api/v1/addresses/", json=addr_payload, headers=headers)
        assert resp_addr.status_code == 201, f"Expected 201, got {resp_addr.status_code}: {resp_addr.text}"
        addr_data = resp_addr.json()["data"]
        addr_uuid = addr_data["uuid"]
        assert addr_data["is_default"] is True
        print(f"  ✓ Address created with UUID: {addr_uuid}")

        # 10. Test List Addresses
        print("\n[TEST 10] Testing Address Listing (/api/v1/addresses/)...")
        resp_list_addr = await client.get("/api/v1/addresses/", headers=headers)
        assert resp_list_addr.status_code == 200
        addresses = resp_list_addr.json()["data"]
        assert len(addresses) >= 1
        print(f"  ✓ User has {len(addresses)} saved address(es)")

        # 11. Test Profile Retrieval showing nested Addresses
        print("\n[TEST 11] Testing Profile with eager-loaded addresses (selectinload optimization)...")
        resp_profile_with_addr = await client.get("/api/v1/users/me", headers=headers)
        assert resp_profile_with_addr.status_code == 200
        profile_data = resp_profile_with_addr.json()["data"]
        assert len(profile_data["addresses"]) >= 1
        print(f"  ✓ Profile successfully returned with {len(profile_data['addresses'])} eager-loaded address(es)")

    print("\n==================================================")
    print("🎉 ALL 11 ENTERPRISE VERIFICATION TESTS PASSED! 🎉")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
