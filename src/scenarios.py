"""Scenario shocks added to the 2023-07-31 continuous zero curve.

Historical shocks are the full function Δz(T) = z_end(T) - z_start(T).
They are transplanted onto the valuation-date curve. Cash-flow dates do not move.
The March 2023 shock is not a claim that the book was held in March.

The two twists are linear blends in maturity between the 2-year and 10-year
key-rate nodes, and constant outside that segment:

    steepener:  -50 bp at and before 2y, +100 bp at and beyond 10y
    flattener:  +100 bp at and before 2y, -50 bp at and beyond 10y

Between 2y and 10y the shock is linear in year-fraction T. These are not
bear steepeners or bull flatteners: the short and long ends move in opposite
directions.
"""

from __future__ import annotations

from .bonds import KEY_RATE_NODES
from .curve import zero_decimal

BP = 0.0001
TWIST_SHORT_NODE = 2.0
TWIST_LONG_NODE = 10.0
STEEPENER_SHORT_BP = -50.0
STEEPENER_LONG_BP = 100.0
FLATTENER_SHORT_BP = 100.0
FLATTENER_LONG_BP = -50.0

SCENARIO_ORDER = (
    "parallel_plus_100bp",
    "parallel_minus_100bp",
    "twist_steepener",
    "twist_flattener",
    "hist_2023_03_08_to_2023_03_13",
    "hist_2023_07_31_to_2023_10_19",
)


def piecewise_linear_bp(maturity_years: float, left_node: float, left_bp: float, right_node: float, right_bp: float) -> float:
    if maturity_years <= left_node:
        return left_bp
    if maturity_years >= right_node:
        return right_bp
    span = right_node - left_node
    weight = (maturity_years - left_node) / span
    return left_bp + (right_bp - left_bp) * weight


def steepener_bp(maturity_years: float) -> float:
    return piecewise_linear_bp(
        maturity_years,
        TWIST_SHORT_NODE,
        STEEPENER_SHORT_BP,
        TWIST_LONG_NODE,
        STEEPENER_LONG_BP,
    )


def flattener_bp(maturity_years: float) -> float:
    return piecewise_linear_bp(
        maturity_years,
        TWIST_SHORT_NODE,
        FLATTENER_SHORT_BP,
        TWIST_LONG_NODE,
        FLATTENER_LONG_BP,
    )


def bp_to_decimal(shock_bp: float) -> float:
    return shock_bp * BP


def parallel_dz(shock_bp: float):
    shift = bp_to_decimal(shock_bp)
    return lambda _t: shift


def twist_dz(shock_bp_fn):
    return lambda t: bp_to_decimal(shock_bp_fn(t))


def historical_dz(beta_start: dict, beta_end: dict):
    def dz(t: float) -> float:
        return zero_decimal(t, beta_end) - zero_decimal(t, beta_start)
    return dz


def node_shocks_bp(shock_bp_fn) -> list[float]:
    return [float(shock_bp_fn(node)) for node in KEY_RATE_NODES]


def build_scenarios(curves: dict[str, dict]) -> dict[str, dict]:
    march = historical_dz(curves["2023-03-08"], curves["2023-03-13"])
    jul_oct = historical_dz(curves["2023-07-31"], curves["2023-10-19"])

    def constant_bp(level: float):
        return lambda _t: level

    specs = {
        "parallel_plus_100bp": {
            "label": "Parallel +100 bp",
            "family": "parallel",
            "dz": parallel_dz(100.0),
            "shock_bp_fn": constant_bp(100.0),
        },
        "parallel_minus_100bp": {
            "label": "Parallel -100 bp",
            "family": "parallel",
            "dz": parallel_dz(-100.0),
            "shock_bp_fn": constant_bp(-100.0),
        },
        "twist_steepener": {
            "label": "Twist steepener: -50 bp at 2y to +100 bp at 10y",
            "family": "twist",
            "dz": twist_dz(steepener_bp),
            "shock_bp_fn": steepener_bp,
        },
        "twist_flattener": {
            "label": "Twist flattener: +100 bp at 2y to -50 bp at 10y",
            "family": "twist",
            "dz": twist_dz(flattener_bp),
            "shock_bp_fn": flattener_bp,
        },
        "hist_2023_03_08_to_2023_03_13": {
            "label": "Historical 2023-03-08 to 2023-03-13, transplanted",
            "family": "historical",
            "dz": march,
            "shock_bp_fn": lambda t: (
                zero_decimal(t, curves["2023-03-13"]) - zero_decimal(t, curves["2023-03-08"])
            ) * 10000.0,
        },
        "hist_2023_07_31_to_2023_10_19": {
            "label": "Historical 2023-07-31 to 2023-10-19, transplanted",
            "family": "historical",
            "dz": jul_oct,
            "shock_bp_fn": lambda t: (
                zero_decimal(t, curves["2023-10-19"]) - zero_decimal(t, curves["2023-07-31"])
            ) * 10000.0,
        },
    }
    for name, spec in specs.items():
        spec["name"] = name
        spec["node_shock_bp"] = node_shocks_bp(spec["shock_bp_fn"])
    return specs
