"""
debug_demo.py — a small script to step through in the VS Code Python Debugger.

Suggested breakpoints (click the gutter):
  • Line with  thresh = poverty_threshold(incomes)   inside summarise()
  • Line with  flagged.append(r["label"])             inside flag_high_poverty()
"""
from silc_toolkit.indicators import arop_rate, gini_coefficient, poverty_threshold


def summarise(label: str, incomes: list[float]) -> dict:
    thresh = poverty_threshold(incomes)          # ← breakpoint here
    rate   = arop_rate(incomes)
    gini   = gini_coefficient(incomes)
    return {"label": label, "arop": rate, "gini": gini, "n": len(incomes), "thresh": thresh}


def flag_high_poverty(results: list[dict], threshold: float = 0.20) -> list[str]:
    """Return labels where AROP exceeds the threshold."""
    flagged = []
    for r in results:
        if r["arop"] > threshold:
            flagged.append(r["label"])           # ← breakpoint here
    return flagged


if __name__ == "__main__":
    waves = {
        "Wave A": [3_000,  5_000,  8_000, 12_000, 20_000] * 20,
        "Wave B": [8_000, 10_000, 14_000, 18_000, 25_000] * 20,
        "Wave C": [2_000,  3_000,  4_000,  6_000,  9_000] * 20,
    }

    results = [summarise(label, inc) for label, inc in waves.items()]

    for r in results:
        print(f"{r['label']}: AROP={r['arop']:.1%}  Gini={r['gini']:.4f}  threshold=€{r['thresh']:,.0f}")

    high = flag_high_poverty(results)
    print(f"\nWaves above 20% AROP threshold: {high or 'none'}")
