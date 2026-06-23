"""
CSV, pandas, and Parquet loaders for EU-SILC PUF data.

All functions accept a ``data_dir`` argument so they work with any copy
of the PUF, regardless of installation path.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

H_COLS_MINIMAL = ["HB010", "HB020", "HB030", "HY010", "HY020", "HX040"]
D_COLS_MINIMAL = ["DB010", "DB020", "DB030", "DB040", "DB090"]

DTYPE_H = {
    "HB010": "int16",
    "HB020": "category",
    "HB030": "int32",
    "HY010": "float32",
    "HY020": "float32",
    "HX040": "float32",
}


def load_incomes(
    country: str,
    year: int,
    data_dir: Path,
    *,
    min_income: float = 0.0,
    max_rows: Optional[int] = None,
) -> list[float]:
    """Load equivalised disposable incomes from the H-file."""
    path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}h_EUSILC.csv"
    if not path.exists():
        raise FileNotFoundError(f"No H-file for {country} {year}: {path}")
    incomes: list[float] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            if max_rows is not None and i >= max_rows:
                break
            inc_str  = row.get("HY020", "").strip()
            size_str = row.get("HX040", "").strip()
            if not inc_str or inc_str == "NA":
                continue
            income = float(inc_str)
            size   = max(1, int(float(size_str))) if size_str and size_str != "NA" else 1
            equiv  = income / (1.0 + 0.5 * (size - 1))
            if equiv >= min_income:
                incomes.append(equiv)
    return incomes


def load_household_df(
    country: str,
    year: int,
    data_dir: Path,
    cols: Optional[list[str]] = None,
) -> pd.DataFrame:
    """Load H-file for one country-year; merge with D-file for weight+region."""
    cols = cols or H_COLS_MINIMAL
    h_path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}h_EUSILC.csv"
    d_path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}d_EUSILC.csv"
    if not h_path.exists():
        raise FileNotFoundError(f"H-file not found: {h_path}")
    df_h = pd.read_csv(h_path, dtype={k: v for k, v in DTYPE_H.items()},
                       na_values=["NA", ""])
    available_h = [c for c in cols if c in df_h.columns]
    df_h = df_h[available_h].copy()
    if d_path.exists():
        df_d = pd.read_csv(d_path, usecols=lambda c: c in D_COLS_MINIMAL)
        if "DB030" in df_d.columns and "HB030" in df_h.columns:
            df = df_h.merge(
                df_d[[c for c in ["DB030", "DB090", "DB040"] if c in df_d.columns]],
                left_on="HB030", right_on="DB030", how="left",
            ).drop(columns="DB030", errors="ignore")
        else:
            df = df_h
    else:
        df = df_h
    for col in ["HY010", "HY020"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "HX040" in df.columns:
        df["HX040"] = pd.to_numeric(df["HX040"], errors="coerce").fillna(1).clip(lower=1)
    if "DB090" in df.columns:
        df["DB090"] = pd.to_numeric(df["DB090"], errors="coerce").fillna(1.0)
    if "HY020" in df.columns and "HX040" in df.columns:
        df["equiv_income"] = df["HY020"] / (1.0 + 0.5 * (df["HX040"] - 1)).clip(lower=1)
    return df


def load_multi_year(
    country: str,
    years: list[int],
    data_dir: Path,
) -> pd.DataFrame:
    """Concatenate household DataFrames across multiple years for one country."""
    frames = []
    for year in years:
        try:
            df = load_household_df(country, year, data_dir)
            df["survey_year"] = year
            frames.append(df)
        except FileNotFoundError:
            logger.warning("No H-file for %s %d — skipped", country, year)
    if not frames:
        raise ValueError(f"No data found for {country} in years {years}")
    return pd.concat(frames, ignore_index=True)


def load_parquet(
    country: str,
    parquet_dir: Path,
    columns: Optional[list[str]] = None,
) -> pd.DataFrame:
    """Load a pre-built Parquet file for one country."""
    path = parquet_dir / f"{country}_households.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No Parquet for {country}: {path}")
    return pd.read_parquet(path, columns=columns)
