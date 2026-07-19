import sys
import os

# Adjust this path to match your PythonAnywhere username
sys.path.insert(0, '/home/Khageswar2712/dataset-explorer/backend')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Wrap FastAPI (ASGI) as WSGI for PythonAnywhere
from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
