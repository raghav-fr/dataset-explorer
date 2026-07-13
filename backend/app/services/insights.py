from app.services import gemini_client
import json
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
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return json.loads(match.group(1))
    
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    
    return json.loads(text)


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
Analyze the following dataset summary and column metadata:
{json.dumps(df_summary, indent=2)}

Determine a set of all highly relevant visualization tasks for a thorough Exploratory Data Analysis (EDA) of this dataset.
You MUST include a balanced mix of all the column that is required:
- Univariate analyses (understanding all individual key columns numerical as well as categorical)
- Bivariate analyses (relationships between pairs of all numerical columns that can have relationship or correlation)
- Multivariate analyses (multi-variable interactions, e.g., scatter plots with hue, pairplots, heatmaps)

For each analysis task, specify:
1. "type": "univariate", "bivariate", or "multivariate"
2. "title": Descriptive title of what the chart represents (e.g. "Distribution of Age", "Salary vs Experience by Gender").
3. "columns": List of column names involved.
4. "plot_type": One of: "histplot", "boxplot", "violinplot", "kdeplot", "countplot", "pie_chart", "scatterplot", "lineplot", "barplot", "pairplot", "heatmap"
5. "parameters": Dict of additional options (e.g., {{"kde": true}}, {{"hue": "gender"}}, etc.)
6. "reasoning": A 1-2 sentence business explanation of why this specific analysis is crucial for this dataset.

You MUST respond ONLY with a JSON object in this format (do not include any additional text or explanation outside of the JSON):
{{
  "analyses": [
    {{
      "type": "univariate",
      "title": "Distribution of Age",
      "columns": ["age"],
      "plot_type": "histplot",
      "parameters": {{"kde": true}},
      "reasoning": "Examines the age profile of customers to determine the primary target demographic."
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


