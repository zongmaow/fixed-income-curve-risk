"""Synthetic USD fixed-coupon bullets and risk measures.

Valuation date 2023-07-31. Every bond accrues from that date, so accrued
interest is zero and clean price equals dirty price. The first coupon is
2024-01-31. Later coupons fall on calendar semi-annual month-ends through
maturity. Each period pays annual coupon / 2. Discount time is actual days
divided by 365 (ACT/365F). There is no holiday adjustment and no settlement lag.
"""

from __future__ import annotations

import calendar
from datetime import date

from .curve import zero_decimal

VALUATION_DATE = date(2023, 7, 31)
FACE = 100.0
KEY_RATE_NODES = (0.5, 2.0, 5.0, 10.0, 20.0, 30.0)
BP = 0.0001

# (id, annual coupon in percent, maturity)
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
INSTRUMENT_IDS = tuple(row[0] for row in CONTRACTS)


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return month_end(year, month)


def year_fraction(pay_date: date, valuation_date: date = VALUATION_DATE) -> float:
    return (pay_date - valuation_date).days / 365.0


def cashflow_schedule(annual_coupon_percent: float, maturity: date) -> list[dict]:
    """Cash flows per 100 face. Coupon each period is annual coupon / 2."""
    coupon = annual_coupon_percent / 2.0
    flows = []
    pay = add_months(VALUATION_DATE, 6)
    while pay < maturity:
        flows.append(
            {
                "pay_date": pay,
                "T": year_fraction(pay),
                "cf": coupon,
                "is_principal": False,
            }
        )
        pay = add_months(pay, 6)
    if pay != maturity:
        raise ValueError(f"maturity {maturity} is not on the semi-annual month-end grid (got {pay})")
    flows.append(
        {
            "pay_date": pay,
            "T": year_fraction(pay),
            "cf": coupon + FACE,
            "is_principal": True,
        }
    )
    return flows


def key_rate_weights(maturity_years: float, nodes: tuple[float, ...] = KEY_RATE_NODES) -> list[float]:
    """Piecewise-linear tent weights. Weights sum to 1.

    Cash flows before the first node, or beyond the last node, load entirely
    on the nearest end node.
    """
    weights = [0.0] * len(nodes)
    if maturity_years <= nodes[0]:
        weights[0] = 1.0
        return weights
    if maturity_years >= nodes[-1]:
        weights[-1] = 1.0
        return weights
    index = 0
    for i in range(len(nodes) - 1):
        if nodes[i] <= maturity_years <= nodes[i + 1]:
            index = i
            break
    span = nodes[index + 1] - nodes[index]
    weights[index] = (nodes[index + 1] - maturity_years) / span
    weights[index + 1] = (maturity_years - nodes[index]) / span
    return weights


def price_cashflows(flows: list[dict], zero_fn) -> float:
    """Dirty price per 100 face. zero_fn(T) returns a decimal continuous zero."""
    total = 0.0
    for flow in flows:
        t = flow["T"]
        total += flow["cf"] * math_exp(-zero_fn(t) * t)
    return total


def math_exp(x: float) -> float:
    import math
    return math.exp(x)


def present_value_detail(flows: list[dict], beta: dict) -> list[dict]:
    rows = []
    for flow in flows:
        z = zero_decimal(flow["T"], beta)
        discount = math_exp(-z * flow["T"])
        rows.append(
            {
                **flow,
                "zero_percent": z * 100.0,
                "zero_decimal": z,
                "discount": discount,
                "pv": flow["cf"] * discount,
            }
        )
    return rows


def shifted_zero(beta: dict, shift: float, extra_fn=None):
    def zero_fn(t: float) -> float:
        z = zero_decimal(t, beta) + shift
        if extra_fn is not None:
            z += extra_fn(t)
        return z
    return zero_fn


def dv01_per_100(flows: list[dict], beta: dict, step_bp: float = 1.0) -> float:
    """Central difference of a parallel shift, normalized to 1 bp.

    ``step_bp`` is the half-width of the step in basis points. The result is
    ``(P(z-h) - P(z+h)) / 2 / step_bp`` with ``h = step_bp * 0.0001``.
    The default step is 1 bp, which is the DV01 used for the mandate.
    Positive DV01 is the price decline for a rise in zeros.
    """
    if step_bp <= 0.0:
        raise ValueError("step_bp must be positive")
    h = step_bp * BP
    down = price_cashflows(flows, shifted_zero(beta, -h))
    up = price_cashflows(flows, shifted_zero(beta, +h))
    return (down - up) / 2.0 / step_bp


def kr01_per_100(flows: list[dict], beta: dict) -> list[float]:
    """Central ±1 bp key-rate DV01 on the piecewise-linear tents."""
    out = []
    for key in range(len(KEY_RATE_NODES)):
        down = price_cashflows(
            flows,
            shifted_zero(beta, 0.0, lambda t, key=key: -BP * key_rate_weights(t)[key]),
        )
        up = price_cashflows(
            flows,
            shifted_zero(beta, 0.0, lambda t, key=key: BP * key_rate_weights(t)[key]),
        )
        out.append((down - up) / 2.0)
    return out


def analytic_duration_convexity(detail: list[dict]) -> tuple[float, float]:
    """Continuous Macaulay-style duration and convexity, in years and years^2.

    duration = sum(T * PV) / Price
    convexity = sum(T^2 * PV) / Price
    """
    price = sum(row["pv"] for row in detail)
    if price == 0.0:
        raise ValueError("zero price")
    duration = sum(row["T"] * row["pv"] for row in detail) / price
    convexity = sum(row["T"] * row["T"] * row["pv"] for row in detail) / price
    return duration, convexity


def build_instruments(beta: dict) -> dict[str, dict]:
    instruments = {}
    for instrument_id, coupon, maturity in CONTRACTS:
        flows = cashflow_schedule(coupon, maturity)
        detail = present_value_detail(flows, beta)
        dirty = sum(row["pv"] for row in detail)
        dv01 = dv01_per_100(flows, beta)
        kr01 = kr01_per_100(flows, beta)
        duration, convexity = analytic_duration_convexity(detail)
        instruments[instrument_id] = {
            "id": instrument_id,
            "coupon_percent": coupon,
            "maturity": maturity.isoformat(),
            "n_cashflows": len(flows),
            "flows": flows,
            "detail": detail,
            "dirty": dirty,
            "clean": dirty,
            "accrued": 0.0,
            "dv01_per_100": dv01,
            "dv01_per_dollar": dv01 / dirty,
            "duration": duration,
            "convexity": convexity,
            "kr01_per_100": kr01,
        }
    return instruments


def revalue(instrument: dict, beta: dict, dz_fn) -> float:
    """Dirty price per 100 face on the valuation-date curve plus dz(T)."""
    return price_cashflows(
        instrument["flows"],
        shifted_zero(beta, 0.0, dz_fn),
    )


def full_reval_pnl_per_100(instrument: dict, beta: dict, dz_fn) -> float:
    return revalue(instrument, beta, dz_fn) - instrument["dirty"]


def kr01_approx_pnl_per_100(instrument: dict, node_shock_bp: list[float]) -> float:
    """First-order P&L from node shocks, per 100 face. Losses are negative."""
    return -sum(k * s for k, s in zip(instrument["kr01_per_100"], node_shock_bp))


def cf_first_order_pnl_per_100(instrument: dict, dz_fn) -> float:
    """Cash-flow derivative: sum -T * PV * dz(T), using the unshocked PVs."""
    total = 0.0
    for row in instrument["detail"]:
        total += -row["T"] * row["pv"] * dz_fn(row["T"])
    return total
