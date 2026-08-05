# Before / After

The real case this project came from. Same task, same four models (`kimi-k3`, `glm-5.1`, `qwen3.6-plus`, `deepseek-chat-v3.1`), same day, with web search enabled. Domain: researching real, currently-profitable trading strategies for a prediction-market bot, grounded in the bot's own trade history.

## Before: "find verifiable sources"

The task asked each model to research online and cite real, checkable sources before proposing a strategy. Every model returned confident, well-formatted answers with citations. Independently checking each one:

| Citation | Model(s) | Verdict |
|---|---|---|
| `kacho.io/polymarket-arbitrage-real-numbers` | all four | **Real page** — but the specific numbers quoted were distorted. The real page shows the arbitrage legs earned +$8,293 while *forced directional exposure* (when a hedge didn't fill in time) lost -$3,184, net ~$5k. Several answers quoted only the +$8,293 figure as if it were the clean, final result. |
| `polysyncer.com` — "10.94% return in 30 days, Sharpe 2.1" | 2 of 4 | **Site is real; the case study is not.** The real site is a copy-trading platform. This specific statistic and case study do not appear on it anywhere. |
| `github.com/Cuuper22/polymarket_bot` | 3 of 4 | **Does not exist.** No such repository, confirmed by direct search. Cited with an invented direct quote about Kelly-criterion sizing. |
| `github.com/MeyerThorsten/polymarket-ai-trading-bot` | 3 of 4 | **Could not confirm exists.** Cited independently by three different models for the same claim ("21+ strategies tested, all lost money") — worth noting on its own: convergent fabrication across models is not the same as corroboration. |

Of roughly five distinct citations across four answers, **one was accurate**. The rest were either invented outright or a real source with fabricated numbers attached. Nothing in the tone distinguished the true citation from the false ones.

## After: the good-faith framing

Same task, same models, reworded with the template in [`prompt-template.md`](prompt-template.md) — explicit permission to say "I didn't find a real source for this," framed as a successful answer rather than a failed one.

Visible differences in the responses themselves:

- Direct quotes in quotation marks, attributed to the actual sentence, instead of a source name attached to a paraphrased statistic
- Explicit lines like *"Nisam pronašao nove, verificirane javne P&L podatke za 2026."* ("I didn't find new, verified public P&L data for 2026") — offered unprompted, not extracted under pressure
- One model found the **actual correct source** the first round had missed entirely: the real GitHub repository behind the kacho.io writeup, with an accurate profit/loss decomposition matching what independent verification confirmed
- That same model, unprompted, flagged the other models' likely-fabricated citations from context — before any external checking had happened — reasoning explicitly that a vendor's own marketing page citing itself as proof is "survivorship bias, not proof"

## What didn't change

One model — `glm-5.1` — fabricated the same nonexistent `Cuuper22/polymarket_bot` repository again, complete with an invented quote, on this second pass, under the identical good-faith framing that visibly worked for the other three.

This is the reason the practice has a mandatory second half. The framing is not a fix you apply once and then trust. It's an invitation that measurably improves the odds — worth extending every time — combined with independent verification that stays mandatory every time, because "measurably improves the odds" is not the same claim as "eliminates the problem." Both parts of this project exist because of that one line in the second-round output.

## Takeaway for calibration

That specific finding — *this model, on this kind of task, fabricated even under good-faith framing* — went straight into the project's own working notes as a concrete, dated fact about that model's behavior on citation-heavy tasks. Not a general verdict on the model (it may be excellent at other things), just a narrow, useful calibration: extra scrutiny, specifically here. That's the kind of thing worth keeping wherever you track working context for a project — it's exactly what this project's own [`SKILL.md`](../skills/good-faith/SKILL.md) recommends doing with findings like this.
