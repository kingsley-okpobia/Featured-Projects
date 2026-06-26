"""
file_parser.py
Handles CSV and JSON file parsing into a pandas DataFrame.
Returns (df, file_type) or raises ValueError with a user-facing message.
"""
import json
import pandas as pd


MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def parse_upload(uploaded) -> tuple[pd.DataFrame, str]:
    """
    Parse a Streamlit UploadedFile object.

    Returns:
        (df, file_type)  where file_type is "CSV" or "JSON"

    Raises:
        ValueError with a user-facing message on any error.
    """
    if uploaded.size > MAX_FILE_SIZE:
        raise ValueError("File too large. Maximum supported size is 50 MB.")

    name = uploaded.name.lower()
    if not (name.endswith(".csv") or name.endswith(".json")):
        raise ValueError(
            "Unsupported format. Please upload a .csv or .json file."
        )

    uploaded.seek(0)

    try:
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded)
            ftype = "CSV"
        else:
            raw = json.load(uploaded)
            if isinstance(raw, list):
                df = pd.json_normalize(raw)
            else:
                df = pd.json_normalize([raw])
            ftype = "JSON"
    except Exception as exc:
        raise ValueError(f"Could not read file: {exc}") from exc

    if df.empty:
        raise ValueError(
            "No data found in this file. Please check the file and try again."
        )

    return df, ftype