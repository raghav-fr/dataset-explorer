from fastapi import APIRouter, HTTPException, Query
from app.services import dataset_store, eda_engine, insights
from app.models.schemas import EDAResponse

router = APIRouter(prefix="/api/dataset", tags=["eda"])


@router.get("/{dataset_id}/eda", response_model=EDAResponse)
def get_eda(dataset_id: str, ai_insights: bool = Query(default=True)):
    if ai_insights:
        cached = dataset_store.load_eda_cache(dataset_id)
        if cached:
            return EDAResponse(**cached)

    try:
        df = dataset_store.load_dataframe(dataset_id)
    except dataset_store.DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    result = eda_engine.run_full_eda(df, generate_ai_insights=ai_insights)
    result.dataset_id = dataset_id

    if ai_insights:
        try:
            dataset_store.save_eda_cache(dataset_id, result.model_dump())
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to save EDA cache: {e}")

    return result


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
    text = insights.explain_dataset_overview(summary, cleaning.model_dump())
    
    result = {"executive_summary": text}
    try:
        dataset_store.save_summary_cache(dataset_id, result)
    except Exception as e:
        from loguru import logger
        logger.error(f"Failed to save summary cache: {e}")

    return result


