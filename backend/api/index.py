"""
Vercel Python Serverless Function — entry point.

Vercel's @vercel/python runtime looks for a file in api/ that exports a
WSGI or ASGI callable named `app` or `handler`.

We use Mangum to wrap the FastAPI ASGI app as an AWS Lambda-compatible handler,
which is what Vercel's Python runtime expects.

Matplotlib backend must be set BEFORE any import that triggers matplotlib;
we set it here as the very first thing after stdlib.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Environment bootstrap
# ---------------------------------------------------------------------------

# Ensure non-GUI matplotlib backend (no display available in serverless)
os.environ.setdefault("MPLBACKEND", "Agg")

# Make sure the backend package is importable when Vercel runs this file
# from backend/api/index.py — add the backend dir to sys.path.
_this_dir = os.path.dirname(os.path.abspath(__file__))          # backend/api/
_backend_dir = os.path.dirname(_this_dir)                        # backend/
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Load .env when running locally (Vercel injects env vars natively)
from dotenv import load_dotenv
load_dotenv(os.path.join(_backend_dir, ".env"))

# ---------------------------------------------------------------------------
# FastAPI app + Mangum ASGI adapter
# ---------------------------------------------------------------------------

from app.main import app  # noqa: E402  (import after path setup)
from mangum import Mangum  # noqa: E402

# Mangum wraps the ASGI app for Lambda-compatible runtimes (which Vercel uses)
handler = Mangum(app, lifespan="off")
