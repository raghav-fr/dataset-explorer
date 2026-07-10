import pandas as pd
import numpy as np
from app.services import visualization, insights
from app.models.schemas import ColumnStats, EDAResponse


def _numeric_stats(series: pd.Series) -> dict:
    desc = series.describe()
    return {
        "count": int(desc.get("count", 0)),
        "mean": round(float(series.mean()), 4) if series.notna().any() else None,
        "median": round(float(series.median()), 4) if series.notna().any() else None,
        "mode": float(series.mode().iloc[0]) if not series.mode().empty else None,
        "std": round(float(series.std()), 4) if series.notna().any() else None,
        "variance": round(float(series.var()), 4) if series.notna().any() else None,
        "skewness": round(float(series.skew()), 4) if series.notna().any() else None,
        "kurtosis": round(float(series.kurt()), 4) if series.notna().any() else None,
        "min": float(desc.get("min")) if "min" in desc else None,
        "max": float(desc.get("max")) if "max" in desc else None,
        "q1": round(float(series.quantile(0.25)), 4) if series.notna().any() else None,
        "q3": round(float(series.quantile(0.75)), 4) if series.notna().any() else None,
        "missing": int(series.isna().sum()),
    }


def _categorical_stats(series: pd.Series) -> dict:
    vc = series.value_counts(dropna=True)
    return {
        "unique_values": int(series.nunique(dropna=True)),
        "top_categories": vc.head(10).to_dict(),
        "missing": int(series.isna().sum()),
    }


def run_full_eda(df: pd.DataFrame, generate_ai_insights: bool = True) -> EDAResponse:
    summary = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
        "missing_values_total": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [
        c
        for c in df.select_dtypes(include=["object", "category", "bool"]).columns
        if c not in numeric_cols
    ]

    # Collect numerical stats & plots
    numerical_results = []
    numerical_info_for_ai = []
    for col in numeric_cols:
        stats = _numeric_stats(df[col])
        chart = visualization.histogram(df, col)
        numerical_results.append(
            ColumnStats(name=col, dtype=str(df[col].dtype), stats=stats, chart=chart, ai_insight=None)
        )
        if generate_ai_insights:
            numerical_info_for_ai.append({"column": col, "statistics": stats})

    # Collect categorical stats & plots
    categorical_results = []
    categorical_info_for_ai = []
    for col in categorical_cols:
        stats = _categorical_stats(df[col])
        chart = visualization.count_plot(df, col)
        categorical_results.append(
            ColumnStats(name=col, dtype=str(df[col].dtype), stats=stats, chart=chart, ai_insight=None)
        )
        if generate_ai_insights:
            categorical_info_for_ai.append({"column": col, "top_categories": stats["top_categories"]})

    # Find correlation pairs & plot
    correlation_chart = None
    top_pairs = []
    if len(numeric_cols) >= 2:
        correlation_chart = visualization.correlation_heatmap(df)
        corr = df[numeric_cols].corr()
        pairs = []
        seen = set()
        for a in corr.columns:
            for b in corr.columns:
                if a == b or (b, a) in seen:
                    continue
                seen.add((a, b))
                pairs.append((a, b, round(float(corr.loc[a, b]), 3)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        top_pairs = [p for p in pairs[:5] if abs(p[2]) > 0.3]

    # Generate insights in a single batch call if generate_ai_insights is True
    correlation_insight = None
    if generate_ai_insights:
        from loguru import logger
        try:
            batch_insights = insights.explain_eda_batch(
                numerical_info_for_ai,
                categorical_info_for_ai,
                top_pairs
            )
            
            # Distribute numerical insights
            num_insights = batch_insights.get("numerical", {}) if isinstance(batch_insights, dict) else {}
            for col_stat in numerical_results:
                col_stat.ai_insight = num_insights.get(col_stat.name) if isinstance(num_insights, dict) else None
            
            # Distribute categorical insights
            cat_insights = batch_insights.get("categorical", {}) if isinstance(batch_insights, dict) else {}
            for col_stat in categorical_results:
                col_stat.ai_insight = cat_insights.get(col_stat.name) if isinstance(cat_insights, dict) else None
                
            correlation_insight = batch_insights.get("correlation") if isinstance(batch_insights, dict) else None
            
        except Exception as e:
            logger.error(f"Failed to generate batch AI insights: {e}")
            fallback_msg = "AI insight temporarily unavailable due to rate limits or API errors."
            
            # Set fallback insights
            for col_stat in numerical_results:
                col_stat.ai_insight = fallback_msg
            for col_stat in categorical_results:
                col_stat.ai_insight = fallback_msg
            correlation_insight = fallback_msg if top_pairs else None

    return EDAResponse(
        dataset_id="",  # filled in by router
        summary=summary,
        numerical_columns=numerical_results,
        categorical_columns=categorical_results,
        correlation=correlation_chart,
        correlation_insight=correlation_insight,
    )

