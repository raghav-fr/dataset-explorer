from fastapi import APIRouter, HTTPException
from app.services import dataset_store, chunking, qdrant_store

router = APIRouter(prefix="/api/dataset", tags=["rag"])


@router.post("/{dataset_id}/index")
def index_dataset_for_chat(dataset_id: str, max_rows: int = 2000):
    try:
        df = dataset_store.load_dataframe(dataset_id)
    except dataset_store.DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    chunks = chunking.build_all_chunks(df, max_rows=max_rows)
    indexed_count = qdrant_store.index_chunks(dataset_id, chunks)

    return {
        "dataset_id": dataset_id,
        "chunks_indexed": indexed_count,
        "status": "ready_for_chat",
    }


@router.get("/{dataset_id}/index-status")
def get_index_status(dataset_id: str):
    return {
        "dataset_id": dataset_id,
        "indexed": qdrant_store.is_indexed(dataset_id)
    }
