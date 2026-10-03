# Fixed-income curve risk

This case asks whether a bond book that matches a benchmark's parallel DV01 is inside a relative loss budget when the curve changes shape. The book is a set of synthetic USD fixed-coupon bullets, valued on 31 July 2023. Holdings, the benchmark, the loss budget, and transaction costs are synthetic. The curve changes are not. They are taken from the Federal Reserve's Gürkaynak–Sack–Wright (GSW) Svensson fit and added, as a function of maturity, to the valuation-date zero curve.

Two historical episodes are used. From 8 March to 13 March 2023, fitted zeros fell, especially around the two-year point. From 31 July to 19 October 2023, longer zeros rose. The October date is an endpoint chosen after the fact, not a date a portfolio manager could have known in July. A parallel move of 100 bp in each direction, and two defined twists, complete a six-scenario set. Nothing here is a forecast, and nothing here is a claim that any real fund predicted or avoided a crisis.

## Scope

The contracts and the mandate are synthetic. They are not a regulatory limit and not an industry standard.

Historical curve changes come from the Fed GSW fit of off-the-run Treasury coupon securities. The fit is not a bill curve, not a set of executable quotes, and not the Treasury's constant-maturity par yield. CMT yields are not used to discount cash flows. The source can be revised. This repository freezes the file downloaded on 3 October 2026 at 00:55:19 PT, and records that file's SHA-256 in `data/source_manifest.json`.

The March shock is transplanted onto the July book. The cash-flow dates stay at their 31 July 2023 remaining maturities. The scenario is not a claim that these contracts were held in March, and it is not a fund's March return. There is no carry, roll-down, coupon income, or passage of time.

This version does not demonstrate accrued interest. Every contract accrues from the valuation date, the first coupon is 31 January 2024, and accrued interest is zero, so the clean price equals the dirty price. There is no holiday adjustment and no settlement lag. Discount time is actual days over 365.

On the valuation date the Svensson decay parameters are nearly equal (`TAU1` 1.71415, `TAU2` 1.71447) and `BETA2` and `BETA3` are large and opposite in sign. The zero curve is still the Svensson function of maturity. Shocks are added to that zero curve. The six parameters are not bumped.

The 30-year zero rose less than the 10-year and 20-year zeros from 31 July to 19 October (+93.82 bp, against +108.10 bp and +119.44 bp, rounded to 0.01 bp). A large absolute loss therefore need not breach a relative budget. In this case the current book loses about $4.14 million on that shock and lags the benchmark by about $0.13 million, inside the $1 million relative budget.

A 10% turnover in the candidate family defined below relieves the two budget breaches and repairs neither. The expanded trade is the same S05Y direction with a larger turnover. It is not a global optimum, and the calculation does not prove that no other portfolio inside a 10% turnover cap could satisfy the budget.

This is not a reconstruction of SVB or of UK LDI. There are no liabilities, deposits, redemptions, or repo.

GSW documentation: [nominal yield curve](https://www.federalreserve.gov/data/nominal-yield-curve.htm). The July–October move is the episode discussed in the Board note [The Treasury Tantrum of 2023](https://www.federalreserve.gov/econres/notes/feds-notes/the-treasury-tantrum-of-2023-20240903.html); that note starts on 26 July, so the shocks here are recomputed from 31 July and are not the note's cumulative figures. The March backdrop is the [March 2023 FOMC minutes](https://www.federalreserve.gov/monetarypolicy/fomcminutes20230322.htm). The minutes are context. They are not the discount curve and they are not a transaction-cost observation.

## Mandate

| Item | Setting |
| --- | --- |
| Initial NAV | $100,000,000 |
| Parallel DV01 | $50,000 per bp, tolerance ±2% |
| Positions | Long only, no leverage, weights at least zero |
| Relative budget | In every named scenario, P&L versus the benchmark, after the candidate's one-time cost, not worse than −1% of initial NAV (−$1,000,000) |
| Absolute loss | No limit |
| Routine turnover | 10% of NAV. Turnover = 0.5 × sum of absolute market-value changes / initial NAV. Gross buys plus sells are reported separately |
| Illustrative cost | 2 bp of traded market value on buys and 2 bp on sells. Not a historical spread |

The 1% budget and the 10% turnover cap were set as part of the case, not tightened after seeing the results.

## Contracts

Price per 100 face is the sum of cash flow times `exp(-z(T) T)`, with `z` the continuous zero in decimal. Parallel DV01 is the central difference of a ±1 bp shift of the whole zero curve. Key-rate DV01 uses tents on 0.5, 2, 5, 10, 20, and 30 years; weights sum to 1, and a cash flow outside the end nodes uses the nearest node. The 30-year bond's final maturity is slightly longer than 30 on an ACT/365F count, so that principal payment loads on the 30-year node. Formulas are in `docs/method.md`.

| ID | Coupon | Maturity | Dirty per 100 on 31 Jul 2023 |
| --- | ---: | --- | ---: |
| S06M | 4.75% | 2024-01-31 | 99.582157 |
| S02Y | 4.50% | 2025-07-31 | 99.194643 |
| S03Y | 4.25% | 2026-07-31 | 99.065240 |
| S05Y | 4.00% | 2028-07-31 | 99.087613 |
| S07Y | 4.00% | 2030-07-31 | 99.566682 |
| S10Y | 4.00% | 2033-07-31 | 99.582423 |
| S20Y | 4.00% | 2043-07-31 | 98.181553 |
| S30Y | 4.00% | 2053-07-31 | 97.092721 |

These prices match an independent stdlib recomputation to about 1e-14 per 100 face. Full precision is in `outputs/instruments.csv`.

## Books

Weights are market-value weights. Face equals market value / dirty price × 100. Every book below is $100 million with parallel DV01 of $50,000 per bp before costs.

| Instrument | Current | Benchmark | 10% S05Y | Expanded S05Y | Control 2y/20y |
| --- | ---: | ---: | ---: | ---: | ---: |
| S06M | 73.5824% | 0 | 65.9823% | 39.7210% | 0 |
| S02Y | 0 | 15.0648% | 0 | 0 | 74.4201% |
| S03Y | 0 | 15% | 0 | 0 | 0 |
| S05Y | 0 | 30% | 10% | 44.5543% | 0 |
| S07Y | 0 | 20% | 0 | 0 | 0 |
| S10Y | 0 | 19.9352% | 0 | 0 | 0 |
| S20Y | 0 | 0 | 0 | 0 | 25.5799% |
| S30Y | 26.4176% | 0 | 24.0177% | 15.7247% | 0 |

The current book solves the 6-month and 30-year weights. The benchmark holds the 3-year, 5-year, and 7-year weights fixed at 15/30/20 and solves the 2-year and 10-year weights. The control book is only the 2-year and 20-year bonds, with the same NAV and DV01. Its weights are in `outputs/positions.csv`.

The 30-year bond is 26.42% of current market value and 92.58% of current DV01. The 20-year and 30-year key-rate nodes together are 75.87% of current KR01. Those are different allocations of the same risk: one by instrument, one by the maturity of each cash flow. Analytic convexity is about 111.54 years² for the current book and 32.37 years² for the benchmark, which is why the two parallel full revaluations are not identical even though DV01 matches.

## Scenarios

Historical shocks are the full function Δz(T) = z_end(T) − z_start(T), not a six-node interpolant. Rounded to 0.01 bp, the fitted zeros moved as follows.

| Shock | 0.5y | 2y | 5y | 10y | 20y | 30y |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 31 Jul 2023 to 19 Oct 2023 | +0.90 | +26.18 | +77.43 | +108.10 | +119.44 | +93.82 |
| 8 Mar 2023 to 13 Mar 2023 | −37.57 | −95.13 | −62.51 | −41.39 | −21.86 | −13.14 |

The twists are linear in maturity between the 2-year and 10-year key-rate nodes and flat outside that segment. In basis points:

```
steepener:  -50  for T ≤ 2;   -50 + 150 × (T − 2) / 8  for 2 < T < 10;   +100 for T ≥ 10
flattener:  +100 for T ≤ 2;   +100 − 150 × (T − 2) / 8  for 2 < T < 10;   −50  for T ≥ 10
```

At the nodes the steepener is (−50, −50, +6.25, +100, +100, +100) bp. Short and long yields move in opposite directions. These are not bear steepeners or bull flatteners. For this particular twist the node tents reproduce the shock exactly, so the gap between the KR01 approximation and full revaluation is higher order. For the historical shocks the six nodes do not reproduce Δz(T), so that gap is not all convexity. Both approximations are in `outputs/scenario_bond_results.csv` and `outputs/case_results.json`.

## Results

Own full-revaluation P&L, in dollars. Candidate columns are before the one-time cost. Current, benchmark, and control are not charged.

| Scenario | Current | Benchmark | 10% S05Y | Expanded S05Y | Control |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parallel +100 bp | −4,488,675 | −4,842,174 | −4,524,208 | −4,646,991 | −4,695,244 |
| Parallel −100 bp | 5,611,015 | 5,165,999 | 5,566,790 | 5,413,973 | 5,343,328 |
| Steepener | −3,666,610 | −1,621,897 | −3,351,801 | −2,264,004 | −2,288,390 |
| Flattener | 1,814,301 | −765,805 | 1,443,028 | 160,118 | 167,290 |
| March 2023 | 1,136,871 | 2,957,070 | 1,329,187 | 1,993,723 | 2,385,854 |
| July–October 2023 | −4,142,728 | −4,012,229 | −4,103,698 | −3,968,835 | −4,061,014 |

Relative P&L versus the benchmark after the candidate's cost, in dollars. A figure below −1,000,000 is outside the budget.

| Scenario | Current | Benchmark | 10% S05Y | Expanded S05Y | Control |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parallel +100 bp | 353,499 | 0 | 313,966 | 177,361 | 146,930 |
| Parallel −100 bp | 445,017 | 0 | 396,791 | 230,152 | 177,329 |
| Steepener | −2,044,713 | 0 | −1,733,905 | −659,928 | −666,493 |
| Flattener | 2,580,106 | 0 | 2,204,833 | 908,101 | 933,095 |
| March 2023 | −1,820,199 | 0 | −1,631,882 | −981,168 | −571,216 |
| July–October 2023 | −130,498 | 0 | −95,469 | 25,573 | −48,785 |

The July–October loss is large and the relative gap is not. The March shock makes money on the current book and still misses the relative budget, because the benchmark holds the part of the curve that rallied. Matching parallel DV01 does not match those two shapes.

The 2-year/20-year control, with the same NAV and the same DV01, is inside the $1 million relative budget in all six scenarios under the twist defined above. That is a computed result for this control, not a statement about barbells in general.

## The 10% trade, and the other five directions

The candidate family buys one of S02Y, S03Y, S05Y, S07Y, S10Y, or S20Y, financed by selling S06M and S30Y so that pre-cost market value and parallel DV01 stay put. The sale is the unique split that satisfies those two constraints. It is not a pro-rata sale by market value. Turnover `u` means buying market value `u × NAV`.

At a 10% cap the book under review buys S05Y: about $7.600 million of the 6-month bond and $2.400 million of the 30-year bond are sold, and $10 million of the 5-year bond is bought. Gross traded value is $20 million. Turnover is 10%. The illustrative cost is $4,000. March is still behind the benchmark by about $1.632 million, and the steepener by about $1.734 million. The trade relieves both breaches and repairs neither.

Within this family, no other tenor clears every scenario at a lower turnover.

| Buy | Clears all six? | Turnover that just clears | What binds |
| --- | --- | ---: | --- |
| S02Y | Yes | 62.1578% | March 2023 |
| S03Y | Yes | 50.3814% | March 2023 |
| S05Y | Yes | 43.5543% | March 2023 |
| S07Y | Yes | 44.5318% | Steepener |
| S10Y | No | — | Steepener gets worse as the 10-year weight rises, and it is already outside the budget |
| S20Y | No | — | Same problem, and July–October also deteriorates |

S05Y is the lowest turnover in the family that clears the set. That is a comparison inside six prespecified directions, not a search over all long-only books. A 10% cap is not shown to be infeasible for every possible trade.

## Expanded S05Y trade

Along the buy-S05Y direction, 43.5543% turnover is the smallest trade that puts every scenario on the budget after the 2 bp one-sided cost. The binding scenario is March 2023. The published expanded book adds one percentage point of NAV turnover, to 44.5543%:

- sell about $33.861 million of S06M
- sell about $10.693 million of S30Y
- buy about $44.554 million of S05Y
- gross traded value about $89.109 million
- illustrative cost about $17,822

After that cost, all six scenarios are inside the budget. The tightest is still March, with relative P&L of −$981,168 and a cushion of $18,832 to the −$1,000,000 line. The one-sided cost that would use up that cushion is 4.11 bp. At 4.2 bp the March scenario falls outside the budget. `fixed_income_case.xlsx` recomputes this from the cost input: Notes!B13 is the live break-even, and Notes!B14 answers whether 4.2 bp would exhaust the cushion.

The expanded trade gives up part of the book's advantage in a parallel rally and in the flattener. It is not better in every scenario, and it is not a global optimum. It exceeds the routine 10% turnover authority.

## Where an earlier design table differs

Parallel moves, both historical shocks, the March and July–October relatives, the control book's historical relatives, the 43.5543% just-clearing turnover, and the expanded book's March cushion agree with an earlier design table at the table's reported precision (0.01 × $10,000). The twist in that table was not accompanied by an explicit formula. This repository uses the 2y/10y blend above and keeps these calculated twist P&Ls. In units of $10,000, the design table and this calculation compare as follows.

| | Design, current / benchmark / 10% relative / expanded relative | This calculation |
| --- | --- | --- |
| Steepener | −365.48 / −147.78 / −184.01 / −67.60 | −366.66 / −162.19 / −173.39 / −65.99 |
| Flattener | 189.85 / 24.62 / 145.77 / 78.51 | 181.43 / −76.58 / 220.48 / 90.81 |

The flattener benchmark P&L changes sign. Relative rankings of the historical scenarios do not. `outputs/case_results.json` lists every differing cell under `design_note_differences`.

## Reproduce

From this directory, with no network:

```bash
python3 reproduce_case.py
python3 validate_independently.py
python3 -m unittest tests/test_case.py
```

`reproduce_case.py` reads only the frozen parameters and the frozen SVENY excerpt, and rewrites `outputs/` and `fixed_income_case.xlsx`. Dependencies are numpy, pandas, and openpyxl. The independent check uses the standard library only. Tests fail if a dirty price moves by 1e-6 per 100 face or if a book's NAV or DV01 match breaks.

The frozen curve has the 499 usable business days from 1 January 2022 through 31 December 2023. Twenty-one dated rows in that window have no BETA or TAU and are listed in `data/dropped_dates.csv` and in the manifest: 2022-01-17, 2022-02-21, 2022-04-15, 2022-05-30, 2022-06-20, 2022-07-04, 2022-09-05, 2022-10-10, 2022-11-11, 2022-11-24, 2022-12-26, 2023-01-02, 2023-01-16, 2023-02-20, 2023-05-29, 2023-06-19, 2023-07-04, 2023-09-04, 2023-10-09, 2023-11-23, 2023-12-25.

On the four event dates, the Svensson formula and the published SVENY01–SVENY30 series differ by at most about 0.005 bp. The check is `data/source_curve_check.json`.
