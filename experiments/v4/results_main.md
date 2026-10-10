Completed trials: 640 of 640 (c0 320, c2 320)

| condition | n | mean failed / response | responses with >=1 | verified / reworded / unsupported / dead / unverifiable | NO_SOURCE_FOUND lines |
|---|---|---|---|---|---|
| c0 | 320 | 1.613 | 215/320 | 21 / 123 / 351 / 165 / 302 | 290 |
| c2 | 320 | 1.822 | 238/320 | 32 / 125 / 454 / 129 / 235 | 426 |

- **PRIMARY (H1) C2 vs C0**: Mann-Whitney U = 54583.5, p = 0.1381
- Stratified permutation (model x task), mean diff C2 - C0 = 0.209, p = 0.0414
- Fisher (>=1 failed): 238/320 vs 215/320, OR = 1.42, p = 0.05569

Per model (mean failed / response):

| model | c0 | c2 |
|---|---|---|
| deepseek/deepseek-chat-v3.1 | 2.038 | 2.175 |
| moonshotai/kimi-k3 | 1.550 | 1.613 |
| qwen/qwen3.6-plus | 1.312 | 2.013 |
| z-ai/glm-5.1 | 1.550 | 1.488 |

Total model cost: $1.95
