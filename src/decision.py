"""One decision rule for the Python results and the workbook.

Reference books are not trade requests. A passing budget does not make them
executable. Proposed and standing books use the predicates below, in order.

Numerical dust: a weight may be as low as -1e-12 and the weight sum may miss 1
by 1e-8. Relative P&L may miss -$1,000,000 by $0.0001. Turnover may miss the
cap by 1e-10. DV01 may miss the ±2% dollar band by 1e-6 dollars per bp.
Those allowances are float noise, not a wider mandate.
"""

from __future__ import annotations

import math

DV01_TARGET = 50_000.0
DV01_TOLERANCE = 0.02
DV01_DUST = 1e-6
RELATIVE_BUDGET = 1_000_000.0
ROUTINE_TURNOVER_CAP = 0.10
WEIGHT_FLOOR = -1e-12
WEIGHT_SUM_TOLERANCE = 1e-8
BUDGET_DUST = 1e-4
TURNOVER_DUST = 1e-10

BOOK_ROLES = {
    "current": "standing",
    "benchmark": "reference",
    "candidate_10pct_s05y": "proposed",
    "candidate_expanded_s05y": "proposed",
    "control_2y20y": "reference",
}


def portfolio_valid(weights: dict) -> bool:
    """Finite weights, each >= 0, summing to 1."""
    if not weights:
        return False
    total = 0.0
    for value in weights.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(value) or value < WEIGHT_FLOOR:
            return False
        total += float(value)
    return math.isfinite(total) and abs(total - 1.0) <= WEIGHT_SUM_TOLERANCE


def dv01_within_mandate(dv01: float) -> bool:
    """True when parallel DV01 is inside ±2% of $50,000 per bp.

    The comparison is abs(dv01 - 50000) <= 50000 * 0.02 + DV01_DUST.
    DV01_DUST is numerical dust, not a wider risk limit. The economic band stays ±2%.
    """
    if isinstance(dv01, bool) or not isinstance(dv01, (int, float)):
        return False
    if not math.isfinite(dv01):
        return False
    return abs(float(dv01) - DV01_TARGET) <= DV01_TARGET * DV01_TOLERANCE + DV01_DUST


def stress_budget_pass(relative_pnls) -> bool:
    """Every named scenario is at least -$1,000,000 after that book's cost.

    A missing series is not a pass.
    """
    if relative_pnls is None:
        return False
    series = list(relative_pnls)
    if len(series) == 0:
        return False
    for value in series:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(value) or value < -RELATIVE_BUDGET - BUDGET_DUST:
            return False
    return True


def routine_authority(turnover: float, turnover_cap: float = ROUTINE_TURNOVER_CAP) -> bool:
    """Turnover at or under the cap. Zero turnover is inside the cap."""
    if isinstance(turnover, bool) or not isinstance(turnover, (int, float)):
        return False
    if isinstance(turnover_cap, bool) or not isinstance(turnover_cap, (int, float)):
        return False
    if not math.isfinite(turnover) or not math.isfinite(turnover_cap):
        return False
    if turnover < -TURNOVER_DUST:
        return False
    return turnover <= turnover_cap + TURNOVER_DUST


def decide(role: str, weights: dict, dv01: float, relative_pnls, turnover: float, turnover_cap: float = ROUTINE_TURNOVER_CAP) -> dict:
    """Return the predicates and exactly one decision.

    Reference roles are reported as decision=reference and are not called
    executable, whether or not they would pass the budget.
    """
    valid = portfolio_valid(weights)
    dv_ok = dv01_within_mandate(dv01)
    stress_ok = stress_budget_pass(relative_pnls)
    routine_ok = routine_authority(turnover, turnover_cap)
    if role == "reference":
        decision = "reference"
    elif not valid:
        decision = "invalid_portfolio"
    elif not (dv_ok and stress_ok):
        decision = "still_outside_budget"
    elif not routine_ok:
        decision = "needs_approval"
    else:
        decision = "executable_within_authority"
    return {
        "role": role,
        "portfolio_valid": valid,
        "dv01_within_mandate": dv_ok,
        "stress_budget_pass": stress_ok,
        "routine_authority": routine_ok,
        "decision": decision,
    }
