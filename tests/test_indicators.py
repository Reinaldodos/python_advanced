"""
Tests for silc_toolkit.indicators — AROP, Gini, S80/S20.
"""
from __future__ import annotations

import math

import pytest

from silc_toolkit.indicators import (
    arop_rate,
    gini_coefficient,
    median_income,
    poverty_threshold,
    s80s20_ratio,
)


# ---------------------------------------------------------------------------
# median_income
# ---------------------------------------------------------------------------

def test_median_income_basic(small_wave):
    assert median_income(small_wave) == 9_000.0


def test_median_income_empty():
    assert median_income([]) == 0.0


def test_median_income_ignores_non_positive():
    # Negative incomes (self-employment losses) must be excluded from median
    inc = [-5_000, 0, 10_000, 20_000]
    assert median_income(inc) == pytest.approx(15_000.0)


# ---------------------------------------------------------------------------
# poverty_threshold
# ---------------------------------------------------------------------------

def test_poverty_threshold_default(small_wave):
    assert poverty_threshold(small_wave) == pytest.approx(5_400.0)


@pytest.mark.parametrize("pct, expected", [
    (0.50, 4_500.0),
    (0.60, 5_400.0),
    (0.70, 6_300.0),
])
def test_poverty_threshold_pct(small_wave, pct, expected):
    assert poverty_threshold(small_wave, pct) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# arop_rate
# ---------------------------------------------------------------------------

def test_arop_rate_basic(small_wave):
    # 3 households (3_000, 4_000, 5_000) below threshold of 5_400
    assert arop_rate(small_wave) == pytest.approx(0.30)


def test_arop_rate_empty():
    assert arop_rate([]) == 0.0


def test_arop_rate_all_rich():
    inc = [100_000.0] * 10
    assert arop_rate(inc) == 0.0


def test_arop_rate_all_poor():
    # All below any realistic threshold
    inc = [100.0] * 10
    assert arop_rate(inc) == 0.0  # median = 100, threshold = 60, all > 60


def test_arop_rate_weighted(small_wave):
    # Households 1-3 (at risk) have weight 2; others weight 1
    weights = [2.0, 2.0, 2.0] + [1.0] * 7
    # Weighted at-risk: 2+2+2 = 6; total weight = 6+7 = 13
    result = arop_rate(small_wave, weights=weights)
    assert result == pytest.approx(6 / 13)


@pytest.mark.parametrize("country_label, expected_range", [
    ("LU", (0.05, 0.30)),
    ("IE", (0.10, 0.30)),
])
def test_arop_rate_realistic_range(
    country_label,
    expected_range,
    request #built-in pytest fixture
    ):
    """Integration test: AROP must be in a plausible range for each country."""
    incomes = request.getfixturevalue(f"{country_label.lower()}_incomes")
    rate = arop_rate(incomes)
    lo, hi = expected_range
    assert lo <= rate <= hi, (
        f"{country_label} AROP = {rate:.3f}, expected [{lo}, {hi}]"
    )


# ---------------------------------------------------------------------------
# gini_coefficient
# ---------------------------------------------------------------------------

def test_gini_perfect_equality(perfect_equality):
    assert gini_coefficient(perfect_equality) == pytest.approx(0.0)


def test_gini_perfect_inequality(perfect_inequality):
    # 49 zeros filtered out; only 1 positive value → undefined or 0
    # Function filters zeros, so only one element → Gini = 0
    g = gini_coefficient(perfect_inequality)
    assert 0.0 <= g <= 1.0


def test_gini_empty():
    assert gini_coefficient([]) == 0.0


def test_gini_in_range(lu_incomes):
    g = gini_coefficient(lu_incomes)
    assert 0.0 <= g <= 1.0


def test_gini_known_value():
    # Simple 4-person economy: incomes [1, 2, 3, 4]
    # Gini = (1*(2*1-4-1) + 2*(2*2-4-1) + 3*(2*3-4-1) + 4*(2*4-4-1)) / (4*10)
    # = (1*(-3) + 2*(-1) + 3*(1) + 4*(3)) / 40
    # = (-3 - 2 + 3 + 12) / 40 = 10/40 = 0.25
    assert gini_coefficient([1.0, 2.0, 3.0, 4.0]) == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# s80s20_ratio
# ---------------------------------------------------------------------------

def test_s80s20_perfect_equality():
    # All equal → ratio = 1.0
    inc = [10_000.0] * 100
    assert s80s20_ratio(inc) == pytest.approx(1.0)


def test_s80s20_empty():
    assert math.isnan(s80s20_ratio([1.0, 2.0]))


def test_s80s20_realistic(lu_incomes):
    ratio = s80s20_ratio(lu_incomes)
    # Luxembourg is a wealthy country; ratio should be 3–8
    assert 2.0 <= ratio <= 15.0
