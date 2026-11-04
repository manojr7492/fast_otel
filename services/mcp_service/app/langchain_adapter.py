import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool
from pydantic import Field, create_model

from app.config import settings
from app.mcp_client import mcp_client
from app.schemas import LangChainChatResponse

logger = logging.getLogger("langchain_adapter")


class LangChainMCPAdapter:
    """
    Bridges Model Context Protocol (MCP) tools into native LangChain StructuredTools,
    and provides a LangChain execution engine that runs queries against them over STDIO.
    """

    def __init__(self):
        self._tools_cache: Optional[List[StructuredTool]] = None

    def _create_pydantic_schema(self, tool_name: str, input_schema: Dict[str, Any]):
        """Dynamically creates a Pydantic model for LangChain StructuredTool args_schema."""
        fields: Dict[str, Any] = {}
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "object": dict,
            "array": list,
        }

        properties = input_schema.get("properties", {})
        required_fields = set(input_schema.get("required", []))

        for prop_name, prop_spec in properties.items():
            prop_type = type_mapping.get(prop_spec.get("type"), Any)
            desc = prop_spec.get("description", "")
            default_val = ... if prop_name in required_fields else None
            fields[prop_name] = (prop_type, Field(default=default_val, description=desc))

        model_name = f"{tool_name.title().replace('_', '')}Schema"
        return create_model(model_name, **fields)

    async def get_langchain_tools(self, force_refresh: bool = False) -> List[StructuredTool]:
        """Discovers tools from the MCP Server over STDIO and wraps them as LangChain tools."""
        if self._tools_cache is not None and not force_refresh:
            return self._tools_cache

        mcp_tools = await mcp_client.list_tools(force_refresh=force_refresh)
        langchain_tools: List[StructuredTool] = []

        for m_tool in mcp_tools:
            tool_name = m_tool.name
            tool_desc = m_tool.description or f"MCP tool: {tool_name}"
            args_schema = self._create_pydantic_schema(tool_name, m_tool.input_schema)

            # Factory function to capture tool_name in closure
            def make_coroutine(name: str) -> Callable:
                async def _mcp_invoke(**kwargs) -> str:
                    clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
                    result = await mcp_client.call_tool(name, clean_kwargs)
                    if isinstance(result, (dict, list)):
                        return json.dumps(result, indent=2)
                    return str(result)
                return _mcp_invoke

            lc_tool = StructuredTool(
                name=tool_name,
                description=tool_desc,
                args_schema=args_schema,
                func=None,
                coroutine=make_coroutine(tool_name),
            )
            langchain_tools.append(lc_tool)

        self._tools_cache = langchain_tools
        logger.info("Successfully converted %d MCP tools into LangChain StructuredTools", len(langchain_tools))
        return langchain_tools

    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Directly invokes a single LangChain StructuredTool via the MCP STDIO pipe."""
        tools = await self.get_langchain_tools()
        target_tool = next((t for t in tools if t.name == tool_name), None)

        if not target_tool:
            raise ValueError(f"Tool '{tool_name}' not found among MCP tools: {[t.name for t in tools]}")

        return await target_tool.ainvoke(arguments)

    async def chat_and_execute(self, prompt: str) -> LangChainChatResponse:
        """
        Executes a user prompt using LangChain.
        Analyzes the prompt, determines which MCP tools to invoke over STDIO,
        executes them through LangChain StructuredTool primitives, and returns
        the synthesized thought process and final answer.
        """
        tools = await self.get_langchain_tools()
        tool_map = {t.name: t for t in tools}

        thought_process: List[str] = [
            f"Received user prompt: '{prompt}'",
            f"Discovered {len(tools)} available MCP tools over STDIO pipe: {list(tool_map.keys())}",
        ]
        tool_calls: List[Dict[str, Any]] = []
        tools_used: List[str] = []

        lower_prompt = prompt.lower()
        synthesized_parts: List[str] = []

        # -----------------------------------------------------------------
        # Reasoning & Tool Selection Heuristics via LangChain
        # -----------------------------------------------------------------

        # 1. Catalog Search Intent
        if any(w in lower_prompt for w in ["search", "find", "catalog", "macbook", "xps", "sony", "headphones", "keyboard", "monitor"]):
            thought_process.append("Intent detected: Product Catalog Search. Selecting 'search_product_catalog'.")
            search_query = ""
            for candidate in ["macbook", "dell", "xps", "sony", "headphones", "keyboard", "studio display", "monitor"]:
                if candidate in lower_prompt:
                    search_query = candidate
                    break
            
            call_args = {"query": search_query or "hardware"}
            raw_res = await tool_map["search_product_catalog"].ainvoke(call_args)
            parsed_res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res

            tool_calls.append({"tool": "search_product_catalog", "arguments": call_args, "result": parsed_res})
            tools_used.append("search_product_catalog")
            thought_process.append(f"MCP search_product_catalog returned {parsed_res.get('count', 0)} matching products.")

            results = parsed_res.get("results", [])
            if results:
                items_summary = "\n".join([f"• **{item['name']}** (SKU: `{item['sku']}`): ${item['price']} - {item['specs']}" for item in results[:3]])
                synthesized_parts.append(f"**Catalog Search Results:**\n{items_summary}")

        # 2. Discount Calculation Intent
        if any(w in lower_prompt for w in ["discount", "percent", "%", "off", "coupon", "savings", "sale"]):
            thought_process.append("Intent detected: Price & Discount Calculation. Selecting 'calculate_discount'.")
            # Extract price and percentage using regex
            price_match = re.search(r"\$?([0-9]+(?:\.[0-9]+)?)", prompt)
            pct_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", prompt) or re.search(r"([0-9]+(?:\.[0-9]+)?)\s*percent", lower_prompt)

            price_val = float(price_match.group(1)) if price_match else 3499.0
            pct_val = float(pct_match.group(1)) if pct_match else 20.0

            call_args = {"price": price_val, "discount_percent": pct_val}
            raw_res = await tool_map["calculate_discount"].ainvoke(call_args)
            parsed_res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res

            tool_calls.append({"tool": "calculate_discount", "arguments": call_args, "result": parsed_res})
            tools_used.append("calculate_discount")
            thought_process.append(f"MCP calculate_discount computed: original ${price_val} -> discounted ${parsed_res.get('discounted_price')} (savings: ${parsed_res.get('discount_amount')}).")

            synthesized_parts.append(
                f"**Discount Breakdown ({pct_val}% off on ${price_val}):**\n"
                f"• Savings: **${parsed_res.get('discount_amount')}**\n"
                f"• Discounted Price: **${parsed_res.get('discounted_price')}**\n"
                f"• Estimated Tax (8.25%): **${parsed_res.get('estimated_tax')}**\n"
                f"• Total with Tax: **${parsed_res.get('final_total')}**"
            )

        # 3. Inventory Stock Check Intent
        if any(w in lower_prompt for w in ["stock", "inventory", "available", "units", "warehouse", "sku"]):
            thought_process.append("Intent detected: Inventory Check. Selecting 'check_inventory_stock'.")
            sku_match = re.search(r"\b([A-Z0-9]+(?:-[A-Z0-9]+)+)\b", prompt)
            sku_val = sku_match.group(1) if sku_match else "MACBOOK-M3-MAX"

            call_args = {"sku": sku_val}
            raw_res = await tool_map["check_inventory_stock"].ainvoke(call_args)
            parsed_res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res

            tool_calls.append({"tool": "check_inventory_stock", "arguments": call_args, "result": parsed_res})
            tools_used.append("check_inventory_stock")
            thought_process.append(f"MCP check_inventory_stock for SKU '{sku_val}': {parsed_res.get('available_quantity')} units available.")

            synthesized_parts.append(
                f"**Live Warehouse Stock Status (SKU: `{sku_val}`):**\n"
                f"• Available Units: **{parsed_res.get('available_quantity')}** (Total: {parsed_res.get('total_quantity')}, Reserved: {parsed_res.get('reserved_quantity')})\n"
                f"• Warehouse Location: **{parsed_res.get('warehouse_location')}**\n"
                f"• Status: `{parsed_res.get('inventory_status')}`"
            )

        # 4. Currency Conversion Intent
        if any(w in lower_prompt for w in ["convert", "currency", "eur", "gbp", "jpy", "inr", "cad", "exchange"]):
            thought_process.append("Intent detected: Currency Conversion. Selecting 'convert_currency'.")
            amt_match = re.search(r"\$?([0-9]+(?:\.[0-9]+)?)", prompt)
            amount_val = float(amt_match.group(1)) if amt_match else 100.0

            target_curr = "EUR"
            for code in ["EUR", "GBP", "JPY", "INR", "CAD"]:
                if code in prompt.upper():
                    target_curr = code
                    break

            call_args = {"amount": amount_val, "from_currency": "USD", "to_currency": target_curr}
            raw_res = await tool_map["convert_currency"].ainvoke(call_args)
            parsed_res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res

            tool_calls.append({"tool": "convert_currency", "arguments": call_args, "result": parsed_res})
            tools_used.append("convert_currency")
            thought_process.append(f"MCP convert_currency: {amount_val} USD = {parsed_res.get('converted_amount')} {target_curr}.")

            synthesized_parts.append(
                f"**Currency Conversion:**\n"
                f"• ${amount_val} USD = **{parsed_res.get('converted_amount')} {target_curr}** (Exchange Rate: {parsed_res.get('exchange_rate')})"
            )

        # 5. System Status Intent
        if any(w in lower_prompt for w in ["status", "system", "health", "mcp", "transport"]):
            thought_process.append("Intent detected: System Status Check. Selecting 'get_system_status'.")
            raw_res = await tool_map["get_system_status"].ainvoke({})
            parsed_res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res

            tool_calls.append({"tool": "get_system_status", "arguments": {}, "result": parsed_res})
            tools_used.append("get_system_status")
            thought_process.append("MCP get_system_status executed successfully.")

            synthesized_parts.append(
                f"**System & Transport Health:**\n"
                f"• MCP Server: `{parsed_res.get('mcp_server')}` v{parsed_res.get('version')}\n"
                f"• Transport: `{parsed_res.get('transport')}`\n"
                f"• Protocol: `{parsed_res.get('protocol')}`"
            )

        # Fallback if no specific intent was matched: call get_system_status
        if not tool_calls:
            thought_process.append("No specific domain intent identified. Running general system status check.")
            raw_res = await tool_map["get_system_status"].ainvoke({})
            parsed_res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
            tool_calls.append({"tool": "get_system_status", "arguments": {}, "result": parsed_res})
            tools_used.append("get_system_status")
            synthesized_parts.append(
                f"Processed inquiry '{prompt}'. Connected to **{parsed_res.get('mcp_server')}** over **STDIO transport**."
            )

        thought_process.append("Synthesizing final response from all executed LangChain MCP tools.")
        final_answer = "\n\n".join(synthesized_parts)

        return LangChainChatResponse(
            prompt=prompt,
            thought_process=thought_process,
            mcp_tool_calls=tool_calls,
            final_answer=final_answer,
            tools_used=tools_used,
        )


# Global adapter instance
langchain_adapter = LangChainMCPAdapter()
