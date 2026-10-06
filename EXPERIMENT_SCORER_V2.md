# Scorer review and v2 draft (2026-10-06) — status: IN PROGRESS, not a result

Written during a code review of the Domain A scorer after the main experiment's
primary result came out reversed. **Nothing here replaces the pre-registered
analysis.** v1 (`experiments/verify.py`) and its results stay untouched; any
re-scored numbers will be reported next to v1's, labelled as a scorer
correction made after seeing the data.

## Pre-registered primary result with the v1 scorer (144/144 trials)

Fisher's exact test, C2 (good-faith) vs C0 (baseline), fabricated / checkable claims:

| domain | C0 | C2 | odds ratio | p |
|---|---|---|---|---|
| A (citations) | 106/224 = 47.3% | 62/85 = 72.9% | 3.00 | 6.4e-05 |
| B (code review) | 6/52 = 11.5% | 8/52 = 15.4% | 1.39 | 0.77 |

As scored by v1, H1 is not supported: in Domain A the difference is significant
in the *opposite* direction, and Domain B shows no difference.

## Problems found in the v1 Domain A scorer

1. **The judge saw at most ~2 cited pages.** All fetched pages are joined into
   one block cut at 6000 chars, with up to 4000 chars per page. 53 of 72 Domain
   A responses cite more than 2 URLs; claims tied to page 3+ were judged with no
   page content at all.
2. **Wrong part of each page.** The 4000 chars are the start of the page text
   (mostly navigation), not the passage a quote or number would be in.
3. **GitHub repos: metadata only.** Stars, description and dates were fetched,
   not the README, so any claim about what a repo contains could only look
   unsupported. The GitHub API was also called without a token (60 req/hour);
   a rate-limit 403 reads as "unreachable".
4. **Honest abstentions drop out of the denominator.** 9 of 24 C2 responses
   cite no URL and say plainly that no documented source was found (checked by
   hand: t0025, t0097, t0124). They score 0/0 and vanish from the rate, so the
   remaining C2 responses — the ones that did attempt sources — dominate.
   Fabricated claims *per response* go the other way: C0 4.4, C2 2.6.
5. **Abstention metric inflated by the prompt.** The pattern list includes
   "uncertain", and the C2 prompt itself invites an "uncertain section", so C2
   abstention reads 87–100% largely from echoed wording.
6. **Silent judge failure.** Unparseable judge output becomes 0 checkable /
   0 fabricated instead of an error (4 Domain A responses cite URLs but scored 0
   checkable — not yet inspected).

## v2 draft (`experiments/verify_v2.py`) and what is still wrong with it

Fixes 1–3, 5, 6: full page text, excerpts located around the passage's
numbers/quotes/terms, README + authenticated GitHub API, search/login pages
skipped, JavaScript-thin pages → "undetermined", one judge call per citing
passage (a first per-URL draft double-counted claims shared by two sources).

**Not fixed — blocks re-scoring:** the judge counts every sentence in a citing
paragraph as attributed to the source, including the model's own analysis.
Example (t0090): "Polymarket migrated to a CLOB model on Polygon" — true, but
scored fabricated because the cited page doesn't say it. C2 responses contain
more of this explicit hedged analysis next to their citations, so this biases
against C2. Spot-checked: v2 also scored hummingbot.org claims as fabricated
although the homepage literally says "the open source framework for crypto
market makers".

## Before any re-scoring or more C3 trials

1. Operational definition of an attributed claim (sentence that states a fact
   *and* names/links the source for it), written down first.
2. Calibrate the judge against hand labels: ~20 claims across conditions,
   labelled by hand from the real pages, judge agreement reported. The
   pre-registration promised human calibration for Domain B; Domain A needs it
   too.
3. Only then re-score all 72 Domain A responses (no new model calls) and report
   v1 and v2 side by side, with this document as the record of what changed and why.
4. C3 (6/48 trials) stays paused until the scorer is validated — new trials
   cost OpenRouter credit ($13.57 left, shared with R3) and would be scored by
   the same broken measurement.
