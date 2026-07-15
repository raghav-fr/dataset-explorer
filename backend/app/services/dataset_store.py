import os
import uuid
import json
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


def save_eda_cache(dataset_id: str, eda_data: dict) -> None:
    path = os.path.join(settings.reports_dir, f"{dataset_id}_eda.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(eda_data, f, ensure_ascii=False, indent=2)


def load_eda_cache(dataset_id: str) -> dict | None:
    path = os.path.join(settings.reports_dir, f"{dataset_id}_eda.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_summary_cache(dataset_id: str, summary_data: dict) -> None:
    path = os.path.join(settings.reports_dir, f"{dataset_id}_summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)


def load_summary_cache(dataset_id: str) -> dict | None:
    path = os.path.join(settings.reports_dir, f"{dataset_id}_summary.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

