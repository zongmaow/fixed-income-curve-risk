"""Market-value weights, DV01 matching, turnover, and the candidate family.

All books are long-only, unlevered, and scaled to the same initial NAV.
Parallel DV01 is matched before transaction costs. The routine candidate
buys one belly or long bond and finances it by selling S06M and S30Y so that
pre-cost market value and parallel DV01 do not change. That financing split
is the unique solution of those two constraints.
"""

from __future__ import annotations

NAV = 100_000_000.0
DV01_TARGET = 50_000.0
RELATIVE_BUDGET = 1_000_000.0
ROUTINE_TURNOVER_CAP = 0.10
ONE_SIDED_COST_BP = 2.0
ONE_SIDED_COST = ONE_SIDED_COST_BP / 10_000.0
DISPLAY_TURNOVER_INCREMENT = 0.01
BUY_CHOICES = ("S02Y", "S03Y", "S05Y", "S07Y", "S10Y", "S20Y")
CASE_BUY = "S05Y"


def _d(instruments: dict, instrument_id: str) -> float:
    return instruments[instrument_id]["dv01_per_dollar"]


def solve_two_bond(instruments: dict, first: str, second: str) -> dict[str, float]:
    """Market-value weights on two bonds that hit NAV and the DV01 target."""
    d1 = _d(instruments, first)
    d2 = _d(instruments, second)
    target = DV01_TARGET / NAV
    weight_first = (target - d2) / (d1 - d2)
    weight_second = 1.0 - weight_first
    if weight_first < -1e-12 or weight_second < -1e-12:
        raise ValueError(f"two-bond solution left the long-only set: {first}={weight_first}, {second}={weight_second}")
    return {first: weight_first, second: weight_second}


def solve_benchmark(instruments: dict) -> dict[str, float]:
    """S03Y 15%, S05Y 30%, S07Y 20% fixed. Solve S02Y and S10Y for DV01."""
    fixed = {"S03Y": 0.15, "S05Y": 0.30, "S07Y": 0.20}
    residual_weight = 1.0 - sum(fixed.values())
    target = DV01_TARGET / NAV
    used = sum(weight * _d(instruments, name) for name, weight in fixed.items())
    d2 = _d(instruments, "S02Y")
    d10 = _d(instruments, "S10Y")
    weight_2 = (target - used - residual_weight * d10) / (d2 - d10)
    weight_10 = residual_weight - weight_2
    weights = {**fixed, "S02Y": weight_2, "S10Y": weight_10}
    if weight_2 < -1e-12 or weight_10 < -1e-12:
        raise ValueError(f"benchmark solution left the long-only set: {weights}")
    return weights


def financing_split(instruments: dict, buy: str) -> float:
    """Fraction of the purchase financed by selling S06M. The rest sells S30Y."""
    d_buy = _d(instruments, buy)
    d_short = _d(instruments, "S06M")
    d_long = _d(instruments, "S30Y")
    return (d_buy - d_long) / (d_short - d_long)


def candidate_weights(current: dict[str, float], instruments: dict, buy: str, turnover: float) -> dict[str, float]:
    """Buy `turnover` of NAV in `buy`. Turnover equals the buy weight because
    sales match the purchase one-for-one in market value.
    """
    alpha = financing_split(instruments, buy)
    weights = {
        "S06M": current["S06M"] - turnover * alpha,
        buy: turnover,
        "S30Y": current["S30Y"] - turnover * (1.0 - alpha),
    }
    return weights


def max_feasible_turnover(current: dict[str, float], instruments: dict, buy: str) -> float:
    alpha = financing_split(instruments, buy)
    limits = []
    if alpha > 1e-15:
        limits.append(current["S06M"] / alpha)
    if (1.0 - alpha) > 1e-15:
        limits.append(current["S30Y"] / (1.0 - alpha))
    if not limits:
        raise ValueError("financing split has no positive sale")
    return min(limits)


def normalize_weights(partial: dict[str, float], ids: tuple[str, ...]) -> dict[str, float]:
    return {name: float(partial.get(name, 0.0)) for name in ids}


def market_values(weights: dict[str, float]) -> dict[str, float]:
    return {name: weight * NAV for name, weight in weights.items()}


def faces(weights: dict[str, float], instruments: dict) -> dict[str, float]:
    """Face such that market value / dirty * 100."""
    out = {}
    for name, weight in weights.items():
        if weight == 0.0:
            out[name] = 0.0
        else:
            out[name] = (weight * NAV) / instruments[name]["dirty"] * 100.0
    return out


def portfolio_dv01(weights: dict[str, float], instruments: dict) -> float:
    return sum(weight * NAV * _d(instruments, name) for name, weight in weights.items() if weight)


def portfolio_convexity(weights: dict[str, float], instruments: dict) -> float:
    return sum(weight * instruments[name]["convexity"] for name, weight in weights.items() if weight)


def portfolio_kr01(weights: dict[str, float], instruments: dict) -> list[float]:
    totals = [0.0] * 6
    for name, weight in weights.items():
        if not weight:
            continue
        scale = weight * NAV / instruments[name]["dirty"]
        for i, kr in enumerate(instruments[name]["kr01_per_100"]):
            totals[i] += scale * kr
    return totals


def turnover_and_gross(weights: dict[str, float], current: dict[str, float]) -> tuple[float, float, float, float]:
    """Return turnover, gross traded dollars, buys, sells.

    Turnover = 0.5 * sum(|Δ market value|) / initial NAV.
    """
    buys = 0.0
    sells = 0.0
    for name in set(weights) | set(current):
        delta = weights.get(name, 0.0) * NAV - current.get(name, 0.0) * NAV
        if delta > 0.0:
            buys += delta
        elif delta < 0.0:
            sells += -delta
    gross = buys + sells
    turnover = 0.5 * gross / NAV
    return turnover, gross, buys, sells


def transaction_cost(gross_traded: float, one_sided_cost: float = ONE_SIDED_COST) -> float:
    """Illustrative cost: the same one-sided rate on buys and on sells."""
    return one_sided_cost * gross_traded


def candidate_stress_cushion(
    current: dict[str, float],
    instruments: dict,
    returns: dict[str, dict[str, float]],
    benchmark_pnl: dict[str, float],
    buy: str,
    turnover: float,
    one_sided_cost: float,
    scenarios: tuple[str, ...] | list[str],
    budget: float = RELATIVE_BUDGET,
) -> dict:
    """Evaluate after-cost stress P&L and minimum budget headroom for a fixed purchase size.

    Report pre-cost DV01 and convexity. The cost is charged once against P&L.
    """
    weights = candidate_weights(current, instruments, buy, turnover)
    turn, gross, buys, sells = turnover_and_gross(weights, current)
    cost = transaction_cost(gross, one_sided_cost)
    dv01 = portfolio_dv01(weights, instruments)
    convexity = portfolio_convexity(weights, instruments)
    relative = {}
    for scenario in scenarios:
        pnl = book_pnl(weights, returns[scenario])
        relative[scenario] = pnl - cost - benchmark_pnl[scenario]
    worst = min(relative, key=relative.get)
    weight_sum = sum(weights.values())
    long_only = abs(weight_sum - 1.0) <= 1e-8 and all(value >= -1e-12 for value in weights.values())
    return {
        "buy": buy,
        "turnover": turn,
        "gross_traded": gross,
        "buys": buys,
        "sells": sells,
        "cost": cost,
        "one_sided_cost": one_sided_cost,
        "dv01": dv01,
        "convexity": convexity,
        "long_only": long_only,
        "worst_scenario": worst,
        "worst_relative_pnl": relative[worst],
        "cushion_vs_budget": relative[worst] + budget,
        "relative_pnl": relative,
        "weights": weights,
    }


def scenario_return(instrument: dict, pnl_per_100: float) -> float:
    """P&L per dollar of market value."""
    return pnl_per_100 / instrument["dirty"]


def book_pnl(weights: dict[str, float], returns: dict[str, float]) -> float:
    return sum(weights.get(name, 0.0) * NAV * ret for name, ret in returns.items())


def scenario_turnover_bound(slope: float, relative_at_zero: float, budget: float = RELATIVE_BUDGET, slope_epsilon: float = 1e-8) -> dict:
    """Map one scenario's linear relative P&L to a turnover bound.

    A zero slope does not create a turnover number. If the book is already
    inside the budget, no trade is required. If it is outside, the direction
    cannot repair that scenario at any size.
    """
    record = {
        "relative_at_zero_turnover": relative_at_zero,
        "slope_dollars_per_unit_turnover": slope,
    }
    if abs(slope) <= slope_epsilon:
        record["kind"] = "flat"
        if relative_at_zero >= -budget:
            record["feasible_if"] = "already_inside"
        else:
            record["feasible_if"] = "impossible"
        return record
    record["kind"] = "lower_bound" if slope > 0.0 else "upper_bound"
    record["turnover_bound"] = (-budget - relative_at_zero) / slope
    return record


def aggregate_clearing(bounds: list[dict], max_turnover: float) -> dict:
    """Combine scenario bounds. Flat rows are not read for a turnover number."""
    lowers = []
    uppers = []
    blocked = []
    for row in bounds:
        kind = row["kind"]
        if kind == "flat":
            if "turnover_bound" in row:
                raise ValueError("a flat scenario must not carry turnover_bound")
            if row.get("feasible_if") == "impossible":
                blocked.append(row)
            elif row.get("feasible_if") != "already_inside":
                raise ValueError("flat scenario needs feasible_if already_inside or impossible")
            continue
        if kind == "lower_bound":
            lowers.append(row)
        elif kind == "upper_bound":
            uppers.append(row)
        else:
            raise ValueError(f"unknown bound kind {kind}")
    turnover_just = max([0.0] + [row["turnover_bound"] for row in lowers])
    turnover_cap = min([max_turnover] + [row["turnover_bound"] for row in uppers])
    bad_upper = any(row["turnover_bound"] < -1e-12 for row in uppers)
    feasible = (not blocked) and (not bad_upper) and turnover_just <= turnover_cap + 1e-12
    binding = None
    if lowers:
        binding = max(lowers, key=lambda row: row["turnover_bound"]).get("scenario")
    return {
        "turnover_just": turnover_just,
        "turnover_cap_from_constraints": turnover_cap,
        "feasible": feasible,
        "binding_lower_scenario": binding,
        "blocked_flat_scenarios": [row.get("scenario") for row in blocked],
    }
