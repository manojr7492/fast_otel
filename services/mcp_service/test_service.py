import asyncio
import os
import sys

# Ensure mcp_service root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.mcp_client import mcp_client
from app.langchain_adapter import langchain_adapter


async def run_tests():
    print("=" * 65)
    print("🧪 MCP SERVER, CLIENT & LANGCHAIN INTEGRATION TEST SUITE")
    print("=" * 65)

    # -------------------------------------------------------------
    # Test 1: MCP Client over STDIO
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing MCP Client Discovery over STDIO...")
    tools = await mcp_client.list_tools()
    tool_names = [t.name for t in tools]
    print(f"  ✓ Discovered {len(tools)} tools: {tool_names}")
    assert "calculate_discount" in tool_names
    assert "search_product_catalog" in tool_names
    assert "check_inventory_stock" in tool_names
    assert "convert_currency" in tool_names
    assert "get_system_status" in tool_names

    # -------------------------------------------------------------
    # Test 2: MCP Tool Execution via STDIO
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Direct MCP Tool Calls via STDIO...")
    # A. calculate_discount
    discount_res = await mcp_client.call_tool("calculate_discount", {"price": 1000.0, "discount_percent": 15.0})
    print(f"  ✓ calculate_discount result: {discount_res}")
    assert discount_res["discounted_price"] == 850.0
    assert discount_res["discount_amount"] == 150.0

    # B. check_inventory_stock
    stock_res = await mcp_client.call_tool("check_inventory_stock", {"sku": "MACBOOK-M3-MAX"})
    print(f"  ✓ check_inventory_stock result: {stock_res}")
    assert stock_res["sku"] == "MACBOOK-M3-MAX"
    assert stock_res["available_quantity"] > 0

    # C. convert_currency
    curr_res = await mcp_client.call_tool("convert_currency", {"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"})
    print(f"  ✓ convert_currency result: {curr_res}")
    assert curr_res["converted_amount"] == 92.0

    # -------------------------------------------------------------
    # Test 3: LangChain StructuredTool Conversion
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing LangChain StructuredTool Conversion...")
    lc_tools = await langchain_adapter.get_langchain_tools()
    print(f"  ✓ Wrapped {len(lc_tools)} tools into LangChain StructuredTools:")
    for t in lc_tools:
        print(f"    - {t.name}: {t.description[:55]}...")
    assert len(lc_tools) >= 5

    # -------------------------------------------------------------
    # Test 4: LangChain Agent Execution over STDIO
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing LangChain Chat Agent Reasoning & Execution...")
    prompt = "Find a MacBook Pro and calculate a 20% discount on it, then check stock for MACBOOK-M3-MAX"
    agent_resp = await langchain_adapter.chat_and_execute(prompt)
    print("  ✓ Thought Process:")
    for step in agent_resp.thought_process:
        print(f"    → {step}")
    print(f"\n  ✓ Tools Invoked ({len(agent_resp.tools_used)}): {agent_resp.tools_used}")
    print(f"\n  ✓ Final Synthesized Answer:\n{agent_resp.final_answer}")
    assert len(agent_resp.tools_used) >= 2

    # -------------------------------------------------------------
    # Test 5: FastAPI Endpoints via ASGI Client
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing FastAPI REST Endpoints via ASGI...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A. /health
        h_resp = await client.get("/health")
        assert h_resp.status_code == 200
        print(f"  ✓ GET /health: {h_resp.json()['status']} (MCP: {h_resp.json()['transport']})")

        # B. /mcp/tools
        t_resp = await client.get("/mcp/tools")
        assert t_resp.status_code == 200
        print(f"  ✓ GET /mcp/tools: {len(t_resp.json())} tools listed")

        # C. /mcp/tools/call
        c_resp = await client.post("/mcp/tools/call", json={
            "tool_name": "convert_currency",
            "arguments": {"amount": 500.0, "from_currency": "USD", "to_currency": "GBP"}
        })
        assert c_resp.status_code == 200
        print(f"  ✓ POST /mcp/tools/call: {c_resp.json()['result']}")

        # D. /langchain/chat
        chat_resp = await client.post("/langchain/chat", json={
            "prompt": "What is 15% discount on $2000?"
        })
        assert chat_resp.status_code == 200
        print(f"  ✓ POST /langchain/chat: Answer generated ({len(chat_resp.json()['tools_used'])} tools used)")

    print("\n" + "=" * 65)
    print("🎉 ALL MCP CLIENT, MCP SERVER & LANGCHAIN TESTS PASSED! 🎉")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_tests())

