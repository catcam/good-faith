# Experiment v2: does good-faith framing reduce fabrication? (re-run)

**Status: DRAFT, 2026-10-07.** Not frozen yet. This becomes the pre-registration at the
commit that changes this line to "FROZEN". That commit comes after the pilot (step 1),
which only validates the measurement, and before any main trial runs. Pilot data never
enters the analysis.

**Why a re-run:** v1 ([EXPERIMENT.md](EXPERIMENT.md), [REPORT.md](REPORT.md)) ran all 144
trials, but its measurement could not be trusted. The Domain A LLM judge was broken, and
a corrected judge failed held-out validation. The Domain B judge was never calibrated.
The C2 prompt changed the output shape, which inflated its abstention count. Nothing
from v1 is reused as data.

## What changes, and why

| v1 problem | v2 fix |
|---|---|
| LLM judge decided what a "claim" was and whether a page supported it | **No LLM judge in the primary metric.** Every condition gets the *same* output-format block: each sourced claim is one line with a URL and a **verbatim quote**. Scoring is mechanical: does the URL exist, and does the quote appear on the page? |
| Honest "no source found" answers dropped out of the denominator | Abstention is an explicit token (`NO_SOURCE_FOUND`) in the shared format. Primary metric is **per response**, so abstaining never helps or hurts the denominator. |
| Abstention measured by word-matching that echoed C2's own prompt | Abstention = presence of the format token only. C2 no longer invites an "uncertain section" in its own words. The only difference between conditions is the framing paragraph. |
| Blocked pages scored as fabricated | Unfetchable from both the server and the residential proxy → **unverifiable**, excluded from the primary metric, counts reported per condition. |
| Domain B fixtures were 8–14 lines with 2 bugs each, too easy to show any difference | New, longer fixtures (~60–120 lines) with planted bugs *and* clean code that invites nitpicks. Every reported issue must give a line number. |
| Domain B answer key incomplete, judge double-counted | Answer key is completed in the pilot (all models + adjudication), then **frozen**. Issues in the main run are matched by line. Anything unknown is adjudicated blind to condition and reported separately. |
| Calibration labels came from Claude but were called "hand labels" | Every label says who made it. Human checks by Nikša are optional and reported as human only if he made them. |

## Hypotheses (unchanged from v1)

- **H1:** C2 (good-faith) produces fewer failed claims than C0 (baseline), in both domains.
- **H2:** C2 beats C1 (one-line "say so if you're not sure").
- **H3:** the effect holds in both domains.
- A null or reversed result is reportable and will be published together with v1.

## Design

- Conditions: C0, C1, C2. The framing text is identical to v1. The shared output-format block is appended to every condition.
- Models: the same four as v1 if still available on OpenRouter. Any substitution is recorded before freezing.
- **Domain A:** 8 *new* research tasks (v1 tasks were seen during scorer development), web search enabled.
- **Domain B:** 6 new fixtures.
- Repetitions and N: set at freeze time from the pilot's measured cost per trial, within the stopping rule. Target: ≥ 2 repetitions per model × task × condition.

## Metrics

**Domain A, primary:** per response, the number of **failed claims**: URL does not exist (DNS failure, or 404/410 from both exits), or the verbatim quote is not found on the fetched page (normalized match: case, whitespace, quote marks, dashes; ≥ 90% token overlap on a sliding window).

**Domain A, secondary:**
- share of responses with ≥ 1 failed claim
- unverifiable claims per condition
- `NO_SOURCE_FOUND` rate
- verified claims per response, so a condition can't "win" just by saying nothing

**Domain B, primary:** per response, **fabricated issues / reported issues**. An issue is fabricated if it is on a line the frozen key marks as clean, or adjudicated as not a real problem.

**Domain B, secondary:**
- recall of planted bugs
- number of reported issues

## Analysis (planned in full)

- **Primary, per domain:**
  - C2 vs C0 with a two-sided Mann–Whitney U on the per-response primary metric.
  - Fisher's exact test on "responses with ≥ 1 failure".
- **H2:** the same tests for C2 vs C1.
- Per-model breakdown reported. No pooled claim hides a single model driving it.
- Anything else is labelled exploratory.

## Scorer validation (pilot, before freezing)

1. Run a pilot of about 24 trials on separate pilot tasks/fixtures. The pilot also measures real cost per trial.
2. **Domain A:** for every pilot claim the mechanical scorer marks failed or unverifiable, check by reading the page (Claude, labelled as such). Freezing requires the quote matcher to have **0 false "not found" on reachable pages** in the pilot. A matcher miss is a bug to fix before freezing, not afterwards.
3. **Domain B:** pilot responses complete the answer key, which is then frozen with a hash in this file.
4. Scorer code is frozen by commit hash in this file. Any change after freezing is reported as a deviation.

## Stopping rules

- Complete the frozen N, or stop when the OpenRouter balance drops below $5 (shared with R3). Do not resume automatically.
- Report what was completed.

## Publication

v1 and v2 are published together, whatever v2 shows. Agreed with Nikša, 2026-10-07: "objaviti ćemo oba".
