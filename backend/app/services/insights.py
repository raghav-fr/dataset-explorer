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
    response_text = gemini_client.generate_text(prompt, system_instruction=SYSTEM_INSTRUCTION)
    try:
        # Robust JSON extraction
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL | re.IGNORECASE)
        if match:
            parsed = json.loads(match.group(1))
        else:
            match = re.search(r"(\{.*\})", response_text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(1))
            else:
                parsed = json.loads(response_text)
        return parsed
    except Exception as e:
        logger.error(f"Failed to parse batched EDA insights JSON: {e}. Raw response: {response_text}")
        raise ValueError(f"Failed to parse batched EDA insights: {e}")

