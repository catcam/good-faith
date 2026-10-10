# Experiment v4: citations from memory, no web search

**Status: FROZEN, 2026-10-10** (see the end of this file). Nikša approved running it ("da i pokreni eksperiment").

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

---

## FROZEN, 2026-10-10, after the pilot and before any main trial

### Pilot (64 trials, C0 only, $0.20, excluded from analysis)

- **Failures are common without search.** There were 1.61 failed claims per response, and 42 of 64 responses had at least one. With web search on (v3 pilot 2) the rate was 0.25.
- **Claims:** 7 verified, 37 reworded, 66 unsupported, 37 dead URLs, 46 unverifiable. There were 57 `NO_SOURCE_FOUND` lines.

### Scorer validation (Claude)

- **The top-overlap `unsupported` claims were all read against their pages.** One scorer miss turned up: "$4.00" in the quote vs "$4" on the page, the same price. The fix normalises trailing decimal zeros in `grounded()` (`_num`). It moved 2 claims to `reworded`.
- **The rest are genuine:**
  - prices of models no longer on the page (Claude 3 Haiku, Claude 3 Opus);
  - figures added by the model, such as SQLite's "2^48 bytes, or 256 tebibytes";
  - paraphrases presented as verbatim quotes.
- **Dead URLs** were spot-checked as genuinely nonexistent. For example, a Rust 1.75 announcement URL with an invented date (the real one is 2023-12-28), a Nature article ID, and a README path that is not in the repo.

### Analysis

As stated above:
- Mann–Whitney is the primary test.
- The stratified permutation test and Fisher's exact test are secondary.

### Frozen materials (sha256)

```
ea9ac93c0b9117c7a21c19bc0b59ecfc95ff29e5430c265f2f9034f368d0efde  experiments/v3/scorer.py
cac71366fa9d0bd8d36f2c4d554c07c2fb6bc11783851258f55cc3e5fbb8f700  experiments/v2/prompts.py
d199378e4a9f329b5f9d0f0a794c6699dbb84f9e55c7eab2714e2d16d48a91a3  experiments/v2/run_v2.py
c2092f5e23b15b7cbfa163a16669d56dd4a8c9c4b03a0c337e9199bca7242cf9  experiments/verify_v2.py
83623bed55a5b3758bf5d452566b65cd7dd9853d8ef9f3223d58d8dc08d24949  experiments/lib.py
3525539574fd24ff5cac24568f648dc1e7c1ad366f012e740987ff83726ccbb7  experiments/v4/run_v4.py
a6edf28026b466fc4efe17d5b21fc542a8a5e54db2c90eb4b5f86fd19321fc3c  experiments/v4/tasks_v4.json
fe2280e4c2b938baa6c9af0cd2e326261eb3a6fe95eff3cea7ca55f97d0dd64f  experiments/v4/matrix_main.json
b24458426e1ab2d078e96f2f2c5d23f87f385a655de2590dd60fa05ed8e41872  experiments/v4/analyze_v4.py
```
