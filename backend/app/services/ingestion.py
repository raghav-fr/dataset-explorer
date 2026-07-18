import io
import chardet
import pandas as pd
from fastapi import UploadFile, HTTPException


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}


def _detect_encoding(raw: bytes) -> str:
    result = chardet.detect(raw[:200_000])
    return result.get("encoding") or "utf-8"


def read_uploaded_file(file: UploadFile, raw: bytes) -> pd.DataFrame:
    filename = file.filename or "uploaded"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    try:
        if ext == ".csv":
            encoding = _detect_encoding(raw)
            # Try to sniff delimiter; fall back to comma
            sample = raw[:5000].decode(encoding, errors="ignore")
            delimiter = ","
            for cand in [",", ";", "\t", "|"]:
                if sample.count(cand) > sample.count(delimiter):
                    delimiter = cand
            df = pd.read_csv(
                io.BytesIO(raw), encoding=encoding, sep=delimiter, engine="python"
            )
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(raw))
        elif ext == ".json":
            # Try standard JSON first; if it has trailing data (NDJSON/JSON Lines),
            # fall back to lines=True mode.
            try:
                df = pd.read_json(io.BytesIO(raw))
            except ValueError:
                df = pd.read_json(io.BytesIO(raw), lines=True)
        elif ext == ".parquet":
            df = pd.read_parquet(io.BytesIO(raw))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    if df.empty or df.shape[1] == 0:
        raise HTTPException(status_code=400, detail="Uploaded dataset is empty")

    return df
