import json
import math
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.services import dataset_store, eda_engine, insights
from app.models.schemas import EDAResponse
from loguru import logger

_eda_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="eda-worker")


def _sanitize(obj):
    """Recursively replace NaN/Inf floats and numpy scalars with JSON-safe values."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize(i) for i in obj]
    elif hasattr(obj, "item"):          # numpy scalar (int64, float64, …)
        return _sanitize(obj.item())
    elif hasattr(obj, "tolist"):        # numpy array
        return _sanitize(obj.tolist())
    return obj


router = APIRouter(prefix="/api/dataset", tags=["eda"])


@router.get("/{dataset_id}/eda")
async def get_eda(dataset_id: str, ai_insights: bool = Query(default=True)):
    try:
        df = dataset_store.load_dataframe(dataset_id)
    except dataset_store.DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    async def event_stream():
        # ── 1. Serve cached result instantly ─────────────────────────────
        if ai_insights:
            cached = dataset_store.load_eda_cache(dataset_id)
            if cached:
                payload = json.dumps({"type": "complete", "data": _sanitize(cached)})
                yield f"data: {payload}\n\n"
                return

        # ── 2. Bridge the sync generator to async via a queue ────────────
        #    The blocking EDA generator runs in a thread-pool worker so it
        #    never stalls the asyncio event loop.  Each yielded event is
        #    put into an asyncio.Queue and consumed here, allowing uvicorn
        #    to flush bytes between events in real-time.
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        SENTINEL = object()

        def _run_eda():
            try:
                for event in eda_engine.run_full_eda_generator(
                    df, generate_ai_insights=ai_insights
                ):
                    loop.call_soon_threadsafe(q.put_nowait, event)
            except Exception as exc:
                loop.call_soon_threadsafe(
                    q.put_nowait, {"type": "error", "error": str(exc)}
                )
            finally:
                loop.call_soon_threadsafe(q.put_nowait, SENTINEL)

        loop.run_in_executor(_eda_executor, _run_eda)

        # ── 3. Stream events as they arrive ──────────────────────────────
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=300)
            except asyncio.TimeoutError:
                logger.error("EDA stream timed out waiting for next event")
                yield f"data: {json.dumps({'type': 'error', 'error': 'EDA generation timed out'})}\n\n"
                return

            if event is SENTINEL:
                return

            event_type = event.get("type")
            logger.info(f"Streaming event: {event_type}")

            if event_type == "complete":
                data = _sanitize(event["data"])
                data["dataset_id"] = dataset_id

                if ai_insights:
                    try:
                        dataset_store.save_eda_cache(dataset_id, data)
                    except Exception as e:
                        logger.error(f"Failed to save EDA cache: {e}")

                payload = json.dumps({"type": "complete", "data": data})
                yield f"data: {payload}\n\n"

            elif event_type == "error":
                yield f"data: {json.dumps(event)}\n\n"

            else:
                # progress or any other event type
                safe_event = _sanitize(event)
                yield f"data: {json.dumps(safe_event)}\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "Content-Type": "text/event-stream",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@router.get("/{dataset_id}/executive-summary")
def get_executive_summary(dataset_id: str):
    cached = dataset_store.load_summary_cache(dataset_id)
    if cached:
        return cached

    try:
        df = dataset_store.load_dataframe(dataset_id)
    except dataset_store.DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    from app.services import preprocessing

    summary = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
    }
    cleaning = preprocessing.analyze(df)
    try:
        text = insights.explain_dataset_overview(summary, cleaning.model_dump())
    except Exception as e:
        logger.error(f"Failed to generate executive summary: {e}")
        text = (
            "AI executive summary generation failed due to API connectivity issues. "
            "Please try again later."
        )

    result = {"executive_summary": text}
    try:
        dataset_store.save_summary_cache(dataset_id, result)
    except Exception as e:
        logger.error(f"Failed to save summary cache: {e}")

    return result
