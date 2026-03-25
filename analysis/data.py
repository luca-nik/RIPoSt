"""
Data loading, preprocessing, and subtype filtering.
"""
import pandas as pd
import numpy as np
from .config import DATA_FILE, SHEET_NAME, EXCLUDE_COLS, SUBTYPE_COL, SUBTYPES


def load_raw() -> pd.DataFrame:
    """Load the raw Excel sheet."""
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode categorical columns numerically for analysis.
    Boolean columns are cast to int (0/1).
    Categorical strings are one-hot encoded.
    Returns a copy.
    """
    df = df.copy()

    # Cast booleans to int
    bool_cols = df.select_dtypes(include="bool").columns
    df[bool_cols] = df[bool_cols].astype(int)

    # Encode Genere: M=1, F=0
    df["Genere"] = (df["Genere"] == "M").astype(int)

    # Encode marital_status as one-hot (drop first to avoid collinearity)
    if "marital_status" in df.columns:
        dummies = pd.get_dummies(df["marital_status"], prefix="marital", drop_first=True)
        df = pd.concat([df.drop(columns=["marital_status"]), dummies], axis=1)

    # Encode mood diagnosis as one-hot (reference = NO)
    if "mood" in df.columns:
        dummies = pd.get_dummies(df["mood"], prefix="mood", drop_first=False)
        # Drop reference category (NO) if present
        if "mood_NO" in dummies.columns:
            dummies = dummies.drop(columns=["mood_NO"])
        df = pd.concat([df.drop(columns=["mood"]), dummies], axis=1)

    return df


def get_predictors(df: pd.DataFrame) -> list[str]:
    """Return predictor column names (all columns except excluded ones)."""
    return [c for c in df.columns if c not in EXCLUDE_COLS]


def filter_subtype(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """
    Filter dataframe by ADHD subtype.
    sample: 'full' | 'inat' | 'comb' | 'iper'
    """
    if sample not in SUBTYPES:
        raise ValueError(f"Unknown sample '{sample}'. Choose from: {list(SUBTYPES)}")
    subtype_val = SUBTYPES[sample]
    if subtype_val is None:
        return df.copy()
    return df[df[SUBTYPE_COL] == subtype_val].copy()


def prepare(sample: str) -> tuple[pd.DataFrame, list[str]]:
    """
    Full pipeline: load → preprocess → filter by subtype.
    Returns (dataframe, predictor_columns).
    """
    df_raw = load_raw()
    df = preprocess(df_raw)
    df = filter_subtype(df, sample)
    predictors = get_predictors(df)
    return df, predictors
