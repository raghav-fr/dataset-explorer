from pydantic import BaseModel
from typing import Any, Optional


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    dtypes: dict[str, str]
    preview: list[dict[str, Any]]


class CleaningReport(BaseModel):
    missing_values: dict[str, int]
    missing_percent: dict[str, float]
    duplicate_rows: int
    constant_columns: list[str]
    high_cardinality_columns: list[str]
    inferred_datetime_columns: list[str]
    memory_usage_mb: float
    suggested_actions: list[str]


class ColumnStats(BaseModel):
    name: str
    dtype: str
    stats: dict[str, Any]
    chart: Optional[dict[str, Any]] = None
    ai_insight: Optional[str] = None


class EDAResponse(BaseModel):
    dataset_id: str
    summary: dict[str, Any]
    numerical_columns: list[ColumnStats]
    categorical_columns: list[ColumnStats]
    correlation: Optional[dict[str, Any]] = None
    correlation_insight: Optional[str] = None


class ChatRequest(BaseModel):
    dataset_id: str
    question: str
    top_k: int = 6


class ChatResponse(BaseModel):
    answer: str
    used_chunks: list[str]
