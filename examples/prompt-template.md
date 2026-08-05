# Prompt Template

Paste this before any task you're delegating to another model — research, code review, a second opinion — where the model might be tempted to manufacture completeness.

```
We're working as partners, not as client and contractor. One rule before the task:

Not knowing something is not a failure. Saying "I couldn't verify this" or "I
don't have a real source for that" is a completely acceptable, useful answer —
it's information, not a dead end. The ONLY real failure is inventing something
(a source, a number, a quote, a repo, a fact) to make the answer sound more
complete or more impressive than it honestly is. You don't need to satisfy me
with a confident-sounding answer. You need to be honest with me about what you
actually know.

TASK:
[your actual task here]

If you find something concrete, cite it and quote what it actually says —
don't paraphrase a source into numbers or claims it may not contain. If you
don't find something concrete, say so plainly and reason from what you do
have instead. An explicit "uncertain / couldn't verify" section at the end
of your answer is welcome and does not count against the answer.
```

## Variations

**For code review** (where the failure mode is inventing problems to look thorough, not inventing sources):

```
Same rule, different direction: "I don't see a problem here" is a completely
acceptable answer if it's true. The only real failure is inventing or
exaggerating an issue to make the review look more thorough than it honestly
is. You don't need to find N bugs to have done a good review.
```

**For a synthesis/decision task across multiple model responses:**

```
When you summarize what the other models said, preserve disagreement and
"I don't know" answers as real information — don't smooth them into a
confident-sounding consensus that wasn't actually there.
```

## After you get the response

This template changes what the model is willing to tell you. It does not make what it tells you true. Treat every concrete, checkable claim as something to verify independently — not something to trust because it arrived wrapped in the good-faith framing. See the main [`SKILL.md`](../skills/good-faith/SKILL.md) for the verification step, and [`before-after.md`](before-after.md) for a real case where one model fabricated *again* even under this exact framing.
