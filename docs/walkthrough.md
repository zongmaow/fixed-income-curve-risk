# Walkthrough

The case scope is in the [README](../README.md). The calculations below use the 31 July 2023 cash flows.

## One bond

S05Y is a synthetic 4% bullet maturing 31 July 2028. Per 100 face it has ten semiannual cash flows. The first nine are coupons of 2. The last is 102. Time is actual days over 365. Each flow is discounted on the valuation-date continuous zero. There is no accrued interest.

| Item | Value |
| --- | ---: |
| Present value of the first cash flow | 1.945439 |
| Present value of the last cash flow | 82.993486 |
| Dirty price per 100 face | 99.087613 |
| Price, zeros down 1 bp | 99.133091 |
| Price, zeros up 1 bp | 99.042158 |
| Central DV01 per 100 face | 0.04546657 |
| Face for $10 million market value | $10,092,079 |
| Dollar DV01 of that market value | $4,588.52 per bp |

The central DV01 is (99.133091 − 99.042158) / 2. Buying $10 million of the bond is not buying $10 million face. The dirty price is 99.087613 per 100, so $10 million of market value is $10,092,079 face.

Book risk uses market value, not face weight:

\[
\mathrm{DV01}_{\$}=\mathrm{MV}\times\frac{\mathrm{DV01\ per\ 100}}{P}.
\]

That is the same as face/100 times DV01 per 100. In this example the dirty price is 99.087613 per 100, so $10 million of market value is $10,092,079 face and that position has $4,588.52 of dollar DV01. A small long-bond weight can still dominate the book because the 30-year bond's DV01 per dollar of market value is about 35 times the 6-month bond's. In the current book the 30-year weight is 26.42% of market value and 92.58% of bond DV01.

S06M is not a Treasury bill. It is a synthetic 4.75% coupon bond with one payment, 102.375, on 31 January 2024. About 74% of market value in that bond is not 74% cash. Its dollar DV01 is about $3,709 per bp. The 30-year holding is about $46,291 per bp. Together they are the $50,000 per bp mandate.

## The same total DV01

The current book and the benchmark are both solved to $50,000 per bp of parallel DV01. The first-order P&L of a parallel 100 bp rise is therefore −$5,000,000 on each book: 100 times the matched DV01.

Under the parallel 100 bp rise, full revaluation gives losses of $4,488,675 for the current book and $4,842,174 for the benchmark. The difference comes from convexity and higher-order effects: the current book's analytic convexity is 111.54 years², compared with 32.37 for the benchmark. Matching first-order DV01 therefore does not match full-revaluation P&L.

## Where along the curve

A non-parallel shock is a different question. The same $50,000 per bp does not pin down how that risk sits by maturity. Key-rate DV01 splits the book across 0.5, 2, 5, 10, 20, and 30 years. On the current book the 20-year and 30-year nodes are 75.87% of KR01. The benchmark holds none of S06M, S20Y, or S30Y. Same total exposure, different maturity risk.

For the twist defined in [method.md](method.md), the six nodes represent the shock exactly, so the gap between the node approximation and full revaluation is convexity and higher order. For a historical move they do not. The March current-book figures in [method.md](method.md) are the case where the node approximation is numerically closer than the cash-flow approximation, because the representation gap and the higher-order gap offset.

## Budget, cost, and who may approve

Relative P&L is the book's full revaluation, minus a one-time cost if the book is a candidate, minus the benchmark. The budget is −$1 million. There is no absolute-loss limit.

| Shock | Current book's own P&L | Relative to the benchmark | Inside −$1 million? |
| --- | ---: | ---: | --- |
| 8–13 March 2023, transplanted | +1,136,871 | −1,820,199 | No |
| 31 July–19 October 2023 | −4,142,728 | −130,498 | Yes |

The March book makes money and still misses the relative budget. The July–October book loses about $4.14 million and does not miss this budget. Passing the relative budget does not mean the client has no view on a $4.14 million loss.

A 10% buy of the 5-year, financed to hold DV01, trades $20 million gross and costs $4,000 at 2 bp each side. The trade reduces both breaches, but the March and steepener scenarios still exceed the $1 million relative-loss limit. March is still about −$1.63 million relative. The steepener is still about −$1.73 million. That trade is inside routine authority and outside the budget.

The smallest 5-year buy in the six-name family that clears all six scenarios is 43.5543% turnover. The shown book is 44.5543%, with about $17,822 of illustrative cost. It clears under the stated assumptions. Turnover is above 10%, so it needs manager and risk approval. The tightest cushion is $18,832. Convexity falls to 76.28 years², and some of the gain in the parallel rally and the flattener is given up.

The cost, turnover, and cushion comparison is in [cushion.md](cushion.md).
