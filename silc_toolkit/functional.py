"""
Functional programming utilities for SILC data processing.
Decorators, generators, and higher-order helpers.
"""
from __future__ import annotations

import csv
import functools
import logging
import time
from pathlib import Path
from typing import Generator, Iterator

logger = logging.getLogger(__name__)


# ── Decorators ───────────────────────────────────────────────────────────────

def timer(func):
    """Print elapsed time for each call."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        ms = (time.perf_counter() - t0) * 1000
        print(f"⏱️  {func.__name__}() → {ms:.2f} ms")
        return result
    return wrapper


def log_call(func):
    """Log INFO messages on entry and exit."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        n = len(args[0]) if args and hasattr(args[0], "__len__") else "?"
        logger.info("→ %s(n=%s)", func.__name__, n)
        result = func(*args, **kwargs)
        logger.info("← %s done", func.__name__)
        return result
    return wrapper


def validate_output(min_val: float, max_val: float):
    """Parametrised decorator: assert return value in [min_val, max_val]."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if not (min_val <= result <= max_val):
                raise ValueError(
                    f"{func.__name__} returned {result:.6f}, "
                    f"expected [{min_val}, {max_val}]"
                )
            return result
        return wrapper
    return decorator


def retry(max_attempts: int = 3, exceptions: tuple = (Exception,)):
    """Retry a function up to max_attempts times on specified exceptions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    logger.warning("Attempt %d/%d failed: %s", attempt, max_attempts, e)
            raise last_exc
        return wrapper
    return decorator


# ── Generators ───────────────────────────────────────────────────────────────

def stream_silc_households(
    country: str, year: int, data_dir: Path
) -> Generator[dict, None, None]:
    """Yield raw H-file rows as dicts without loading the full CSV."""
    path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}h_EUSILC.csv"
    if not path.exists():
        logger.warning("No H-file for %s %d at %s", country, year, path)
        return
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            yield row


def stream_silc_persons(
    country: str, year: int, data_dir: Path
) -> Generator[dict, None, None]:
    """Yield raw P-file rows (persons 16+) as dicts."""
    path = data_dir / f"{country}_PUF_EUSILC" / f"{country}_{year}p_EUSILC.csv"
    if not path.exists():
        logger.warning("No P-file for %s %d at %s", country, year, path)
        return
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            yield row


def stream_all_countries(
    countries: list[str], year: int, data_dir: Path
) -> Iterator[tuple[str, float]]:
    """Yield (country, equivalised_income) for every household across countries."""
    for country in countries:
        for row in stream_silc_households(country, year, data_dir):
            inc_str  = row.get("HY020", "").strip()
            size_str = row.get("HX040", "").strip()
            if not inc_str or inc_str == "NA":
                continue
            income = float(inc_str)
            size   = max(1, int(float(size_str))) if size_str and size_str != "NA" else 1
            scale  = 1.0 + 0.5 * (size - 1)
            yield (country, income / scale)


# ── Higher-order helpers ─────────────────────────────────────────────────────

def arop_rate(incomes: list[float], threshold_pct: float = 0.60) -> float:
    """At-risk-of-poverty rate: share of incomes below threshold_pct * median."""
    if not incomes:
        return 0.0
    median    = sorted(incomes)[len(incomes) // 2]
    threshold = threshold_pct * median
    return sum(1 for i in incomes if i < threshold) / len(incomes)


def make_poverty_classifier(threshold: float):
    """Return a function classifying income against an absolute threshold."""
    def classify(equivalised_income: float) -> str:
        return "at risk" if equivalised_income < threshold else "not at risk"
    return classify
