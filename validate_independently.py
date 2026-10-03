"""Independent recomputation with the Python standard library only.

Does not import the case package, numpy, or pandas. Reads the frozen curve
and the generated outputs, reprices every contract, and checks prices, DV01,
scenario P&L, costs, and turnover.
"""

from __future__ import annotations

import calendar
import csv
import json
import math
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"

VALUATION = date(2023, 7, 31)
NAV = 100_000_000.0
DV01_TARGET = 50_000.0
DV01_TOLERANCE = 0.02
DV01_DUST = 1e-6
BUDGET = 1_000_000.0
ONE_SIDED = 0.0002
BP = 0.0001
NODES = (0.5, 2.0, 5.0, 10.0, 20.0, 30.0)
KR01_COLUMNS = (
    "kr01_0.5y_per_100",
    "kr01_2y_per_100",
    "kr01_5y_per_100",
    "kr01_10y_per_100",
    "kr01_20y_per_100",
    "kr01_30y_per_100",
)
# Per 100 face. The current file matches to 0; do not widen this to hide a mismatch.
KR01_BOND_TOLERANCE = 1e-12
# Dollars per bp. Face-scaled gaps on this file are about 5.7e-14. Not a whole-dollar band.
KR01_BOOK_TOLERANCE = 1e-12
IDS = ("S06M", "S02Y", "S03Y", "S05Y", "S07Y", "S10Y", "S20Y", "S30Y")
CONTRACTS = (
    ("S06M", 4.75, date(2024, 1, 31)),
    ("S02Y", 4.50, date(2025, 7, 31)),
    ("S03Y", 4.25, date(2026, 7, 31)),
    ("S05Y", 4.00, date(2028, 7, 31)),
    ("S07Y", 4.00, date(2030, 7, 31)),
    ("S10Y", 4.00, date(2033, 7, 31)),
    ("S20Y", 4.00, date(2043, 7, 31)),
    ("S30Y", 4.00, date(2053, 7, 31)),
)
SCENARIOS = (
    "parallel_plus_100bp",
    "parallel_minus_100bp",
    "twist_steepener",
    "twist_flattener",
    "hist_2023_03_08_to_2023_03_13",
    "hist_2023_07_31_to_2023_10_19",
)


def load_curves():
    table = {}
    with (DATA / "curve_parameters_2022_2023.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            table[row["Date"]] = {k: float(row[k]) for k in ("BETA0", "BETA1", "BETA2", "BETA3", "TAU1", "TAU2")}
    return table


def y_percent(n, beta):
    b0, b1, b2, b3 = beta["BETA0"], beta["BETA1"], beta["BETA2"], beta["BETA3"]
    t1, t2 = beta["TAU1"], beta["TAU2"]
    x1 = n / t1
    x2 = n / t2
    e1 = math.exp(-x1)
    e2 = math.exp(-x2)
    g1 = (1.0 - e1) / x1
    g2 = (1.0 - e2) / x2
    return b0 + b1 * g1 + b2 * (g1 - e1) + b3 * (g2 - e2)


def z_of(n, beta):
    return y_percent(n, beta) / 100.0


def add_months(day, months):
    index = day.month - 1 + months
    year = day.year + index // 12
    month = index % 12 + 1
    return date(year, month, calendar.monthrange(year, month)[1])


def cashflows(coupon, maturity):
    flows = []
    pay = add_months(VALUATION, 6)
    coupon_payment = coupon / 2.0
    while pay < maturity:
        flows.append(((pay - VALUATION).days / 365.0, coupon_payment))
        pay = add_months(pay, 6)
    if pay != maturity:
        raise RuntimeError(f"maturity off grid: {maturity} vs {pay}")
    flows.append(((pay - VALUATION).days / 365.0, coupon_payment + 100.0))
    return flows


def price(flows, zero_fn):
    total = 0.0
    for t, cf in flows:
        total += cf * math.exp(-zero_fn(t) * t)
    return total


def dv01(flows, beta):
    down = price(flows, lambda t: z_of(t, beta) - BP)
    up = price(flows, lambda t: z_of(t, beta) + BP)
    return (down - up) / 2.0


def twist_bp(t, left, right):
    if t <= 2.0:
        return left
    if t >= 10.0:
        return right
    return left + (right - left) * (t - 2.0) / 8.0


def shock_functions(curves):
    def hist(start, end):
        return lambda t: z_of(t, curves[end]) - z_of(t, curves[start])

    return {
        "parallel_plus_100bp": lambda t: 0.01,
        "parallel_minus_100bp": lambda t: -0.01,
        "twist_steepener": lambda t: twist_bp(t, -50.0, 100.0) * BP,
        "twist_flattener": lambda t: twist_bp(t, 100.0, -50.0) * BP,
        "hist_2023_03_08_to_2023_03_13": hist("2023-03-08", "2023-03-13"),
        "hist_2023_07_31_to_2023_10_19": hist("2023-07-31", "2023-10-19"),
    }


def solve_weights(d):
    target = DV01_TARGET / NAV
    w_short = (target - d["S30Y"]) / (d["S06M"] - d["S30Y"])
    current = {name: 0.0 for name in IDS}
    current["S06M"] = w_short
    current["S30Y"] = 1.0 - w_short
    fixed = {"S03Y": 0.15, "S05Y": 0.30, "S07Y": 0.20}
    used = sum(weight * d[name] for name, weight in fixed.items())
    w2 = (target - used - 0.35 * d["S10Y"]) / (d["S02Y"] - d["S10Y"])
    benchmark = {name: 0.0 for name in IDS}
    benchmark.update(fixed)
    benchmark["S02Y"] = w2
    benchmark["S10Y"] = 0.35 - w2
    w_control = (target - d["S20Y"]) / (d["S02Y"] - d["S20Y"])
    control = {name: 0.0 for name in IDS}
    control["S02Y"] = w_control
    control["S20Y"] = 1.0 - w_control
    return current, benchmark, control


def finance(current, d, buy, turnover):
    alpha = (d[buy] - d["S30Y"]) / (d["S06M"] - d["S30Y"])
    weights = {name: 0.0 for name in IDS}
    weights["S06M"] = current["S06M"] - turnover * alpha
    weights[buy] = turnover
    weights["S30Y"] = current["S30Y"] - turnover * (1.0 - alpha)
    return weights


def pnl(weights, rets):
    return sum(weights[name] * NAV * rets[name] for name in IDS)


def gross(weights, current):
    buys = 0.0
    sells = 0.0
    for name in IDS:
        delta = (weights[name] - current[name]) * NAV
        if delta > 0.0:
            buys += delta
        elif delta < 0.0:
            sells -= delta
    return buys + sells, buys, sells


def key_rate_weights(t):
    weights = [0.0] * 6
    if t <= NODES[0]:
        weights[0] = 1.0
        return weights
    if t >= NODES[-1]:
        weights[-1] = 1.0
        return weights
    for i in range(5):
        if NODES[i] <= t <= NODES[i + 1]:
            span = NODES[i + 1] - NODES[i]
            weights[i] = (NODES[i + 1] - t) / span
            weights[i + 1] = (t - NODES[i]) / span
            return weights
    raise RuntimeError(f"no key-rate bracket for {t}")


def kr01(flows, beta):
    out = []
    for key in range(6):
        down = price(flows, lambda t, key=key: z_of(t, beta) - BP * key_rate_weights(t)[key])
        up = price(flows, lambda t, key=key: z_of(t, beta) + BP * key_rate_weights(t)[key])
        out.append((down - up) / 2.0)
    return out



def bond_kr01_max_abs_gap(computed, published_instruments):
    """Max |independent KR01 - instruments.csv| over bonds and nodes, per 100 face."""
    gap = 0.0
    for name, nodes in computed.items():
        row = published_instruments[name]
        for value, column in zip(nodes, KR01_COLUMNS):
            gap = max(gap, abs(float(value) - float(row[column])))
    return gap


def bond_kr01_within_tolerance(computed, published_instruments, tolerance=KR01_BOND_TOLERANCE):
    return bond_kr01_max_abs_gap(computed, published_instruments) <= tolerance


def book_kr01_max_abs_gap(computed_by_book, published_book_rows):
    """Max |scaled KR01 - BOOK row| in dollars per bp."""
    gap = 0.0
    for book, nodes in computed_by_book.items():
        for node, value in zip(NODES, nodes):
            published = published_book_rows[book][node]
            gap = max(gap, abs(float(value) - float(published)))
    return gap


def decision_from_predicates(role, weights, dv01, relatives, turnover):
    """Same order as src/decision.py. Reference books are not executable."""
    valid = (
        len(weights) > 0
        and all(math.isfinite(value) and value >= -1e-12 for value in weights.values())
        and abs(sum(weights.values()) - 1.0) <= 1e-8
    )
    # Same dollar band as src/decision.py. DV01_DUST is numerical dust, not a wider limit.
    dv_ok = math.isfinite(dv01) and abs(dv01 - DV01_TARGET) <= DV01_TARGET * DV01_TOLERANCE + DV01_DUST
    stress_ok = len(relatives) > 0 and all(math.isfinite(value) and value >= -BUDGET - 1e-4 for value in relatives)
    routine_ok = math.isfinite(turnover) and -1e-10 <= turnover <= 0.10 + 1e-10
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
        "portfolio_valid": valid,
        "dv01_within_mandate": dv_ok,
        "stress_budget_pass": stress_ok,
        "routine_authority": routine_ok,
        "decision": decision,
    }


ROLES = {
    "current": "standing",
    "benchmark": "reference",
    "candidate_10pct_s05y": "proposed",
    "candidate_expanded_s05y": "proposed",
    "control_2y20y": "reference",
}


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    failures = []
    notes = []

    def check(name, ok, detail):
        if ok:
            notes.append(f"PASS  {name}: {detail}")
        else:
            failures.append(f"FAIL  {name}: {detail}")
            notes.append(f"FAIL  {name}: {detail}")

    curves = load_curves()
    check("usable days", len(curves) == 499, f"{len(curves)}")
    beta = curves["2023-07-31"]
    shocks = shock_functions(curves)

    built = {}
    max_price_gap = 0.0
    max_dv01_gap = 0.0
    published_instruments = {row["instrument"]: row for row in read_csv(OUT / "instruments.csv")}
    for name, coupon, maturity in CONTRACTS:
        flows = cashflows(coupon, maturity)
        dirty = price(flows, lambda t, beta=beta: z_of(t, beta))
        risk = dv01(flows, beta)
        built[name] = {"flows": flows, "dirty": dirty, "dv01": risk, "d": risk / dirty}
        published_price = float(published_instruments[name]["dirty_per_100"])
        published_dv = float(published_instruments[name]["dv01_per_100"])
        max_price_gap = max(max_price_gap, abs(dirty - published_price))
        max_dv01_gap = max(max_dv01_gap, abs(risk - published_dv))
    check("prices vs instruments.csv", max_price_gap < 1e-9, f"max abs gap {max_price_gap:.3e} per 100")
    check("DV01 vs instruments.csv", max_dv01_gap < 1e-9, f"max abs gap {max_dv01_gap:.3e} per 100")

    returns = {scenario: {} for scenario in SCENARIOS}
    max_bond_pnl_gap = 0.0
    bond_rows = read_csv(OUT / "scenario_bond_results.csv")
    published_bond = {(row["instrument"], row["scenario"]): float(row["full_reval_pnl_per_100"]) for row in bond_rows}
    for scenario in SCENARIOS:
        dz = shocks[scenario]
        for name, _coupon, _maturity in CONTRACTS:
            flows = built[name]["flows"]
            dirty = built[name]["dirty"]
            shocked = price(flows, lambda t, dz=dz, beta=beta: z_of(t, beta) + dz(t))
            bond_pnl = shocked - dirty
            returns[scenario][name] = bond_pnl / dirty
            max_bond_pnl_gap = max(max_bond_pnl_gap, abs(bond_pnl - published_bond[(name, scenario)]))
    check("bond scenario P&L", max_bond_pnl_gap < 1e-8, f"max abs gap {max_bond_pnl_gap:.3e} per 100")

    d = {name: built[name]["d"] for name in IDS}
    current, benchmark, control = solve_weights(d)
    case = json.loads((OUT / "case_results.json").read_text())
    expanded_u = case["expanded_s05y"]["turnover_with_one_point_buffer"]
    candidate_10 = finance(current, d, "S05Y", 0.10)
    expanded = finance(current, d, "S05Y", expanded_u)
    solved = {
        "current": current,
        "benchmark": benchmark,
        "candidate_10pct_s05y": candidate_10,
        "candidate_expanded_s05y": expanded,
        "control_2y20y": control,
    }
    max_weight_gap = 0.0
    for book, weights in solved.items():
        for name in IDS:
            max_weight_gap = max(max_weight_gap, abs(weights[name] - case["books"][book]["weights"][name]))
        dv = sum(weights[name] * NAV * d[name] for name in IDS)
        check(f"{book} DV01", abs(dv - DV01_TARGET) < 1e-6, f"{dv:.8f}")
        check(f"{book} weights sum to 1", abs(sum(weights.values()) - 1.0) < 1e-12, f"{sum(weights.values())}")
        check(f"{book} long only", all(weight >= -1e-12 for weight in weights.values()), "non-negative")
    check("weights vs case_results.json", max_weight_gap < 1e-10, f"max abs gap {max_weight_gap:.3e}")

    # Control must actually contain the 2y/20y weights in positions.csv.
    positions = read_csv(OUT / "positions.csv")
    control_rows = {row["instrument"]: float(row["market_value_weight"]) for row in positions if row["book"] == "control_2y20y"}
    check(
        "control weights in positions.csv",
        abs(control_rows["S02Y"] - control["S02Y"]) < 1e-10 and abs(control_rows["S20Y"] - control["S20Y"]) < 1e-10,
        f"S02Y {control_rows['S02Y']:.8f}, S20Y {control_rows['S20Y']:.8f}",
    )

    max_pnl_gap = 0.0
    max_rel_gap = 0.0
    for book, weights in solved.items():
        charge = book in ("candidate_10pct_s05y", "candidate_expanded_s05y")
        traded, _buys, _sells = gross(weights, current)
        turnover = 0.5 * traded / NAV
        cost = ONE_SIDED * traded if charge else 0.0
        published_book = case["books"][book]
        check(f"{book} turnover", abs(turnover - published_book["turnover_vs_current"]) < 1e-10, f"{turnover:.12f}")
        check(f"{book} cost", abs(cost - published_book["cost"]) < 1e-6, f"{cost:.6f}")
        for scenario in SCENARIOS:
            value = pnl(weights, returns[scenario])
            relative = value - cost - pnl(benchmark, returns[scenario])
            published = published_book["scenarios"][scenario]
            max_pnl_gap = max(max_pnl_gap, abs(value - published["pnl"]))
            max_rel_gap = max(max_rel_gap, abs(relative - published["relative_pnl_after_cost"]))
    check("portfolio scenario P&L", max_pnl_gap < 1e-4, f"max abs gap ${max_pnl_gap:.3e}")
    check("relative P&L after cost", max_rel_gap < 1e-4, f"max abs gap ${max_rel_gap:.3e}")

    just = case["expanded_s05y"]["turnover_just"]
    just_weights = finance(current, d, "S05Y", just)
    just_traded, _, _ = gross(just_weights, current)
    just_cost = ONE_SIDED * just_traded
    march = "hist_2023_03_08_to_2023_03_13"
    march_rel = pnl(just_weights, returns[march]) - just_cost - pnl(benchmark, returns[march])
    check("just-clearing March relative", abs(march_rel + BUDGET) < 1e-2, f"{march_rel:.6f}")

    max_kr_gap = 0.0
    weight_failures = 0
    kr_by_bond = {}
    for name, _coupon, _maturity in CONTRACTS:
        flows = built[name]["flows"]
        for t_cf, _cf in flows:
            weights_k = key_rate_weights(t_cf)
            if any(w < -1e-15 for w in weights_k) or abs(sum(weights_k) - 1.0) > 1e-12:
                weight_failures += 1
        nodes = kr01(flows, beta)
        kr_by_bond[name] = nodes
        max_kr_gap = max(max_kr_gap, abs(sum(nodes) - built[name]["dv01"]))
    check("key-rate weights", weight_failures == 0, f"{weight_failures} cash flows failed")
    check("KR01 sum versus DV01", max_kr_gap < 1e-6, f"max abs gap {max_kr_gap:.3e} per 100")
    kr_node_gap = bond_kr01_max_abs_gap(kr_by_bond, published_instruments)
    check(
        "KR01 nodes vs instruments.csv",
        bond_kr01_within_tolerance(kr_by_bond, published_instruments),
        f"max abs gap {kr_node_gap:.3e} per 100",
    )
    published_book_kr = {book: {} for book in solved}
    for row in read_csv(OUT / "kr01_by_bond.csv"):
        if row["instrument"] != "BOOK":
            continue
        published_book_kr[row["book"]][float(row["node_years"])] = float(row["kr01_dollars"])
    # Scale the independent per-100 KR01 by published face. Market value divided by a
    # repriced dirty turns a 1e-14 price gap into about 1e-11 dollars and is not the
    # comparison against the portfolio KR01 file.
    faces = {}
    for row in read_csv(OUT / "positions.csv"):
        faces.setdefault(row["book"], {})[row["instrument"]] = float(row["face"])
    computed_book_kr = {}
    for book in solved:
        totals = [0.0] * 6
        for name in IDS:
            face = faces[book][name]
            for i, node_kr in enumerate(kr_by_bond[name]):
                totals[i] += (face / 100.0) * node_kr
        computed_book_kr[book] = totals
    kr_book_gap = book_kr01_max_abs_gap(computed_book_kr, published_book_kr)
    check(
        "KR01 books vs kr01_by_bond.csv",
        kr_book_gap <= KR01_BOOK_TOLERANCE,
        f"max abs gap {kr_book_gap:.3e} dollars per bp",
    )

    for book, weights in solved.items():
        charge = book in ("candidate_10pct_s05y", "candidate_expanded_s05y")
        traded, _, _ = gross(weights, current)
        turnover = 0.5 * traded / NAV
        cost = ONE_SIDED * traded if charge else 0.0
        relatives = []
        for scenario in SCENARIOS:
            relatives.append(pnl(weights, returns[scenario]) - cost - pnl(benchmark, returns[scenario]))
        verdict = decision_from_predicates(ROLES[book], weights, sum(weights[name] * NAV * d[name] for name in IDS), relatives, turnover)
        published = case["books"][book]["governance"]
        same = all(verdict[key] == published[key] for key in verdict)
        check(f"{book} decision", same, f"{verdict['decision']} vs {published['decision']}")

    lines = [
        "# Independent validation",
        "",
        "This check reimplements the curve, the cash flows, DV01, key-rate DV01, the six scenarios, the five books, turnover, cost, and the decision predicates with the Python standard library. It does not import the pricing package.",
        "",
        "The independent calculation is a consistency check of the implementation. It is not a check against executable Treasury quotes.",
        "",
        f"Maximum price gap versus `instruments.csv`: {max_price_gap:.3e} per 100 face.",
        f"Maximum DV01 gap versus `instruments.csv`: {max_dv01_gap:.3e} per 100 face.",
        f"Maximum KR01 node gap versus `instruments.csv`: {kr_node_gap:.3e} per 100 face.",
        f"Maximum book KR01 gap: ${kr_book_gap:.3e} per bp.",
        f"Maximum bond scenario P&L gap: {max_bond_pnl_gap:.3e} per 100 face.",
        f"Maximum portfolio P&L gap: ${max_pnl_gap:.3e}.",
        f"Maximum relative P&L gap: ${max_rel_gap:.3e}.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {note}" for note in notes)
    lines.append("")
    if failures:
        lines.append(f"Result: FAIL ({len(failures)} checks).")
    else:
        lines.append("Result: PASS.")
    lines.append("")
    (OUT / "validation.md").write_text("\n".join(lines))
    print("\n".join(notes))
    if failures:
        print(f"\n{len(failures)} failed", file=sys.stderr)
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
