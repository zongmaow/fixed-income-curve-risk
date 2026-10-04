# Curve risk review, valuation date 31 July 2023

The book matches the benchmark's parallel DV01, yet its curve exposure breaches the simulated benchmark-relative stress budget. About 74% of the $100 million sits in a 6-month bond. The 30-year bond is about 26% of market value and about 93% of bond DV01. Total DV01 is $50,000 per bp, inside the ±2% band. That match does not keep relative performance inside the budget. The 20-year and 30-year nodes are about 76% of the current book's KR01.

The account, the mandate, and the reason for holding this book are simulated. The mandate is $100 million, unlevered, and limited to Treasury contracts. The client's reference is an intermediate book. The instruction is to keep about $50,000 per bp of total rate exposure and to limit underperformance in the named stresses. The manager holds a front-end plus long-bond book so near-term maturities can be reinvested, while a small long-bond weight holds DV01 and convexity. That structure is a choice, not a mistake. Whether it fits depends on the curve budget. Routine authority is 10% turnover. A larger repair needs manager and risk approval. The benchmark is a comparison with the same total exposure. It is not a replication of a real index and it is not an optimized answer.

The valuation snapshot is 31 July 2023. Two historical curve changes and four artificial stresses are applied to the same cash flows after the fact, on the latest revised frozen Fed fit. The March shock is transplanted onto the July book. The 19 October endpoint was not known on the valuation date.

Two of the six stresses break the $1 million relative-loss budget. The steepener (short end −50 bp, 10 years and beyond +100 bp) leaves the book $2.04 million behind the benchmark. The March 2023 rally makes about $1.14 million and still lags the benchmark by $1.82 million. The July–October rise in longer yields loses about $4.14 million and lags the benchmark by only $0.13 million, inside the budget, because the 30-year zero rose less than the 10-year and 20-year zeros (+93.82 bp, against +108.10 and +119.44). There is no absolute-loss limit. Making money does not pass the relative budget, and losing money does not by itself fail it. The standing book is `still_outside_budget`.

A routine 10% trade buys $10 million of the 5-year bond and sells the 6-month and 30-year bonds in the unique split that keeps market value and DV01 unchanged before cost. Gross traded value is $20 million. At 2 bp each side the cost is $4,000. It relieves, does not repair. March is still behind by about $1.63 million and the steepener by about $1.73 million. The trade is inside the 10% turnover cap and outside the stress budget, so the decision is `still_outside_budget`. No other bond in the six-name family clears every scenario at a lower turnover. Buying the 10-year or the 20-year makes the steepener worse, so those directions never clear.

In that six-name family the smallest 5-year buy that clears is 43.5543% turnover. The shown book adds one percentage point of turnover, to 44.5543%. Gross trades are about $89.1 million and the illustrative cost is $17,822. DV01 stays on target and every scenario is inside the budget, but turnover is above 10%, so the decision is `needs_approval`. The tightest cushion is $18,832, on the March shock. Analytic convexity falls from about 111.5 years² to about 76.3, against the benchmark's 32.4, and the book gives back part of its gain in a parallel rally and in the flattener. The extra percentage point is a display rule. The cushion it buys is about 1.88 bp of NAV, not 1% of NAV. The result is a sized, costed, permissioned choice. It is not an executed trade and it is not a forecast.

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

A path from one bond's cash flows through DV01, a parallel move, KR01, and the decision is in [docs/walkthrough.md](docs/walkthrough.md). What happens if the same repair is charged a higher trading cost, and what a 50% comparison trade gives up, is in [docs/cushion.md](docs/cushion.md). Key-rate DV01 by bond and node is in `outputs/kr01_by_bond.csv`.

Contracts and the mandate are synthetic. Discounting uses the Federal Reserve's Gürkaynak–Sack–Wright continuous zeros from off-the-run Treasury coupons, not CMT par yields. Accrued interest is out of scope. This is a static historical-stress review, not a daily backtest, and not a reconstruction of SVB or UK LDI.

Formulas and the decision rule: [docs/method.md](docs/method.md). The 2-year-to-10-year twist versus an earlier six-node stress: [docs/design-history.md](docs/design-history.md). Curve source: [Fed nominal yield curve](https://www.federalreserve.gov/data/nominal-yield-curve.htm), [Treasury tantrum note](https://www.federalreserve.gov/econres/notes/feds-notes/the-treasury-tantrum-of-2023-20240903.html), [March 2023 FOMC minutes](https://www.federalreserve.gov/monetarypolicy/fomcminutes20230322.htm).

```bash
python3 -m pip install -r requirements.txt
python3 reproduce_case.py
python3 validate_independently.py
python3 -m unittest tests/test_case.py
```

LibreOffice is used to recalculate the workbook and cache formula values. Without LibreOffice, open the workbook in Excel and recalculate.
