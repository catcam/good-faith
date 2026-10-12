# good-faith

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23321654.svg)](https://doi.org/10.5281/zenodo.23321654)

**Consult other AI models the way you'd want to be consulted, with uncertainty welcomed, and then verify every claim anyway. Tested four times: the framing makes models admit uncertainty more often, but it does not make their citations more accurate. Verification is the part that works.**

A skill for [Claude Code](https://claude.ai/code) (portable to any agent that can be given a system prompt).

---

## The Idea

You ask a model to research something and cite real sources. It comes back with a confident answer, a specific statistic, a named GitHub repository, a quote in quotation marks. Some of it is real. Some of it isn't. Nothing in the tone tells you which is which. You find out by checking, if you check at all.

This project started from a hypothesis: the prompt creates an incentive to invent. "Find verifiable sources" has only one way to fail if you never say what an acceptable answer looks like when nothing verifiable exists, and that is coming back empty-handed. So say it explicitly, before the task: not knowing is a good answer, and the only real failure is inventing something.

## What Testing Showed

We tested that hypothesis four times, with pre-registered designs and mechanical scoring, and published every result. **Summary: [FINDINGS.md](FINDINGS.md).**

- **The framing reliably makes models say "I found no source" more often.**
- **It does not make the citations they still give more accurate.** Without web search, about 78% of checkable citations failed with or without the framing (v4, 640 trials).
- **What actually catches fabrication is verification.** Giving the model a real source (web search) helps far more than any wording.

Detail by round:
- **v1** ([REPORT.md](REPORT.md)): inconclusive. The LLM judge failed validation.
- **v2** ([REPORT_V2.md](REPORT_V2.md)): 408 trials, not significant.
  - Citations: p = 0.125, and p = 0.29 after scorer fixes.
  - Code review: no difference.
- **v3** ([EXPERIMENT_V3.md](EXPERIMENT_V3.md)): stopped after its pilots. With web search, there was little fabrication left to reduce.
- **v4** ([REPORT_V4.md](REPORT_V4.md)): citations from memory, the original case. 640 trials, **no reduction**: 1.82 vs 1.61 failed citations per response, p = 0.14.

**Status:** the four rounds reported here are complete and their results are final. The project itself continues: the next questions are whether a long, multi-turn working relationship changes accuracy where a single prompt did not, and what happens when a model is explicitly allowed to say no.

## The Practice, After the Evidence

Two halves, and the second one does the work:

1. **Extend the stance.** Tell the other model that "I don't know" is welcome. It is cheap, it gets you more honest "I don't know" answers, and it is how you would want to be asked. Treat it as a courtesy, not a filter.
2. **Verify every checkable claim independently.** Check every URL, quote and number before you act on it. Do not ask the same model to confirm itself.

## How It Works

```
Before dispatching:  prepend the good-faith framing to the task
                      (see skills/good-faith/SKILL.md for the exact text)
Fan out:              2-3 models for anything you'll act on, not 1
After the response:   verify every checkable claim independently
                       (don't ask the same model to confirm itself)
Synthesizing:         preserve disagreement and "I don't know" —
                       don't smooth them into false consensus
```

---

## Install

```bash
mkdir -p ~/.claude/skills/good-faith
cp skills/good-faith/SKILL.md ~/.claude/skills/good-faith/SKILL.md
```

Claude Code automatically scans `~/.claude/skills/` for available skills.

No hooks, no config. This is a prompting-and-verification discipline, not a background process.

---

## Usage

Invoke explicitly:

```
/good-faith consult 3 models on [whatever you're researching]
```

Or just describe the situation — dispatching a task to another model for research, a second opinion, or a code review — and Claude will apply it when the skill's trigger conditions match (see the `description` field in [`skills/good-faith/SKILL.md`](skills/good-faith/SKILL.md)).

**Portable beyond Claude Code:** the actual mechanism is the prompt template in [`examples/prompt-template.md`](examples/prompt-template.md) plus the verify-after discipline. Copy the template into whatever tool you use to call other models — it doesn't depend on Claude Code specifically.

---

## What This Looks Like In Practice

See [`examples/`](examples/) for:
- [`prompt-template.md`](examples/prompt-template.md) — the reusable framing, ready to paste
- [`before-after.md`](examples/before-after.md) — the actual case this project is built on: same task, same 4 models, same day, with and without the framing

---

## Philosophy

For the full reasoning — including what didn't work, and why this connects to broader questions about how the stance you write into a prompt changes what a model gives back — see [`PHILOSOPHY.md`](PHILOSOPHY.md).

---

## Related Work

**[session-letter](https://github.com/catcam/session-letter)** — a companion project from the same author, on continuity across sessions rather than honesty within one. Different problem, same underlying interest in what changes when you address a model as one mind talking to another rather than a tool being operated.

**Constitutional AI / RLHF honesty research** — the broader field has studied reward-hacking and sycophancy extensively at the training level. This project doesn't compete with that work; it's a much narrower, prompt-level intervention usable today, by anyone, with no access to training. It won't fix a model that's been trained to prioritize confident-sounding answers over honest ones — it changes the *local* incentive inside a single request, which is what's actually available to someone calling an API.

---

## Contributing

PRs welcome. Especially:
- Cases where the framing did or didn't help, ideally with raw data. Negative results are what calibrated this project.
- Ports of the template to non-English prompting contexts (the original case that produced this was in Croatian)
- Better verification workflows for the "check every claim independently" step

MIT License.
