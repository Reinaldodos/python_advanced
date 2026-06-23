"""
EU-SILC poverty and inequality indicators.

All functions take plain ``list[float]`` or numpy arrays for testability.
Weighted versions accept a parallel list of weights.
"""

from __future__ import annotations

import math
import statistics
from typing import Optional, Sequence


def median_income(incomes: Sequence[float]) -> float:
    """Median of a sequence of incomes."""
    pos = [x for x in incomes if x > 0]
    if not pos:
        return 0.0
    return statistics.median(pos)


def poverty_threshold(
    incomes: Sequence[float],
    threshold_pct: float = 0.60,
) -> float:
    """
    EU at-risk-of-poverty threshold.
    Default: 60% of median equivalised disposable income (EU definition).
    """
    return threshold_pct * median_income(incomes)


def arop_rate(
    incomes: Sequence[float],
    threshold_pct: float = 0.60,
    weights: Optional[Sequence[float]] = None,
) -> float:
    """
    At-risk-of-poverty rate (AROP).

    Parameters
    ----------
    incomes       : equivalised disposable household incomes
    threshold_pct : fraction of median (default 0.60 = EU definition)
    weights       : household design weights (DB090); if None, unweighted

    Returns
    -------
    Rate as a fraction in [0, 1]
    """
    if not incomes:
        return 0.0
    thresh = poverty_threshold(incomes, threshold_pct)
    if weights is None:
        at_risk = sum(1 for i in incomes if i < thresh)
        return at_risk / len(incomes)
    else:
        w_poor = sum(w for i, w in zip(incomes, weights) if i < thresh)
        w_total = sum(weights)
        return w_poor / w_total if w_total > 0 else 0.0


def gini_coefficient(incomes: Sequence[float]) -> float:
    """
    Gini coefficient of income inequality.
    Range: 0 (perfect equality) to 1 (maximum inequality).
    Uses the efficient sorted-rank formula.
    """
    xs = sorted(x for x in incomes if x > 0)
    n = len(xs)
    if n == 0:
        return 0.0
    total = sum(xs)
    if total == 0:
        return 0.0
    cumsum = sum(x * (2 * rank - n - 1) for rank, x in enumerate(xs, 1))
    return cumsum / (n * total)


def material_deprivation_rate(flags: Sequence[int], threshold: int = 3) -> float:
    """
    Severe material deprivation rate.
    A household is severely deprived if it is unable to afford
    at least ``threshold`` items from the standard EU-SILC list.

    Parameters
    ----------
    flags     : number of deprivation items per household (0–9)
    threshold : minimum items lacking to be classified as deprived (default 3)
    """
    if not flags:
        return 0.0
    deprived = sum(1 for f in flags if f >= threshold)
    return deprived / len(flags)


def s80s20_ratio(incomes: Sequence[float]) -> float:
    """
    Income quintile share ratio (S80/S20).
    Total income of top 20% divided by total income of bottom 20%.
    """
    xs = sorted(x for x in incomes if x > 0)
    n = len(xs)
    if n < 5:
        return float("nan")
    q = n // 5
    bottom_20 = sum(xs[:q])
    top_20 = sum(xs[-q:])
    return top_20 / bottom_20 if bottom_20 > 0 else float("inf")
