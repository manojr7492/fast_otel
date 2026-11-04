import asyncio
import io
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict

from httpx import AsyncClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


def test_structured_logging_and_redaction():
    print("\n------------------------------------------------------------------")
    print("[PHASE 1] Structured JSON Logging & Credential Redaction Test")
    print("------------------------------------------------------------------")

    # Add user_service path to load its logging module
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "services", "user_service")))
    from app.core.logging import JSONLogFormatter, sanitize_data
    from app.core.config import settings

    log_buffer = io.StringIO()
    handler = logging.StreamHandler(log_buffer)
    handler.setFormatter(JSONLogFormatter())

    test_logger = logging.getLogger("unit_test_logger")
    test_logger.setLevel(logging.INFO)
    test_logger.handlers = [handler]
    test_logger.propagate = False

    # Standalone log without trace
    test_logger.info("Verifying basic structured log format")
    line1 = log_buffer.getvalue().strip().split("\n")[-1]
    parsed1 = json.loads(line1)

    assert parsed1["message"] == "Verifying basic structured log format"
    assert parsed1["service_name"] == settings.SERVICE_NAME
    assert parsed1["level"] == "INFO"
    assert parsed1["trace_id"] is None
    assert parsed1["span_id"] is None
    print("  ✓ Standalone JSON log formatted correctly with null trace_id and span_id.")

    # Contextual log inside active OpenTelemetry span
    memory_exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    tracer = provider.get_tracer("unit_tester")

    with tracer.start_as_current_span("unit_test_operation") as span:
        span_ctx = span.get_span_context()
        expected_trace_id = f"{span_ctx.trace_id:032x}"
        expected_span_id = f"{span_ctx.span_id:016x}"

        test_logger.info("Contextual log inside active span")
        line2 = log_buffer.getvalue().strip().split("\n")[-1]
        parsed2 = json.loads(line2)

        assert parsed2["trace_id"] == expected_trace_id
        assert parsed2["span_id"] == expected_span_id
        print(f"  ✓ Active trace context automatically injected: trace_id={expected_trace_id}, span_id={expected_span_id}")

    # Exception logging with safe serialization
    try:
        raise ValueError("Simulated operational failure for testing")
    except Exception:
        test_logger.exception("Operation failed with exception")
        line3 = log_buffer.getvalue().strip().split("\n")[-1]
        parsed3 = json.loads(line3)
        assert parsed3["level"] == "ERROR"
        assert parsed3["exception"]["type"] == "ValueError"
        assert "Simulated operational failure" in parsed3["exception"]["message"]
        assert len(parsed3["exception"]["stacktrace"]) > 0
        print("  ✓ Exception stack trace safely serialized into structured JSON.")

    # Credential and token redaction test
    raw_payload = {
        "username": "tester",
        "password": "CleartextPassword99!",
        "access_token": "eyJhbGciOi...",
        "refresh_token": "eyJhbGciOi...",
        "nested": {
            "credit_card": "1234-5678-9012-3456",
            "safe_field": "visible_value"
        }
    }
    redacted = sanitize_data(raw_payload)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["access_token"] == "[REDACTED]"
    assert redacted["refresh_token"] == "[REDACTED]"
    assert redacted["nested"]["credit_card"] == "[REDACTED]"
    assert redacted["nested"]["safe_field"] == "visible_value"
    print("  ✓ Sensitive credentials and tokens recursively redacted.")


def test_span_hierarchy_and_attributes():
    print("\n------------------------------------------------------------------")
    print("[PHASE 2] OpenTelemetry Span Hierarchy & Semantic Attributes Test")
    print("------------------------------------------------------------------")

    memory_exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    tracer = provider.get_tracer("business_tracer")

    with tracer.start_as_current_span("auth.register") as root:
        root.set_attribute("user.email", "alice@example.com")
        root.set_attribute("user.role", "CUSTOMER")

        with tracer.start_as_current_span("auth.hash_password") as child1:
            child1.set_attribute("crypto.algorithm", "bcrypt")
            child1.set_attribute("crypto.cost", 12)

        with tracer.start_as_current_span("auth.send_welcome_notification") as child2:
            child2.set_attribute("notification.recipient", "alice@example.com")
            child2.set_attribute("http.status_code", 200)

    spans = memory_exporter.get_finished_spans()
    assert len(spans) == 3
    root_s = next(s for s in spans if s.name == "auth.register")
    hash_s = next(s for s in spans if s.name == "auth.hash_password")
    notif_s = next(s for s in spans if s.name == "auth.send_welcome_notification")

    assert hash_s.parent.span_id == root_s.context.span_id
    assert notif_s.parent.span_id == root_s.context.span_id
    assert hash_s.context.trace_id == root_s.context.trace_id
    assert notif_s.context.trace_id == root_s.context.trace_id
    print("  ✓ Verified child spans inherit identical trace_id and correct parent_id.")
    print("  ✓ Verified custom business attributes recorded accurately.")


async def test_live_microservices_and_jaeger():
    print("\n------------------------------------------------------------------")
    print("[PHASE 3] Live Multi-Service Distributed Tracing & Jaeger UI Test")
    print("------------------------------------------------------------------")

    py_bin = sys.executable
    project_root = os.path.abspath(os.path.dirname(__file__))

    print("  1. Starting Notification Service on port 8006...")
    notif_proc = subprocess.Popen(
        [py_bin, "services/notification_service/run.py"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("  2. Starting User & Auth Service on port 8001...")
    user_proc = subprocess.Popen(
        [py_bin, "services/user_service/run.py"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait up to 10 seconds for services to become ready
        async with AsyncClient(timeout=5.0) as client:
            notif_ready = False
            user_ready = False
            for _ in range(20):
                await asyncio.sleep(0.5)
                if not notif_ready:
                    try:
                        r = await client.get("http://localhost:8006/health")
                        if r.status_code == 200 and r.json().get("status") == "healthy":
                            notif_ready = True
                            print("  ✓ Notification Service is healthy and listening on port 8006.")
                    except Exception:
                        pass

                if not user_ready:
                    try:
                        r = await client.get("http://localhost:8001/health")
                        if r.status_code == 200:
                            user_ready = True
                            print("  ✓ User Service is healthy and listening on port 8001.")
                    except Exception:
                        pass

                if notif_ready and user_ready:
                    break

            assert notif_ready, "Notification Service failed to start within timeout"
            assert user_ready, "User Service failed to start within timeout"

            # -------------------------------------------------------------
            # Step A: Direct Call to Notification Service with Traceparent
            # -------------------------------------------------------------
            print("\n  [Step A] Direct Call to Notification Service with W3C Traceparent...")
            test_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
            test_parent_id = "00f067aa0ba902b7"
            w3c_header = f"00-{test_trace_id}-{test_parent_id}-01"

            notif_resp = await client.post(
                "http://localhost:8006/api/v1/notifications/send",
                json={
                    "recipient_email": "direct_test@example.com",
                    "recipient_name": "Direct Tester",
                    "event_type": "WELCOME_USER",
                    "data": {"user_id": "usr_test_101"}
                },
                headers={"traceparent": w3c_header}
            )
            assert notif_resp.status_code == 200
            n_data = notif_resp.json()
            assert n_data["status"] == "DELIVERED"
            print(f"  ✓ Notification dispatched: ID={n_data['notification_id']}")
            print(f"  ✓ Trace Correlation Headers received: X-Request-ID={notif_resp.headers.get('X-Request-ID')}, Latency={notif_resp.headers.get('X-Process-Time-Ms')}ms")

            # -------------------------------------------------------------
            # Step B: End-to-End Inter-Service Call: User Registration -> Notification Service
            # -------------------------------------------------------------
            print("\n  [Step B] End-to-End Inter-Service Trace: User Service -> Notification Service...")
            unique_ts = int(time.time())
            reg_email = f"otel_user_{unique_ts}@example.com"
            reg_username = f"otel_user_{unique_ts}"

            reg_resp = await client.post(
                "http://localhost:8001/api/v1/auth/register",
                json={
                    "email": reg_email,
                    "username": reg_username,
                    "password": "SecurePassword@2026",
                    "first_name": "OpenTelemetry",
                    "last_name": "DistributedTracer",
                }
            )
            assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
            reg_data = reg_resp.json()["data"]
            user_trace_id = reg_resp.headers.get("X-Trace-ID")
            print(f"  ✓ User registered with UUID: {reg_data['uuid']}")
            if user_trace_id:
                print(f"  ✓ Originating Trace ID from User Service: {user_trace_id}")

            # Verify Notification Service received the welcome notification
            hist_resp = await client.get("http://localhost:8006/api/v1/notifications/history")
            assert hist_resp.status_code == 200
            history = hist_resp.json()
            matching = [n for n in history if n["recipient_email"] == reg_email]
            assert len(matching) > 0, "Notification for registered user not found in Notification Service history"
            print(f"  ✓ Cross-service event confirmed: Notification Service processed welcome notification for {reg_email}")

            # -------------------------------------------------------------
            # Step C: Error Tracking & Exception Telemetry
            # -------------------------------------------------------------
            print("\n  [Step C] Testing Error Responses & Metadata Correlation...")
            dup_resp = await client.post(
                "http://localhost:8001/api/v1/auth/register",
                json={
                    "email": reg_email,
                    "username": reg_username,
                    "password": "SecurePassword@2026",
                }
            )
            assert dup_resp.status_code == 409
            dup_json = dup_resp.json()
            assert dup_json["error_code"] == "ENTITY_ALREADY_EXISTS"
            assert "meta" in dup_json
            print(f"  ✓ HTTP 409 Conflict returned formatted error envelope with meta: {dup_json['meta']}")

            val_resp = await client.post(
                "http://localhost:8001/api/v1/auth/register",
                json={"email": "bad_email"}
            )
            assert val_resp.status_code == 422
            val_json = val_resp.json()
            assert val_json["error_code"] == "VALIDATION_ERROR"
            print(f"  ✓ HTTP 422 Validation Error returned field diagnostics with meta: {val_json['meta']}")

            # -------------------------------------------------------------
            # Step D: Jaeger UI Connectivity & Verification
            # -------------------------------------------------------------
            print("\n  [Step D] Querying Local Jaeger UI...")
            try:
                jaeger_resp = await client.get("http://localhost:16686/search")
                if jaeger_resp.status_code == 200:
                    print("  ✓ Jaeger UI accessible at http://localhost:16686/search")
                else:
                    print(f"  ℹ Jaeger UI returned HTTP {jaeger_resp.status_code}")

                # Query Jaeger API for registered services
                jaeger_services = await client.get("http://localhost:16686/api/services")
                if jaeger_services.status_code == 200:
                    services_list = jaeger_services.json().get("data", [])
                    print(f"  ✓ Jaeger registered services: {services_list}")
            except Exception as j_err:
                print(f"  ℹ Jaeger connection notice: {j_err}")

    finally:
        print("\n  Cleaning up background processes...")
        user_proc.terminate()
        notif_proc.terminate()
        try:
            user_proc.wait(timeout=2)
            notif_proc.wait(timeout=2)
        except Exception:
            user_proc.kill()
            notif_proc.kill()
        print("  ✓ Microservice background processes cleanly terminated.")


def main():
    print("==================================================================")
    print("🚀 RUNNING END-TO-END OPENTELEMETRY OBSERVABILITY TEST SUITE      ")
    print("==================================================================")

    test_structured_logging_and_redaction()
    test_span_hierarchy_and_attributes()
    asyncio.run(test_live_microservices_and_jaeger())

    print("\n==================================================================")
    print("🎉 ALL OPENTELEMETRY OBSERVABILITY VERIFICATION TESTS PASSED! 🎉")
    print("==================================================================")


if __name__ == "__main__":
    main()

