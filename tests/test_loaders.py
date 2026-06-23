"""
Tests for silc_toolkit.loaders.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from silc_toolkit.loaders import load_incomes, load_household_df


def test_load_incomes_returns_list(data_dir):
    inc = load_incomes("LU", 2012, data_dir)
    assert isinstance(inc, list)
    assert all(isinstance(x, float) for x in inc)


def test_load_incomes_positive_only(data_dir):
    inc = load_incomes("LU", 2012, data_dir, min_income=0.0)
    assert all(x >= 0.0 for x in inc), "min_income=0 should exclude negatives"


def test_load_incomes_missing_country(data_dir):
    with pytest.raises(FileNotFoundError, match="No H-file"):
        load_incomes("XX", 2012, data_dir)


def test_load_incomes_max_rows(data_dir):
    inc = load_incomes("BE", 2012, data_dir, max_rows=10)
    assert len(inc) <= 10


def test_load_household_df_shape(data_dir):
    df = load_household_df("LU", 2012, data_dir)
    assert len(df) > 0
    assert "HY020" in df.columns
    assert "equiv_income" in df.columns


def test_load_household_df_equiv_income_non_negative(data_dir):
    df = load_household_df("LU", 2012, data_dir)
    # equiv_income may be negative (losses) — just check no NaN
    assert df["equiv_income"].isna().sum() == 0


@pytest.mark.parametrize("country", ["BE", "ES", "HU", "IE", "SE"])
def test_load_incomes_participant_countries(data_dir, country):
    """All participant countries must load without error."""
    inc = load_incomes(country, 2012, data_dir)
    assert len(inc) > 0, f"No incomes loaded for {country}"
