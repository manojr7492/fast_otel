#!/bin/bash

# ==============================================================================
# Stop all 6 FastAPI E-Commerce Microservices
# ==============================================================================

echo "Stopping microservices and React frontend on ports 8001 through 8007 and 5173..."

for port in 8001 8002 8003 8004 8005 8006 8007 5173; do
    pid=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "  → Killing process on port $port (PID: $pid)..."
        kill -15 $pid 2>/dev/null || kill -9 $pid 2>/dev/null
    else
        echo "  ℹ Port $port is already free."
    fi
done

echo "✓ All services stopped."

