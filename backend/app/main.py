import os

# Force non-interactive matplotlib backend (prevents GUI init hang on headless server)
os.environ["MPLBACKEND"] = "Agg"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.routers import upload, eda


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Dataset Explorer backend started.")
    yield
    logger.info("AI Dataset Explorer backend shutting down.")


app = FastAPI(
    title="AI Dataset Explorer API",
    description="Auto-EDA + AI insights over uploaded datasets",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(eda.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "storage": "redis" if settings.use_redis else "filesystem",
    }
