# Curve risk review, 31 July 2023

The book matches the benchmark's parallel DV01 and still has the wrong curve shape. About 74% of the $100 million sits in a 6-month bond. The 30-year bond is 26% of market value and about 93% of DV01. Total DV01 is $50,000 per bp, inside the ±2% band. That match does not keep relative performance inside the budget.

Two of the six stresses break the $1 million relative-loss budget. The steepener (short end −50 bp, 10 years and beyond +100 bp) leaves the book $2.04 million behind the benchmark. The March 2023 rally, transplanted onto this July book, makes about $1.14 million and still lags the benchmark by $1.82 million. The July–October rise in longer yields loses about $4.14 million and lags the benchmark by only $0.13 million, inside the budget, because the 30-year zero rose less than the 10-year and 20-year zeros (+93.82 bp, against +108.10 and +119.44). There is no absolute-loss limit. The standing book is `still_outside_budget`.

A routine 10% trade buys $10 million of the 5-year bond and sells the 6-month and 30-year bonds in the unique split that keeps market value and DV01 unchanged before cost. Gross traded value is $20 million. At 2 bp each side the cost is $4,000. It relieves, does not repair. March is still behind by $1.63 million and the steepener by $1.73 million. The trade is inside the 10% turnover cap and outside the stress budget, so the decision is `still_outside_budget`. No other bond in the six-name family clears every scenario at a lower turnover. Buying the 10-year or the 20-year makes the steepener worse, so those directions never clear.

The repair that does clear is the same 5-year purchase at 43.5543% turnover. The proposed book adds one point of NAV, to 44.5543%. Gross trades are about $89.1 million and the illustrative cost is about $17,822. DV01 stays on target and every scenario is inside the budget, but turnover is above 10%, so the decision is `needs_approval`. It is not a routine trade and it is not a search over all portfolios.

What is given up is convexity and a thin cushion. Analytic convexity is about 112 years² against the benchmark's 32. After the expanded trade the March relative P&L is −$981,168, only $18,832 inside the budget. A one-sided cost of 4.11 bp, instead of 2 bp, uses that cushion up. The book also gives back part of its gain in a parallel rally and in the flattener.

| Book | Role | Decision |
| --- | --- | --- |
| Current | standing | still_outside_budget |
| Benchmark | reference | reference |
| 10% buy S05Y | proposed | still_outside_budget |
| Expanded buy S05Y | proposed | needs_approval |
| Control 2y/20y | reference | reference |

The benchmark and the 2-year/20-year control are reference books, not trade requests. The control is inside the budget in all six scenarios. That is this control, not a claim about every barbell.

Where the current book's dollars sit in the two breaches (`outputs/scenario_contributions.csv` has every book, bond, and scenario):

| Bond | Steepener | March 2023 |
| --- | ---: | ---: |
| S06M | +185,702 | +142,320 |
| S30Y | −3,852,311 | +994,551 |

Key-rate DV01 by bond and node is in `outputs/kr01_by_bond.csv`. The 20-year and 30-year nodes are about 76% of the current book's KR01.

Contracts and the mandate are synthetic. Discounting uses the Federal Reserve's Gürkaynak–Sack–Wright continuous zeros from off-the-run Treasury coupons, not CMT par yields. The March shock is transplanted onto the July book. Accrued interest is out of scope. This is a static historical-stress review, not a daily backtest, and not a reconstruction of SVB or UK LDI.

Formulas and the decision rule: [docs/method.md](docs/method.md). The 2-year-to-10-year twist versus an earlier six-node stress: [docs/design-history.md](docs/design-history.md). Curve source: [Fed nominal yield curve](https://www.federalreserve.gov/data/nominal-yield-curve.htm), [Treasury tantrum note](https://www.federalreserve.gov/econres/notes/feds-notes/the-treasury-tantrum-of-2023-20240903.html), [March 2023 FOMC minutes](https://www.federalreserve.gov/monetarypolicy/fomcminutes20230322.htm).

```bash
python3 reproduce_case.py
python3 validate_independently.py
python3 -m unittest tests/test_case.py
```
