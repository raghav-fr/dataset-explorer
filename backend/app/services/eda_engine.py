import pandas as pd
import numpy as np
from app.services import visualization, insights , gemini_client
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
    
    # 1. Build a column metadata summary to send to AI
    col_metadata = []
    for col in df.columns:
        # Determine basic type info
        if pd.api.types.is_numeric_dtype(df[col]):
            col_type = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_type = "datetime"
        elif pd.api.types.is_bool_dtype(df[col]):
            col_type = "boolean"
        else:
            col_type = "categorical"
            
        missing_count = int(df[col].isna().sum())
        unique_count = int(df[col].nunique())
        
        # Get up to 5 non-null sample values as native python types
        sample_vals = df[col].dropna().head(5).tolist()
        sample_vals = [x.item() if hasattr(x, "item") else str(x) for x in sample_vals]
        
        col_metadata.append({
            "name": col,
            "type": col_type,
            "missing": missing_count,
            "unique": unique_count,
            "sample_values": sample_vals
        })
        
    df_summary = {
        "summary": summary,
        "columns": col_metadata
    }
    
    # 2. Query AI to generate the EDA visualization plan
    planned_analyses = []
    from loguru import logger
    try:
        plan_response = insights.plan_eda_analyses(df_summary)
        planned_analyses = plan_response.get("analyses", [])
    except Exception as e:
        logger.error(f"Failed to get AI planned EDA: {e}. Falling back to default heuristics.")
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = [c for c in df.select_dtypes(include=["object", "category", "bool"]).columns if c not in numeric_cols]
        
        # Univariate fallbacks
        for col in numeric_cols[:2]:
            planned_analyses.append({
                "type": "univariate",
                "title": f"Distribution of {col}",
                "columns": [col],
                "plot_type": "histplot",
                "parameters": {"kde": True},
                "reasoning": "Analyze numerical column distribution."
            })
        for col in cat_cols[:1]:
            planned_analyses.append({
                "type": "univariate",
                "title": f"Distribution of {col}",
                "columns": [col],
                "plot_type": "countplot",
                "parameters": {},
                "reasoning": "Analyze categorical column distribution."
            })
            
        # Bivariate fallback
        if len(numeric_cols) >= 2:
            planned_analyses.append({
                "type": "bivariate",
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
                "columns": [numeric_cols[0], numeric_cols[1]],
                "plot_type": "scatterplot",
                "parameters": {},
                "reasoning": "Explore relationship between numeric features."
            })
            
        # Multivariate fallback
        if len(numeric_cols) >= 2 and len(cat_cols) >= 1:
            planned_analyses.append({
                "type": "multivariate",
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]} by {cat_cols[0]}",
                "columns": [numeric_cols[0], numeric_cols[1], cat_cols[0]],
                "plot_type": "scatterplot",
                "parameters": {"hue": cat_cols[0]},
                "reasoning": "Explore multi-variable interaction across classes."
            })
            
    # 3. Execute planned analyses
    numerical_results = []
    categorical_results = []
    custom_analyses_results = []
    
    analyses_to_explain = []
    
    for idx, plan in enumerate(planned_analyses):
        cols = plan.get("columns", [])
        p_type = plan.get("plot_type", "histplot")
        params = plan.get("parameters", {})
        a_type = plan.get("type", "univariate")
        title = plan.get("title", f"Analysis {idx+1}")
        reasoning = plan.get("reasoning", "")
        
        # Verify columns exist in dataframe
        cols = [c for c in cols if c in df.columns]
        if not cols:
            continue
            
        # Generate Seaborn/Matplotlib base64 chart
        chart = visualization.generate_custom_plot(df, cols, p_type, params)
        if not chart:
            continue
            
        # Compute summary stats for this analysis to help the AI explain it
        stats = {}
        try:
            if len(cols) == 1:
                col = cols[0]
                if pd.api.types.is_numeric_dtype(df[col]):
                    stats = _numeric_stats(df[col])
                else:
                    stats = _categorical_stats(df[col])
            elif len(cols) == 2:
                col1, col2 = cols[0], cols[1]
                if pd.api.types.is_numeric_dtype(df[col1]) and pd.api.types.is_numeric_dtype(df[col2]):
                    stats = {"correlation": round(float(df[col1].corr(df[col2])), 4)}
                elif pd.api.types.is_numeric_dtype(df[col1]) or pd.api.types.is_numeric_dtype(df[col2]):
                    num_col = col1 if pd.api.types.is_numeric_dtype(df[col1]) else col2
                    cat_col = col2 if num_col == col1 else col1
                    stats = {"group_means": df.groupby(cat_col)[num_col].mean().round(4).to_dict()}
                else:
                    stats = {"contingency_table": df.groupby(col1)[col2].value_counts().head(10).to_dict()}
            else:
                # Multivariate stats
                numeric_df = df[cols].select_dtypes(include="number")
                if numeric_df.shape[1] >= 2:
                    stats = {"correlations": numeric_df.corr().round(4).to_dict()}
                else:
                    stats = {"unique_value_counts": {c: int(df[c].nunique()) for c in cols}}
        except Exception as ex:
            logger.warning(f"Error computing stats for columns {cols}: {ex}")
            stats = {"error": str(ex)}
            
        analysis_data = {
            "title": title,
            "type": a_type,
            "columns": cols,
            "plot_type": p_type,
            "reasoning": reasoning,
            "statistics": stats,
            "chart": chart
        }
        
        analyses_to_explain.append(analysis_data)
        
    # 4. Generate batch AI insights for the executed analyses
    ai_insights = {}
    if generate_ai_insights and analyses_to_explain:
        try:
            # We pass a slimmed down list of analyses (without raw base64 charts) to the AI to write insights
            analyses_meta = [
                {
                    "title": a["title"],
                    "type": a["type"],
                    "columns": a["columns"],
                    "plot_type": a["plot_type"],
                    "reasoning": a["reasoning"],
                    "statistics": a["statistics"]
                }
                for a in analyses_to_explain
            ]
            batch_result = insights.explain_custom_analyses_batch(analyses_meta)
            ai_insights = batch_result.get("insights", [])
        except Exception as e:
            logger.error(f"Failed to generate batch AI insights for custom analyses: {e}")
            
    # 5. Distribute insights and map back to response schema
    from app.models.schemas import ColumnStats, CustomAnalysis
    
    for i, analysis in enumerate(analyses_to_explain):
        insight = ai_insights[i] if (isinstance(ai_insights, list) and i < len(ai_insights)) else "Insight unavailable."
        
        # Determine if this goes into standard univariate sections or new custom sections
        if analysis["type"] == "univariate" and len(analysis["columns"]) == 1:
            col = analysis["columns"][0]
            col_stats = ColumnStats(
                name=col,
                dtype=str(df[col].dtype),
                stats=analysis["statistics"],
                chart=analysis["chart"],
                ai_insight=insight
            )
            if pd.api.types.is_numeric_dtype(df[col]):
                numerical_results.append(col_stats)
            else:
                categorical_results.append(col_stats)
        else:
            # Bivariate or Multivariate or multi-column Univariate
            custom_analyses_results.append(CustomAnalysis(
                title=analysis["title"],
                type=analysis["type"],
                columns=analysis["columns"],
                plot_type=analysis["plot_type"],
                chart=analysis["chart"],
                ai_insight=insight,
                reasoning=analysis["reasoning"]
            ))
            
    # Compute correlation heatmap as standard for compatibility if not already present
    correlation_chart = None
    correlation_insight = None
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) >= 2:
        correlation_chart = visualization.correlation_heatmap(df)
        if generate_ai_insights:
            try:
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
                correlation_insight = insights.explain_correlation(top_pairs)
            except Exception as e:
                logger.error(f"Failed to generate standard correlation insight: {e}")
                correlation_insight = "Correlation heatmap generated."

    return EDAResponse(
        dataset_id="",  # filled in by router
        summary=summary,
        numerical_columns=numerical_results,
        categorical_columns=categorical_results,
        correlation=correlation_chart,
        correlation_insight=correlation_insight,
        custom_analyses=custom_analyses_results
    )

