import pandas as pd


def row_to_chunk(row: pd.Series, row_index: int) -> str:
    fields = "\n".join(f"{col}: {row[col]}" for col in row.index)
    return f"Record #{row_index}\n{fields}"


def dataframe_to_row_chunks(df: pd.DataFrame, max_rows: int = 2000) -> list[str]:
    """
    Convert dataset rows into text chunks. For very large datasets, sample
    representatively (random sample + always include head/tail) to keep
    embedding volume manageable, and rely on column_summary_chunks for
    aggregate questions.
    """
    if len(df) <= max_rows:
        subset = df
    else:
        edge_size = min(200, max_rows // 4)
        head = df.head(edge_size)
        tail = df.tail(edge_size)
        remaining = max(0, max_rows - 2 * edge_size)
        # Sample from the middle, excluding rows already in head/tail
        middle = df.iloc[edge_size : max(edge_size, len(df) - edge_size)]
        sample_n = min(remaining, len(middle))
        sample = middle.sample(n=sample_n, random_state=42) if sample_n > 0 else middle.iloc[0:0]
        subset = pd.concat([head, sample, tail]).drop_duplicates()

    return [row_to_chunk(row, idx) for idx, row in subset.iterrows()]


def column_summary_chunks(df: pd.DataFrame) -> list[str]:
    chunks = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            text = (
                f"Column summary for '{col}' (numeric): "
                f"count={int(desc.get('count', 0))}, mean={round(float(series.mean()), 3) if series.notna().any() else 'NA'}, "
                f"min={desc.get('min')}, max={desc.get('max')}, "
                f"missing={int(series.isna().sum())}."
            )
        else:
            vc = series.value_counts(dropna=True).head(5)
            text = (
                f"Column summary for '{col}' (categorical): "
                f"unique_values={int(series.nunique(dropna=True))}, "
                f"top_categories={vc.to_dict()}, missing={int(series.isna().sum())}."
            )
        chunks.append(text)

    overview = (
        f"Dataset overview: {df.shape[0]} rows, {df.shape[1]} columns. "
        f"Columns: {', '.join(df.columns.astype(str))}."
    )
    chunks.append(overview)
    return chunks


def build_all_chunks(df: pd.DataFrame, max_rows: int = 2000) -> list[str]:
    return column_summary_chunks(df) + dataframe_to_row_chunks(df, max_rows=max_rows)
