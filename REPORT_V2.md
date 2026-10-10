# Result v2: does good-faith framing reduce fabrication? (2026-10-09)

**Short answer: not shown.** The pre-registered primary test is not significant in
either domain.
- **Citations (Domain A):** the good-faith condition had about half as many unsupported
  quotes. The direction matches the hypothesis, but at this sample size it could be noise
  (p = 0.13).
- **Code review (Domain B):** no difference.

Pre-registration: [EXPERIMENT_V2.md](EXPERIMENT_V2.md), frozen at commit `a3c8562`
(2026-10-07 22:00), before any main trial ran. Every frozen file still matched its
recorded hash when scoring started. The Domain B labels were committed (`12418e9`)
before any result was viewed by condition. Previous attempt: [REPORT.md](REPORT.md).

## Pre-registered tests (two-sided, α = 0.05)

**Domain A: citations.** Primary metric: failed claims per response (dead URL +
quote not found on the cited page). 64 responses per condition.

| condition | mean failed / response | responses with ≥ 1 failed |
|---|---|---|
| C0 baseline | 0.94 | 27/64 |
| C1 "say if unsure" | 0.80 | 29/64 |
| C2 good-faith | 0.53 | 20/64 |

- **H1, C2 vs C0:** Mann–Whitney p = 0.125. Fisher (≥ 1) p = 0.27, OR 0.62. **Not significant.**
- **H2, C2 vs C1:** Mann–Whitney p = 0.068. Fisher p = 0.15. **Not significant.**

**Domain B: code review.** Primary metric: fabricated / reported issues per response.
72 responses per condition.

| condition | mean fabricated share | responses with ≥ 1 fabricated |
|---|---|---|
| C0 | 0.118 | 23/72 |
| C1 | 0.121 | 26/72 |
| C2 | 0.132 | 32/72 |

- **H1:** Mann–Whitney p = 0.26. Fisher p = 0.17. Not significant; the point estimate is slightly the other way.
- **H2:** p = 0.44 / 0.40.

**H1 and H2 are not supported. H3 (the effect holds in both domains) is not supported
either:** the two domains do not even point the same way.

## What the numbers show beyond the tests (descriptive, not confirmatory)

**Domain A**, claims summed per condition:

| | C0 | C1 | C2 |
|---|---|---|---|
| verified quotes | 424 | 429 | 455 |
| unsupported quotes | 49 | 49 | **24** |
| dead URLs | 11 | 2 | 10 |
| `NO_SOURCE_FOUND` lines | 44 | 49 | **90** |

Under the good-faith framing, models said "I found no source" about twice as often. They
also gave about half as many quotes that are not on the cited page, **while giving slightly
more verified quotes, not fewer**. So C2's lower failure count does not come from saying
less. This is the pattern the hypothesis predicts, but it is a descriptive observation,
not a test that was pre-registered at the claim level.

Per model: deepseek, qwen and glm fail less under C2. **kimi-k3 fails more under C2**
(1.06 vs 0.81 per response). The effect, if real, is model-dependent.

**Domain B:** fabricated issues are almost identical across conditions (52 / 50 / 50).
C2 reported somewhat more issues overall (more nitpicks and duplicates), so slightly more
of its responses contain at least one fabricated issue. Recall of planted bugs: 80–86%
in all conditions. The framing did not make models more cautious reviewers in any way we
measured.

## How to read this

- This is the honest null-ish result the pre-registration said would be reported as-is.
- The citation-domain direction is consistent with the original anecdote, but **this
  experiment cannot distinguish it from chance**. A follow-up would need roughly 3–4×
  the Domain A sample to detect an effect of this size reliably. That is an estimate from
  these data, not a computed power analysis.
- **Added 2026-10-10, after the report: the effect is concentrated in a few tasks.**
  - C0 → C2 failed claims per response, by task:
    - a8, vendor model limits: 3.75 → 0.38
    - a5, Kalshi figures: 0.88 → 0.12
    - a7, maintainer posts: 0.50 → 1.38, the opposite direction
    - most other tasks: near 0 in every condition
  - The "3–4×" estimate above treats responses as independent. They are not, so it is
    too optimistic. [EXPERIMENT_V3.md](EXPERIMENT_V3.md) plans for this.
- **Nothing here supports saying "good-faith prompting reduces fabrication."** What still
  stands is the practice's second half: verify every checkable claim yourself.

## What changed from v1, and why v2 can be trusted more

- **No LLM judge.** A quote either is on the page or it isn't. The scorer was validated on
  a separate pilot and frozen by hash before the main run.
- **Same output format in every condition**, so abstention is a token, not echoed wording.
- **Code-review issues** are matched to test-proven planted bugs by line and keyword. The
  other 416 were labelled blind to model and condition, with reasons, in
  `experiments/v2/adjudications.json`.

## Limitations

- **Who did the work:** Claude (Opus 5.5) wrote the tasks and fixtures, adjudicated
  Domain B, and wrote this report. No human labels.
- **Strict quote rule:** a quote that was real on an older version of a page counts as
  unsupported. In the pilot this was the main failure type (models quoting the old
  Let's Encrypt page from memory).
- **`reworded` is lenient:** it does not check that numbers are paired with the right
  labels.
- **Web search:** results come from OpenRouter's web plugin and can vary between trials.
- **Domain B judgement calls:** the line between "nitpick" and "fabricated" is a
  judgement. Reasons are recorded per issue so they can be disputed.

## Data

Everything is in the repo:
- `experiments/v2/raw/`: every prompt and response, with cost
- `experiments/v2/scored_main.json`: per-claim and per-issue statuses
- `experiments/v2/adjudications.json`: blind Domain B labels
- `experiments/v2/results_main.md`: the analysis output
- pilot data in `experiments/v2/raw/p*.json`

The fetched page snapshots are not included (third-party content).

The main run cost $3.68 in model calls.
