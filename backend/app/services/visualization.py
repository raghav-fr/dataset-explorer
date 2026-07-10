import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json


def _fig_to_dict(fig) -> dict:
    return json.loads(fig.to_json())


def histogram(df: pd.DataFrame, column: str) -> dict:
    fig = px.histogram(df, x=column, marginal="box", nbins=40, title=f"Distribution of {column}")
    return _fig_to_dict(fig)


def boxplot(df: pd.DataFrame, column: str) -> dict:
    fig = px.box(df, y=column, title=f"Boxplot of {column}")
    return _fig_to_dict(fig)


def count_plot(df: pd.DataFrame, column: str, top_n: int = 15) -> dict:
    counts = df[column].value_counts().head(top_n)
    fig = px.bar(
        x=counts.index.astype(str),
        y=counts.values,
        labels={"x": column, "y": "count"},
        title=f"Top categories in {column}",
    )
    return _fig_to_dict(fig)


def pie_chart(df: pd.DataFrame, column: str, top_n: int = 8) -> dict:
    counts = df[column].value_counts().head(top_n)
    fig = px.pie(values=counts.values, names=counts.index.astype(str), title=f"{column} share")
    return _fig_to_dict(fig)


def correlation_heatmap(df: pd.DataFrame, method: str = "pearson") -> dict | None:
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        return None
    corr = numeric_df.corr(method=method)
    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.columns.tolist(),
            colorscale="RdBu",
            zmid=0,
            text=corr.round(2).values,
            texttemplate="%{text}",
        )
    )
    fig.update_layout(title=f"{method.title()} Correlation Heatmap")
    return _fig_to_dict(fig)


def missing_values_chart(df: pd.DataFrame) -> dict:
    missing_pct = (df.isna().sum() / len(df) * 100).sort_values(ascending=False)
    missing_pct = missing_pct[missing_pct > 0]
    if missing_pct.empty:
        fig = go.Figure()
        fig.update_layout(title="No missing values detected")
        return _fig_to_dict(fig)
    fig = px.bar(
        x=missing_pct.index.astype(str),
        y=missing_pct.values,
        labels={"x": "column", "y": "% missing"},
        title="Missing Values (%) by Column",
    )
    return _fig_to_dict(fig)
