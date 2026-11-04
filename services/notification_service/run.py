import os
import sys
import uvicorn

# Ensure notification_service is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
    )

