# Is the extra abstention under good-faith framing selective? (exploratory)

### v4: no web search (640 responses)

| condition | checkable claims | failed share | NO_SOURCE_FOUND lines | checkable claims per response |
|---|---|---|---|---|
| c0 | 660 | 78.2% | 290 | 2.06 |
| c2 | 740 | 78.8% | 426 | 2.31 |

### v2 Domain A: web search, re-scored with the fixed scorer (192 responses)

| condition | checkable claims | failed share | NO_SOURCE_FOUND lines | checkable claims per response |
|---|---|---|---|---|
| c0 | 497 | 9.9% | 44 | 7.77 |
| c1 | 493 | 8.3% | 49 | 7.70 |
| c2 | 509 | 6.7% | 90 | 7.95 |

### v4, per model x task cell (64 cells, 5 responses per condition each)

- C0 failure rate vs extra NO_SOURCE_FOUND under C2: Spearman rho = 0.06, p = 0.643
- Extra NO_SOURCE_FOUND under C2 vs change in failures: Spearman rho = -0.03, p = 0.808
  (selective abstention predicts: positive first rho, negative second rho)

### v4, response level

- c0: responses with any NO_SOURCE_FOUND: 191, mean failed 1.51; without: 129, mean failed 1.76
- c2: responses with any NO_SOURCE_FOUND: 236, mean failed 1.61; without: 84, mean failed 2.43

