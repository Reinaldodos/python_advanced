from __future__ import annotations

from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from silc_toolkit.indicators import arop_rate, gini_coefficient, s80s20_ratio

# ── Create the MCP application ───────────────────────────────────────────────
mcp = FastMCP(
    name="SILC Statistics Server",
    instructions=(
        "You have access to EU-SILC Public Use File microdata for 20+ EU countries "
        "(2004-2013). Use these tools to answer questions about poverty, inequality, "
        "and living conditions. All data is synthetic — safe for education."
    ),
)

# Lazy-load data directory (set by the caller or use default)
_DATA_DIR: Path | None = None


def _get_data_dir() -> Path:
    global _DATA_DIR
    if _DATA_DIR is None:
        # Walk up from this file to find the project root
        here = Path(__file__).resolve().parent
        for candidate in [here, *here.parents]:
            if (candidate / "pyproject.toml").exists():
                _DATA_DIR = candidate / "data"
                return _DATA_DIR
        raise FileNotFoundError("Cannot locate data/ directory")
    return _DATA_DIR


_COUNTRY_NAMES: dict[str, str] = {
    "austria": "AT", "belgium": "BE", "bulgaria": "BG", "cyprus": "CY",
    "czechia": "CZ", "czech republic": "CZ", "germany": "DE", "denmark": "DK",
    "estonia": "EE", "greece": "EL", "hellas": "EL", "spain": "ES",
    "finland": "FI", "france": "FR", "croatia": "HR", "hungary": "HU",
    "ireland": "IE", "italy": "IT", "lithuania": "LT", "luxembourg": "LU",
    "latvia": "LV", "malta": "MT", "netherlands": "NL", "holland": "NL",
    "romania": "RO", "sweden": "SE", "slovenia": "SI", "slovakia": "SK",
    "united kingdom": "UK", "uk": "UK",
}


def _resolve_country(country: str) -> str:
    """Resolve a full country name or ISO code to the 2-letter ISO code."""
    return _COUNTRY_NAMES.get(country.strip().lower(), country.strip().upper())


def _load(country: str, year: int) -> list[float]:
    from silc_toolkit.loaders import load_incomes
    return load_incomes(_resolve_country(country), year, _get_data_dir())


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_arop(
    country: Annotated[str, "ISO 2-letter country code or full name (e.g. 'LU', 'BE', 'Belgium', 'Spain')"],
    year:    Annotated[int, "Survey year 2004-2013"],
    threshold_pct: Annotated[float, "Threshold as fraction of median (default 0.60)"] = 0.60,
) -> dict:
    "Compute the at-risk-of-poverty rate for a country and year."
    iso = _resolve_country(country)
    try:
        incomes = _load(country, year)
        if not incomes:
            return {"error": f"No data for {iso} {year}"}
        rate = arop_rate(incomes, threshold_pct=threshold_pct)
        median = sorted(incomes)[len(incomes) // 2]
        return {
            "country":    iso,
            "year":       year,
            "arop_rate":  round(rate, 4),
            "arop_pct":   round(rate * 100, 1),
            "n_households": len(incomes),
            "median_income": round(median, 0),
            "threshold":  round(median * threshold_pct, 0),
        }
    except FileNotFoundError:
        return {"error": f"No PUF data for country {iso!r}. "
                "Available: AT BE BG CY DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL RO SE SI SK"}


@mcp.tool()
def get_gini(
    country: Annotated[str, "ISO 2-letter country code or full name (e.g. 'LU', 'Luxembourg')"],
    year:    Annotated[int, "Survey year 2004-2013"],
) -> dict:
    "Compute the Gini coefficient of income inequality for a country and year."
    iso = _resolve_country(country)
    try:
        incomes = _load(country, year)
        if not incomes:
            return {"error": f"No data for {iso} {year}"}
        g = gini_coefficient(incomes)
        s = s80s20_ratio(incomes)
        return {
            "country": iso,
            "year":    year,
            "gini":    round(g, 4),
            "s80s20":  round(s, 2),
            "interpretation": (
                "low inequality (Gini < 0.28)" if g < 0.28 else
                "moderate inequality (Gini 0.28-0.35)" if g < 0.35 else
                "high inequality (Gini > 0.35)"
            ),
        }
    except FileNotFoundError:
        return {"error": f"No PUF data for {iso!r}"}


@mcp.tool()
def compare_countries(
    countries: Annotated[list[str], "List of country codes or full names to compare (e.g. ['BE', 'Belgium', 'ES'])"],
    year:      Annotated[int, "Survey year 2004-2013"],
) -> dict:
    "Compare AROP rate and Gini across multiple EU countries for a given year."
    results = []
    for country in countries:
        iso = _resolve_country(country)
        try:
            incomes = _load(country, year)
            if incomes:
                results.append({
                    "country":  iso,
                    "arop_pct": round(arop_rate(incomes) * 100, 1),
                    "gini":     round(gini_coefficient(incomes), 4),
                    "s80s20":   round(s80s20_ratio(incomes), 2),
                    "n_hh":     len(incomes),
                })
        except FileNotFoundError:
            results.append({"country": iso, "error": "No data"})

    results.sort(key=lambda x: x.get("arop_pct", 999))
    return {"year": year, "countries": results}


@mcp.tool()
def get_trend(
    country: Annotated[str, "ISO 2-letter country code or full name (e.g. 'LU', 'Luxembourg')"],
    start_year: Annotated[int, "First year (2004-2012)"] = 2008,
    end_year:   Annotated[int, "Last year (2005-2013)"] = 2013,
) -> dict:
    "Get AROP trend for a country across multiple years."
    iso = _resolve_country(country)
    trend = []
    for year in range(start_year, end_year + 1):
        try:
            incomes = _load(country, year)
            if incomes:
                trend.append({"year": year, "arop_pct": round(arop_rate(incomes) * 100, 1)})
        except FileNotFoundError:
            pass
    if not trend:
        return {"error": f"No data for {iso} in {start_year}-{end_year}"}

    arop_values = [t["arop_pct"] for t in trend]
    change = arop_values[-1] - arop_values[0]
    return {
        "country": iso,
        "trend":   trend,
        "change_pp": round(change, 1),
        "direction": "improving" if change < 0 else "worsening" if change > 0 else "stable",
    }


if __name__ == "__main__":
    # Run as stdio MCP server: python -m silc_toolkit.mcp_server
    mcp.run(transport="stdio")
