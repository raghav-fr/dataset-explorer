from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings
from app.services import ingestion, preprocessing, dataset_store
from app.models.schemas import UploadResponse, CleaningReport

router = APIRouter(prefix="/api/dataset", tags=["dataset"])


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    raw = await file.read()
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max is {settings.max_upload_mb} MB.",
        )

    df = ingestion.read_uploaded_file(file, raw)
    df = preprocessing.apply_basic_cleaning(df)
    dataset_id = dataset_store.save_dataframe(df)

    preview = df.head(10).astype(object).where(df.head(10).notna(), None).to_dict(orient="records")

    return UploadResponse(
        dataset_id=dataset_id,
        filename=file.filename or "uploaded",
        rows=df.shape[0],
        columns=df.shape[1],
        column_names=df.columns.astype(str).tolist(),
        dtypes={c: str(t) for c, t in df.dtypes.items()},
        preview=preview,
    )


@router.get("/{dataset_id}/cleaning-report", response_model=CleaningReport)
async def get_cleaning_report(dataset_id: str):
    try:
        df = dataset_store.load_dataframe(dataset_id)
    except dataset_store.DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return preprocessing.analyze(df)
