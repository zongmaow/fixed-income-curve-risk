# Method

Valuation date: 31 July 2023. Discounting uses the Federal Reserve Gürkaynak–Sack–Wright Svensson zero curve for that date. Shocks are added to the zero curve. The six Svensson parameters are an input, not a risk factor.

## Zero curve

Maturity \(n\) is in years. The Fed parameters produce a continuously compounded zero yield in percent:

\[
y(n)=\beta_0+\beta_1\frac{1-e^{-n/\tau_1}}{n/\tau_1}+\beta_2\left[\frac{1-e^{-n/\tau_1}}{n/\tau_1}-e^{-n/\tau_1}\right]+\beta_3\left[\frac{1-e^{-n/\tau_2}}{n/\tau_2}-e^{-n/\tau_2}\right].
\]

The discount rate is \(z(n)=y(n)/100\). On 31 July 2023, \(\tau_1\) and \(\tau_2\) are almost equal and \(\beta_2\), \(\beta_3\) are large and opposite in sign. The zero function is still evaluated as written. Parameters are not bumped.

## Cash flows and price

Contracts accrue from the valuation date. Accrued interest is zero, so the clean price equals the dirty price. The first coupon is 31 January 2024. Later coupons are calendar semi-annual month-ends through maturity. The coupon each period is the annual coupon divided by 2, per 100 face. Principal is repaid at maturity.

Time is actual days over 365:

\[
T=\frac{\text{payment date}-\text{valuation date}}{365}.
\]

There is no holiday calendar and no settlement lag. The dirty price per 100 face is

\[
P=\sum_i \mathrm{CF}_i\,e^{-z(T_i)T_i}.
\]

## DV01 and key rates

Parallel DV01 is the central difference of a shift of the whole zero curve:

\[
\mathrm{DV01}=\frac{P(z-1\,\mathrm{bp})-P(z+1\,\mathrm{bp})}{2},\qquad 1\,\mathrm{bp}=0.0001.
\]

Positive DV01 is the price decline when zeros rise. Portfolio DV01 in dollars uses market value, not face weight:

\[
\mathrm{DV01}_{\mathrm{book}}=\sum_i \mathrm{MV}_i\cdot\frac{\mathrm{DV01}_i}{P_i}.
\]

Key-rate nodes are 0.5, 2, 5, 10, 20, and 30 years. The weight on node \(k\) is a tent: 1 at that node, 0 at the neighbouring nodes, linear in maturity between them, and the weights sum to 1. A cash flow before 0.5 years, or beyond 30 years, is assigned entirely to the nearest end node. The 30-year bond's maturity is slightly past 30 years on an ACT/365F count, so that principal payment loads on the 30-year node.

KR01 uses the same central ±1 bp difference, applied to one tent at a time. Summed KR01 is not algebraically identical to parallel DV01, because the finite difference does not commute with the split, but the gap is negligible at a 1 bp step.

Analytic duration and convexity, from the unshocked present values, are

\[
D=\frac{\sum_i T_i\,\mathrm{PV}_i}{P},\qquad C=\frac{\sum_i T_i^2\,\mathrm{PV}_i}{P}.
\]

## Scenarios

A scenario replaces \(z(T)\) with \(z_{2023\text{-}07\text{-}31}(T)+\Delta z(T)\) and reprices the same cash flows. Nothing is earned in carry, roll-down, or coupon income, and time does not pass.

Parallel shocks are \(\Delta z=\pm 0.01\).

The steepener and the flattener are linear in maturity between the 2-year and 10-year nodes and flat outside that segment:

\[
\begin{aligned}
s_{\mathrm{steep}}(T)&=
\begin{cases}
-50 & T\le 2\\
-50+150\cdot(T-2)/8 & 2<T<10\\
+100 & T\ge 10
\end{cases}\\
s_{\mathrm{flat}}(T)&=
\begin{cases}
+100 & T\le 2\\
+100-150\cdot(T-2)/8 & 2<T<10\\
-50 & T\ge 10
\end{cases}
\end{aligned}
\]

with \(s\) in basis points and \(\Delta z=s\times 10^{-4}\). Short and long yields move in opposite directions. These are not bear steepeners or bull flatteners.

At the key-rate nodes the steepener is \((-50,-50,+6.25,+100,+100,+100)\) bp. Because that vector lies on the same piecewise-linear shape as \(s(T)\), rebuilding the shock from key-rate tents reproduces \(s(T)\) exactly. It does not reproduce a historical \(\Delta z(T)\).

Historical shocks use the full fitted curve, not the six nodes:

\[
\Delta z(T)=z_{\mathrm{end}}(T)-z_{\mathrm{start}}(T).
\]

The March 2023 change is applied to the July contracts. That is a transplanted scenario.

## Two first-order approximations

Node approximation, with \(s_k\) the scenario shock in basis points at node \(k\):

\[
\Delta P \approx -\sum_k \mathrm{KR01}_k\, s_k.
\]

Cash-flow approximation, using the actual \(\Delta z\) at each payment time:

\[
\Delta P \approx \sum_i -T_i\,\mathrm{PV}_i\,\Delta z(T_i).
\]

For a parallel move, or for the twist defined above, the node shocks represent \(\Delta z(T)\) exactly, so the gap between the node approximation and full revaluation is convexity and higher order. For a historical move, the six nodes do not represent \(\Delta z(T)\). The gap versus full revaluation then mixes that representation error with convexity. Calling the whole node gap "convexity" is not right.

The cash-flow approximation uses the exact shock at each payment time and removes the node representation error. Its remaining gap reflects higher-order revaluation effects, but it is not necessarily numerically closer to full revaluation: representation and higher-order errors can offset in the node approximation.

On the current book, under the March 2023 shock transplanted onto the July contracts, the three P&Ls are:

| Method | P&L | Full revaluation minus this |
| --- | ---: | ---: |
| Full revaluation \(F\) | +1,136,871.10 | |
| Node KR01 approximation \(K\) | +1,135,463.50 | +1,407.61 |
| Cash-flow approximation \(L\) | +1,117,369.00 | +19,502.10 |

\(F - K = (F - L) + (L - K)\). The cash-flow gap is +19,502.10. \(L - K\), −18,094.50, is mainly the node-representation gap and includes a small finite-difference discrepancy between summed KR01 and the cash-flow derivative. They offset, and the node approximation is the closer of the two here: 19,502.102 + (−18,094.497) = 1,407.605, which is \(F - K\) before rounding to the cent. A small residual does not, by itself, show that the node story is the right split.

## Books, turnover, cost

Initial NAV is \$100,000,000. Weights are market-value weights. Face is \(\mathrm{MV}/P\times 100\).

The current book and the 2-year/20-year control book each solve two weights so that parallel DV01 is \$50,000 per bp. The benchmark fixes 15% / 30% / 20% in the 3-year / 5-year / 7-year bonds and solves the 2-year and 10-year weights for the same DV01. S06M, S20Y, and S30Y are zero in the benchmark.

A routine candidate of turnover \(u\) buys market value \(u\times\mathrm{NAV}\) of one bond \(b\) from \{S02Y, S03Y, S05Y, S07Y, S10Y, S20Y\} and sells S06M and S30Y. Let \(d_i\) be DV01 per dollar of market value. The sale weights that keep market value and parallel DV01 unchanged are

\[
\Delta w_{\mathrm{S06M}}=-u\frac{d_b-d_{\mathrm{S30Y}}}{d_{\mathrm{S06M}}-d_{\mathrm{S30Y}}},\qquad
\Delta w_{\mathrm{S30Y}}=-u-\Delta w_{\mathrm{S06M}}.
\]

Turnover is

\[
u=\frac{0.5\sum_i |\Delta \mathrm{MV}_i|}{\mathrm{NAV}}.
\]

Gross traded market value, buys plus sells, is also reported. The illustrative cost is 2 bp of buys and 2 bp of sells, so \(0.0002\times(\text{buys}+\text{sells})\). It is not a historical bid–ask.

Relative P&L is the book's full-revaluation P&L, minus that one-time cost when the book is a candidate, minus the benchmark's full-revaluation P&L. The benchmark, the current book, and the control book are not charged. The budget is an underperformance of \$1,000,000, which is 1% of initial NAV. There is no absolute-loss limit.

Along the buy-S05Y direction, \(u^\star\) is the smallest turnover that puts every scenario inside the budget after cost, subject to non-negative weights. The expanded book uses \(u^\star+0.01\). The residual cushion is the tightest scenario's distance to −\$1,000,000. Raising the one-sided cost rate until that cushion is zero gives the break-even cost in basis points.

## Decision

The same predicates are used in `src/decision.py` and on the Portfolio sheet.

- `portfolio_valid`: every weight is finite and at least zero, and the weights sum to 1.
- `dv01_within_mandate`: parallel DV01 is within ±2% of $50,000 per bp, tested as abs(DV01 − 50000) <= 50000 × 0.02 + 1e-6. The 1e-6 dollars per bp is numerical dust, not a wider risk limit.
- `stress_budget_pass`: every named scenario's relative P&L, after that book's one-time cost, is at least −$1,000,000. No relative series means not a pass.
- `routine_authority`: turnover versus the current book is at or under the cap in Inputs!B7 (10% of NAV). Zero turnover is inside the cap.

Reference books (the benchmark and the 2-year/20-year control) are not trade requests. Their decision is `reference`. For a standing book or a proposed trade the decision is `invalid_portfolio`, then `still_outside_budget`, then `needs_approval`, then `executable_within_authority`, in that order.
