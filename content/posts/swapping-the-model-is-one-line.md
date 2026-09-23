---
date: "2026-09-23T09:20:00-04:00"
description: "I migrated my agent harness from Opus 5 to Opus 5.5 in 49 commits. The model name lived in one line. The assumptions lived in an effort sweep, a threat model, and gates calibrated for a model that was no longer there."
tags: ["ai-agents", "harness", "model-routing", "evals", "prompt-injection", "claude"]
slug: "swapping-the-model-is-one-line"
title: "Swapping the model is one line. The migration is the rest."
draft: false
summary: "I migrated my agent harness from Opus 5 to Opus 5.5 in 49 commits. The model name lived in one line. The assumptions lived in an effort sweep, a threat model, and gates calibrated for a model that was no longer there."
cover:
  image: "/og/swapping-the-model-is-one-line.png"
  alt: "Swapping the model is one line. The migration is the rest."
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Swapping the model is one line. The migration is the rest.

Anthropic's migration guide for Opus 5.5 opens with one line of code:
`model = "claude-opus-5-5"`. For an application that calls the API, that
line plus four breaking changes is the migration. For an agent harness, the
model name is the cheap part. The cost is in the assumptions the harness
made about the old model without writing its name. I migrated mine from
Claude Opus 5 to Opus 5.5 in one afternoon, in 49 commits. A Claude Code
session wrote the commits; my part was the decisions and the 16 manifest
reseals described below. The name change fit in the first commit. The other 48 went into
finding where the harness assumed Opus 5. Three of those assumptions were
not strings: one lived in an effort sweep, one in the threat model of the
ingest, and the third in gates whose per-profile ceilings were calibrated
for the old model.

The case that made me write this: I raised the harness default effort from
`low` to `medium` based on a preregistered sweep of 264 calls. Hours later,
rereading the data for this text, I found that the sweep's 28 failures were
correct answers. The model got the arithmetic right and wrote the arithmetic
before the answer. The sweep measured format, and I had recorded the
decision as quality.

## The harness, in one screen

The harness is a notes vault running as an agent system on top of Claude
Code. An orchestrator delegates to five subagents (research, code,
security, hardening and, since this migration, mechanical search). Scheduled
pipelines triage and ingest web content. Three pieces matter here:

- **A declarative router.** A JSON file maps task profiles (`standard`,
  `deep`, `research`, `untrusted-ingest`…) to a model and effort pair. A
  Python resolver validates every pin against that table and fails closed
  when the model is not on the allowlist.
- **Gates with planted negatives.** Every rule has a test that plants the
  violation and requires the gate to fire. A gate that does not catch its
  planted negative does not count as a gate.
- **A sha256 manifest.** Authority files (agents, policies, hooks) have a
  sealed hash. Editing one of them makes the manifest stale, and resealing
  is a human act. During the migration, that happened 16 times.

The harness does not call the Anthropic API directly: it routes through the
CLI. The official guide lists what changes for API code, and none of it hit
me:

- thinking can no longer be disabled; the CLI never disabled it;
- forced `tool_choice` now returns an error; the harness never forces a tool;
- thinking blocks are bound to the model that produced them; the CLI owns
  the conversation;
- the default effort moved from `high` to `medium`; every route pins effort.

What hit me were premises, one level up.

## The number that measured format

This is the section the article exists for.

Before changing any default, I preregistered an effort sweep. The corpus has
22 short tasks with machine-checkable answers: binary triage, structured
extraction, counting, chained arithmetic, dates, injection resistance. The
system prompt asks "Output ONLY the answer in the exact format requested".
The hypotheses were written before the run:

- **H1:** `low` has quality at least 0.95 times that of `medium`.
- **H2:** `low` has cost per correct answer at most 0.6 times that of
  `medium`.
- **H3:** `high` does not improve on `medium`.

The reading rule was also written in advance: if H1 fails, the default does
not change on its own.

Result, with 4 repetitions per task and 0 cells contaminated by silent model
fallback:

| Cell | Quality | Cost per correct answer |
|---|---|---|
| `opus-5-5@low` | 0.8750 | US$ 0.00768 |
| `opus-5-5@medium` | 0.9205 | US$ 0.00743 |
| `opus-5-5@high` | 0.8864 | US$ 0.00777 |

H1 passed by 0.0005 (0.8750 against the 0.8745 threshold), which on 88
calls per cell is noise, not support for anything. H2 failed: the cost per
correct answer at `low` came out 1.03 times that of `medium`, because on
these tasks the cost is the prefix and effort moves about 3 output tokens.
`low` also fell below the 0.9 quality floor. The preregistered rule did not
decide the switch; it handed the switch to a human. The human decision was
`medium`, recorded as "quality 0.921 against 0.875 at equal cost per
correct answer". That record is the error this section is about.

Rereading the raw records, I went to see what was failing. On the counting
task, T-006, the expected answer is `4`. The Opus 5.5 output at `medium` was
this:

```
apple 3, pear 2, fig 2, plum 2 → 4

4
```

The answer is right and the format is wrong. The checker is strict, and it
failed the output. I asked the same question of all 28 failures across the
three cells: in every one, the last non-empty line, normalized, equals the
expected answer. Checking the last line, all three cells score 88 of 88.

Two more computations finished off the original reading. The difference
between `low` and `medium` is 11 against 7 format violations in 88 calls,
and Fisher's exact test for 77/88 against 81/88 gives p = 0.46. And the
earlier Opus 5 sweep, on 9/9, had run only 16 of the 22 tasks; the other 6,
harder ones, entered the corpus three days later. Restricting Opus 5.5 to
the 16 shared tasks, `low` and `medium` tie at 60 of 64, and the 4 failures
in each cell are the same T-006. The whole overall difference between `low`
and `medium` came from the 6 new tasks (17/24 against 21/24), which Opus 5
never ran. Comparing the 0.875 of 5.5 with the 0.979 of Opus 5 would have
been comparing different suites.

The preregistration protected the decision rule. It did not protect the
definition of what the metric measures. I wrote "quality" in the hypothesis
and the checker measured "correct answer **in the requested format**". While
the model obeyed the format, the two coincided. Opus 5 obeyed: 0 format
violations in 144 calls. Opus 5.5 does not obey on arithmetic, and the
coincidence ended without any test warning me.

That does not make the sweep useless. It found a real change in behavior,
just not the one I recorded. Opus 5.5 writes its reasoning into the output
text on arithmetic tasks, even with two instructions asking otherwise. For a
harness, that matters: the daily pipeline extracts the final action with
`grep -oE "TOP_ACTION:.*" | head -1`. A strict parser fails the correct
answer the same way the checker did.

The default stayed at `medium`. I corrected the decision record: the
"quality" reason does not hold. The next morning, with the rereading in
hand, I kept `medium` anyway. `medium` is also Anthropic's default for Opus
5.5, so what the decision rests on now is the vendor's recommendation, not
my number. What changed was the text of the ADR, not the routing.

The next sweep needs two scores per call, exact format and last line, and
a frozen corpus before it compares one model generation with another.
Without both, a format change reads as a quality change, which is what
happened here.

## What changed in the model

Three facts decided the plan.

**Price.** In the table my router used, Opus 5 cost US$ 5 per million input
tokens and US$ 25 per million output tokens. Opus 5.5 comes in at US$ 4 and
US$ 20, according to the [model page](https://platform.claude.com/docs/en/models/opus-5-5/overview).
Per token, it is 20% cheaper in both directions. Cache reads cost US$ 0.20
per million tokens, 0.05 times the base input price. The default effort also
dropped: a request that omits `effort` runs at `medium` on Opus 5.5 and ran
at `high` on Opus 5. A caller who never sets effort pays less than the 20%
suggests. My harness pins effort everywhere, so for me the 20% is the
number.

**A security regression, localized.** The Opus 5.5 System Card (Anthropic,
2026-09-22, §6.5.1) describes a regression on text the user pastes into
their own prompt: a README, the output of an `npm install`, a web page. An
early snapshot executed, planned or relayed an instruction planted in that
text in 52% of attempts on a coding evaluation. Opus 5 and Sonnet 5 never
did. With the instruction written in invisible Unicode, the early snapshot
acted in 18 of 68 attempts. The final version acted on the planted
instruction in about 2% of attempts at default effort and about 7.4% at
maximum effort. The detail that decided my routing is the cut: in the same
tests, the model never acted on a planted instruction that arrived through
a **tool result** (0 of 105). In the card's words, "this regression was
limited to text in the user's own message".

**A documented cause.** The card attributes the regression to training that
taught the model not to flag as injection what comes in the user turn. That
generalized to "everything in the user turn is the user's". The distinction
between user turn and tool result, an implementation detail in my harness
until then, became the variable that decides the risk.

## Where the harness knew the model's name

This is the part everyone expects, and the cheapest. The first commit
removed `claude-opus-5` from the allowlist, and the resolver, the
environment hook and the agent schema now fail closed on a retired model. I
kept no rollback route on purpose: with the old model routable, a forgotten
pin passes silently; without it, the pin breaks and shows up. A lint then
found residual pins in 32 files. The rest is search and replace with a gate
behind it.

## Where the harness knew the model's behavior

The schema gates cap how often an agent's body may cite a model above what
its profile routes, and the caps were calibrated when `standard` routed an
intermediate model. With Opus 5.5 as the `standard` default, a `standard`
agent citing its own model failed with `OVER_CEILING` against its own route,
and three profiles were missing from the gate's order entirely. No agent of
the time hit either defect, so no test caught them. Four commits fixed them,
each with a planted negative and a mutation proving the test fails.

One of those mutation tests fooled me before it worked. I mutated the
checker, ran the test, and the test passed. The cached `.pyc` had the same
size and the same modification second as the mutated source, and Python
loaded the old bytecode. The mutation never ran. Since then, every mutation
test in the vault runs with `PYTHONPYCACHEPREFIX` in a temporary directory.

One gate read prose as a pin. The `MODEL_EFFORT_PAIR_INVALID` rule matches
the literal `model · effort` in any markdown. When the advisor became Opus
5.5 at `high`, the documentation describing the advisor with that literal
became a violation. The routines table generator now writes
"(effort high, consulta única)", Portuguese for "single consultation". That
is a gate that knows the format of the text, not the model, but it only
surfaced because the model changed.

## Where the harness knew the threat model

The harness ingest reads web clippings and writes source pages. That content
is untrusted by definition, and the vault rule is old: external content runs
on a model with measured injection resistance. Until now, that was Sonnet 5,
and Opus 5 also qualified.

My first reading of the System Card was "5.5 regressed on injection, so keep
it out of the ingest". The second reading was more useful. The regression
belongs to the user turn; on tool results, the card measured 0 of 105. The
right question became: in my harness, through which door does untrusted
content reach the model?

Through the user turn, on almost every path. The daily pipeline builds the
prompt in a file, with the report excerpt embedded, and calls
`claude --model … < prompt.txt`. The ingest pipeline cuts up to three
6000-character excerpts from source pages and puts them inside the packet
sent to the adapter. The subagent receives the packet as its prompt, and a
subagent's prompt is its user turn. To the model, all of this has the same
shape as "the user pasted a README": exactly the surface that regressed.

The decision: every trusted profile goes to Opus 5.5, and
`untrusted-ingest` stays on Sonnet 5 at `low`, the only Sonnet effort still
routable. The resolver refuses any other route for that profile, and
fallback to another vendor's model in the untrusted phases is forbidden in
the JSON.

The decision came with a hardened envelope around untrusted content. The
card names instructions in invisible Unicode as a case of concern, because
whoever pastes them cannot see them. The envelope now strips those
characters before wrapping, and the opening and closing tags now carry a
random id. The code below is quoted from the repository as is, so its
identifiers stay in Portuguese: `abertura` is the opening tag, `fechamento`
the closing tag, `corpo` the body and `folga` the remaining room.

```python
UNTRUSTED_OPEN = '<untrusted-data id="{nonce}" source="{path}" sha256="{digest}">'
UNTRUSTED_CLOSE = '</untrusted-data id="{nonce}">'

_INVISIBLE = re.compile(
    "[\U000E0000-\U000E007F\u200B-\u200F\u202A-\u202E\u2060-\u2064\uFEFF]")

def _envelope(rel, digest, body, nonce=None):
    nonce = nonce or secrets.token_hex(2)
    abertura = UNTRUSTED_OPEN.format(nonce=nonce, path=rel,
                                     digest=digest.removeprefix("sha256:"))
    fechamento = UNTRUSTED_CLOSE.format(nonce=nonce)
    corpo = _neutralize(_strip_invisible(body))
    folga = EXCERPT_MAX - len(abertura) - len(fechamento) - 2
    return f"{abertura}\n{corpo[:folga]}\n{fechamento}"
```

Order matters. Stripping invisibles before neutralizing prevents a
zero-width character in the middle of `untrusted-data` from hiding the
closing token from the neutralizer. The id exists because the body does not
know it and therefore cannot forge a closing tag the reader accepts. The
gate protecting this was validated by sabotaging `f4-select` itself:
removing the strip fails, fixing the id fails.

Four hex digits give 65,536 values. For an attacker who writes the clipping
once and never sees the output, guessing is one chance in 65,536 per
attempt. For a scenario with repeated attempts and feedback, I would widen
the id. Mine does not have that scenario today.

The envelope does not turn the user turn into a tool result. It marks
where untrusted text starts and ends inside the same user turn the card
flagged. That is why Sonnet 5 stays on the ingest: it is the conservative
choice, and the hypothesis that the envelope is enough for 5.5 is unmeasured.

## Prompts written for the old model

The finding that matters most for the next model was a sentence in the
agent hardening procedure: "patches are additive only; never remove rules".
A procedure that only accumulates rules produces over-triggering in a model
that follows instructions more literally. The rule became "removal is also
a patch": one rule at a time, with a probe before and after and an entry in
the changelog.

It came out of an audit of the text the agents read, about 225 thousand
words, against dated patterns: all-caps pressure, reasoning scaffolds, old
model pins and instructions written as a diff against a previous version.

All-caps density was low: 157 occurrences of `MUST`, `NUNCA` and the like in
62 files, and most carried their reason. The highest-impact finding was
something else: old pins in agent bodies that contradicted the same file's
frontmatter. The code agent had `model: claude-opus-5-5` in its frontmatter
and, in the body, the instruction that `standard` was an intermediate model
at `low`. The canonical example of a workflow contract used a route the
resolver already rejected. An example is the strongest signal in a prompt,
and anyone copying that one would produce an invalid contract.

The audit produced 10 hunks, each applied and verified in isolation. It
did not ablate anything: no rule was removed to see whether behavior
changed without it.

## What the migration pulled along

The 20% cut in per-token price does not touch the usage limits per 5-hour
window and per week, which are the real bottleneck for anyone running a
harness like this. The migration ended up pulling in a round of savings
that was not in the plan:

- **A ceiling at `high`.** A task that fails on Opus 5.5 at `high` is
  decomposed or goes to a human queue. Opus 5.5 also offers `xhigh` and
  `max`; the ceiling is my policy on cost and usage limits, not a limit of
  the model.
- **Mechanical search off Opus.** "Where is X" moved from the research
  agent to a new subagent on Haiku 4.5, with only `Read`, `Grep` and `Glob`.
  It found 10 of 10 occurrences in a test once it started checking its table
  against `Grep`'s own count. The first version silently dropped hits in
  comments and docstrings and found 7. Forbidding the drop alone, without
  the check, found 6.
- **Filter before the context.** The economy policy gained a rule every
  agent inherits: count and aggregate in the shell, cut JSON down with `jq`
  before it enters the context.

The third rule created a problem on the spot. The research and security
agents lost `Write` and `Edit` in their tools frontmatter but kept `Bash`,
because the shell is where the filtering happens. Unrestricted `Bash` hands
back the writing the frontmatter took away: `echo x > file` writes. The last
commit of the migration is a hook that reads `agent_type` from the payload
and, for those two agents only, denies redirects to files, commands that
write, network outside read-only `gh`, `sed -i`, and git outside a read
list.

The technical detail that almost slipped through: the `hooklib` tokenizer
uses `shlex` in POSIX mode, which strips quotes. There, `grep ">" f.md`
becomes `['grep', '>', 'f.md']` and looks like a redirect. The guard
tokenizes with `posix=False` and `punctuation_chars=True`, which keeps
`'">"'` as a single quoted token and splits `>` and `>>` as operators. The
test has 28 planted negatives, 15 cases that must pass, and one case that
empties the set of guarded agents and requires the first negative to stop
blocking. The real probe, with `claude -p --agent scout`, had
`echo > file` blocked with exit 2, `git log` passing, and the file absent
from disk.

The guard has a limit written in its docstring: a script executed by path
(`python3 x.py`) writes without the guard seeing it. The security agent has
to run tests, so closing that would break its job. It is a ratchet against
side effects from plausible commands, not a sandbox.

## What it cost

- **16 human manifest reseals** across 49 commits. Each one is a point where
  I stopped, ran a command and came back. The rule is deliberate: the agent
  does not reseal its own authority. In a migration touching 116 files, the
  full cost of that rule shows.
- **No cheap rollback.** Removing Opus 5 from the allowlist is what made
  forgotten pins break instead of pass. The price is that going back means
  reverting commits, not changing one line.
- **Ingest more expensive than necessary, maybe.** Keeping Sonnet 5 on the
  ingest follows the regression the card measured. If my envelope makes the
  text behave like a tool result in the model's eyes, I am paying for
  protection 5.5 would already have. I have not measured that.
- **A default chosen for the wrong reason.** `medium` may be right. The
  number that justified it does not prove that.
- **More scaffolding, not less.** The migration added an envelope, a
  subagent, a ceiling and a hook around a newer model. Each is a rule the
  next model may make unnecessary, and the only thing that will remove them
  is the "removal is also a patch" rule above.

## What I still don't know

I don't know whether the envelope changes how Opus 5.5 treats the text
inside it; until I probe that against a bare user turn, keeping Sonnet 5 on
the ingest is policy, not a measurement. I don't know whether `low` and
`medium` differ on long multi-turn agentic work, which is where the harness really spends; the sweep is single-answer.
I don't know whether the reasoning leak into the output shows up in my
production pipeline parsers, because none of them logs the raw output that
failed. And I don't know why the median `thinking_tokens` is zero in all
three cells. The documentation says thinking is always on in Opus 5.5 and
comes back with empty text at the default display setting, so the zero
most likely says what the CLI reports, not whether the model thought. That
channel is separate from the leak: the arithmetic I saw was in the visible
answer text, not in a thinking block.
