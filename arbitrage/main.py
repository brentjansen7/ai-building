#!/usr/bin/env python3
"""Main entry point for AI Arbitrage System"""

import asyncio
import uvicorn
from api.simple import app

if __name__ == "__main__":
    # Run API server on localhost:8000
    uvicorn.run(
        "api.simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
