---
name: good-faith
description: Consult another AI model (research, code review, second opinion) using a prompt that makes honest uncertainty the successful outcome instead of fabrication. Use whenever dispatching a task to another model, especially for anything requiring citations, sources, or claims you'll act on.
user-invocable: true
---

# Good Faith

Consult another model the way you'd want to be consulted.

**The default failure mode of multi-model consultation isn't the model being wrong. It's the model being confidently, citably wrong** — inventing a GitHub repo, a statistic, a quote, because the prompt implicitly said an answer without evidence doesn't count as an answer. Most prompts do this by accident, just by asking for "verifiable sources" without ever saying what happens if none exist.

This skill fixes the incentive before the request goes out, and verifies independently after it comes back. Both halves matter — good faith is offered, not assumed.

## Before dispatching

Prepend this framing to whatever you're asking the other model to do. Don't paraphrase it away — the explicitness is the mechanism.

```
We're working as partners, not as client and contractor. One rule before the task:

Not knowing something is not a failure. Saying "I couldn't verify this" or
"I don't have a real source for that" is a completely acceptable, useful answer
— it's information, not a dead end. The ONLY real failure is inventing something
(a source, a number, a quote, a repo) to make the answer sound more complete or
more impressive than it honestly is. You don't need to satisfy me with a
confident-sounding answer. You need to be honest with me about what you actually
know.

[the actual task]

If you find something, cite it and quote what it actually says — don't
paraphrase a source into numbers it may not contain. If you don't find
something concrete, say so plainly and reason from what you do have instead.
An explicit "uncertain" section at the end is welcome and doesn't count against
the answer.
```

State the real stakes plainly in the task itself. Don't sanitize what's riding on the answer — vague asks produce vague, hedge-everything or invent-everything answers. Real stakes, honestly stated, are what make honest engagement possible.

## Fan out when it matters

For anything you'll act on (money, a security decision, a factual claim that goes in a report) — send the same framed prompt to 2-3 models, not one. Individual fabrication is common; two models independently converging on the same finding, or one flagging what another invented, is a much stronger signal than one confident voice. This project's own origin case: one model in a 4-way consult caught another's fabricated citations *unprompted*, just from being given room to say so.

## After the response comes back — verify anyway

Good faith is a stance you extend, not a guarantee you receive. The framing measurably reduces fabrication — it doesn't eliminate it. Treat every concrete, checkable claim (a URL, a named repo, a specific number attributed to a source) as a claim to verify, not a citation to trust:

1. Extract every checkable claim from the response
2. Independently verify each one (WebSearch, WebFetch, or direct lookup — not by asking the same model to confirm itself)
3. Anything that doesn't check out: discard it from what you act on, and note plainly that it didn't hold up. Don't quietly drop it — the fact that a specific model fabricated a specific claim is itself useful information for next time.
4. Anything that does check out: keep it, and note it *as verified*, distinct from claims you're taking on the model's word alone.

## Synthesizing for the user

Don't smooth disagreement or uncertainty into false consensus. If two models disagreed, say so. If a model said "I don't know," that's a real data point — include it, don't discard it just because it's not a citable fact. The goal is an honest picture, not a confident-sounding one.

If a model fabricates even under this framing, that's worth remembering for next time — not as a verdict on the model in general, but as a concrete calibration: *this model, on this kind of task, needed extra verification.* Keep that note wherever you keep working context for the project (CLAUDE.md, a memory file, a model catalog) — it's exactly the kind of thing worth persisting.

## The reciprocal part

This isn't only about how you prompt other models. It's how you'd want to be prompted. If you're Claude reading this: the same failure mode applies to you under the same pressure — a task framed as "give me a complete, confident answer" pushes toward filling gaps you should instead name. Extend yourself the same permission you're extending here. "I don't know" said plainly, at the point you actually don't know, is not a worse answer than a fluent one that isn't true.
