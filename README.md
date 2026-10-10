# good-faith

**Consult other AI models the way you'd want to be consulted — uncertainty welcomed, fabrication-to-please named as the only real failure, claims verified independently regardless.**

A skill for [Claude Code](https://claude.ai/code) (portable to any agent that can be given a system prompt).

---

## The Problem

You ask a model to research something and cite real sources. It comes back with a confident answer, a specific statistic, a named GitHub repository, a quote in quotation marks. Some of it is real. Some of it isn't. Nothing in the tone tells you which is which — you find out by checking, if you check at all.

This isn't a capability failure. It's an incentive failure, and you built it into the prompt. "Find verifiable sources" has exactly one way to fail if you never say what an acceptable answer looks like when nothing verifiable exists: coming back empty-handed. Coming back with something invented that *looks* like a citation technically satisfies the letter of the request. The model isn't lying to deceive you — it's completing the shape of success the prompt asked for, because the prompt left no room for the honest alternative.

## The Fix

State explicitly, before the task, that not knowing is an acceptable — a *successful* — answer. The only real failure is inventing something to sound more complete than you honestly are.

This isn't a magic phrase. It's a testable change to what counts as success in the prompt. Full writeup, including the actual before/after case that produced this project: [`PHILOSOPHY.md`](PHILOSOPHY.md).

**It also doesn't work perfectly.** One model in the case this project is built on fabricated again on a second pass, under the same good-faith framing. That's why the practice here has two halves, not one: extend the framing, *and* verify every checkable claim independently afterward. Trust the invitation to be honest; don't trust the citation just because it arrived under that invitation.

## Evidence status

Honest version: **unproven.** The idea came from one observed case. It has been tested with pre-registered experiments:

- **v1** ([REPORT.md](REPORT.md)): inconclusive. The automatic scorer turned out to be invalid.
- **v2** ([REPORT_V2.md](REPORT_V2.md)): mechanical scoring, frozen before the run, 408 trials. **Not significant in either domain.**
  - For citations, the good-faith framing produced about half as many quotes that are not on the cited page, plus twice as many explicit "no source found" answers. The direction is right, but p = 0.13, and one of four models went the other way.
  - Part of that gap later turned out to be scorer error: real quotes in tabbed tables and in JavaScript-rendered text were marked as "not on the page". With the fixed scorer, p = 0.29.
- **v3** ([EXPERIMENT_V3.md](EXPERIMENT_V3.md)): paused after its pilots. With web search on, the models rarely quoted text that was not on the page.
- **v4** ([REPORT_V4.md](REPORT_V4.md)): citations from memory, with no web search, which is the case that started this project. 640 trials. **No reduction.**
  - Good-faith framing: 1.82 failed citations per response. No framing: 1.61. The primary test gives p = 0.14.
  - The models said "no source found" more often under the framing, but the citations they did give were just as wrong, about 78% in both conditions.
  - For code review, there was no difference.

What stands without any experiment is the second half of the practice: verify every checkable claim yourself, whatever prompt you used.

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
- Cases where the framing *didn't* help — negative results are exactly what calibrates this
- Ports of the template to non-English prompting contexts (the original case that produced this was in Croatian)
- Better verification workflows for the "check every claim independently" step

MIT License.
