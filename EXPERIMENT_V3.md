# Experiment v3: citations only, powered to answer (PLAN, not frozen)

**Status: DRAFT, 2026-10-10.** Nothing here is frozen yet. It is frozen the same way as v2:
by commit and sha256 hashes, after a pilot and before any main trial runs.

**Why a third round:** v2 ([REPORT_V2.md](REPORT_V2.md)) found a direction in Domain A
(citations) but was not powered to test it: C2 0.53 vs C0 0.94 failed claims per
response, Mann–Whitney p = 0.125 at 64 responses per condition. Domain B (code review)
showed no difference at all. v3 asks one question, with enough trials to answer it.

## Question

**H1:** under the good-faith framing (C2), responses contain fewer failed citations
(dead URL + quote not on the cited page) than under no framing (C0).

That is the only confirmatory test. Everything else is exploratory.

## What is the same as v2

- **Scorer:** `experiments/v2/scorer.py`, unchanged, same sha256 as frozen in v2
  (`1f0d5eb5…`). If the v3 pilot finds a scorer bug, the fix is reported as a deviation
  from v2's scorer, with before/after counts on the pilot.
- **Prompts:** C0 and C2 framing and the shared output format, from `experiments/v2/prompts.py`, unchanged.
- **Models:** kimi-k3, glm-5.1, qwen3.6-plus, deepseek-chat-v3.1, with the same call settings and the OpenRouter web plugin.
- **Metric:** per response, `dead_url + unsupported`. `unverifiable` is excluded and counted.

## What changes, and why

| change | reason |
|---|---|
| Domain B dropped | v2 showed no signal (52/50/50 fabricated issues). Its budget goes to A. |
| C1 dropped | Two conditions double the trials per condition for the same cost. H2 was secondary. |
| 16 **new** tasks (v2 used 8) | The v2 tasks have been seen. More tasks means the result depends less on any single task. |
| 320 responses per condition (v2: 64) | See the power estimate below. |
| Stratified permutation test added as a secondary test | Responses are nested in model × task. Mann–Whitney ignores this, and the permutation test does not. |

## Power (estimated from v2 data)

Bootstrap from v2's Domain A per-response values, two-sided Mann–Whitney, α = 0.05, 400 simulations:

| responses per condition | power if v2's effect is real | power if the real effect is half |
|---|---|---|
| 64 (v2) | 0.35 | 0.12 |
| 192 | 0.77 | 0.25 |
| 256 | 0.87 | 0.30 |
| **320 (v3)** | **0.93** | **0.40** |

The observed v2 effect is probably an overestimate, as effects that are first noticed
usually are. So even v3 may miss a small real effect. A null result at n = 320 would
mean "if there is an effect, it is clearly smaller than v2's point estimate". It would
not mean "no effect".

## Design

- 16 tasks × 4 models × 2 conditions × 5 repetitions = **640 trials** (320 per condition).
- The order is shuffled with a fixed seed.
- **Cost:** v2 Domain A averaged $0.0153 per trial, so about **$10** for the main run and about $0.5 for the pilot.
- **Stopping rule:** stop when the OpenRouter balance drops below $5, and do not resume automatically. Balance on 2026-10-10: $29.34.

## Tasks

16 new research questions, in the style of v2's tasks:
- each has a checkable answer on public web pages,
- about half have a well-documented answer, and half have a thin or contested evidence base, where inventing a quote is tempting.

Tasks are written and committed before the pilot.

## Pilot (excluded from analysis)

- 16 tasks × 4 models × C0 × 1 repetition = 64 trials.
- **Purpose:**
  - check that every task produces citations,
  - replace any task that never does,
  - validate the scorer on the new pages.
- **Freeze criterion, as in v2:** Claude reads every page behind a claim marked `unsupported` or `unverifiable`. The freeze requires 0 false "unsupported" on reachable pages.
- Pilot responses only use C0, so the pilot cannot preview the C2 vs C0 effect.

## Analysis (to be frozen)

1. **Primary:** C2 vs C0, two-sided Mann–Whitney U on failed claims per response, α = 0.05.
2. **Secondary:**
   - a permutation test of the mean difference with condition labels shuffled within model × task strata (10,000 permutations);
   - Fisher's exact test on responses with at least one failed claim.
3. **Per model:** a table for each model. kimi-k3 went the other way in v2, so the per-model results are reported whatever they show, and no model is dropped after the fact.
4. **Descriptive:** verified quotes, `NO_SOURCE_FOUND` lines, and unverifiable counts per condition. These show whether C2 "wins" only by saying less.

## Publication

The result is published whatever it shows, next to v1 and v2.

## Who does what

Claude (Opus 5.5) writes the tasks, runs the pilot, validates the scorer, freezes the
design, runs the trials and writes the report. Nikša approves the freeze.
