from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolInfo(BaseModel):
    name: str = Field(..., description="Unique tool name")
    description: Optional[str] = Field(None, description="Tool description for LLM reasoning")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema defining parameters")


class CallToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the MCP tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class CallToolResponse(BaseModel):
    success: bool
    tool_name: str
    result: Any
    transport: str = "STDIO"
    error: Optional[str] = None


class LangChainChatRequest(BaseModel):
    prompt: str = Field(..., description="Natural language prompt or user question")
    session_id: Optional[str] = Field("default-session", description="Session identifier")


class LangChainChatResponse(BaseModel):
    prompt: str
    thought_process: List[str] = Field(default_factory=list, description="Reasoning steps and thoughts")
    mcp_tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="MCP tools invoked over STDIO")
    final_answer: str = Field(..., description="Synthesized response from LangChain")
    tools_used: List[str] = Field(default_factory=list, description="List of MCP tool names used")


class HealthResponse(BaseModel):
    status: str
    service: str
    mcp_server: str
    transport: str
    discovered_tools_count: int
    tools: List[str]

