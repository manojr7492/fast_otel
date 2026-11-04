import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server.mcpserver import MCPServer

# Set up logging to stderr only so stdout remains clean for MCP JSON-RPC protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MCP-Server] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_server")

# Initialize MCP Server instance
server = MCPServer(name="ecommerce-mcp-server", version="1.0.0")


# -----------------------------------------------------------------------------
# MCP Tools Exposed via Model Context Protocol
# -----------------------------------------------------------------------------

@server.tool()
def calculate_discount(price: float, discount_percent: float) -> str:
    """
    Calculate discounted price, total savings, and estimated tax for an e-commerce item.
    Args:
        price: Original item price in USD (e.g. 3499.00).
        discount_percent: Percentage discount to apply (e.g. 20.0 for 20%).
    """
    logger.info("Executing calculate_discount: price=%.2f, discount=%.1f%%", price, discount_percent)
    discount_amount = round((price * discount_percent) / 100.0, 2)
    discounted_price = round(price - discount_amount, 2)
    tax = round(discounted_price * 0.0825, 2)
    final_total = round(discounted_price + tax, 2)

    result = {
        "original_price": price,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "discounted_price": discounted_price,
        "estimated_tax": tax,
        "final_total": final_total,
        "currency": "USD",
    }
    return json.dumps(result, indent=2)


@server.tool()
def search_product_catalog(query: str, category: Optional[str] = "") -> str:
    """
    Search the hardware product catalog for laptops, monitors, audio, and keyboards.
    Args:
        query: Search term (e.g. 'macbook', 'headphones', 'keyboard', 'monitor').
        category: Optional category filter (e.g. 'laptops', 'audio', 'displays').
    """
    category = category or ""
    logger.info("Executing search_product_catalog: query='%s', category='%s'", query, category)
    catalog = [
        {
            "sku": "MACBOOK-M3-MAX",
            "name": "Apple MacBook Pro 16\" M3 Max",
            "category": "laptops",
            "price": 3499.00,
            "specs": "16-core CPU, 40-core GPU, 48GB Unified Memory, 1TB SSD",
            "stock": 42,
        },
        {
            "sku": "DELL-XPS-16-9640",
            "name": "Dell XPS 16 OLED Workstation",
            "category": "laptops",
            "price": 2699.00,
            "specs": "Intel Core Ultra 9, RTX 4070, 32GB RAM, 4K OLED",
            "stock": 18,
        },
        {
            "sku": "SONY-WH1000XM5-BLK",
            "name": "Sony WH-1000XM5 Noise Canceling Headphones",
            "category": "audio",
            "price": 399.99,
            "specs": "Dual QN1 ANC Processors, LDAC Wireless, 30hr battery",
            "stock": 65,
        },
        {
            "sku": "KEYCHRON-Q1-PRO-MAX",
            "name": "Keychron Q1 Pro Custom Mechanical Keyboard",
            "category": "keyboards",
            "price": 199.00,
            "specs": "CNC Aluminum, Double-Gasket, QMK/VIA, Bluetooth 5.1",
            "stock": 54,
        },
        {
            "sku": "APPLE-STUDIO-DISP-5K",
            "name": "Apple Studio Display 27\" 5K Retina",
            "category": "displays",
            "price": 1599.00,
            "specs": "5120x2880 5K, 600 nits, 12MP Center Stage Camera",
            "stock": 12,
        },
    ]

    q_lower = query.lower()
    cat_lower = category.lower()
    matches = []
    for item in catalog:
        if cat_lower and cat_lower not in item["category"].lower():
            continue
        if (
            q_lower in item["name"].lower()
            or q_lower in item["sku"].lower()
            or q_lower in item["specs"].lower()
            or q_lower in item["category"].lower()
        ):
            matches.append(item)

    if not matches and not q_lower:
        matches = catalog

    return json.dumps({"count": len(matches), "query": query, "results": matches}, indent=2)


@server.tool()
def check_inventory_stock(sku: str) -> str:
    """
    Check real-time stock levels, warehouse location, and reservation availability for a SKU.
    Args:
        sku: Product SKU identifier (e.g. 'MACBOOK-M3-MAX', 'SONY-WH1000XM5-BLK').
    """
    logger.info("Executing check_inventory_stock: sku='%s'", sku)
    stock_registry = {
        "MACBOOK-M3-MAX": {"quantity": 42, "reserved": 2, "warehouse": "SAN-FRANCISCO-HUB", "status": "IN_STOCK"},
        "DELL-XPS-16-9640": {"quantity": 18, "reserved": 0, "warehouse": "NEW-YORK-HUB", "status": "IN_STOCK"},
        "SONY-WH1000XM5-BLK": {"quantity": 65, "reserved": 5, "warehouse": "AUSTIN-HUB", "status": "IN_STOCK"},
        "KEYCHRON-Q1-PRO-MAX": {"quantity": 54, "reserved": 1, "warehouse": "CHICAGO-HUB", "status": "IN_STOCK"},
        "APPLE-STUDIO-DISP-5K": {"quantity": 12, "reserved": 0, "warehouse": "SAN-FRANCISCO-HUB", "status": "LOW_STOCK"},
    }

    clean_sku = sku.strip().upper()
    info = stock_registry.get(clean_sku, {
        "quantity": 25,
        "reserved": 0,
        "warehouse": "CENTRAL-DISTRIBUTION-HUB",
        "status": "IN_STOCK (DEFAULT)",
    })

    result = {
        "sku": clean_sku,
        "available_quantity": info["quantity"] - info["reserved"],
        "total_quantity": info["quantity"],
        "reserved_quantity": info["reserved"],
        "warehouse_location": info["warehouse"],
        "inventory_status": info["status"],
    }
    return json.dumps(result, indent=2)


@server.tool()
def convert_currency(amount: float, from_currency: Optional[str] = "USD", to_currency: Optional[str] = "EUR") -> str:
    """
    Convert monetary amounts between currencies (USD, EUR, GBP, JPY, CAD, INR).
    Args:
        amount: Value to convert.
        from_currency: Base currency code (default: USD).
        to_currency: Target currency code (default: EUR).
    """
    from_currency = from_currency or "USD"
    to_currency = to_currency or "EUR"
    logger.info("Executing convert_currency: %s %s -> %s", amount, from_currency, to_currency)
    rates_from_usd = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 154.5,
        "CAD": 1.38,
        "INR": 83.45,
    }

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    rate_from = rates_from_usd.get(from_curr, 1.0)
    rate_to = rates_from_usd.get(to_curr, 1.0)

    # Convert to USD first, then to target currency
    in_usd = amount / rate_from
    converted = round(in_usd * rate_to, 2)

    result = {
        "original_amount": amount,
        "from_currency": from_curr,
        "to_currency": to_curr,
        "exchange_rate": round(rate_to / rate_from, 4),
        "converted_amount": converted,
    }
    return json.dumps(result, indent=2)


@server.tool()
def get_system_status() -> str:
    """
    Inspect the status of the MCP server, active transport, and linked microservices.
    """
    logger.info("Executing get_system_status")
    status = {
        "mcp_server": "ecommerce-mcp-server",
        "version": "1.0.0",
        "transport": "STDIO (Standard Input/Output JSON-RPC)",
        "protocol": "Model Context Protocol (MCP 2.x)",
        "active_tools_count": 5,
        "tracing_backend": "Jaeger OTLP HTTP (http://localhost:4318/v1/traces)",
        "framework": "FastAPI + LangChain",
    }
    return json.dumps(status, indent=2)


# -----------------------------------------------------------------------------
# STDIO Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting MCP Server over STDIO pipe...")
    asyncio.run(server.run_stdio_async())
