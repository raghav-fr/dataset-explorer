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


def _prepare_df_for_eda(df: pd.DataFrame) -> pd.DataFrame:
    """Return a working copy of df with date columns detected, converted,
    and granularity-reduced when they contain more than 20 unique values.

    Reduction ladder:
      full datetime  → MM-YY string  (if unique > 20)
      MM-YY string   → YYYY string   (if still unique > 20)
    """
    df = df.copy()

    for col in df.columns:
        series = df[col]

        # Already datetime dtype — no conversion needed
        if pd.api.types.is_datetime64_any_dtype(series):
            dt_series = series
        elif series.dtype == object or pd.api.types.is_string_dtype(series):
            # Try to parse as datetime; accept if ≥80% of non-null values parse OK
            sample = series.dropna().astype(str)
            if sample.empty:
                continue
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() < 0.8:
                continue  # Not a date column
            # Convert the full column
            df[col] = pd.to_datetime(series, errors="coerce", format="mixed")
            dt_series = df[col]
        else:
            continue  # Numeric / bool — skip

        unique_count = int(dt_series.dropna().nunique())

        if unique_count <= 20:
            # Granularity is fine — keep as datetime
            continue

        # Step 1: reduce to MM-YY
        mm_yy = dt_series.dropna().dt.strftime("%m-%y")
        if int(mm_yy.nunique()) <= 20:
            df[col] = dt_series.dt.strftime("%m-%y")
            continue

        # Step 2: still > 20 → reduce to YYYY
        df[col] = dt_series.dt.strftime("%Y")

    return df


def run_full_eda_generator(df: pd.DataFrame, generate_ai_insights: bool = True):
    yield {"type": "progress", "message": "Analyzing dataset dimensions and computing summary statistics..."}

    # Work on a prepared copy: date columns detected, converted, and granularity-reduced
    df = _prepare_df_for_eda(df)

    summary = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
        "missing_values_total": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    # 1. Build a rich column metadata summary to send to AI
    col_metadata = []
    total_rows = len(df)
    for col in df.columns:
        series = df[col]

        # --- Determine column type ---
        if pd.api.types.is_numeric_dtype(series):
            col_type = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            col_type = "datetime"
        elif pd.api.types.is_bool_dtype(series):
            col_type = "boolean"
        else:
            col_type = "categorical"

        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))
        missing_pct = round(missing_count / total_rows * 100, 2) if total_rows > 0 else 0.0

        # High-cardinality flag (categorical only)
        is_high_cardinality = (col_type in ("categorical", "boolean")) and (unique_count > 45)

        # --- Per-type stats ---
        col_stats = None
        top_values = None

        if col_type == "numeric":
            non_null = series.dropna()
            if non_null.empty:
                col_stats = {}
            else:
                col_stats = {
                    "min": round(float(non_null.min()), 4),
                    "max": round(float(non_null.max()), 4),
                    "mean": round(float(non_null.mean()), 4),
                    "median": round(float(non_null.median()), 4),
                    "std": round(float(non_null.std()), 4),
                    "skew": round(float(non_null.skew()), 4),
                }

        elif col_type == "datetime":
            non_null = series.dropna()
            if non_null.empty:
                col_stats = {}
            else:
                col_stats = {
                    "min_date": str(non_null.min()),
                    "max_date": str(non_null.max()),
                    "date_range_days": int((non_null.max() - non_null.min()).days),
                }

        else:  # categorical / boolean / reduced-date string
            vc = series.value_counts(dropna=True)
            top_values = {str(k): int(v) for k, v in vc.head(10).items()}

        # --- Sample values (up to 5 non-null) ---
        raw_samples = series.dropna().head(5).tolist()
        sample_vals = [x.item() if hasattr(x, "item") else str(x) for x in raw_samples]

        col_metadata.append({
            "name": col,
            "type": col_type,
            "dtype": str(series.dtype),
            "missing": missing_count,
            "missing_pct": missing_pct,
            "unique": unique_count,
            "is_high_cardinality": is_high_cardinality,
            "stats": col_stats,
            "top_values": top_values,
            "sample_values": sample_vals,
        })

    df_summary = {
        "summary": summary,
        "columns": col_metadata,
    }
    
    # 2. Query AI to generate the EDA visualization plan
    planned_analyses = []
    from loguru import logger
    try:
        if generate_ai_insights:
            yield {"type": "progress", "message": "Planning optimal visualizations with AI..."}
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
        
        logger.info(f"Generating visualization {idx+1}/{len(planned_analyses)}: {title} ({p_type})...")
        yield {"type": "progress", "message": f"Generating visualization {idx+1}/{len(planned_analyses)}: {title}..."}
        
        # Verify columns exist in dataframe
        cols = [c for c in cols if c in df.columns]
        if not cols:
            continue

        # Guard: block countplot/barplot for high-cardinality columns in univariate analyses.
        # A count/bar chart with >50 categories is unreadable and provides no analytical value.
        if (
            a_type == "univariate"
            and len(cols) == 1
            and p_type in ("countplot", "barplot")
            and int(df[cols[0]].nunique(dropna=True)) > 45
        ):
            logger.warning(
                f"Skipping {p_type} for '{cols[0]}' — {int(df[cols[0]].nunique())} unique values "
                f"exceeds the 50-category readability limit."
            )
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
                    s = df.groupby(col1)[col2].value_counts().head(10)
                    contingency_table = {}
                    for k, count in s.items():
                        if isinstance(k, tuple) and len(k) == 2:
                            k1, k2 = str(k[0]), str(k[1])
                            if k1 not in contingency_table:
                                contingency_table[k1] = {}
                            contingency_table[k1][k2] = int(count)
                        else:
                            contingency_table[str(k)] = int(count)
                    stats = {"contingency_table": contingency_table}
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
        yield {"type": "progress", "message": f"Completed visualization {idx+1}/{len(planned_analyses)}: {title}"}

        
    # 4. Generate batch AI insights for the executed analyses
    ai_insights = {}
    if generate_ai_insights and analyses_to_explain:
        yield {"type": "progress", "message": f"Crafting AI business insights for all {len(analyses_to_explain)} visualizations..."}
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
        yield {"type": "progress", "message": "Computing numerical correlation heatmaps..."}
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
    final_response = EDAResponse(
        dataset_id="",  # filled in by router
        summary=summary,
        numerical_columns=numerical_results,
        categorical_columns=categorical_results,
        correlation=correlation_chart,
        correlation_insight=correlation_insight,
        custom_analyses=custom_analyses_results
    )
    yield {"type": "complete", "data": final_response.model_dump()}
