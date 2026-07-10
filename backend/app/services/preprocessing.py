import pandas as pd
import numpy as np
from app.models.schemas import CleaningReport


def infer_datetime_columns(df: pd.DataFrame) -> list[str]:
    candidates = []
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str).head(50)
            if sample.empty:
                continue
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                candidates.append(col)
    return candidates


def analyze(df: pd.DataFrame) -> CleaningReport:
    missing = df.isna().sum()
    missing_pct = (missing / len(df) * 100).round(2)

    constant_cols = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]

    high_card_cols = [
        c
        for c in df.select_dtypes(include=["object", "category"]).columns
        if df[c].nunique(dropna=True) > max(50, int(0.5 * len(df)))
    ]

    datetime_cols = infer_datetime_columns(df)
    duplicate_rows = int(df.duplicated().sum())
    memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3)

    suggestions = []
    if duplicate_rows > 0:
        suggestions.append(f"Drop {duplicate_rows} duplicate row(s).")
    if constant_cols:
        suggestions.append(f"Remove constant column(s): {', '.join(constant_cols)}.")
    high_missing = missing_pct[missing_pct > 40].index.tolist()
    if high_missing:
        suggestions.append(
            f"Consider dropping or imputing high-missing columns: {', '.join(high_missing)}."
        )
    if datetime_cols:
        suggestions.append(
            f"Convert to datetime dtype: {', '.join(datetime_cols)}."
        )
    if high_card_cols:
        suggestions.append(
            f"High-cardinality categorical column(s) may need encoding/hashing: {', '.join(high_card_cols)}."
        )
    if not suggestions:
        suggestions.append("Dataset looks clean; no major issues detected.")

    return CleaningReport(
        missing_values={k: int(v) for k, v in missing.items()},
        missing_percent={k: float(v) for k, v in missing_pct.items()},
        duplicate_rows=duplicate_rows,
        constant_columns=constant_cols,
        high_cardinality_columns=high_card_cols,
        inferred_datetime_columns=datetime_cols,
        memory_usage_mb=memory_mb,
        suggested_actions=suggestions,
    )


def apply_basic_cleaning(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
    drop_constant: bool = True,
    parse_datetime: bool = True,
) -> pd.DataFrame:
    df = df.copy()
    if drop_duplicates:
        df = df.drop_duplicates()
    if drop_constant:
        constant_cols = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
        df = df.drop(columns=constant_cols)
    if parse_datetime:
        for col in infer_datetime_columns(df):
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
    # Optimize memory for integer/float columns
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")
    return df
