#!/bin/bash

# ==============================================================================
# Start all 6 FastAPI E-Commerce Microservices in the background
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Virtual environment not found at $PROJECT_ROOT/.venv"
    exit 1
fi

LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

echo "=================================================="
echo "🚀 Starting All 6 E-Commerce Microservices..."
echo "=================================================="

start_service() {
    local name="$1"
    local port="$2"
    local script="$3"
    local log="$LOG_DIR/$name.log"

    # Check if already running on port
    if lsof -i :$port > /dev/null 2>&1; then
        echo "  ℹ $name is already running on port $port."
    else
        echo "  → Starting $name on port $port..."
        nohup "$PYTHON_BIN" "$PROJECT_ROOT/$script" > "$log" 2>&1 &
        echo $! > "$LOG_DIR/$name.pid"
    fi
}

start_service "notification_service" 8006 "services/notification_service/run.py"
start_service "product_service"      8002 "services/product_service/run.py"
start_service "inventory_service"    8005 "services/inventory_service/run.py"
start_service "payment_service"      8004 "services/payment_service/run.py"
start_service "order_service"        8003 "services/order_service/run.py"
start_service "user_service"         8001 "services/user_service/run.py"
start_service "mcp_service"          8007 "services/mcp_service/run.py"

echo ""
echo "Waiting for services to become healthy..."
sleep 2

for port in 8001 8002 8003 8004 8005 8006 8007; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" 2>/dev/null || echo "offline")
    if [ "$status" = "200" ]; then
        echo "  ✓ Port $port is healthy (HTTP 200)"
    else
        echo "  ⏳ Port $port status: $status"
    fi
done

echo ""
echo "=================================================="
echo "🎉 All services launched! Check logs in $LOG_DIR"
echo "To stop all services, run: ./stop_all.sh"
echo "=================================================="

