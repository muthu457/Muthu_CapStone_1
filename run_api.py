#!/usr/bin/env python
"""Simple API server runner"""
import subprocess
import sys
import time

print("=" * 60)
print("SUPPORT TRIAGE CO-PILOT - API SERVER")
print("=" * 60)
print("\n[OK] API will run on http://0.0.0.0:8000")
print("[OK] Press Ctrl+C to stop\n")

try:
    import uvicorn
    from api import app
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )
except KeyboardInterrupt:
    print("\n\nShutting down...")
    sys.exit(0)
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
