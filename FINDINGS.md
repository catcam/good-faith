# What four rounds of testing found (2026-10-12)

**The idea:** if a prompt says, before the task, that "I don't know" is a good answer and
inventing is the only real failure, other models will fabricate fewer citations.

**The result: not confirmed.** The framing makes models *say* "I found no source" more
often. It does not make the citations they still give more accurate. Verification is what
catches fabrication, not the framing.

## The rounds

| round | design | outcome |
|---|---|---|
| v1 ([REPORT.md](REPORT.md)) | 144 trials, an LLM judge | Inconclusive. The judge failed validation. |
| v2 ([REPORT_V2.md](REPORT_V2.md)) | 408 trials, mechanical scoring, pre-registered. Citations with web search + code review. | Not significant (citations p = 0.125, code review no difference). Later scorer fixes weakened citations to p = 0.29. |
| v3 ([EXPERIMENT_V3.md](EXPERIMENT_V3.md)) | 2 pilots, 160 trials | Stopped before the main run. With web search, models rarely quote what is not on the page, so there is little to reduce. The pilots exposed three scorer defects. |
| v4 ([REPORT_V4.md](REPORT_V4.md)) | 640 trials, pre-registered. Citations **from memory**, the original case. | No reduction: 1.82 vs 1.61 failed citations per response (p = 0.14). The direction is slightly against the hypothesis. |

## Three things we learned

**1. The framing raises abstention, but the abstention is not selective.**
- Lines saying "no source found":
  - v2: 44 without the framing, 90 with it
  - v4: 290 without the framing, 426 with it
- An exploratory check ([experiments/exploratory/abstention_v4.md](experiments/exploratory/abstention_v4.md)) asked whether models abstain where they would otherwise be wrong. They do not:
  - The share of checkable citations that fail is unchanged: 78.2% vs 78.8%.
  - The extra abstentions do not fall in the model × task cells where the baseline fails most (Spearman ρ = 0.06).
  - Under the framing, models gave *more* checkable citations (2.31 vs 2.06 per response), not fewer. The "no source" lines came on top of the citations, not instead of them.

**2. Without a source at hand, most citations are wrong whatever the prompt.**
- With no web search, about 4 in 5 checkable citations failed: a dead URL, or a quote that is not on the page. Examples:
  - Rust release-announcement URLs with invented dates
  - Nature article IDs that do not exist
  - prices of models no longer listed on the page
  - figures added to real documentation
- This looks less like "inventing to please" and more like a model that does not know which of its memories are wrong. Kindness cannot fix a gap the model cannot see.

**3. Measuring this is harder than it looks.** The automatic scorer marked real quotes as
fabricated in several ways:
- tables hidden behind tabs,
- figures that JavaScript fills in after the page loads,
- editorial "[and]" inserted in a quote,
- "$4.00" vs "$4".

Some of these errors were not evenly spread across conditions. In v2 they made the framing look better than it was. Each defect was found by Claude reading the pages by hand, and each is written up in the round where it was found.

## What this means for the practice

- **Keep the stance, drop the claim.**
  - Telling a model that "I don't know" is welcome costs nothing, and it reliably gets more "I don't know" answers.
  - It is consistent with how you would want to be treated, and some people (the author of this project among them) would extend it on ethical grounds whatever it measured.
  - It is not a fabrication filter, and it should not be sold as one.
- **Verify every checkable claim.** This is the half of the practice that does the work. Without search it catches most citations, and with search it catches the occasional stale or invented one.
- **Give the model a source.** Web search cut failed citations from about 80% of checkable claims (v4) to under 10% (v2 re-scored). That is a much bigger difference than any prompt wording made.

## Honest limits of these tests

- Four open-weight models via OpenRouter.
- One wording per condition.
- English research questions only.
- Claude wrote the tasks and the scorer, and validated the scorer by hand. No human labels.
- The case that started the project was a long multi-turn consultation. These tests are single-turn.

Every prompt, response and per-claim score is in `experiments/`.
