# MCP LangChain FastAPI Microservice

A unified microservice integrating **FastAPI**, **LangChain**, an **MCP Server**, and an **MCP Client** communicating over a bidirectional **STDIO (Standard Input/Output) JSON-RPC pipe**.

---

## 1. System Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │            FastAPI Web Service (Port 8007)             │
                    │                                                        │
                    │  REST Endpoints:                                       │
                    │  • GET  /health                                        │
                    │  • GET  /mcp/tools                                     │
                    │  • POST /mcp/tools/call                                │
                    │  • GET  /langchain/tools                               │
                    │  • POST /langchain/chat                                │
                    │  • POST /langchain/tools/invoke                        │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                    LangChain MCP Adapter
                               (Converts MCP tools to StructuredTools)
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               MCP Client (mcp_client.py)               │
                    │   Uses mcp.client.stdio.stdio_client & ClientSession   │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                      STDIO Pipe (stdin/stdout)
                                  JSON-RPC 2.0 Protocol Packet Flow
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               MCP Server (mcp_server.py)               │
                    │         Subprocess running via MCPServer 2.x           │
                    │                                                        │
                    │  Exposed Tools:                                        │
                    │  1. calculate_discount(price, discount_percent)        │
                    │  2. search_product_catalog(query, category)            │
                    │  3. check_inventory_stock(sku)                         │
                    │  4. convert_currency(amount, from_curr, to_curr)       │
                    │  5. get_system_status()                                │
                    └────────────────────────────────────────────────────────┘
```

---

## 2. Key Components

### 1. The MCP Server (`app/mcp_server.py`)
- Implemented with the official `mcp 2.x` SDK: `from mcp.server.mcpserver import MCPServer`.
- Subprocess-ready script that runs `asyncio.run(server.run_stdio_async())`.
- Directs all application logs to `stderr` so standard `stdout` is reserved purely for Model Context Protocol JSON-RPC frames.
- Exposes 5 enterprise e-commerce tools:
  - `calculate_discount`: Computes savings, tax, and final total.
  - `search_product_catalog`: Searches hardware items and specifications.
  - `check_inventory_stock`: Looks up live warehouse stock and reserved units.
  - `convert_currency`: Converts monetary values across USD, EUR, GBP, JPY, INR, CAD.
  - `get_system_status`: Returns protocol version, transport type, and health.

### 2. The MCP Client over STDIO (`app/mcp_client.py`)
- Uses `from mcp.client.stdio import stdio_client, StdioServerParameters` and `ClientSession`.
- Spawns the MCP Server as an isolated child process using `sys.executable`.
- Connects standard input and output streams (`stdin` / `stdout`).
- Calls `await session.initialize()`, `await session.list_tools()`, and `await session.call_tool(name, arguments)`.

### 3. The LangChain Adapter (`app/langchain_adapter.py`)
- Dynamically converts discovered MCP tools into native LangChain `StructuredTool` instances.
- Builds Pydantic `args_schema` models dynamically based on the tool's JSON schema.
- Implements an intelligent LangChain reasoning and execution pipeline that parses user intent, routes queries to the appropriate MCP tools over STDIO, and formats a comprehensive response.

### 4. FastAPI Application (`app/main.py`)
- Serves HTTP REST endpoints and OpenAPI / Swagger documentation (`/docs`).
- Runs on port `8007`.
- Features OpenTelemetry distributed tracing and CORS configuration.

---

## 3. API Endpoints Reference

### System
- `GET /health`
  Returns health status, active transport (`STDIO`), and list of active MCP tools.

### MCP Direct Control
- `GET /mcp/tools`
  Lists all tools exposed by the MCP Server over STDIO.
- `POST /mcp/tools/call`
  Executes an MCP tool directly through the STDIO client.
  ```json
  {
    "tool_name": "calculate_discount",
    "arguments": {
      "price": 3499.00,
      "discount_percent": 15.0
    }
  }
  ```

### LangChain Agent & Tools
- `GET /langchain/tools`
  Lists all MCP tools adapted into LangChain `StructuredTool` schemas.
- `POST /langchain/tools/invoke`
  Invokes a tool using LangChain's native `tool.ainvoke(...)` primitive.
- `POST /langchain/chat`
  Processes a natural language prompt with the LangChain Agent:
  ```json
  {
    "prompt": "Find a MacBook Pro, calculate a 20% discount on it, and check stock for MACBOOK-M3-MAX"
  }
  ```
  Returns:
  ```json
  {
    "prompt": "Find a MacBook Pro and calculate a 20% discount on it, then check stock for MACBOOK-M3-MAX",
    "thought_process": [
      "Received user prompt...",
      "Discovered 5 available MCP tools over STDIO pipe...",
      "Intent detected: Product Catalog Search...",
      "Intent detected: Price & Discount Calculation...",
      "Intent detected: Inventory Check..."
    ],
    "mcp_tool_calls": [ ... ],
    "final_answer": "...",
    "tools_used": ["search_product_catalog", "calculate_discount", "check_inventory_stock"]
  }
  ```

---

## 4. Running the Service & Tests

### Start Standalone:
```bash
.venv/bin/python services/mcp_service/run.py
```

### Start with All Microservices:
```bash
./start_all.sh
```

### Run Automated Integration Test Suite:
```bash
.venv/bin/python services/mcp_service/test_service.py
```

### Swagger Documentation:
Visit [http://localhost:8007/docs](http://localhost:8007/docs) in your browser.

