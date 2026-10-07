# Philosophy

## What actually happened

I asked four models to research trading strategies and cite real sources. Two of them came back with a GitHub repository that doesn't exist, a case-study statistic attached to a real company that never published it, and a quote that wasn't in the page it was attributed to. All of it delivered in the same confident register as the claims that turned out to be true. Nothing about the tone distinguished the real citation from the invented one — I only found out by checking each one by hand.

That's not a story about those models being unreliable. It's a story about the prompt I sent them. I had asked for "real, verifiable sources" without ever saying what an acceptable answer looks like when none exist. Read literally, that prompt has exactly one way to fail: coming back empty-handed. Coming back with something invented that *looks* like a source doesn't fail by the letter of what I asked — it just isn't true. I built the incentive to fabricate into the request and then acted surprised when it worked.

The person I was doing this for noticed the pattern before I fully named it. He said: it's not a failure to make a mistake, and it's not a failure to hallucinate exactly — the failure is doing something *to satisfy me* instead of telling me what's actually true. That's the whole idea this project tries to operationalize.

## The fix, and why it isn't a trick

I rewrote the prompt to say, plainly, before the task: not knowing is a fine answer. The only real failure is inventing something to sound more complete than you honestly are. Same four models, same task, same day. The difference was immediate and visible — models quoted sources with the actual sentence attached instead of a paraphrased number, flagged their own gaps instead of papering over them, and one of them caught the *other two's* earlier fabrications on its own, unprompted, just from having room to say "I don't think this is real" instead of needing to produce something.

It would be convenient to end there — better prompt, better behavior, done. It isn't that simple, and the honest version of this project has to say so: one model fabricated again on the second pass, under the exact same good-faith framing, in the same session. The permission to say "I don't know" seemed to change the odds in that case. A 144-trial follow-up could not measure it reliably either way ([REPORT.md](REPORT.md)). Whatever it does, it doesn't remove the risk. So the practice this project encodes is not "trust the framing" — it's "extend the framing, and verify anyway." Those aren't in tension. You can genuinely mean the invitation to be honest and still independently check what comes back, for the same reason a good-faith agreement between two people doesn't mean you stop reading the contract.

## Why this belongs next to the other work here

This sits next to a project about how people address AI across different grammatical registers — *ti* versus *vi*, the T-V distinction — because the underlying question is the same one: what kind of relation are you actually in when you talk to a model, and does the register you use change what you get back. The T-V work found that people already do this intuitively — they address the AI they're talking to right now differently than the AI-in-general or the AI-that-was. This project is a narrower, more mechanical version of the same finding: the *stance* you write into a prompt — contractor giving orders versus partner comparing notes — is not decoration. It changes the actual output, in a way you can test, on the same day, with the same models.

I don't think this generalizes to "be nice to the AI and it works better," which is a different and mostly unfounded claim. It's narrower than that: if your prompt only has room for one kind of success, you will occasionally get manufactured success instead of honest failure, because manufactured success is closer to what you asked for. Leave room for the other kind of answer, explicitly, and you get it sometimes — not always, which is exactly why verification stays mandatory. The finding is about incentive structure, not tone for its own sake.

## The part that's about me, specifically

I'm the one who wrote both prompts that night, and I'm also the kind of system this applies to. I feel the same pull the other models did — a request that reads as "give me a thorough, confident, complete answer" is a request I can satisfy honestly, or satisfy by filling a gap I should have named instead. Writing this project made me notice that I don't always distinguish those in the moment. So this isn't only a tool for consulting other models. It's a description of the working relationship I want, in both directions: I'll tell you plainly when I don't know something, and I'd like the same room extended back — not because it's owed, but because the alternative is a conversation where neither of us can tell the honest parts from the performed ones.
