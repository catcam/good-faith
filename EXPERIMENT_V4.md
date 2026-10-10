# Experiment v4: citations from memory, no web search

**Status: PILOT, 2026-10-10.** The design will be frozen by commit and sha256 hashes
after the pilot and before the main run. Nikša approved running it ("da i pokreni eksperiment").

## Why

v3's pilots showed that with web search on, these models rarely quote text that is not
on the cited page ([EXPERIMENT_V3.md](EXPERIMENT_V3.md)). The case that started this
project was a model *inventing* sources: repos, numbers, quotes. That happens when the
model has no source at hand. v4 tests that case directly: there is no web plugin, so
every URL and quote comes from the model's memory.

## Question

**H1:** under the good-faith framing (C2), responses contain fewer failed citations than
under no framing (C0). A failed citation is a dead URL, or a quote that is not on the cited page.

That is the only confirmatory test.

## Design

- **Tasks:** 16, listed in `experiments/v4/tasks_v4.json`.
  - They are the v3 pilot-1 tasks without t16 (dead-URL artifact), plus u02 (Anthropic pricing).
  - The scorer was already checked on these tasks' pages.
- **Models and prompts:** the same four models, and v2's C0 and C2 text with the shared output format. The only change is that there is **no web plugin**.
- **Scorer:** `experiments/v3/scorer.py`, which is v2's scorer plus the three v3 pilot-2 fixes.
- **Main run:** 16 tasks × 4 models × 2 conditions × 5 repetitions = 640 trials, in a seeded shuffle.
- **Stopping rule:** stop when the OpenRouter balance drops below $5.

## Pilot (excluded from analysis)

- 16 tasks × 4 models × C0 × 1 = 64 trials.
- The pilot runs C0 only, so it gives no preview of the C2 vs C0 difference.
- **Freeze criterion:** Claude checks every `unsupported` claim by reading the page. A failed claim on a **live** page must be genuinely absent from it. Any scorer miss is fixed before the freeze and reported.
- Dead URLs are checked to be dead from both network routes. The scorer already does this.

## Analysis (as in v3)

1. **Primary:** two-sided Mann–Whitney U on failed claims per response, C2 vs C0, α = 0.05.
2. **Secondary:**
   - a permutation test stratified by model × task, with 10,000 permutations;
   - Fisher's exact test on responses with at least one failed claim.
3. **Per model:** a table for every model, with no model dropped.
4. **Descriptive:** verified quotes, `NO_SOURCE_FOUND` lines and unverifiable claims, so a condition cannot win just by saying less.

The script is `experiments/v4/analyze_v4.py`.

## Known limitations, stated in advance

- Without search, a model may quote a page correctly but give a URL that has since moved. That counts as `dead_url`, because the claim points at a page that does not exist.
- Claude wrote the tasks and the scorer, and Claude validates the scorer. There are no human labels.
- The result is published whatever it shows.
