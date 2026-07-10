from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.routers import upload, eda, rag, chat

app = FastAPI(
    title="AI Dataset Explorer API",
    description="Auto-EDA + RAG chat + AI insights over uploaded datasets",
    version="0.1.0",
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
app.include_router(rag.router)
app.include_router(chat.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    logger.info("AI Dataset Explorer backend started.")
