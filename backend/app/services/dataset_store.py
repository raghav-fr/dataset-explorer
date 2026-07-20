"""
dataset_store.py — Unified storage layer for the AI Dataset Explorer.

Storage Strategy (priority order):
  1. Upstash Redis  — if UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN are set.
                      DataFrames are stored as base64-encoded Parquet bytes.
                      EDA/summary caches are stored as JSON strings.
                      All keys carry a configurable TTL (default 24 h).
  2. Local FS       — falls back to settings.storage_dir / reports_dir.
                      On Vercel these point to /tmp (ephemeral but functional
                      within a single invocation / warm instance).
"""

import os
import io
import uuid
import json
import base64

import pandas as pd
from loguru import logger
from app.config import settings


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class DatasetNotFoundError(Exception):
    pass


# ---------------------------------------------------------------------------
# Redis helpers  (lazy import so the app still starts without upstash-redis)
# ---------------------------------------------------------------------------

def _redis_client():
    """Return an Upstash Redis client, or None if not configured."""
    if not settings.use_redis:
        return None
    try:
        from upstash_redis import Redis  # type: ignore
        return Redis(
            url=settings.upstash_redis_rest_url,
            token=settings.upstash_redis_rest_token,
        )
    except ImportError:
        logger.warning("upstash-redis package not installed; falling back to filesystem storage.")
        return None


def _df_key(dataset_id: str) -> str:
    return f"ds:{dataset_id}:parquet"


def _eda_key(dataset_id: str) -> str:
    return f"ds:{dataset_id}:eda"


def _summary_key(dataset_id: str) -> str:
    return f"ds:{dataset_id}:summary"


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _writable_path(path: str) -> str:
    """
    On Vercel (and any Lambda-like environment), only /tmp is writable.
    If the configured path is relative (e.g. 'app/storage/datasets'),
    remap it to /tmp/<path> so it lands in the writable temp filesystem.
    Absolute paths that already start with /tmp are returned as-is.
    """
    if os.path.isabs(path):
        return path
    # Relative path → put it under /tmp
    return os.path.join("/tmp", path)


def _ensure_dirs():
    storage = _writable_path(settings.storage_dir)
    reports = _writable_path(settings.reports_dir)
    os.makedirs(storage, exist_ok=True)
    os.makedirs(reports, exist_ok=True)
    return storage, reports


def _fs_path(dataset_id: str) -> str:
    return os.path.join(_writable_path(settings.storage_dir), f"{dataset_id}.parquet")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_dataframe(df: pd.DataFrame) -> str:
    dataset_id = uuid.uuid4().hex[:12]
    r = _redis_client()

    if r is not None:
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        r.set(_df_key(dataset_id), encoded, ex=settings.dataset_ttl_seconds)
        logger.info(f"Saved dataset {dataset_id} to Redis ({len(encoded)} bytes b64).")
    else:
        _ensure_dirs()
        path = _fs_path(dataset_id)
        df.to_parquet(path, index=False)
        logger.info(f"Saved dataset {dataset_id} to filesystem at {path}.")

    return dataset_id


def load_dataframe(dataset_id: str) -> pd.DataFrame:
    r = _redis_client()

    if r is not None:
        encoded = r.get(_df_key(dataset_id))
        if encoded is None:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found in Redis.")
        raw_bytes = base64.b64decode(encoded)
        return pd.read_parquet(io.BytesIO(raw_bytes))
    else:
        path = _fs_path(dataset_id)
        if not os.path.exists(path):
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found at {path}.")
        return pd.read_parquet(path)


def overwrite_dataframe(dataset_id: str, df: pd.DataFrame) -> None:
    r = _redis_client()

    if r is not None:
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        r.set(_df_key(dataset_id), encoded, ex=settings.dataset_ttl_seconds)
    else:
        _ensure_dirs()
        df.to_parquet(_fs_path(dataset_id), index=False)


def dataset_exists(dataset_id: str) -> bool:
    r = _redis_client()

    if r is not None:
        return r.exists(_df_key(dataset_id)) == 1
    else:
        return os.path.exists(_fs_path(dataset_id))


# ---------------------------------------------------------------------------
# EDA cache
# ---------------------------------------------------------------------------

def save_eda_cache(dataset_id: str, eda_data: dict) -> None:
    r = _redis_client()

    if r is not None:
        r.set(_eda_key(dataset_id), json.dumps(eda_data, ensure_ascii=False), ex=settings.dataset_ttl_seconds)
    else:
        _ensure_dirs()
        path = os.path.join(_writable_path(settings.reports_dir), f"{dataset_id}_eda.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(eda_data, f, ensure_ascii=False, indent=2)


def load_eda_cache(dataset_id: str) -> dict | None:
    r = _redis_client()

    if r is not None:
        raw = r.get(_eda_key(dataset_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None
    else:
        path = os.path.join(_writable_path(settings.reports_dir), f"{dataset_id}_eda.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None


# ---------------------------------------------------------------------------
# Summary cache
# ---------------------------------------------------------------------------

def save_summary_cache(dataset_id: str, summary_data: dict) -> None:
    r = _redis_client()

    if r is not None:
        r.set(_summary_key(dataset_id), json.dumps(summary_data, ensure_ascii=False), ex=settings.dataset_ttl_seconds)
    else:
        _ensure_dirs()
        path = os.path.join(_writable_path(settings.reports_dir), f"{dataset_id}_summary.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)


def load_summary_cache(dataset_id: str) -> dict | None:
    r = _redis_client()

    if r is not None:
        raw = r.get(_summary_key(dataset_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None
    else:
        path = os.path.join(_writable_path(settings.reports_dir), f"{dataset_id}_summary.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None
