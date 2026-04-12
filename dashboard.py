"""
Main: Teiko Technical Assignment
Sub: dashboard.py — starts FastAPI backend + React frontend dev server

Author: William McLain
Date: 2026-04-12
Version: 1.0.0

Usage:
    python dashboard.py
    OR
    make dashboard
"""

import subprocess
import sys
import os
import time
import signal

ROOT     = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "frontend")
BACKEND  = os.path.join(ROOT, "backend")

# Windows needs "npm.cmd"; Linux/Mac uses "npm"
NPM = "npm.cmd" if sys.platform == "win32" else "npm"

processes = []

def shutdown(sig, frame):
    print("\nShutting down servers...")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

def main():
    print("Starting Teiko Clinical Dashboard...\n")

    # Start FastAPI backend on port 8000
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=BACKEND,
    )
    processes.append(backend_proc)
    print("Backend running at: http://localhost:8000")
    print("API docs at:        http://localhost:8000/docs\n")

    time.sleep(2)

    # Start React frontend dev server on port 5173
    frontend_proc = subprocess.Popen(
        [NPM, "run", "dev"],
        cwd=FRONTEND,
    )
    processes.append(frontend_proc)
    print("Frontend running at: http://localhost:5173\n")

    print("Dashboard ready. Press Ctrl+C to stop.\n")

    # Wait for either process to exit
    for p in processes:
        p.wait()

if __name__ == "__main__":
    main()