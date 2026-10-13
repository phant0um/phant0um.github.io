---
date: "2026-10-13T01:10:00-04:00"
description: "A plan for a smaller model is checkable only if every done_when fails before execution and every test has been seen failing on a planted defect. A green test that was never red proves nothing."
tags: ["ai-agents", "testing", "delegation", "local-models", "plan-handoff", "python"]
slug: "plans-that-fail-before-they-run"
title: "Plans that fail before they run"
draft: false
summary: "A plan for a smaller model is checkable only if every done_when fails before execution and every test has been seen failing on a planted defect. A green test that was never red proves nothing."
cover:
  image: "/og/plans-that-fail-before-they-run.png"
  alt: "Plans that fail before they run"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Plans that fail before they run

The previous article in this series covered the limits of the local models, and this one is about the plan I wrote for a smaller model to build the first piece of a local triage shadow. The claim is narrow: a plan handed to another model is only checkable if every `done_when` fails before anything runs and every test has been seen failing on a planted defect. A green test nobody saw red is green for free. The claim "the tests pass, so the work is done" is false.

## How the plan got made

I did not start with code. The idea went through grill-me first, a skill that attacks assumptions while changing them still costs nothing. The idea shrank to one question: can a local model triage the same items the pipeline already sends to Claude, scored against a labeled corpus?

Then plan-handoff turned the answer into waves. Each wave names an orchestrator and an executor. It has a conflict table in the form "if X, do Y; otherwise stop". It has an EXEC spec in JSON, with a `files_allow` list of the only files the executor may touch. The executor answers with an EXEC report that carries `deviations`, `assumptions` and `conflicts_hit`.

The orchestrator does not trust that report. It reruns every `done_when` itself, checks that the diff stays inside `files_allow`, and validates the spec and report with `check-exec-spec.py`. The report is a claim until those checks pass.

The rule that matters most is that every `done_when` must fail before execution. If one passes on the untouched repository, it is not testing the wave.

## The baseline: nine failures, then thirty-six

In round 1 the orchestrator ran all nine `done_when` commands before writing any code. All nine failed. Some failed with rc=2 because the script was missing, and others with rc=1 because the artifact was missing. The plan records the output of each one.

One of them is worth showing. The W2 check is `test -f f1_shadow.py && ! grep ...`, and the `test -f` is there on purpose. A bare `! grep` passes when the file is missing, because grep fails on a missing file and the negation turns that failure into success. The check would be green with nothing built.

Round 2 was larger: 36 `done_when` across eight waves. All 36 failed on the untouched tree (36 of 36). The spec validator exited 0 for all eight specs. I read that as a statement about the form, not about the checks. A validator that accepts a well-formed spec says nothing about whether the spec's checks can fail.

## Break the check on purpose

Round 1, wave W1, had six tests for a sampler that builds a 700-item sample. The tests were not trusted until the code was broken on purpose. With `strip_frontmatter` turned off, the test run returned rc=1. With the threshold changed from `<=` to `<`, it returned rc=1 too. Both planted defects were caught.

The same wave made other checks that could be read without trusting my own word. The sample hash was the same on Python 3.13 and on the system Python 3.9, which is what the plan needed. I rebuilt the 700 states the model would see and searched them for the `decision:` line from the source frontmatter, the label leak the whole design depended on. I found 0 of 700.

The wave also caught an error in the plan. The plan said to resolve the vault root with `parents[3]`, which points at `07-QUEUE`, not at the vault. The code used `parents[4]`. An executor that followed the plan literally would have read the wrong directory and written nothing useful.

Round 1, wave W2, had nine tests against a fake local server, so they never touched the real model endpoint. The orchestrator planted four mutants: a retry on 4xx responses, a disabled context guard, a `.tmp` file left behind, and a `state_sha` written without an error. All four returned rc=1. A test that also passes on the mutant is the one that gives you false confidence, and each one had to be seen failing.

## The false green in the pipe

The most embarrassing check of the day was the orchestrator's. I ran the W1 test through `tail`, and the exit code I read was `0`. That `0` belonged to `tail`. The test's own exit code was hidden behind the pipe.

I reran without the pipe and read the test's own rc. The lesson is small and specific: a `| tail` in a `done_when` turns the gate into a check on the last command in the pipeline, not on the test. Read the status of the program you meant to test, and keep the pipe out of the check.

## The local model writes the code

Round 1, wave W3, was the metrics module. The file `f1_metrics.py` and its tests were written by the local 12B Gemma, called through `/api/chat` at temperature 0. The orchestrator wrote the prompt, ran the tests and read the output.

It took three generations. The first had a SyntaxError. The second fixed the syntax and the argument handling. The third fixed five defects that the eight existing tests did not catch. Recall for the approved class was always 1.0. The nearest-rank percentile was wrong. The short and long latency figures were placeholders. The calibration score was stuck at 0. The comparison step was a placeholder too.

The `done_when` went green after the second repair. The defects were found in review, not by the gate. The wave ended with 12 tests: the original 8 and 4 more written for defects found in review. I do not claim the 12 cover every defect in the module. The report says they cover the defects found, and that is the only claim I make.

There was also an error of my own. The first scenario I wrote into the prompt for the recall test had a count mistake. The report records it: with 80 approved items, "5 of 20" gave an accuracy of 0.85, so the expected figure I had written did not follow from the scenario. The executor did what it was told, and the wrong input came from the orchestrator.

The W3 report is the executor's claim, so I treated it that way. Its `diff_summary` lists the three generations, the five defects and the test count. I reran the tests and read the output rather than relying on the summary alone. A report that reads well is still a report. The orchestrator's job is to find out which parts of it are false, and it is easy to skip that step when the gate is green.

## Pre-registration and the choose rule

Round 2 had the real selection step. Before any candidate touched the labeled set, I wrote `W4-preregistration.md`. It fixed four things in writing. The base prompt was V2, because the ablation script had picked between two bases by list order and that tie-break was not a decision. The candidate batch was cand-1 to cand-4. The number of comparisons was K=4. And the rule was in code, not in my head.

The rule in `choose` says a candidate wins only if four conditions hold. Its AUROC must beat the base by at least 0.02 on the select split. A paired bootstrap per group must exclude zero at the adjusted level, 1 minus 0.05 over 4, which is 98.75%. Its margin over the length floor must have a positive lower bound. And its hold rate must stay at or below the larger of 0.05 and twice the base's. If nothing qualifies, the base stays. I committed this as local commit `c840fdbb0` before the first select.

The first version of the test for `choose` planted a defect in only one of the five clauses. The Opus reviewer caught it in R2b. The fix was one negative test per clause, 10 tests in all. The reviewer reports that mutating any single clause makes one test fail. The reviewer also flagged an earlier draft of the candidates. One used "hold" as an output and was removed. One encoded a domain policy that the canonical policy does not have, and that was removed too. The pre-registration expected the rule to keep V2. With only 34 disapproved items in select, the interval is too wide to crown a winner, and "no candidate wins" is the rule working, not the loop failing.

## Deviations I am reporting

The plan names a Haiku model as executor. The exec reports log where that did not hold. Here is the list.

In round 1, the orchestrator wrote W1 and W2 itself. The local model was loaded with a 4096-token context, and the plan alone is about nine thousand tokens, so an executor could not read it whole. In W3, the Gemma generation took three calls where the plan allowed one, and the report lists that as a deviation.

In round 2, the orchestrator ran the inference for W3, W4 and W5 as background scripts instead of handing them to executors. It created `ablation.py`, which the plan did not name, and cut the candidate batch from five to four after review. The `final-report.md` file gained a "Pisos" section that I edited by hand so the gate could read the key names. That file is generated, so the edit belongs in the generator. The Opus reviewer's item 8 in R3 flagged exactly this.

## The trade-off is orchestration cost

The method is heavy for the size of the work. The orchestrator reran each `done_when`, checked each report against its spec, and made the selection step wait for a pre-registration commit. Round 2 also added four Opus reviews. That is a lot of ceremony around a sample of 700 items and a handful of prompts.

I did not measure how many tokens the orchestration used, and I will not guess at a number. The honest comparison is not "the method against nothing". It is the method against a bounded model that does the whole job in one pass with its own tests. I have not run that comparison.

The next article in this series, [the gate was right](/posts/the-gate-was-right/), picks up the part of this I trust least: the gate itself, and what it means for a check to be shown failing before anyone relies on it.

## What I still don't know

Whether a local executor with tools could carry the code waves without the orchestrator rewriting its output. Everything measured here had the orchestrator in the loop. I also do not know what the orchestration cost in tokens, because I did not measure it.
