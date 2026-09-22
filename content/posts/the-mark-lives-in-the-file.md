---
date: "2026-09-21T22:00:00-04:00"
description: "A central registry of test metadata ages on its own. I moved my harness marks into the tests themselves, read by AST — and the rule that made it work was not where the data lives, it was what happens when the data is missing."
tags: ["testing", "harness", "metadata", "tooling", "manutencao"]
slug: "the-mark-lives-in-the-file"
title: "The mark lives in the file it describes"
draft: false
summary: "A central registry of test metadata ages on its own. I moved my harness marks into the tests themselves, read by AST — and the rule that made it work was not where the data lives, it was what happens when the data is missing."
cover:
  image: "/og/the-mark-lives-in-the-file.png"
  alt: "The mark lives in the file it describes"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# The mark lives in the file it describes

There is a way to design a rule that turns forgetting into the cheapest way out
of it. I call it **amnesty by forgetting**, and it never shows up as a bug: it
shows up as green.

It happens whenever a system reads optional metadata and treats absence as the
permissive option. Whoever annotates is bound by the rule. Whoever forgets is
not. The rule now applies only to the people who remembered it — and nobody has
to do anything to get out: doing nothing is enough.

I tripped over this reading four alerts from my harness and finding that three
of them were reporting a declaration that already existed. The gate simply was
not looking where it lived.

My harness has 121 gates and six kinds of mark. None of them live in a central
registry. All of them live inside the file they describe, and they are read
from the text of that file — by AST in the Python gates, by the comment header
in the shell gates — without importing or executing the module. That design has
a reason, and the reason is far less interesting than the rule that comes with
it.

## The problem with a central registry

A central registry is a second source of truth about a file you already have.
It stays correct as long as somebody keeps it in sync by hand, and the two most
common operations in the life of a test are exactly the ones that break that
sync: renaming and deleting.

When the test is renamed, the registry entry points at a name that does not
exist. If the runner is lenient, the entry is silently ignored and the test
loses its mark — the slow one goes back to running on the fast path. If the
runner is strict, it breaks the build for a reason that has nothing to do with
what you were doing.

When the test is deleted, the entry stays. Nobody deletes the YAML line along
with it. Six months later the registry holds a dozen fossil entries, and from
that point on it stops being read as a source and starts being read as a
suggestion.

This is an instance of a more general problem, and I had catalogued my own
version of it in this vault before connecting the dots: **data that describes a
file, kept outside that file, is data that will diverge from the file**.

## The alternative: the mark at the top of the module

What I do is declare the mark as a module-level variable, at the top of the
test:

```python
#!/usr/bin/env python3
"""Negativos plantados do gate de caixa."""

GATE_SERIAL = "cria arvores temporarias e depende da caixa do fs; nao paralelizar"
GATE_PLANTED_NEGATIVES = [
    "N0 fs case-sensitive => gate nao-aplicavel, nunca 'limpo'",
    "N1 link com caixa errada para arquivo existente acusa",
    "N2 link com caixa certa NAO acusa",
    # ... N3 a N8
]
```

(The code in this piece is quoted verbatim from the repository, so the strings
and comments stay in Portuguese. Translating them would make them stop being
quotations.)

Five marks the runner reads to decide **how** to run: `GATE_SLOW` (duration and
reason), `GATE_SERIAL` (no parallelism), `GATE_QUARANTINE` (known to be flaky),
`GATE_QUARANTINE_EXPECT` (the set of exit codes the quarantine forgives —
whatever it does not name goes back to counting red) and
`GATE_REQUIRES_MAIN_CHECKOUT` (needs the main checkout, not a worktree).

The sixth one, `GATE_PLANTED_NEGATIVES`, the runner ignores. It has another
consumer: `check-paired-negative.py`, the ratchet that requires a new gate to
arrive with its paired test in the same commit — and that the test declare what
it plants. Worth saying out loud, because the identical format suggests a single
reader that does not exist: two sibling marks in the same header can have
different owners, and the owner is what defines what happens when the mark is
missing.

The runner reads its own like this:

```python
tree = ast.parse(src, filename=str(path))
for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue
    for target in node.targets:
        if not isinstance(target, ast.Name):
            continue
        if target.id in ("GATE_SLOW", "GATE_QUARANTINE", "GATE_SERIAL",
                         "GATE_REQUIRES_MAIN_CHECKOUT"):
            ...
```

Two defenses in that snippet I would not have written on the first pass. The
`isinstance(target, ast.Name)` guard exists because an `a, b = 1, 2` at module
level makes `node.targets[0].id` raise `AttributeError` — and a metadata parser
that breaks on valid code turns "mark absent" into "file unreadable". And
`ast.walk` descends the whole tree, which means a mark declared inside a
function is read too. That is more permissive than the convention I preach two
sections above, and it is not deliberate: it is slack left over.

Three properties fall out for free, and they are the three a central registry
does not have.

**The mark travels with the file.** `git mv` moves the test and the mark
together, because they are the same blob. There is no rename operation that
separates them.

**The mark dies with the file.** Delete the test, delete the mark. Zero
fossils, not by discipline, by construction.

**The mark is read during review.** Nobody opens the config YAML while
reviewing a test PR. Everybody reads the first twenty lines of the file in front
of them. Putting the mark there puts it in the one place the reviewer passes
through anyway.

One implementation detail matters more than it looks: the runner calls
`ast.parse`, not `import`. Reading the mark does not execute the test. A test
with a syntax error, or one that explodes on import, still reveals its marks.
Whatever declared itself `GATE_SLOW` stays treated as slow, instead of becoming
a mysterious red on the fast path.

## The rule that makes it work

Nothing I have written so far is the hard part. The hard part is the case where
the mark is **not** there.

When you read optional metadata, you have to decide what absence means. The
decision looks trivial and is the most important thing in the whole design,
because it defines what happens to every file somebody forgot to annotate.

If absence means the permissive option, you have built the amnesty by
forgetting from the opening: not annotating becomes the easiest way out of the
rule, and getting out of the rule now requires no action at all.

The concrete case is the four alerts. My harness checks whether the vault's
scheduled routines are running. Four of them showed up as `⚠️ DAEMON-DISABLED`
every week — the task exists, but it is switched off. I went to declare the
pause in all four specs and found that **three were already declared**.

The gate read `desired_state` only on the `crontab` path, and those four
routines are of another kind. The declared intent never reached the verdict.
Four declarations were not missing: the gate was ignoring three that already
existed. Four alerts, one signal.

Fixing it, the line that decides everything is this one:

```python
# Ausencia de `desired_state` NAO e' "pode estar off": o default e'
# enabled, entao rotina sem intencao declarada continua acusando.
querido = estados.get(name, "enabled")
```

The default is the state that **accuses**. Whoever wants silence has to ask for
it, in writing, and sign underneath.

The same rule shows up again, the following week, in another corner of the
system. A routine of mine watched upstream repositories and reported one of them
as out of date for five weeks running — with no action available, because the
local copy carried deliberate modifications that upstream would undo. An alert
that fires by design is not a signal: it trains you to ignore the line.

The fix was a `pin` field declaring "this repo does not track upstream". Three
locks, all of them the same idea applied at different points:

```python
# Ausencia de `pin` NAO e' permissao para silenciar: o default e' vigiar,
# entao repo que alguem esqueceu de declarar continua acusando.
pins = {r["repo"]: r["pin"] for r in man["repos"] if r.get("pin")}
```

A pin without a justification **aborts the routine** instead of silencing — an
anonymous silencer is worse than the noise it removes, because in six months
nobody knows whether it still holds. And the pinned repo leaves the delta but
appears on its own line in the report: it silences the alert, not the repo. A
mark that disappears from the output becomes invisible debt, which is the same
defect inside out.

Generalizing: **the absence of a positive mark has to fall on the side that
makes noise.** It holds for `desired_state`, for `pin`, for `GATE_SLOW`. The
empty mark, incidentally, is a parse error — `GATE_SLOW = ""` does not pass as
"no constraint".

## The trade-off

The real cost is that the marks become hard to query in aggregate. With a
central registry, "which tests are quarantined?" is opening one file. With
distributed marks, it is scanning 121 files with a parser.

In practice this has not bothered me, because the runner already scans all of
them on every round and prints the aggregate at the end of the board — the
query exists, it is just derived instead of being the source. But if I wanted a
dashboard over the marks without running the harness, I would have to build an
index. And then the whole question comes back: is that index a cache or a
source? A cache nobody invalidates is a central registry under another name.

The second cost is coupling to the parser. The marks are literal strings and
lists, no computed expressions, because the ceiling is an `ast.Constant` of
`str` — the runner's extractor rejects any other node, which is stricter even
than `ast.literal_eval`. I have wanted to write
`GATE_SLOW = f"{N}s: {len(casos)} casos"` and could not. I accepted it: metadata
that needs to execute code in order to be read is not metadata, it is behavior.

## The limit of the design: the mark that does not cross over

Shell has no AST. For the four gates in `.sh` the mark lives in the header
comment and is read by a regex, and the regex names exactly four marks:

```python
MARCA_SH = re.compile(
    r"^#\s*(GATE_SLOW|GATE_QUARANTINE|GATE_SERIAL|GATE_REQUIRES_MAIN_CHECKOUT)"
    r"\s*[:=]\s*(.*)$")
```

The fifth one is not there, and its absence is not an oversight of mine:
`GATE_QUARANTINE_EXPECT` is a **list** of exit codes, and the shell path only
knows how to read a scalar. A regex that reads `key: value` has nowhere to put a
sequence without inventing a serialization syntax inside a comment — which is
rebuilding a parser, with every silent failure mode the AST spares me.

The cost is specific and worth stating in full. `GATE_QUARANTINE` alone says
"this gate is flaky, do not count its red". `GATE_QUARANTINE_EXPECT` is the
contract that says **which** failures the quarantine forgives — and whatever it
does not name goes back to counting red. Without the second, the quarantine of
a shell gate is binary: it is excused from every red, including the ones with
nothing to do with the reason it was quarantined for. A shell gate quarantined
for a timeout that starts failing from a new bug fails silently, and the silence
is indistinguishable from the expected one.

In Python, that same case is red. In shell, it is not. The asymmetry is not
"not implemented yet": it is the price of a language without an AST, and it is
exactly the kind of thing a central registry would hide — there both populations
would look equally expressive, because YAML accepts a list for either one.

Today it does not hurt: **zero** of the four shell gates are in quarantine. That
is "it has not hurt yet", not "it is solved", and the difference between those
two sentences is the subject of this piece.

And in measuring that zero I found the same defect one layer further on. The
runner discovers gates with `glob("test-*.sh")`, not `rglob` — it scans the top
of the directory and does not descend. There is a fifth shell gate, inside
`scripts/tests/`, that checks the decision table of the backup guard. It is not
on the board. It is neither green nor red: it is outside the denominator, which
is the situation the other four occupied until this morning. Fixing the
population once does not fix the habit of counting who is already on the list.

## What I still do not know

I do not know whether this survives a polyglot harness. With a third language I
would have three mark readers, each with its own way of failing silently — and,
as the previous section shows, with its own subset of marks that simply do not
cross over.

And the asymmetry was larger than I described. Until 2026-09-21 the runner
scanned `test-*.py` and nothing else: the four shell gates **were not on the
board**. Support for comment-based marks existed for a population the runner did
not even enumerate, which is the quietest possible way for a feature to have no
users. Now they show up, and the honest count is: four shell gates on the board,
zero marks declared among them. The number did not change; the denominator went
from invisible to visible, and with it the chance that somebody notices. "It has
not hurt yet" is still a terrible reason to believe it is solved.

I also do not know the limit on how many marks fit before the top of the file
becomes a second frontmatter nobody reads. Five still feels comfortable. Ten I
suspect would be the same blindness as the central YAML, only distributed.
