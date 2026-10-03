"""Gürkaynak–Sack–Wright Svensson zero curve.

Parameters are the Fed staff fit. The continuous zero yield is in percent:

    y(n) = β0
         + β1 * (1 - exp(-n/τ1)) / (n/τ1)
         + β2 * [(1 - exp(-n/τ1)) / (n/τ1) - exp(-n/τ1)]
         + β3 * [(1 - exp(-n/τ2)) / (n/τ2) - exp(-n/τ2)]

Discounting uses the decimal rate z(n) = y(n) / 100.
Curve shocks are added to z. The six parameters are never bumped,
including on days when τ1 and τ2 nearly coincide.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

PARAM_COLUMNS = ("BETA0", "BETA1", "BETA2", "BETA3", "TAU1", "TAU2")


def svensson_zero_percent(maturity_years: float, beta: dict) -> float:
    """Continuous zero yield in percent at maturity n > 0."""
    n = float(maturity_years)
    if n <= 0.0:
        raise ValueError("Svensson maturity must be positive")
    b0 = float(beta["BETA0"])
    b1 = float(beta["BETA1"])
    b2 = float(beta["BETA2"])
    b3 = float(beta["BETA3"])
    tau1 = float(beta["TAU1"])
    tau2 = float(beta["TAU2"])
    x1 = n / tau1
    x2 = n / tau2
    exp1 = math.exp(-x1)
    exp2 = math.exp(-x2)
    g1 = (1.0 - exp1) / x1
    g2 = (1.0 - exp2) / x2
    return b0 + b1 * g1 + b2 * (g1 - exp1) + b3 * (g2 - exp2)


def zero_decimal(maturity_years: float, beta: dict) -> float:
    """Continuous zero in decimal, z = y/100."""
    return svensson_zero_percent(maturity_years, beta) / 100.0


def load_curve_parameters(path: Path | str) -> dict[str, dict]:
    """Load the frozen parameter file. Keys are ISO dates."""
    table: dict[str, dict] = {}
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in ("Date",) + PARAM_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"curve file missing columns: {missing}")
        for row in reader:
            beta = {name: float(row[name]) for name in PARAM_COLUMNS}
            table[row["Date"]] = beta
    return table


def load_published_sveny(path: Path | str) -> dict[str, dict[int, float]]:
    """Published SVENYxx, percent, keyed by date then integer maturity."""
    out: dict[str, dict[int, float]] = {}
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            levels = {}
            for maturity in range(1, 31):
                key = f"SVENY{maturity:02d}"
                raw = row[key]
                if raw in ("", "NA"):
                    continue
                levels[maturity] = float(raw)
            out[row["Date"]] = levels
    return out
