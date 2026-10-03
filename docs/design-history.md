# Earlier twist

An earlier calculation package used a six-node twist. Both the steepener and the flattener put 0 bp on the 5-year node.

This repository does not use that vector. The twist here is flat outside the segment from 2 years to 10 years and linear in maturity between those nodes:

- steepener: −50 bp at and before 2 years, +100 bp at and beyond 10 years
- flattener: the signs are swapped

On that line the 5-year node is +6.25 bp in the steepener and +43.75 bp in the flattener. The 2-year node is −50 bp or +100 bp. The 10-year, 20-year, and 30-year nodes sit on the long-end level, +100 bp or −50 bp.

Both constructions are defined stresses. They are not the same experiment.

Parallel shocks and the two historical curve changes do not go through the twist. The March 2023 and July–October 2023 results are the same under both definitions. The just-clearing buy-S05Y turnover, 43.5543%, the buffered book at 44.5543%, and the one-sided cost break-even near 4.11 bp are properties of the March shock and the cost, not of the twist nodes.

The earlier package reported twist results, in units of $10,000, of:

| | Current P&L | Benchmark P&L | 10% relative | Expanded relative |
| --- | ---: | ---: | ---: | ---: |
| Steepener | −365.48 | −147.78 | −184.01 | −67.60 |
| Flattener | 189.85 | 24.62 | 145.77 | 78.51 |

Those figures are that package's output. This repository does not retune the full revaluation to them. The calculated results are in `outputs/case_results.json`.
