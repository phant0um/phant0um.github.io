---
date: "2026-10-05T11:20:00-04:00"
description: "Between September 24 and October 5 I opened 17 pull requests in 8 open source projects. In 9 of them the bug did not crash anything. A tool reported a wrong precision, a wrong saving, a wrong readiness, a wrong warning or a wrong label, and the user had no reason to doubt it."
tags: ["open-source", "harness", "falso-verde", "testing", "shell", "ai-agents"]
slug: "seventeen-upstream-prs"
title: "Seventeen upstream PRs, and nine fixed a tool that told a false story"
draft: false
summary: "Between September 24 and October 5 I opened 17 pull requests in 8 open source projects. In 9 of them the bug did not crash anything. A tool reported a wrong precision, a wrong saving, a wrong readiness, a wrong warning or a wrong label, and the user had no reason to doubt it."
cover:
  image: "/og/seventeen-upstream-prs.png"
  alt: "Seventeen upstream PRs, and nine fixed a tool that told a false story"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Seventeen upstream PRs, and nine fixed a tool that told a false story

Between September 24 and October 5 I opened 17 pull requests in 8 open source
projects that are not mine. Six are merged, ten are still open and one I closed
myself. In 9 of my 17 PRs the bug did not crash anything. The tool kept running
and stated something false: a precision, a token saving, a readiness, a warning,
a label. A crash is visible, because the user watches the tool fail. A false
report is not, because the user reads it, believes it and moves on.

This series has been about false greens inside my own harness. This post is the
same pattern, found in other people's code. It is also a roundup: what shipped,
what is still waiting, and what I got wrong on the way.

## What merged

**ai-memory** (`akitaonrails/ai-memory`), two PRs, merged on September 24 and
25 (UTC).

PR #876 fixed a hook that spun at 100% CPU on large payloads. Each key lookup
in `hooks/_lib.sh` used `${payload#*"key"}`, and that expansion is quadratic in
the payload size under dash and bash. On macOS `/bin/sh`, a 200 KB payload took
64 seconds to find one key. A single `awk index()` pass took 0.05 seconds. To
show that the new helper returns the same bytes as the old one, I ran both over
38 payloads under dash, bash and macOS sh. The outputs were byte-identical.

While I ran that suite on macOS, one test failed on `main` too:
`url_encode encodes UTF-8 per byte`. That failure became issue #877 and then
PR #879. On macOS, `/bin/sh` is bash 3.2, which sign-extends bytes of 0x80 and
up in `printf "'c"`. A path like `/Users/me/Área de Trabalho` reached the server
as `%FFFFFFFFFFFFFFC3%FFFFFFFFFFFFFFA9` instead of `%C3%A9`. The server then
looked up a different directory.

The test for this had existed since July and had failed on every Mac. CI never
saw it, because the shell job runs only on `ubuntu-latest`, where `sh` is dash.
After the fix the suite ran fully green on macOS for the first time: 73 passed,
0 failed.

**laya** (`NandhaKishorM/laya`), PR #641, merged on September 29 and shipped in
0.3.22.

On Apple's MPS backend, `Agent.dtype` says `float16`. A per-call gate decides
whether each forward pass autocasts. With the gate set high enough, every call
runs in `float32` while `dtype` still says `float16`. A service that logs
`dtype` at start-up records a precision it never uses. The fix adds a
read-only `dtype_for(rows)` that answers for a given call, and the docstring
now says that `dtype` is the autocast target.

**pstack-claude** (`michael-denyer/pstack-claude`), PRs #182, #183 and #184,
merged on October 5.

Two of them are the same bug in two checkers. Notepad and some other Windows
editors save Markdown with a UTF-8 byte-order mark. The checkers anchor their
frontmatter regex on a leading `---`, so the BOM hid the frontmatter and a valid
file failed with invented problems. In `check-plan.mjs` the failure depended on
the file. A BOM before the H1 gave `no H1 title`. A BOM before frontmatter gave
`mid-sentence colon`, because the frontmatter was linted as prose. The third PR
removed a stale entry from `tools/forks.json` that made every sync print a
warning.

## What is still open

These were open on October 5. A maintainer may still reject any of them.

- **Bruno** (`usebruno/bruno`) #9415, #9446, #9447. A `$` in a URL path was
  sent as `%24`, which breaks FHIR operations like `$everything`. The response
  headers lost `Content-Encoding` after axios decompressed the body, so a gzip
  server looked like it sent no compression. And `cleanJson` marked any object
  seen twice as `[Circular Reference]`, even when two variables only shared it.
- **context-mode** (`mksglu/context-mode`) #1252, #1253, #1256. Its stats
  counted binary reads as saved tokens, so reading a PNG raised the savings
  number. Every hook call copied and re-signed a 1.9 MB native binary that was
  already current. And the MCP readiness check answered for the whole machine.
  With several Claude Code sessions open, a session whose own server never
  started was still sent to `ctx_*` tools it could not call.
- **Paperclip** (`paperclipai/paperclip`) #14308, #14309. On Windows, `doctor`
  always warned that the key file was readable by others, and suggested a
  `chmod 600` that has no effect there. On Debian, where `/bin/sh` is dash, one
  bash-only line in `~/.bashrc` killed every SSH run with exit 2 and no output.
- **Hermes Agent** (`NousResearch/hermes-agent`) #125846. `hermes doctor` told
  Vertex users to drop the `google/` prefix from model IDs. Vertex needs that
  prefix, so a user who followed the advice broke their config.
- **ponytail** (`DietrichGebert/ponytail`) #1033, from my issue #1032. The
  status line pointed into the versioned plugin cache, and Claude Code deletes
  old version directories after an update. After the next update the badge
  went blank with no error.

## The false story, counted

The lists above say what each bug did. The table below sorts all 17 by what
the user saw before the fix. A PR counts as a false
report when the tool's own output stated something untrue about the input or
the system. A PR counts as a failure when the tool broke, slowed down or did
the wrong thing without claiming anything false. By that line, 9 of my 17 PRs
fix a false report.

| PR | What the user saw before the fix | Class |
|---|---|---|
| [laya #641](https://github.com/NandhaKishorM/laya/pull/641) | `dtype` says `float16`, the call runs in `float32` | false report |
| [context-mode #1252](https://github.com/mksglu/context-mode/pull/1252) | reading a PNG raises the saved-tokens number | false report |
| [context-mode #1256](https://github.com/mksglu/context-mode/pull/1256) | MCP counts as ready for a session whose server never started | false report |
| [Paperclip #14308](https://github.com/paperclipai/paperclip/pull/14308) | `doctor` warns that a Windows key file is readable by others | false report |
| [Hermes #125846](https://github.com/NousResearch/hermes-agent/pull/125846) | `doctor` tells Vertex users to drop a prefix they need | false report |
| [Bruno #9446](https://github.com/usebruno/bruno/pull/9446) | a gzip response shows no `Content-Encoding` | false report |
| [Bruno #9447](https://github.com/usebruno/bruno/pull/9447) | a shared object shows as `[Circular Reference]` | false report |
| [pstack #182](https://github.com/michael-denyer/pstack-claude/pull/182) | a valid BOM-led playbook fails the check | false report |
| [pstack #183](https://github.com/michael-denyer/pstack-claude/pull/183) | a valid BOM-led plan fails the check | false report |
| [pstack #184](https://github.com/michael-denyer/pstack-claude/pull/184) | a warning on every sync | not false: the entry was stale, as the warning said |
| [ai-memory #876](https://github.com/akitaonrails/ai-memory/pull/876) | a hook at 100% CPU on large payloads | failure (slow) |
| [ai-memory #879](https://github.com/akitaonrails/ai-memory/pull/879) | a non-ASCII path reaches the server mis-encoded | failure |
| [Bruno #9415](https://github.com/usebruno/bruno/pull/9415) | a `$` in the path is sent as `%24` | failure |
| [context-mode #1253](https://github.com/mksglu/context-mode/pull/1253) | a 1.9 MB copy and re-sign on every hook call | failure (cost) |
| [Paperclip #14309](https://github.com/paperclipai/paperclip/pull/14309) | SSH runs exit 2 with no output | failure |
| [ponytail #1033](https://github.com/DietrichGebert/ponytail/pull/1033) | the badge goes blank after an update | failure (silent) |
| [Hermes #125779](https://github.com/NousResearch/hermes-agent/pull/125779) | the documented search command exits with an error | failure (docs), closed as duplicate |

The pstack #184 row is the one a reader might question. The tool printed a
warning, but the warning was true, so the row stays out of the count.
Ai-memory #879 sits on the line from the other side. The hook never claimed
that the path was encoded correctly. It sent the wrong bytes, so it is a
failure, not a false report.

The Hermes case is the worst of the nine, because the false report came with an
instruction. A wrong number misleads you. A wrong fix suggestion makes you
break a working setup, and the tool that told you to do it is a diagnostic
tool, the one you trust most.

In these 17 PRs I see two blind spots. The first is that a test checks that the
tool produces output, but not that the output is true for the input. Five of the
tests I added to Bruno for shared objects failed on `main`, so the suite had
never asserted that an object seen twice without a cycle comes out intact.
The second blind spot is the environment, and it needs its own section.

## The environments outside the test matrix

Five of my 17 PRs fix a bug that appears only in an environment the project's
CI does not run: bash 3.2 on macOS (ai-memory #879), dash (Paperclip #14309),
Windows file modes (Paperclip #14308), and Windows editors that write a BOM
(pstack #182, #183).

The ai-memory case is the clearest example. A failing test sat in the repo
since July. CI stayed green, because CI never ran the shell where the test
fails. That is the denominator problem from an earlier post in this series: the
suite was green over the population it ran, and the population was one shell.

Ponytail #1033 is a close relative, but it is a lifecycle gap, not an
environment gap. The bug needs no special shell or OS. It needs a plugin update
after setup, and no test had run setup, then an update, then the badge.

## What 15 of the PRs had in common

Fifteen of the 17 PR bodies include a red run: the new test fails on `main`, or
on the base commit, and passes with the fix. The other two ship no behavior to
test: removing a stale config entry (pstack #184) and fixing one documented
command (Hermes #125779). In a few I
also reverted the fix and watched the test fail again, or changed the fix on
purpose and checked that a test caught it. For Paperclip #14309, putting `. `
back in place of `command . ` made the dash test fail.

The pstack maintainer's merge comments on #182 and #183 both restate that the
test fails on `main` and passes on the branch. That is two comments, not a
survey, but it matches what I would want as a reviewer. A red run lets a
reviewer trust a fix without rebuilding the bug in their head.

I wrote these PRs with Claude Code, and several bodies say so. The agent did
much of the code and the drafting. The red runs and the decisions about scope
were the part I checked line by line, because those are the claims a reviewer
cannot check without running the code.

## What I got wrong

PR #125779 to Hermes Agent fixed a broken example in `CONTRIBUTING.md`. The
documented `gh search prs --state all` command exits with an error, so a
contributor who copies it gets no results and can skip the duplicate check. My
PR was itself a duplicate. Another contributor had opened the same one-line
change eight days earlier, and my search missed it. I closed mine with an
apology.

The irony is useful. The bug I fixed was "the duplicate check returns nothing",
and I fell into it while using a different search. A clean search result told
me nothing existed, and I believed it. That is the same false story, told by my
own process.

## What comes next

Ten PRs wait for review. The Bruno `console.log` path has its own `seen` set
with the same false-cycle bug, and I offered it as a follow-up. Paperclip
#14309 fixes two of the three items in its issue. The third, keeping
diagnostics when a run exits non-zero with both streams empty, is still open.

Hermes #125846 is narrower than the bug. On October 3 another contributor
posted a review of it, marked as AI-assisted. The review confirms the fix for
Vertex, Novita and GMI. It also finds the same false `doctor` warning in two
model-provider plugins, `commandcode` and `nebius`, whose model IDs my drift
test does not scan. It suggests deriving the exemption from `is_aggregator()`
instead of a hand-kept list. I plan to send a follow-up that does that. The
Vertex bug was a provider missing from a hand-kept list, and a derived rule
cannot forget the next provider.

## What I still don't know

- The count of 9 out of 17 is my own classification of my own PRs, made after
  the fact. The table shows where I drew the line. Another reader could draw
  it in a different place, and the count says nothing about tooling bugs in
  general.
- I do not know whether the open PRs will merge, so the claim that these are
  real bugs rests on reproductions, not on maintainer agreement.
- I suspect that a test which asserts "the output is true for this input" is
  rarer in tooling than in libraries, but I have not measured it outside these
  8 projects.
