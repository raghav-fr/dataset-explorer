from fastapi import APIRouter, HTTPException, Query
from app.services import dataset_store, eda_engine, insights
from app.models.schemas import EDAResponse

router = APIRouter(prefix="/api/dataset", tags=["eda"])


@router.get("/{dataset_id}/eda", response_model=EDAResponse)
def get_eda(dataset_id: str, ai_insights: bool = Query(default=True)):
    try:
        df = dataset_store.load_dataframe(dataset_id)
    except dataset_store.DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    result = eda_engine.run_full_eda(df, generate_ai_insights=ai_insights)
    result.dataset_id = dataset_id
    return result


@router.get("/{dataset_id}/executive-summary")
def get_executive_summary(dataset_id: str):
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
    return {"executive_summary": text}

