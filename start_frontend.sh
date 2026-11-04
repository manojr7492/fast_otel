#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

echo "=================================================="
echo "⚡ Starting React E-Commerce Frontend on :5173..."
echo "=================================================="

cd "$FRONTEND_DIR"
npm run dev

