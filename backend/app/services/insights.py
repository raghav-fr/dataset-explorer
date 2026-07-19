from app.services import gemini_client
import json
import json_repair
import re
from loguru import logger

SYSTEM_INSTRUCTION = (
    "You are a senior data analyst. Explain statistics clearly and concisely "
    "for a business audience. Be specific with numbers. Avoid generic filler. "
    "Keep responses to 2-4 sentences unless asked for more."
)


def explain_numeric_column(column: str, stats: dict) -> str:
    prompt = f"""
Column: {column}
Statistics: {stats}

Explain what this distribution tells us about the data. Mention skewness/outliers
if notable, and one practical implication for analysis.
"""
    return gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)


def explain_categorical_column(column: str, top_categories: dict) -> str:
    prompt = f"""
Column: {column}
Top category frequencies: {top_categories}

Explain the distribution of categories and any imbalance worth noting.
"""
    return gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)


def explain_correlation(pairs: list[tuple[str, str, float]]) -> str:
    prompt = f"""
Strongest correlated feature pairs (feature_a, feature_b, correlation_coefficient):
{pairs}

Explain what these relationships suggest about the dataset, and flag anything
that might indicate multicollinearity or a leakage risk.
"""
    return gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)


def explain_dataset_overview(summary: dict, cleaning_report: dict) -> str:
    prompt = f"""
Dataset summary: {summary}
Cleaning report: {cleaning_report}

Write a short executive summary (4-6 sentences) describing what this dataset
contains, its overall quality, and the top 2-3 things an analyst should
investigate next.
"""
    try:
        return gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)
    except Exception as e:
        logger.error(f"Failed to generate dataset overview summary: {e}")
        return (
            "Executive summary temporarily unavailable. The dataset contains "
            f"{summary.get('columns', 0)} columns and {summary.get('rows', 0)} rows. "
            "Please check the column statistics below."
        )


def explain_eda_batch(numerical_cols: list[dict], categorical_cols: list[dict], correlation_pairs: list) -> dict:
    prompt = f"""
Analyze the following columns and correlations in a dataset.

Numerical Columns Statistics:
{json.dumps(numerical_cols, indent=2)}

Categorical Columns Frequencies:
{json.dumps(categorical_cols, indent=2)}

Strongest Correlated Feature Pairs:
{json.dumps(correlation_pairs, indent=2)}

Generate analytical insights for a business audience. For each numerical and categorical column, provide a concise explanation (2-4 sentences) describing what its distribution/frequency tells us (mention skewness, outliers, or imbalance where notable, and a practical implication). For correlations, provide an overview explanation of relationships and key risks like multicollinearity.

You MUST respond ONLY with a JSON object in the following format (do not include any additional text or explanation outside of the JSON):
{{
  "numerical": {{
    "column_name_1": "Your 2-4 sentence insight here...",
    "column_name_2": "Your 2-4 sentence insight here..."
  }},
  "categorical": {{
    "column_name_1": "Your 2-4 sentence insight here...",
    "column_name_2": "Your 2-4 sentence insight here..."
  }},
  "correlation": "Your correlation insight here or null if no correlations."
}}
"""
def _parse_json(text: str) -> dict:
    """Robustly extracts and parses JSON from text responses."""
    try:
        # First try direct parsing with json_repair
        parsed = json_repair.repair_json(text, return_objects=True)
        if isinstance(parsed, dict):
            return parsed
    except Exception as e:
        logger.warning(f"json_repair direct parse failed: {e}. Falling back to manual extraction.")

    # Fallback to extracting JSON using regex and json_repair
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            parsed = json_repair.repair_json(match.group(1), return_objects=True)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            parsed = json_repair.repair_json(match.group(1), return_objects=True)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
            
    # Try standard json loads with strict=False as absolute fallback
    if match:
        return json.loads(match.group(1), strict=False)
    return json.loads(text, strict=False)


def explain_eda_batch(numerical_cols: list[dict], categorical_cols: list[dict], correlation_pairs: list) -> dict:
    prompt = f"""
Analyze the following columns and correlations in a dataset.

Numerical Columns Statistics:
{json.dumps(numerical_cols, indent=2)}

Categorical Columns Frequencies:
{json.dumps(categorical_cols, indent=2)}

Strongest Correlated Feature Pairs:
{json.dumps(correlation_pairs, indent=2)}

Generate analytical insights for a business audience. For each numerical and categorical column, provide a concise explanation (2-4 sentences) describing what its distribution/frequency tells us (mention skewness, outliers, or imbalance where notable, and a practical implication). For correlations, provide an overview explanation of relationships and key risks like multicollinearity.

You MUST respond ONLY with a JSON object in the following format (do not include any additional text or explanation outside of the JSON):
{{
  "numerical": {{
    "column_name_1": "Your 2-4 sentence insight here...",
    "column_name_2": "Your 2-4 sentence insight here..."
  }},
  "categorical": {{
    "column_name_1": "Your 2-4 sentence insight here...",
    "column_name_2": "Your 2-4 sentence insight here..."
  }},
  "correlation": "Your correlation insight here or null if no correlations."
}}
"""
    response_text = gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)
    try:
        return _parse_json(response_text)
    except Exception as e:
        logger.error(f"Failed to parse batched EDA insights JSON: {e}. Raw response: {response_text}")
        raise ValueError(f"Failed to parse batched EDA insights: {e}")


def plan_eda_analyses(df_summary: dict) -> dict:
    """Queries Gemini to determine which columns to examine and which plot types to use."""
    prompt = f"""
You are a senior data analyst planning a thorough Exploratory Data Analysis (EDA).
Below is the complete dataset metadata. Each column entry includes:
  - name, type (numeric/categorical/datetime/boolean), dtype (raw pandas dtype)
  - missing: count of null values, missing_pct: percentage missing
  - unique: number of unique values
  - is_high_cardinality: true if categorical/boolean with unique > 20
  - stats: numeric stats (min, max, mean, median, std, skew) OR datetime range (min_date, max_date, date_range_days)
  - top_values: top-10 value counts for categorical/boolean columns (null for numeric/datetime)
  - sample_values: up to 5 representative non-null values

Dataset metadata:
{json.dumps(df_summary, indent=2)}

---
PLANNING RULES — follow these strictly:

1. QUANTITY: Generate as many visualizations as genuinely needed to cover the dataset thoroughly.
   Every column must appear in at least one univariate chart. Every meaningful column pair should appear in a bivariate chart.

2. HIGH-CARDINALITY CATEGORICAL (is_high_cardinality = true OR unique > 45):
   - DO NOT plan a "countplot" or "barplot" univariate chart for these columns.
   - These produce unreadable charts with too many bars. Skip univariate entirely for such columns
     OR plan a "histplot" of the value-count frequency distribution if it adds value.
   - For bivariate involving high-cardinality categoricals, use "boxplot", "violinplot", or "scatterplot" (not barplot/countplot).

3. LOW-CARDINALITY CATEGORICAL (unique <= 45, is_high_cardinality = false):
   - "countplot" or "barplot" is appropriate. "pie_chart" is good for <= 8 unique values.

4. DATETIME COLUMNS:
   - Do NOT plan a "countplot" or "barplot" for datetime columns.
   - Plan a time-series trend: use "histplot" (with kde=false) or "barplot" only if the column has been
     reduced to MM-YY or YYYY string format with <= 20 unique values.
   - For raw datetime, use "kdeplot" or group-based "barplot" on aggregated periods.

5. NUMERIC COLUMNS:
   - "histplot" (with kde=true) for distribution.
   - "boxplot" or "violinplot" for outlier inspection.
   - Use stats (skew, std, min/max) to decide: high skew → log-scale or boxplot is more informative.

6. BIVARIATE:
   - numeric vs numeric → "scatterplot" (add regression line via parameters if correlated).
   - numeric vs low-cardinality categorical → "boxplot" or "violinplot".
   - numeric vs high-cardinality categorical → skip or use "scatterplot".
   - datetime vs numeric → line plot / trend (use "barplot" only if date is aggregated to <= 20 periods).

7. MULTIVARIATE:
   - Use "heatmap" for correlation matrix of all numeric columns.
   - Use "pairplot" for numeric columns when there are 3–6 numeric columns.
   - Use "scatterplot" with hue for 2 numeric + 1 low-cardinality categorical.

8. REASONING: Every planned chart must include a non-trivial "reasoning" (1-2 sentences) that references
   actual column details (e.g., skew value, unique count, missing_pct) to justify why this specific chart
   is valuable for this dataset.

---
For each analysis task, specify:
1. "type": "univariate", "bivariate", or "multivariate"
2. "title": Descriptive title (e.g. "Distribution of Age", "Salary vs Experience by Gender")
3. "columns": List of column names involved
4. "plot_type": One of: "histplot", "boxplot", "violinplot", "kdeplot", "countplot", "pie_chart", "scatterplot", "barplot", "pairplot", "heatmap"
5. "parameters": Dict of additional options (e.g., {{"kde": true}}, {{"hue": "gender"}})
6. "reasoning": 1-2 sentence justification referencing actual data characteristics

You MUST respond ONLY with a JSON object in this exact format (no extra text outside JSON):
{{
  "analyses": [
    {{
      "type": "univariate",
      "title": "Distribution of Age",
      "columns": ["age"],
      "plot_type": "histplot",
      "parameters": {{"kde": true}},
      "reasoning": "Age has a skew of 1.2 indicating right-skew; a histogram with KDE reveals the concentration of younger customers."
    }},
    ...
  ]
}}
"""
    response_text = gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)
    try:
        return _parse_json(response_text)
    except Exception as e:
        logger.error(f"Failed to parse planned EDA JSON: {e}. Raw response: {response_text}")
        raise ValueError(f"Failed to parse planned EDA JSON: {e}")


def explain_custom_analyses_batch(analyses_list: list) -> dict:
    """Queries Gemini to generate analytical business insights for a list of executed custom analyses."""
    prompt = f"""
We have performed several analyses and generated charts for a dataset.
For each analysis, review its details, reasoning, and summary statistics, and provide a concise business insight (2-4 sentences) explaining what the chart/statistics reveal.

Analyses and statistics:
{json.dumps(analyses_list, indent=2)}

You MUST respond ONLY with a JSON object containing a list of insights, in the exact same order as the input list (do not include any additional text or explanation outside of the JSON):
{{
  "insights": [
    "Insight for analysis 1...",
    "Insight for analysis 2..."
  ]
}}
"""
    response_text = gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)
    try:
        return _parse_json(response_text)
    except Exception as e:
        logger.error(f"Failed to parse custom analyses insights JSON: {e}. Raw response: {response_text}")
        raise ValueError(f"Failed to parse custom analyses insights: {e}")


