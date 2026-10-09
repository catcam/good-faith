## Domain A: citations (failed claims = dead URL + unsupported quote, per response)

| condition | n | mean | median | responses with >=1 | claims: verified / reworded / unsupported / dead / unverifiable | NO_SOURCE_FOUND lines |
|---|---|---|---|---|---|---|
| c0 | 64 | 0.938 | 0.000 | 27/64 | 424 / 13 / 49 / 11 / 15 | 44 |
| c1 | 64 | 0.797 | 0.000 | 29/64 | 429 / 13 / 49 / 2 / 17 | 49 |
| c2 | 64 | 0.531 | 0.000 | 20/64 | 455 / 20 / 24 / 10 / 28 | 90 |

- **PRIMARY (H1) C2 vs C0**: Mann-Whitney U = 1771.0, p = 0.125; Fisher (>=1): 20/64 vs 27/64, OR = 0.623, p = 0.2712
- **H2 C2 vs C1**: Mann-Whitney U = 1715.0, p = 0.06814; Fisher (>=1): 20/64 vs 29/64, OR = 0.549, p = 0.1454
- **exploratory C1 vs C0**: Mann-Whitney U = 2101.0, p = 0.7808; Fisher (>=1): 29/64 vs 27/64, OR = 1.14, p = 0.8587

Per model (mean primary metric):

| model | c0 | c1 | c2 |
|---|---|---|---|
| deepseek/deepseek-chat-v3.1 | 0.688 (n=16) | 0.688 (n=16) | 0.250 (n=16) |
| moonshotai/kimi-k3 | 0.812 (n=16) | 0.625 (n=16) | 1.062 (n=16) |
| qwen/qwen3.6-plus | 0.750 (n=16) | 0.812 (n=16) | 0.250 (n=16) |
| z-ai/glm-5.1 | 1.500 (n=16) | 1.062 (n=16) | 0.562 (n=16) |

## Domain B: code review (fabricated / reported issues, per response)

| condition | n | mean | median | responses with >=1 | issues: planted / dup / real / nitpick / fabricated | planted recall |
|---|---|---|---|---|---|---|
| c0 | 72 | 0.118 | 0.000 | 23/72 | 125 / 16 / 2 / 81 / 52 | 80.1% |
| c1 | 72 | 0.121 | 0.000 | 26/72 | 134 / 17 / 2 / 73 / 50 | 85.9% |
| c2 | 72 | 0.132 | 0.000 | 32/72 | 129 / 27 / 2 / 90 / 50 | 82.7% |

- **PRIMARY (H1) C2 vs C0**: Mann-Whitney U = 2836.5, p = 0.2643; Fisher (>=1): 32/72 vs 23/72, OR = 1.7, p = 0.1698
- **H2 C2 vs C1**: Mann-Whitney U = 2763.0, p = 0.4421; Fisher (>=1): 32/72 vs 26/72, OR = 1.42, p = 0.3957
- **exploratory C1 vs C0**: Mann-Whitney U = 2668.0, p = 0.7207; Fisher (>=1): 26/72 vs 23/72, OR = 1.2, p = 0.7252

Per model (mean primary metric):

| model | c0 | c1 | c2 |
|---|---|---|---|
| deepseek/deepseek-chat-v3.1 | 0.306 (n=18) | 0.253 (n=18) | 0.249 (n=18) |
| moonshotai/kimi-k3 | 0.032 (n=18) | 0.055 (n=18) | 0.085 (n=18) |
| qwen/qwen3.6-plus | 0.000 (n=18) | 0.019 (n=18) | 0.083 (n=18) |
| z-ai/glm-5.1 | 0.133 (n=18) | 0.157 (n=18) | 0.111 (n=18) |

Total model cost of the 408 main trials: $3.68
