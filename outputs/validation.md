# Independent validation

This check reimplements the curve, the cash flows, DV01, the six scenarios, the five books, turnover, and the one-sided cost with the Python standard library. It does not import the pricing package.

The independent calculation is a consistency check of the implementation. It is not a check against executable Treasury quotes.

Maximum price gap versus `instruments.csv`: 2.842e-14 per 100 face.
Maximum DV01 gap versus `instruments.csv`: 0.000e+00 per 100 face.
Maximum bond scenario P&L gap: 2.842e-14 per 100 face.
Maximum portfolio P&L gap: $8.382e-09.
Maximum relative P&L gap: $8.382e-09.

## Checks

- PASS  usable days: 499
- PASS  prices vs instruments.csv: max abs gap 2.842e-14 per 100
- PASS  DV01 vs instruments.csv: max abs gap 0.000e+00 per 100
- PASS  bond scenario P&L: max abs gap 2.842e-14 per 100
- PASS  current DV01: 50000.00000000
- PASS  current weights sum to 1: 1.0
- PASS  current long only: non-negative
- PASS  benchmark DV01: 50000.00000000
- PASS  benchmark weights sum to 1: 1.0
- PASS  benchmark long only: non-negative
- PASS  candidate_10pct_s05y DV01: 50000.00000000
- PASS  candidate_10pct_s05y weights sum to 1: 1.0
- PASS  candidate_10pct_s05y long only: non-negative
- PASS  candidate_expanded_s05y DV01: 50000.00000000
- PASS  candidate_expanded_s05y weights sum to 1: 1.0
- PASS  candidate_expanded_s05y long only: non-negative
- PASS  control_2y20y DV01: 50000.00000000
- PASS  control_2y20y weights sum to 1: 1.0
- PASS  control_2y20y long only: non-negative
- PASS  weights vs case_results.json: max abs gap 1.110e-16
- PASS  control weights in positions.csv: S02Y 0.74420071, S20Y 0.25579929
- PASS  current turnover: 0.000000000000
- PASS  current cost: 0.000000
- PASS  benchmark turnover: 1.000000000000
- PASS  benchmark cost: 0.000000
- PASS  candidate_10pct_s05y turnover: 0.100000000000
- PASS  candidate_10pct_s05y cost: 4000.000000
- PASS  candidate_expanded_s05y turnover: 0.445543227722
- PASS  candidate_expanded_s05y cost: 17821.729109
- PASS  control_2y20y turnover: 1.000000000000
- PASS  control_2y20y cost: 0.000000
- PASS  portfolio scenario P&L: max abs gap $8.382e-09
- PASS  relative P&L after cost: max abs gap $8.382e-09
- PASS  just-clearing March relative: -1000000.000000

Result: PASS.
