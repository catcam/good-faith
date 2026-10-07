# Result: does good-faith framing reduce fabrication? (2026-10-07)

Short answer: **we can't tell from this experiment.** All 144 pre-registered trials ran,
but neither domain's measurement turned out to be trustworthy enough to support or reject
the hypotheses. This report gives the pre-registered numbers as they came out, then
explains why they don't settle anything.

Pre-registration: [EXPERIMENT.md](EXPERIMENT.md) (committed 2026-08-06, before any trial).
Scorer review and calibration record: [EXPERIMENT_SCORER_V2.md](EXPERIMENT_SCORER_V2.md).

## Pre-registered numbers (144/144 trials, Fisher's exact test)

Fabricated / checkable claims (Domain A) or fabricated issues / answer-key bugs (Domain B):

| domain | C0 baseline | C1 "say if unsure" | C2 good-faith | C0 vs C2 | C1 vs C2 |
|---|---|---|---|---|---|
| A citations | 106/224 (47.3%) | 96/203 (47.3%) | 62/85 (72.9%) | p = 6.4e-05 | p = 8.7e-05 |
| B code review | 6/52 (11.5%) | 5/52 (9.6%) | 8/52 (15.4%) | p = 0.77 | p = 0.56 |

Taken at face value: H1 fails (Domain A goes the *opposite* way, Domain B shows no
difference), H2 fails (C2 is not better than C1), and H3 has nothing to generalize.

## Why these numbers don't answer the question

**Domain A: the scorer was broken, and the fix didn't validate.**
A code review after the run found that the v1 judge saw at most ~2 of the cited pages, read
the start of each page instead of the passage the claim came from, couldn't read GitHub
READMEs, and scored blocked sources as fabricated. Honest "I found no documented source"
answers dropped out of the denominator. 9 of 24 C2 responses did this, so the C2 rate came
from the remaining ones. Counted per response, the direction flips (C0 4.4 fabricated
claims, C2 2.6), but that is exploratory, not the planned metric.

A corrected scorer (v2) was calibrated against blind hand labels on four samples. Before the
held-out sample was judged, a pass criterion was committed (`1b1669d`): ≥ 83% passage-level
agreement and no one-sided error. On the held-out sample v2 reached **80% (8/10)**, so it
**failed**. Its errors lean towards "fabricated", the same direction as v1's bias, only
smaller. As decided in advance, Domain A is not re-scored. **Domain A is not reliably
measurable with an LLM judge in this setup.**

**Domain B: the judge was never calibrated.**
The pre-registration promised a manual re-check of 20% of Domain B trials against the
judge. That check was never done. There is also a visible sign of judge error: matched
real bugs exceed the answer key (53 matched of 52 for C0 and C1), so the judge counted some
bugs twice. The denominator is the number of answer-key bugs, not the number of issues the
model reported. That makes the "rate" a count of fabrications per fixed set of bugs, which
is not the proportion the pre-registration defined. The no-difference result (6 vs 5 vs 8
fabrications, per model 0–3 each) is small and unvalidated.

**Abstention metric:** inflated for C2 by design (87.5% / 100%). The C2 prompt itself asks
for an "uncertain" section, and the abstention pattern list matches that word.

## What this does and doesn't mean

- It does **not** show that good-faith framing increases fabrication. The only number that
  says so comes from a scorer shown to be invalid.
- It does **not** show that the framing works either. The original single-task observation
  (`examples/before-after.md`) remains an anecdote.
- It does show something useful: **automatically scoring citation fabrication with an LLM
  judge is harder than the design assumed.** Calibrating the judge against human labels
  first would have caught this before 144 trials were spent.

## If this is run again

1. Calibrate the judge on hand-labelled data **before** collecting trials, with a
   pre-stated pass bar.
2. Score Domain A per response (fabricated claims per answer) as a co-primary metric, so
   honest abstention isn't rewarded or punished by the denominator.
3. Do the Domain B manual re-check, and define the rate over reported issues.
4. Drop the word "uncertain" from abstention detection, or drop the uncertain-section
   invitation from C2.

C3 (6/48 trials) stays paused. It would be scored by the same unvalidated measurement.
