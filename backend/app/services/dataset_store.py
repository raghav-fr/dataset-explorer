import os
import uuid
import pandas as pd
from app.config import settings


class DatasetNotFoundError(Exception):
    pass


def _path_for(dataset_id: str) -> str:
    return os.path.join(settings.storage_dir, f"{dataset_id}.parquet")


def save_dataframe(df: pd.DataFrame) -> str:
    dataset_id = uuid.uuid4().hex[:12]
    df.to_parquet(_path_for(dataset_id), index=False)
    return dataset_id


def load_dataframe(dataset_id: str) -> pd.DataFrame:
    path = _path_for(dataset_id)
    if not os.path.exists(path):
        raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
    return pd.read_parquet(path)


def overwrite_dataframe(dataset_id: str, df: pd.DataFrame) -> None:
    df.to_parquet(_path_for(dataset_id), index=False)


def dataset_exists(dataset_id: str) -> bool:
    return os.path.exists(_path_for(dataset_id))
