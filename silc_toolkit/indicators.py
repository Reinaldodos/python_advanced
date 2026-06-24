from __future__ import annotations
import math
import statistics
from typing import Optional, Sequence
import numpy as np


def median_income(incomes: Sequence[float]) -> float:
    pos = [x for x in incomes if x > 0]
    return statistics.median(pos) if pos else 0.0


def poverty_threshold(incomes: Sequence[float], threshold_pct: float = 0.60) -> float:
    return threshold_pct * median_income(incomes)


def arop_rate(
    incomes: Sequence[float],
    threshold_pct: float = 0.60,
    weights: Optional[Sequence[float]] = None,
) -> float:
    if not incomes:
        return 0.0
    thresh = poverty_threshold(incomes, threshold_pct)
    if weights is None:
        return sum(1 for i in incomes if i < thresh) / len(incomes)
    w_poor  = sum(w for i, w in zip(incomes, weights) if i < thresh)
    w_total = sum(weights)
    return w_poor / w_total if w_total > 0 else 0.0


def gini_coefficient(incomes: Sequence[float]) -> float:
    xs = sorted(x for x in incomes if x > 0)
    n  = len(xs)
    if n == 0:
        return 0.0
    total = sum(xs)
    if total == 0:
        return 0.0
    return sum(x * (2 * rank - n - 1) for rank, x in enumerate(xs, 1)) / (n * total)


def material_deprivation_rate(flags: Sequence[int], threshold: int = 3) -> float:
    if not flags:
        return 0.0
    return sum(1 for f in flags if f >= threshold) / len(flags)


def s80s20_ratio(incomes: Sequence[float]) -> float:
    xs = sorted(x for x in incomes if x > 0)
    n  = len(xs)
    if n < 5:
        return float("nan")
    q = n // 5
    return sum(xs[-q:]) / sum(xs[:q]) if sum(xs[:q]) > 0 else float("inf")


def arope_rate(
    at_risk: Sequence[bool],
    deprived: Sequence[bool],
    low_work: Sequence[bool],
) -> float:
    n = len(at_risk)
    if n == 0:
        return 0.0
    return sum(1 for a, d, w in zip(at_risk, deprived, low_work) if a or d or w) / n


def gini_numpy(incomes: np.ndarray) -> float:
    xs = np.sort(incomes[incomes > 0])
    n  = len(xs)
    if n == 0:
        return 0.0
    ranks   = np.arange(1, n + 1)
    weights = 2 * ranks - n - 1
    return float(np.dot(weights, xs) / (n * xs.sum()))


def gini_weighted(incomes: np.ndarray, weights: np.ndarray) -> float:
    mask   = incomes > 0
    xs, ws = incomes[mask], weights[mask]
    if xs.size == 0:
        return 0.0
    order   = np.argsort(xs)
    xs, ws  = xs[order], ws[order]
    cumw    = np.cumsum(ws)
    lorenz_y = np.cumsum(ws * xs) / np.dot(ws, xs)
    lorenz_x = cumw / cumw[-1]
    return float(1 - 2 * np.trapz(lorenz_y, lorenz_x))


def equivalised_income_numpy(
    disposable_income: np.ndarray,
    n_adults: np.ndarray,
    n_children: np.ndarray,
) -> np.ndarray:
    scale = 1.0 + 0.5 * (n_adults - 1) + 0.3 * n_children
    return disposable_income / np.maximum(scale, 1.0)
