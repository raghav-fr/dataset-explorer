"""
wsgi.py — Entry point for traditional WSGI servers (e.g. PythonAnywhere / uWSGI).

For Vercel deployment, use backend/api/index.py instead.
"""

import sys
import os
import asyncio

# Force non-interactive matplotlib backend (prevents GUI init hang on headless server)
os.environ.setdefault("MPLBACKEND", "Agg")

# Add the backend directory to sys.path so `app` package is importable.
# Adjust this path if deploying to a different server.
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Load environment variables from the .env file next to this script.
from dotenv import load_dotenv
load_dotenv(os.path.join(_backend_dir, ".env"))

# Create and register a dedicated event loop BEFORE a2wsgi/FastAPI imports.
# This prevents the asyncio deadlock that causes HARAKIRI on uWSGI.
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
