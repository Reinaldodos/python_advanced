"""
CSV and pandas loaders for EU-SILC PUF data.

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

# Columns we always want from the H-file
H_COLS_MINIMAL = ["HB010", "HB020", "HB030", "HY010", "HY020", "HX040"]
# Columns from the D (register) file — household weight and region
D_COLS_MINIMAL = ["DB010", "DB020", "DB030", "DB040", "DB090"]


def load_incomes(
    country: str,
    year: int,
    data_dir: Path,
    *,
    min_income: float = 0.0,
    max_rows: Optional[int] = None,
) -> list[float]:
    """
    Load equivalised disposable incomes from the H-file.
    Returns a list of positive equivalised incomes in euros.
    """
    path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}h_EUSILC.csv"
    if not path.exists():
        raise FileNotFoundError(f"No H-file for {country} {year}: {path}")

    incomes: list[float] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            if max_rows is not None and i >= max_rows:
                break
            inc_str = row.get("HY020", "").strip()
            size_str = row.get("HX040", "").strip()
            if not inc_str or inc_str == "NA":
                continue
            income = float(inc_str)
            size = max(1, int(float(size_str))) if size_str and size_str != "NA" else 1
            equiv = income / (1.0 + 0.5 * (size - 1))
            if equiv >= min_income:
                incomes.append(equiv)
    return incomes


def load_household_df(
    country: str,
    year: int,
    data_dir: Path,
    cols: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Load the H-file for one country-year into a pandas DataFrame.
    Merges with the D-file to add weight (DB090) and region (DB040).
    """
    cols = cols or H_COLS_MINIMAL
    h_path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}h_EUSILC.csv"
    d_path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}d_EUSILC.csv"

    if not h_path.exists():
        raise FileNotFoundError(f"H-file not found: {h_path}")

    # Read H-file; keep only requested columns that exist
    df_h = pd.read_csv(h_path)
    available_h = [c for c in cols if c in df_h.columns]
    df_h = df_h[available_h].copy()

    # Optionally merge D-file for weight + region
    if d_path.exists():
        df_d = pd.read_csv(d_path, usecols=lambda c: c in D_COLS_MINIMAL)
        if "DB030" in df_d.columns and "HB030" in df_h.columns:
            df = df_h.merge(
                df_d[["DB030", "DB090", "DB040"]],
                left_on="HB030",
                right_on="DB030",
                how="left",
            ).drop(columns="DB030", errors="ignore")
        else:
            df = df_h
    else:
        df = df_h

    # Type coercion
    for col in ["HY010", "HY020"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "HX040" in df.columns:
        df["HX040"] = pd.to_numeric(df["HX040"], errors="coerce").fillna(1).astype(int)
    if "DB090" in df.columns:
        df["DB090"] = pd.to_numeric(df["DB090"], errors="coerce").fillna(1.0)

    # Derived column: equivalised income
    if "HY020" in df.columns and "HX040" in df.columns:
        df["equiv_income"] = df["HY020"] / (1.0 + 0.5 * (df["HX040"] - 1)).clip(lower=1)

    logger.info(
        "Loaded %s %d: %d households, %d columns",
        country,
        year,
        len(df),
        len(df.columns),
    )
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
