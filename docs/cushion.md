# Cost, turnover, and cushion

Question: if the manager wants the budget to survive a higher trading cost, how much more turnover, and what convexity is given up?

The rows below reuse the case's buy-S05Y financing. Market value and parallel DV01 are unchanged before the cost. The cost is one illustrative charge, the same rate on buys and on sells. It is not a historical bid–ask. Every row is long-only, DV01 is $50,000 per bp before the cost, and the binding scenario is the transplanted March 2023 shock. Figures are the computed values, rounded to the cent. Convexity is the analytic years² measure already used for the books. The regression tests recompute these rows. `reproduce_case.py` does not write them out.

| Turnover | One-sided cost | Worst relative P&L after the cost | Cushion vs −$1 million | Convexity |
| --- | ---: | ---: | ---: | ---: |
| 44.5543% | 2 bp | −981,168.37 | +18,831.63 | 76.28 |
| 44.5543% | 4.2 bp | −1,000,772.28 | −772.28 | 76.28 |
| 50% | 2 bp | −878,617.41 | +121,382.59 | 71.97 |
| 50% | 4.2 bp | −900,617.41 | +99,382.59 | 71.97 |

The displayed candidate adds one percentage point of turnover to the minimum feasible trade, 43.5543%, to measure a small sizing margin. That is the 44.5543% row. At 2 bp its March relative P&L is −$981,168.37, so the cushion is $18,831.63, about 1.88 bp of NAV, not 1% of NAV. At 4.2 bp that same book is −$1,000,772.28, outside the budget by $772.28. Convexity does not change when only the cost rate changes. The cost break-even is about 4.11 bp per side, so 4.2 bp is a point just above that boundary, not an observed dealing cost.

The 50% row is a round comparison of extra headroom, turnover, and convexity given up, not an optimum and not a different authority setting. Its convexity is 71.97 years², about 4.3 years² below the 44.5543% book. At 4.2 bp it is still inside the budget, with a cushion of $99,382.59. Gross traded value is $100 million, against about $89.1 million. Raising the authority cap to 50% does not make the 44.5543% book pass at 4.2 bp; only implementing the larger trade changes the exposure. That larger trade would still need a larger trading authority. The rest of the case scope is in the [README](../README.md).

## Appendix: the budget also picks the bond

Under 2 bp per side, the lowest-turnover buy in the existing six-name family moves when the relative-loss budget moves. Each scenario supplies a linear turnover bound. The regression tests recompute the three rows. `reproduce_case.py` does not write them out.

| Relative-loss budget | Lowest-turnover buy | Turnover | Scenario that sets it |
| --- | --- | ---: | --- |
| 0.5% of NAV, $0.5 million | S07Y | 66.9338% | March 2023 |
| 1.0% of NAV, $1.0 million | S05Y | 43.5543% | March 2023 |
| 1.5% of NAV, $1.5 million | S05Y | 17.5257% | Steepener |

These are conditional feasibility results inside that candidate family. The same six scenarios are used to choose the trade and to grade it. They are not out-of-sample protection, and they are not a claim that one maturity is best in general. A tighter budget changes the size and, at 0.5% of NAV, the maturity. A looser budget changes which scenario binds.
