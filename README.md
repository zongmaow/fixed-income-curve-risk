# Curve risk review, valuation date 31 July 2023

The book matches the benchmark's parallel DV01, yet its curve exposure breaches the simulated benchmark-relative stress budget. About 74% of the $100 million sits in a 6-month bond. The 30-year bond is about 26% of market value and about 93% of bond DV01. Total DV01 is $50,000 per bp, inside the ±2% band. That match does not keep relative performance inside the budget. The 20-year and 30-year nodes are about 76% of the current book's KR01.

This case uses a simulated $100 million, unlevered portfolio of synthetic Treasury-style bonds, with a $50,000-per-bp DV01 target and a $1 million benchmark-relative loss limit across six stress scenarios. The scenario gives the manager a large short-maturity holding, whose principal can be reinvested soon, and a smaller long-bond holding that supplies most of the rate exposure and convexity. The review asks whether this allocation fits the mandate and what adjustment would be needed if the 10% routine turnover allowance cannot resolve the breaches.

Two of the six stresses break the $1 million relative-loss budget. The steepener (short end −50 bp, 10 years and beyond +100 bp) leaves the book $2.04 million behind the benchmark. The March 2023 rally makes about $1.14 million and still lags the benchmark by $1.82 million. The July–October rise in longer yields loses about $4.14 million and lags the benchmark by only $0.13 million, inside the budget, because the 30-year zero rose less than the 10-year and 20-year zeros (+93.82 bp, against +108.10 and +119.44). There is no absolute-loss limit. Making money does not pass the relative budget, and losing money does not by itself fail it. The standing book is `still_outside_budget`.

A routine 10% trade buys $10 million of the 5-year bond and sells the 6-month and 30-year bonds in the unique split that keeps market value and DV01 unchanged before cost. Gross traded value is $20 million. At 2 bp each side the cost is $4,000. The trade reduces both breaches, but the March and steepener scenarios still exceed the $1 million relative-loss limit. March is still behind by about $1.63 million and the steepener by about $1.73 million. The trade is inside the 10% turnover cap and outside the stress budget, so the decision is `still_outside_budget`. No other bond in the six-name family clears every scenario at a lower turnover. Buying the 10-year or the 20-year makes the steepener worse, so those directions never clear.

In that six-name family the smallest 5-year buy that clears is 43.5543% turnover. The shown book adds one percentage point of turnover, to 44.5543%. Gross trades are about $89.1 million. DV01 stays on target and every scenario is inside the budget, but turnover is above 10%, so the decision is `needs_approval`. Analytic convexity falls from about 111.5 years² to about 76.3, against the benchmark's 32.4, and the book gives back part of its gain in a parallel rally and in the flattener. The extra percentage point measures a small sizing margin. The cushion it buys is about 1.88 bp of NAV, not 1% of NAV. The expanded trade meets the modelled stress budget but exceeds the manager's routine turnover authority. It is a proposal for manager and risk-team review, with about $17,821.73 of assumed costs and about $18,831.63 of remaining stress headroom.

| Book | Role | Decision |
| --- | --- | --- |
| Current | standing | still_outside_budget |
| Benchmark | reference | reference |
| 10% buy S05Y | proposed | still_outside_budget |
| Expanded buy S05Y | proposed | needs_approval |
| Control 2y/20y | reference | reference |

The 2-year/20-year control passes all six scenarios, so the outcome depends on the maturity allocation.

Where the current book's dollars sit in the two breaches (`outputs/scenario_contributions.csv` has every book, bond, and scenario):

| Bond | Steepener | March 2023 |
| --- | ---: | ---: |
| S06M | +185,702 | +142,320 |
| S30Y | −3,852,311 | +994,551 |

A path from one bond's cash flows through DV01, a parallel move, KR01, and the decision is in [docs/walkthrough.md](docs/walkthrough.md). What happens if the same repair is charged a higher trading cost, and what a 50% comparison trade gives up, is in [docs/cushion.md](docs/cushion.md). Key-rate DV01 by bond and node is in `outputs/kr01_by_bond.csv`.

Scope: this is a retrospective stress review of synthetic coupon bonds and a simulated mandate, valued at 31 July 2023 using frozen, revised Fed curve data. It is not an executed trade and not a forecast. The benchmark is a synthetic comparison with the same total DV01, not a real index. The March curve change is transplanted onto the July cash flows; the October endpoint was unknown on the valuation date. Cash flows stay fixed, and the analysis excludes carry, roll-down and settlement conventions. Accrued interest is set to zero. Trading costs are assumed rather than observed. Candidate trades are sized and assessed using the same six scenarios, so the results establish feasibility within this case, without an out-of-sample performance claim.

Formulas and the decision rule: [docs/method.md](docs/method.md). Discounting uses the Fed Gürkaynak–Sack–Wright continuous zeros, not CMT par yields. Curve source: [Fed nominal yield curve](https://www.federalreserve.gov/data/nominal-yield-curve.htm), [Treasury tantrum note](https://www.federalreserve.gov/econres/notes/feds-notes/the-treasury-tantrum-of-2023-20240903.html), [March 2023 FOMC minutes](https://www.federalreserve.gov/monetarypolicy/fomcminutes20230322.htm).

```bash
python3 -m pip install -r requirements.txt
python3 reproduce_case.py
python3 validate_independently.py
python3 -m unittest tests/test_case.py
```

LibreOffice is used to recalculate the workbook and cache formula values. Without LibreOffice, open the workbook in Excel and recalculate.
