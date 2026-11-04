import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace

from app.config import settings
from app.langchain_adapter import langchain_adapter
from app.mcp_client import mcp_client
from app.schemas import (
    CallToolRequest,
    CallToolResponse,
    HealthResponse,
    LangChainChatRequest,
    LangChainChatResponse,
    MCPToolInfo,
)
from app.telemetry import get_tracer, setup_telemetry, shutdown_telemetry

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
logger = logging.getLogger(settings.SERVICE_NAME)
tracer = get_tracer("mcp_fastapi_endpoints")


def get_current_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    span = trace.get_current_span()
    span_ctx = span.get_span_context() if span else None
    if span_ctx and span_ctx.is_valid:
        return f"{span_ctx.trace_id:032x}", f"{span_ctx.span_id:016x}"
    return None, None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing %s in %s mode...", settings.PROJECT_NAME, settings.ENVIRONMENT)

    # 1. Setup OpenTelemetry Distributed Tracing
    setup_telemetry(app=app)

    # 2. Verify MCP Server and STDIO Client connectivity
    try:
        tools = await mcp_client.list_tools()
        logger.info("MCP Server STDIO connection verified. %d tools active: %s", len(tools), [t.name for t in tools])
        # Pre-warm LangChain tools
        await langchain_adapter.get_langchain_tools()
    except Exception as exc:
        logger.error("Failed to connect to MCP Server over STDIO during startup: %s", str(exc), exc_info=True)

    yield

    logger.info("Shutting down %s...", settings.PROJECT_NAME)
    shutdown_telemetry()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="FastAPI Microservice integrating LangChain with an MCP Server and Client using STDIO transport.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def correlation_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = (time.perf_counter() - start_time) * 1000
    trace_id, span_id = get_current_trace_ids()

    response.headers["X-Request-ID"] = request_id
    if trace_id:
        response.headers["X-Trace-ID"] = trace_id
    if span_id:
        response.headers["X-Span-ID"] = span_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# -----------------------------------------------------------------------------
# Liveness & Health Endpoint
# -----------------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check and MCP STDIO status",
    tags=["System"],
)
async def health_check():
    with tracer.start_as_current_span("mcp.health_check") as span:
        try:
            tools = await mcp_client.list_tools()
            tool_names = [t.name for t in tools]
            span.set_attribute("mcp.tools_count", len(tools))
            return HealthResponse(
                status="healthy",
                service=settings.SERVICE_NAME,
                mcp_server="ecommerce-mcp-server",
                transport="STDIO",
                discovered_tools_count=len(tools),
                tools=tool_names,
            )
        except Exception as exc:
            span.record_exception(exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"MCP Server unreachable over STDIO: {str(exc)}",
            )


# -----------------------------------------------------------------------------
# MCP Direct Tool Endpoints (via MCP Client over STDIO)
# -----------------------------------------------------------------------------
@app.get(
    "/mcp/tools",
    response_model=List[MCPToolInfo],
    summary="List all tools discovered from the MCP Server over STDIO",
    tags=["MCP"],
)
async def list_mcp_tools(refresh: bool = False):
    with tracer.start_as_current_span("mcp.list_tools") as span:
        tools = await mcp_client.list_tools(force_refresh=refresh)
        span.set_attribute("mcp.tools_count", len(tools))
        return tools


@app.post(
    "/mcp/tools/call",
    response_model=CallToolResponse,
    summary="Invoke an MCP tool directly through the MCP Client over STDIO",
    tags=["MCP"],
)
async def call_mcp_tool(payload: CallToolRequest):
    with tracer.start_as_current_span("mcp.call_tool") as span:
        span.set_attribute("mcp.tool_name", payload.tool_name)
        try:
            result = await mcp_client.call_tool(payload.tool_name, payload.arguments)
            return CallToolResponse(
                success=True,
                tool_name=payload.tool_name,
                result=result,
                transport="STDIO",
            )
        except Exception as exc:
            span.record_exception(exc)
            logger.error("Failed to execute MCP tool '%s': %s", payload.tool_name, str(exc), exc_info=True)
            return CallToolResponse(
                success=False,
                tool_name=payload.tool_name,
                result=None,
                transport="STDIO",
                error=str(exc),
            )


# -----------------------------------------------------------------------------
# LangChain Integration Endpoints
# -----------------------------------------------------------------------------
@app.get(
    "/langchain/tools",
    summary="List all tools adapted into native LangChain StructuredTools",
    tags=["LangChain"],
)
async def list_langchain_tools():
    with tracer.start_as_current_span("langchain.list_tools") as span:
        lc_tools = await langchain_adapter.get_langchain_tools()
        span.set_attribute("langchain.tools_count", len(lc_tools))
        return [
            {
                "name": t.name,
                "description": t.description,
                "args_schema": t.args_schema.schema() if t.args_schema else {},
            }
            for t in lc_tools
        ]


@app.post(
    "/langchain/chat",
    response_model=LangChainChatResponse,
    summary="Execute a natural language prompt with the LangChain Agent using MCP tools over STDIO",
    tags=["LangChain"],
)
async def langchain_chat(payload: LangChainChatRequest):
    with tracer.start_as_current_span("langchain.chat") as span:
        span.set_attribute("langchain.prompt", payload.prompt)
        try:
            response = await langchain_adapter.chat_and_execute(payload.prompt)
            span.set_attribute("langchain.tools_used_count", len(response.tools_used))
            return response
        except Exception as exc:
            span.record_exception(exc)
            logger.error("LangChain agent execution error: %s", str(exc), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LangChain execution error: {str(exc)}",
            )


@app.post(
    "/langchain/tools/invoke",
    summary="Invoke a tool via LangChain's StructuredTool.ainvoke primitive over STDIO",
    tags=["LangChain"],
)
async def langchain_invoke_tool(payload: CallToolRequest):
    with tracer.start_as_current_span("langchain.tool_invoke") as span:
        span.set_attribute("langchain.tool_name", payload.tool_name)
        try:
            result = await langchain_adapter.invoke_tool(payload.tool_name, payload.arguments)
            return {
                "success": True,
                "tool_name": payload.tool_name,
                "framework": "LangChain",
                "transport": "MCP STDIO",
                "result": result,
            }
        except Exception as exc:
            span.record_exception(exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

