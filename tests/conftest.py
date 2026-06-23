"""
pytest configuration and shared fixtures for silc_toolkit tests.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Absolute path to the project data/ directory."""
    root = Path(__file__).parent.parent
    d = root / "data"
    if not d.exists():
        pytest.skip("data/ directory not found — skipping data-dependent tests")
    return d


@pytest.fixture(scope="session")
def lu_incomes(data_dir) -> list[float]:
    """Luxembourg 2012 equivalised incomes (loaded once per session)."""
    from silc_toolkit.loaders import load_incomes
    return load_incomes("LU", 2012, data_dir)


@pytest.fixture(scope="session")
def ie_incomes(data_dir) -> list[float]:
    """Ireland 2012 equivalised incomes."""
    from silc_toolkit.loaders import load_incomes
    return load_incomes("IE", 2012, data_dir)


# ---------------------------------------------------------------------------
# Small synthetic income lists for fast unit tests (no file I/O)
# ---------------------------------------------------------------------------

@pytest.fixture
def perfect_equality() -> list[float]:
    """50 identical incomes → Gini = 0."""
    return [20_000.0] * 50


@pytest.fixture
def perfect_inequality() -> list[float]:
    """49 zeros + 1 large income → Gini ≈ 1."""
    return [0.0] * 49 + [1_000_000.0]


@pytest.fixture
def small_wave() -> list[float]:
    """
    10 synthetic household incomes for readable expected values.
    Median = (8_000 + 10_000) / 2 = 9_000
    60% threshold = 5_400
    At-risk households: 3_000, 4_000, 5_000 → AROP = 3/10 = 0.30
    """
    return [3_000, 4_000, 5_000, 6_000, 8_000,
            10_000, 12_000, 15_000, 20_000, 30_000]
