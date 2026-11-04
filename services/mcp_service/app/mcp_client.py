import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.schemas import MCPToolInfo

logger = logging.getLogger("mcp_client")

# Path to the MCP server script
MCP_SERVER_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "mcp_server.py")
)


def get_stdio_server_parameters() -> StdioServerParameters:
    """Builds the StdioServerParameters to launch the MCP server as a subprocess."""
    return StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_SCRIPT],
        env=dict(os.environ),
    )


@asynccontextmanager
async def open_mcp_session() -> AsyncGenerator[ClientSession, None]:
    """
    Async context manager that spawns the MCP server subprocess,
    establishes an STDIO communication pipe, initializes the session,
    and yields the ClientSession.
    """
    params = get_stdio_server_parameters()
    logger.debug("Spawning MCP Server subprocess over STDIO: %s %s", params.command, params.args)

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await session.initialize()
            logger.debug(
                "Connected to MCP Server: %s v%s",
                init_result.server_info.name,
                init_result.server_info.version,
            )
            yield session


class MCPClientManager:
    """High-level client interface for discovering and calling MCP tools over STDIO."""

    def __init__(self):
        self._cached_tools: Optional[List[MCPToolInfo]] = None

    async def list_tools(self, force_refresh: bool = False) -> List[MCPToolInfo]:
        """Lists all tools exposed by the MCP Server over STDIO."""
        if self._cached_tools is not None and not force_refresh:
            return self._cached_tools

        async with open_mcp_session() as session:
            tools_result = await session.list_tools()
            tool_list = []
            for tool in tools_result.tools:
                tool_list.append(
                    MCPToolInfo(
                        name=tool.name,
                        description=tool.description,
                        input_schema=getattr(tool, "input_schema", getattr(tool, "inputSchema", {})),
                    )
                )

            self._cached_tools = tool_list
            logger.info("Discovered %d MCP tools over STDIO pipe", len(tool_list))
            return tool_list

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Executes an MCP tool over the STDIO pipe and returns the parsed result.
        """
        logger.info("Calling MCP tool '%s' via STDIO with args: %s", tool_name, arguments)
        async with open_mcp_session() as session:
            call_result = await session.call_tool(name=tool_name, arguments=arguments)

            # Process returned content
            if not call_result.content:
                return None

            # Collect text contents
            text_blocks = []
            for block in call_result.content:
                if hasattr(block, "text"):
                    text_blocks.append(block.text)
                else:
                    text_blocks.append(str(block))

            raw_text = "\n".join(text_blocks)

            # If result is valid JSON, parse it into dict/list for caller convenience
            try:
                parsed_json = json.loads(raw_text)
                return parsed_json
            except (json.JSONDecodeError, TypeError):
                return raw_text


# Global client instance
mcp_client = MCPClientManager()
