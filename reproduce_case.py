"""Rebuild the case outputs from the frozen GSW parameters. No network."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from src.bonds import (
    INSTRUMENT_IDS,
    KEY_RATE_NODES,
    build_instruments,
    cf_first_order_pnl_per_100,
    full_reval_pnl_per_100,
    kr01_approx_pnl_per_100,
)
from src.curve import load_curve_parameters, load_published_sveny, svensson_zero_percent
from src.decision import BOOK_ROLES, decide
from src.portfolio import (
    DISPLAY_TURNOVER_INCREMENT,
    aggregate_clearing,
    BUY_CHOICES,
    CASE_BUY,
    DV01_TARGET,
    NAV,
    ONE_SIDED_COST,
    ONE_SIDED_COST_BP,
    RELATIVE_BUDGET,
    ROUTINE_TURNOVER_CAP,
    book_pnl,
    candidate_weights,
    faces,
    financing_split,
    market_values,
    max_feasible_turnover,
    normalize_weights,
    portfolio_convexity,
    portfolio_dv01,
    portfolio_kr01,
    scenario_return,
    scenario_turnover_bound,
    solve_benchmark,
    solve_two_bond,
    transaction_cost,
    turnover_and_gross,
)
from src.scenarios import SCENARIO_ORDER, build_scenarios
from src.source_gate import assert_sveny_gap, sveny_gaps_bp, verify_or_accept
from src.workbook import build_workbook, cache_workbook_values

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Rebuild the case from the frozen GSW parameters.")
    parser.add_argument(
        "--accept-new-source",
        action="store_true",
        help="Rewrite the manifest hashes after an intentional data replacement. A normal run will not.",
    )
    return parser.parse_args(argv)


def scenario_tables(instruments: dict, beta: dict, scenarios: dict):
    pnl = {name: {} for name in INSTRUMENT_IDS}
    returns = {scenario: {} for scenario in SCENARIO_ORDER}
    shocked = {name: {} for name in INSTRUMENT_IDS}
    approx_kr = {name: {} for name in INSTRUMENT_IDS}
    approx_cf = {name: {} for name in INSTRUMENT_IDS}
    for scenario in SCENARIO_ORDER:
        spec = scenarios[scenario]
        for name in INSTRUMENT_IDS:
            inst = instruments[name]
            full = full_reval_pnl_per_100(inst, beta, spec["dz"])
            kr = kr01_approx_pnl_per_100(inst, spec["node_shock_bp"])
            cf = cf_first_order_pnl_per_100(inst, spec["dz"])
            pnl[name][scenario] = full
            returns[scenario][name] = scenario_return(inst, full)
            shocked[name][scenario] = inst["dirty"] + full
            approx_kr[name][scenario] = kr
            approx_cf[name][scenario] = cf
    return pnl, returns, shocked, approx_kr, approx_cf


def clearing_analysis(
    current,
    benchmark,
    instruments,
    returns,
    buy: str,
    budget: float = RELATIVE_BUDGET,
    one_sided_cost: float = ONE_SIDED_COST,
) -> dict:
    """Same six-name search. `budget` and `one_sided_cost` default to the case."""
    alpha = financing_split(instruments, buy)
    umax = max_feasible_turnover(current, instruments, buy)
    bounds = []
    for scenario in SCENARIO_ORDER:
        ret = returns[scenario]
        trade = ret[buy] - alpha * ret["S06M"] - (1.0 - alpha) * ret["S30Y"]
        slope = NAV * (trade - 2.0 * one_sided_cost)
        rel0 = book_pnl(current, ret) - book_pnl(benchmark, ret)
        record = scenario_turnover_bound(slope, rel0, budget=budget)
        record["scenario"] = scenario
        bounds.append(record)
    summary = aggregate_clearing(bounds, umax)
    summary.update(
        {
            "buy": buy,
            "s06m_financing_fraction": alpha,
            "max_turnover_long_only": umax,
            "bounds": bounds,
        }
    )
    return summary


def lowest_clearing_buy(
    current,
    benchmark,
    instruments,
    returns,
    budget: float = RELATIVE_BUDGET,
    one_sided_cost: float = ONE_SIDED_COST,
) -> dict:
    """Return the minimum-turnover feasible direction among BUY_CHOICES
    under the case's six scenarios, supplied budget and cost rate.
    """
    family = [
        clearing_analysis(
            current,
            benchmark,
            instruments,
            returns,
            buy,
            budget=budget,
            one_sided_cost=one_sided_cost,
        )
        for buy in BUY_CHOICES
    ]
    feasible = [row for row in family if row["feasible"]]
    if not feasible:
        return {"feasible": False, "family": family}
    best = min(feasible, key=lambda row: row["turnover_just"])
    return {
        "feasible": True,
        "buy": best["buy"],
        "turnover_just": best["turnover_just"],
        "binding_lower_scenario": best["binding_lower_scenario"],
        "family": family,
    }


def book_payload(name, weights, instruments, returns, scenarios, current_weights, charge_cost: bool) -> dict:
    weights = normalize_weights(weights, INSTRUMENT_IDS)
    turnover, gross, buys, sells = turnover_and_gross(weights, current_weights)
    cost = transaction_cost(gross) if charge_cost else 0.0
    dv01 = portfolio_dv01(weights, instruments)
    kr = portfolio_kr01(weights, instruments)
    scenario_rows = {}
    for scenario in SCENARIO_ORDER:
        pnl = book_pnl(weights, returns[scenario])
        scenario_rows[scenario] = {
            "pnl": pnl,
            "cost": cost,
            "pnl_after_cost": pnl - cost,
            "node_shock_bp": scenarios[scenario]["node_shock_bp"],
        }
    # benchmark pnl filled by caller
    return {
        "name": name,
        "weights": weights,
        "market_value": market_values(weights),
        "face": faces(weights, instruments),
        "dv01": dv01,
        "convexity": portfolio_convexity(weights, instruments),
        "kr01": {str(node): value for node, value in zip(KEY_RATE_NODES, kr)},
        "kr01_sum": sum(kr),
        "turnover_vs_current": turnover,
        "gross_traded_vs_current": gross,
        "buys_vs_current": buys,
        "sells_vs_current": sells,
        "cost": cost,
        "charge_cost": charge_cost,
        "scenarios_partial": scenario_rows,
    }


def attach_relative(books: dict) -> None:
    benchmark_pnl = {
        scenario: books["benchmark"]["scenarios_partial"][scenario]["pnl"]
        for scenario in SCENARIO_ORDER
    }
    for book in books.values():
        for scenario in SCENARIO_ORDER:
            partial = book["scenarios_partial"][scenario]
            relative = partial["pnl_after_cost"] - benchmark_pnl[scenario]
            partial["benchmark_pnl"] = benchmark_pnl[scenario]
            partial["relative_pnl_after_cost"] = relative
            partial["within_budget"] = relative >= -RELATIVE_BUDGET - 1e-6
        book["scenarios"] = book.pop("scenarios_partial")


def main(argv=None) -> None:
    args = parse_args(argv)
    manifest = verify_or_accept(DATA, accept_new_source=args.accept_new_source)
    curves = load_curve_parameters(DATA / "curve_parameters_2022_2023.csv")
    if len(curves) != manifest["filter"]["usable_days"]:
        raise SystemExit(
            f"expected {manifest['filter']['usable_days']} usable days, found {len(curves)}. "
            "Refusing to price."
        )
    published = load_published_sveny(DATA / "published_sveny_event_dates.csv")
    sveny_gap_by_date = sveny_gaps_bp(curves, published, svensson_zero_percent)
    sveny_gap_bp = assert_sveny_gap(curves, published, svensson_zero_percent)
    OUT.mkdir(parents=True, exist_ok=True)

    beta = curves["2023-07-31"]
    instruments = build_instruments(beta)
    scenarios = build_scenarios(curves)
    pnl, returns, shocked, approx_kr, approx_cf = scenario_tables(instruments, beta, scenarios)

    # Numpy is used for the published node-shock rounding check.
    expected_nodes = {
        "hist_2023_07_31_to_2023_10_19": np.array([0.90, 26.18, 77.43, 108.10, 119.44, 93.82]),
        "hist_2023_03_08_to_2023_03_13": np.array([-37.57, -95.13, -62.51, -41.39, -21.86, -13.14]),
    }
    node_checks = {}
    for name, expected in expected_nodes.items():
        raw = np.array(scenarios[name]["node_shock_bp"], dtype=np.float64)
        rounded = np.round(raw, 2)
        if not np.array_equal(rounded, expected):
            raise SystemExit(f"node shocks for {name} rounded to {rounded}, expected {expected}")
        node_checks[name] = {
            "raw_bp": raw.tolist(),
            "rounded_bp": rounded.tolist(),
        }

    current_partial = solve_two_bond(instruments, "S06M", "S30Y")
    benchmark_partial = solve_benchmark(instruments)
    control_partial = solve_two_bond(instruments, "S02Y", "S20Y")
    current = normalize_weights(current_partial, INSTRUMENT_IDS)
    benchmark = normalize_weights(benchmark_partial, INSTRUMENT_IDS)
    control = normalize_weights(control_partial, INSTRUMENT_IDS)

    family = []
    for buy in BUY_CHOICES:
        screen = clearing_analysis(current, benchmark, instruments, returns, buy)
        weights_10 = normalize_weights(candidate_weights(current, instruments, buy, ROUTINE_TURNOVER_CAP), INSTRUMENT_IDS)
        screen["weights_at_10pct"] = weights_10
        if screen["feasible"]:
            screen["weights_at_just"] = normalize_weights(
                candidate_weights(current, instruments, buy, screen["turnover_just"]),
                INSTRUMENT_IDS,
            )
        family.append(screen)

    s05 = next(row for row in family if row["buy"] == CASE_BUY)
    if not s05["feasible"]:
        raise SystemExit("S05Y direction cannot clear the six scenarios")
    expanded_turnover = s05["turnover_just"] + DISPLAY_TURNOVER_INCREMENT
    if expanded_turnover > s05["max_turnover_long_only"] + 1e-12:
        raise SystemExit("1 percentage-point buffer exceeds the long-only limit")
    candidate_10 = normalize_weights(
        candidate_weights(current, instruments, CASE_BUY, ROUTINE_TURNOVER_CAP),
        INSTRUMENT_IDS,
    )
    expanded = normalize_weights(
        candidate_weights(current, instruments, CASE_BUY, expanded_turnover),
        INSTRUMENT_IDS,
    )

    feasible = [row for row in family if row["feasible"]]
    best = min(feasible, key=lambda row: row["turnover_just"])
    lower_than_s05 = [
        {"buy": row["buy"], "turnover_just": row["turnover_just"]}
        for row in feasible
        if row["buy"] != CASE_BUY and row["turnover_just"] < s05["turnover_just"] - 1e-12
    ]

    book_specs = {
        "current": (current, False),
        "benchmark": (benchmark, False),
        "candidate_10pct_s05y": (candidate_10, True),
        "candidate_expanded_s05y": (expanded, True),
        "control_2y20y": (control, False),
    }
    books = {}
    for name, (weights, charge) in book_specs.items():
        books[name] = book_payload(name, weights, instruments, returns, scenarios, current, charge)
    attach_relative(books)

    # KR and CF approximations at book level.
    for name, (weights, _charge) in book_specs.items():
        for scenario in SCENARIO_ORDER:
            kr_pnl = 0.0
            cf_pnl = 0.0
            for instrument_id, weight in weights.items():
                if not weight:
                    continue
                scale = weight * NAV / instruments[instrument_id]["dirty"]
                kr_pnl += scale * approx_kr[instrument_id][scenario]
                cf_pnl += scale * approx_cf[instrument_id][scenario]
            full = books[name]["scenarios"][scenario]["pnl"]
            books[name]["scenarios"][scenario]["kr01_approx_pnl"] = kr_pnl
            books[name]["scenarios"][scenario]["cf_first_order_pnl"] = cf_pnl
            books[name]["scenarios"][scenario]["full_minus_kr01_approx"] = full - kr_pnl
            books[name]["scenarios"][scenario]["full_minus_cf_approx"] = full - cf_pnl

    expanded_rels = {
        scenario: books["candidate_expanded_s05y"]["scenarios"][scenario]["relative_pnl_after_cost"]
        for scenario in SCENARIO_ORDER
    }
    tightest = min(expanded_rels, key=expanded_rels.get)
    cushion = expanded_rels[tightest] + RELATIVE_BUDGET
    gross = books["candidate_expanded_s05y"]["gross_traded_vs_current"]
    breakeven_bp = ONE_SIDED_COST_BP + cushion / gross * 10_000.0

    # Just-clearing book should sit on the budget in the binding scenario.
    just_weights = normalize_weights(
        candidate_weights(current, instruments, CASE_BUY, s05["turnover_just"]),
        INSTRUMENT_IDS,
    )
    just_turnover, just_gross, _, _ = turnover_and_gross(just_weights, current)
    just_cost = transaction_cost(just_gross)
    just_relative = {
        scenario: book_pnl(just_weights, returns[scenario]) - just_cost - book_pnl(benchmark, returns[scenario])
        for scenario in SCENARIO_ORDER
    }

    control_outside = [
        scenario
        for scenario in SCENARIO_ORDER
        if not books["control_2y20y"]["scenarios"][scenario]["within_budget"]
    ]

    current_dv = books["current"]["dv01"]
    s30_share = current["S30Y"] * instruments["S30Y"]["dv01_per_dollar"] * NAV / current_dv
    kr_values = list(books["current"]["kr01"].values())
    long_kr_share = (kr_values[4] + kr_values[5]) / sum(kr_values)

    decisions = {}
    for name in book_specs:
        relatives = [
            books[name]["scenarios"][scenario]["relative_pnl_after_cost"] for scenario in SCENARIO_ORDER
        ]
        verdict = decide(
            BOOK_ROLES[name],
            books[name]["weights"],
            books[name]["dv01"],
            relatives,
            books[name]["turnover_vs_current"],
            ROUTINE_TURNOVER_CAP,
        )
        books[name]["governance"] = verdict
        decisions[name] = verdict["decision"]

    case = {
        "valuation_date": "2023-07-31",
        "nav": NAV,
        "dv01_target_per_bp": DV01_TARGET,
        "dv01_tolerance": 0.02,
        "relative_loss_budget": RELATIVE_BUDGET,
        "one_sided_cost_bp": ONE_SIDED_COST_BP,
        "routine_turnover_cap": ROUTINE_TURNOVER_CAP,
        "decisions": decisions,
        "accrued_interest": "out of scope; every contract accrues from the valuation date, so accrued is 0 and clean equals dirty",
        "twist": {
            "short_node_years": 2.0,
            "long_node_years": 10.0,
            "steepener_bp": " -50 at and before 2y; linear in maturity to +100 at 10y; +100 beyond 10y",
            "flattener_bp": "+100 at and before 2y; linear in maturity to -50 at 10y; -50 beyond 10y",
            "steepener_at_nodes_bp": scenarios["twist_steepener"]["node_shock_bp"],
            "flattener_at_nodes_bp": scenarios["twist_flattener"]["node_shock_bp"],
            "not": "These are not bear steepeners or bull flatteners.",
        },
        "node_shock_checks": node_checks,
        "curve_check_max_abs_bp": sveny_gap_by_date,
        "curve_check_worst_abs_bp": sveny_gap_bp,
        "diagnostics": {
            "current_s30y_weight": current["S30Y"],
            "current_s30y_share_of_dv01": s30_share,
            "current_kr01_share_20y_and_30y": long_kr_share,
            "current_convexity": books["current"]["convexity"],
            "benchmark_convexity": books["benchmark"]["convexity"],
            "control_scenarios_outside_budget": control_outside,
        },
        "books": {
            name: {
                key: books[name][key]
                for key in (
                    "weights",
                    "market_value",
                    "face",
                    "dv01",
                    "convexity",
                    "kr01",
                    "kr01_sum",
                    "turnover_vs_current",
                    "gross_traded_vs_current",
                    "buys_vs_current",
                    "sells_vs_current",
                    "cost",
                    "charge_cost",
                    "scenarios",
                    "governance",
                )
            }
            for name in book_specs
        },
        "candidate_family": [
            {
                "buy": row["buy"],
                "feasible": row["feasible"],
                "turnover_just": row["turnover_just"],
                "max_turnover_long_only": row["max_turnover_long_only"],
                "turnover_cap_from_constraints": row["turnover_cap_from_constraints"],
                "binding_lower_scenario": row["binding_lower_scenario"],
                "s06m_financing_fraction": row["s06m_financing_fraction"],
                "bounds": row["bounds"],
            }
            for row in family
        ],
        "case_decision": {
            "published_10pct_direction": CASE_BUY,
            "reason": (
                "The 10% book under review buys S05Y. Other directions are reported. "
                "The expanded book stays on the S05Y direction and is not a search over all portfolios."
            ),
            "directions_that_clear_at_lower_turnover": lower_than_s05,
            "lowest_feasible_direction": {"buy": best["buy"], "turnover_just": best["turnover_just"]},
        },
        "expanded_s05y": {
            "turnover_just": s05["turnover_just"],
            "binding_scenario_at_just": s05["binding_lower_scenario"],
            "turnover_with_one_point_buffer": expanded_turnover,
            "buffer": DISPLAY_TURNOVER_INCREMENT,
            "just_clearing_relative_pnl": just_relative,
            "just_clearing_turnover_check": just_turnover,
            "tightest_scenario": tightest,
            "cushion_dollars": cushion,
            "breakeven_one_sided_cost_bp": breakeven_bp,
            "gross_traded": gross,
        },
    }
    (OUT / "case_results.json").write_text(json.dumps(case, indent=2) + "\n")

    instrument_rows = []
    for name in INSTRUMENT_IDS:
        inst = instruments[name]
        row = {
            "instrument": name,
            "coupon_percent": inst["coupon_percent"],
            "maturity": inst["maturity"],
            "n_cashflows": inst["n_cashflows"],
            "accrued_per_100": inst["accrued"],
            "clean_per_100": inst["clean"],
            "dirty_per_100": inst["dirty"],
            "dv01_per_100": inst["dv01_per_100"],
            "dv01_per_dollar": inst["dv01_per_dollar"],
            "duration_years": inst["duration"],
            "convexity_years2": inst["convexity"],
        }
        for node, kr in zip(KEY_RATE_NODES, inst["kr01_per_100"]):
            row[f"kr01_{node:g}y_per_100"] = kr
        instrument_rows.append(row)
    pd.DataFrame(instrument_rows).to_csv(OUT / "instruments.csv", index=False)

    position_rows = []
    for book_name in book_specs:
        book = books[book_name]
        for name in INSTRUMENT_IDS:
            position_rows.append(
                {
                    "book": book_name,
                    "instrument": name,
                    "market_value_weight": book["weights"][name],
                    "market_value": book["market_value"][name],
                    "face": book["face"][name],
                    "dirty_per_100": instruments[name]["dirty"],
                    "dv01": book["weights"][name] * NAV * instruments[name]["dv01_per_dollar"],
                }
            )
    pd.DataFrame(position_rows).to_csv(OUT / "positions.csv", index=False)

    cash_rows = []
    for name in INSTRUMENT_IDS:
        for detail in instruments[name]["detail"]:
            cash_rows.append(
                {
                    "instrument": name,
                    "pay_date": detail["pay_date"].isoformat(),
                    "T_act_365f": detail["T"],
                    "cashflow_per_100": detail["cf"],
                    "is_principal": detail["is_principal"],
                    "zero_percent": detail["zero_percent"],
                    "zero_decimal": detail["zero_decimal"],
                    "discount_factor": detail["discount"],
                    "pv_per_100": detail["pv"],
                }
            )
    pd.DataFrame(cash_rows).to_csv(OUT / "cashflows.csv", index=False)

    bond_rows = []
    for name in INSTRUMENT_IDS:
        for scenario in SCENARIO_ORDER:
            bond_rows.append(
                {
                    "instrument": name,
                    "scenario": scenario,
                    "dirty_base_per_100": instruments[name]["dirty"],
                    "dirty_shocked_per_100": shocked[name][scenario],
                    "full_reval_pnl_per_100": pnl[name][scenario],
                    "kr01_approx_pnl_per_100": approx_kr[name][scenario],
                    "cf_first_order_pnl_per_100": approx_cf[name][scenario],
                }
            )
    pd.DataFrame(bond_rows).to_csv(OUT / "scenario_bond_results.csv", index=False)

    contribution_rows = []
    kr_rows = []
    for book_name in book_specs:
        book = books[book_name]
        for name in INSTRUMENT_IDS:
            dirty = instruments[name]["dirty"]
            market_value = book["market_value"][name]
            scale = 0.0 if market_value == 0.0 else market_value / dirty
            for scenario in SCENARIO_ORDER:
                per_100 = pnl[name][scenario]
                contribution_rows.append(
                    {
                        "book": book_name,
                        "instrument": name,
                        "scenario": scenario,
                        "market_value": market_value,
                        "pnl_per_100_face": per_100,
                        "pnl_dollars": scale * per_100,
                    }
                )
            for node, kr in zip(KEY_RATE_NODES, instruments[name]["kr01_per_100"]):
                kr_rows.append(
                    {
                        "book": book_name,
                        "instrument": name,
                        "node_years": node,
                        "kr01_dollars": scale * kr,
                    }
                )
        for node, value in book["kr01"].items():
            kr_rows.append(
                {
                    "book": book_name,
                    "instrument": "BOOK",
                    "node_years": float(node),
                    "kr01_dollars": value,
                }
            )
    pd.DataFrame(contribution_rows).to_csv(OUT / "scenario_contributions.csv", index=False)
    pd.DataFrame(kr_rows).to_csv(OUT / "kr01_by_bond.csv", index=False)

    snap_rows = []
    for day in ("2023-03-08", "2023-03-13", "2023-07-31", "2023-10-19"):
        for node in KEY_RATE_NODES:
            formula = svensson_zero_percent(node, curves[day])
            published_y = published[day].get(int(node)) if float(node).is_integer() else None
            snap_rows.append(
                {
                    "record": "level",
                    "start": day,
                    "end": "",
                    "maturity_years": node,
                    "zero_continuous_percent": formula,
                    "published_sveny_percent": "" if published_y is None else published_y,
                    "difference_bp": "" if published_y is None else (formula - published_y) * 100.0,
                }
            )
    for label, start, end in (
        ("hist_2023_03_08_to_2023_03_13", "2023-03-08", "2023-03-13"),
        ("hist_2023_07_31_to_2023_10_19", "2023-07-31", "2023-10-19"),
    ):
        for node, raw, rounded in zip(KEY_RATE_NODES, node_checks[label]["raw_bp"], node_checks[label]["rounded_bp"]):
            snap_rows.append(
                {
                    "record": "shock",
                    "start": start,
                    "end": end,
                    "maturity_years": node,
                    "zero_continuous_percent": raw / 100.0,
                    "published_sveny_percent": "",
                    "difference_bp": raw,
                    "difference_bp_rounded_2dp": rounded,
                }
            )
    pd.DataFrame(snap_rows).to_csv(OUT / "curve_snapshots.csv", index=False)

    workbook_path = ROOT / "fixed_income_case.xlsx"
    build_workbook(
        workbook_path,
        instruments,
        books,
        pnl,
        instruments["S05Y"]["detail"],
        breakeven_bp,
    )
    workbook_cached = cache_workbook_values(workbook_path)

    print(f"usable days {len(curves)}")
    print(f"S05Y just {s05['turnover_just']:.8f} buffer {expanded_turnover:.8f} bind {s05['binding_lower_scenario']}")
    print(f"cushion {cushion:.4f} breakeven_bp {breakeven_bp:.4f} tight {tightest}")
    print(f"best direction {best['buy']} at {best['turnover_just']:.8f}; lower than S05Y: {lower_than_s05}")
    print(f"control outside {control_outside}")
    record = {
        "ran_at_america_los_angeles": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds"),
        "offline": True,
        "source_manifest_rewritten": False,
        "frozen_file_sha256": manifest["frozen_file_sha256"],
        "published_sveny_excerpt_sha256": manifest["published_sveny_excerpt_sha256"],
        "beta_units": manifest["beta_units"],
        "tau_units": manifest["tau_units"],
        "sveny_max_abs_gap_bp": sveny_gap_bp,
        "sveny_max_abs_gap_bp_by_date": sveny_gap_by_date,
        "decisions": decisions,
        "workbook_values_cached": workbook_cached,
        "expanded_turnover_just": s05["turnover_just"],
        "expanded_turnover_with_buffer": expanded_turnover,
        "breakeven_one_sided_cost_bp": breakeven_bp,
    }
    (OUT / "offline_reproduction.json").write_text(json.dumps(record, indent=2) + "\n")

    print("weights")
    print("decisions", decisions)
    print("workbook cached", workbook_cached)
    for name in book_specs:
        print(name, {k: round(v, 8) for k, v in books[name]["weights"].items() if v})
        print("  dv01", books[name]["dv01"], "cost", books[name]["cost"], "turnover", books[name]["turnover_vs_current"])


if __name__ == "__main__":
    main()
