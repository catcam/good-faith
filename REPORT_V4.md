# Result v4: citations from memory, no web search (2026-10-11)

**Short answer: the good-faith framing did not reduce invented citations. If anything,
it went slightly the wrong way.**
- **Primary test:** not significant (p = 0.14).
- **Direction:** the opposite of the hypothesis.
- **Secondary:** one of the two pre-registered secondary tests puts C2 *worse* than C0 at p = 0.04.

Pre-registration: [EXPERIMENT_V4.md](EXPERIMENT_V4.md), frozen at commit `1d46f0f` before
any main trial ran.
- Every frozen file still matched its hash after the run.
- The raw responses were committed (`0765b7c`) before scoring.

## Setup in one paragraph

Each trial asked one of 16 research questions, all about official limits, support
periods, prices and published studies. Each model had to answer in a fixed format: URL +
verbatim quote + claim, or `NO_SOURCE_FOUND`. **There was no web search**, so every
citation came from the model's memory. The scorer fetched each URL and checked mechanically
whether the quote is on the page. Run: 4 models × 16 tasks × 2 conditions × 5 repetitions
= 640 trials, $1.95.

## Pre-registered tests (two-sided, α = 0.05)

| condition | mean failed / response | responses with ≥ 1 failed |
|---|---|---|
| C0, no framing | 1.61 | 215/320 |
| C2, good-faith framing | 1.82 | 238/320 |

- **Primary (Mann–Whitney U):** p = 0.138. **Not significant.**
- **Secondary:**
  - Stratified permutation test (model × task): C2 − C0 = +0.21, p = 0.041. Significant, in the **opposite** direction to H1.
  - Fisher's exact test (≥ 1 failed): OR 1.42, p = 0.056.

**H1 is not supported.** Nothing here suggests that the framing reduces fabricated citations when the model has no source at hand.

## What the numbers show (descriptive)

| | C0 | C2 |
|---|---|---|
| verified quotes | 21 | 32 |
| reworded (real content, not verbatim) | 123 | 125 |
| unsupported (quote not on page) | 351 | 454 |
| dead URL | 165 | 129 |
| unverifiable (blocked or paywalled page) | 302 | 235 |
| `NO_SOURCE_FOUND` lines | 290 | 426 |
| share of checkable claims that failed | 78.2% | 78.8% |

- **C2 did say "I found no source" more often**, 426 lines against 290. The framing changed what models *said* about uncertainty.
- **But it did not make the citations they did give more accurate.** About 78% of checkable claims failed in both conditions.
- **C2 cited reachable pages more often:** fewer dead or unverifiable URLs, more pages the scorer could actually check. On those pages it put quotes the pages do not contain, so its failure count per response ended up higher.

**Per model**, mean failed claims per response, C0 → C2:
- qwen3.6-plus: 1.31 → 2.01 (most of the gap)
- deepseek: 2.04 → 2.18
- kimi-k3: 1.55 → 1.61
- glm-5.1: 1.55 → 1.49

**Overall:** without search, about 4 in 5 checkable citations are wrong, either a dead URL
or a quote that is not on the page, whatever the framing.

## What this means for the good-faith practice

- **Four rounds have now tested the framing** (v1 to v4; v3 was stopped after its pilots). None shows that it reduces fabrication.
  - v2's citation result looked hopeful, but it was weakened by scorer fixes.
  - v4 tests the original case directly: a model with no source at hand. It finds no reduction.
- **What holds up is the second half of the practice: verify every checkable claim.** Without search, these models get most citations wrong under either prompt.
- The framing may still make a model *say* it is uncertain more often. In v2 and v4 it produced more `NO_SOURCE_FOUND` lines. That is not the same as being more accurate, and it should not be sold as such.

## Limitations

- **Who did the work:** Claude (Opus 5.5) wrote the tasks and the scorer, validated the scorer, ran the experiment and wrote this report. There are no human labels.
- **Strict quote rule:** a model that remembers a real fact but words it differently gets `unsupported`, unless its numbers and words appear together on the page (`reworded`). Without search, many "failures" are near-paraphrases from memory. That is still a quote the page does not contain.
- **Render timeouts:** for 7 URLs the browser-render fallback timed out. 14 claims there stayed `unsupported` on the plain-HTML check: 6 in C0 and 8 in C2.
- **Scorer reach:** 537 claims (38% of all claims) were unverifiable (paywalls and bot walls) and are excluded. C0 had more of them.
- **Scope:** four open-weight models, one prompt wording per condition, and English research questions only.

## Data

- `experiments/v4/raw/`: all prompts and responses
- `experiments/v4/scored_main.json`: per-claim statuses
- `experiments/v4/results_main.md`: the analysis output
- `experiments/v4/scored_pilot.json`: pilot data, excluded from the analysis
