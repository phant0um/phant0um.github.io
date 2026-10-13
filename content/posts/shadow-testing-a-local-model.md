---
date: "2026-10-13T01:00:00-04:00"
description: "Before comparing a local model with Claude on triage, I measured its physical limits. The probe overturned two of my assumptions, and the routing moved from tying models to phases to a size cut per item."
tags: ["local-llm", "ollama", "evals", "shadow-testing", "model-routing"]
slug: "shadow-testing-a-local-model"
title: "Probe the limits first: designing a shadow test for a local model"
draft: false
summary: "Before comparing a local model with Claude on triage, I measured its physical limits. The probe overturned two of my assumptions, and the routing moved from tying models to phases to a size cut per item."
cover:
  image: "/og/shadow-testing-a-local-model.png"
  alt: "Probe the limits first: designing a shadow test for a local model"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Probe the limits first: designing a shadow test for a local model

Before you compare a local model with a cloud model, measure the local one's physical limits, because the design you draw from assumed limits will break on the first real input. I assumed four characters per token and a server that cuts long inputs quietly. Both were wrong, and the probe that showed it cost a few minutes.

This is the first article in a series about a shadow test of local models on the triage step of my notes vault.

## What the shadow test is for

The vault runs an ingest routine I call `pipeline-drain`. It has five phases. F0 is deterministic filtering. F1 is triage, where a decision model says whether a web clipping goes into the knowledge base. F2 is ingest, where a generative model writes the source page. F3 is a deterministic report. F4 is learning, also generative.

Today F1 runs on Claude. I wanted to know whether a small model on my own machine could take it over. The vault's rules say a change of who decides needs evidence first, so the test runs in shadow. The local model sees the same items Claude already classified, writes its own decision to a separate file, and touches nothing else. It does not merge, and it does not write state, manifest or receipts. Promotion is a separate decision that needs a human.

The design has four parts. A POST to the local Ollama server, using the standard library and no new dependency. A script that reads the shards Claude already classified. Validation of the local answer with the validator the vault already had. And a JSONL file with both decisions side by side.

In the shadow folder, `f1_shadow.py` is 220 lines and `f1_metrics.py` is 285, before tests. The metrics code grew because the question changed. It stopped being "does the model run" and became "does the gate detect a model that is wrong". A gate that cannot fail proves nothing, so the metrics had to earn their lines.

## The physical limits

The machine is a Mac with 24 GB of RAM. The number that matters is the GPU cap, which is lower than the total. On this machine the local models I could run were:

- `clef-flash`, 9.5B parameters, 12 GB on disk by `ollama list`, default context 16384.
- `laya`, 421M parameters, context 512.
- `gemma4:12b-mlx`, 7.7 GB.

A larger 18 GB generative model does not fit the 24 GB GPU cap, so it was out. The rule I adopted was one model loaded at a time, with `keep_alive: 0` whenever the phase changed. That rule shapes everything else. A shadow run that mixes a decision model and a generative model has to unload one before it loads the other, and it cannot run them side by side.

## The probe disproved two assumptions

Before running the model on anything, I wrote a small probe against the endpoint. It found three facts.

First, the context-size option is ignored. The same 20000-character text produced the same token count under three different settings, so I cannot tune the window from the client.

Second, there is no silent truncation. I had expected the server to read the head of a long document and answer anyway. It rejects instead. `clef-flash` returns HTTP 413 above 64 KiB, and `laya` returns HTTP 400 above 447 tokens, a limit that includes the question. A rejection is a visible failure. It is also the reason the numbers in the later articles can be trusted, because a quiet cut would have scored items the model never read.

Third, my ratio was wrong. I had used characters divided by four. The probe measured about 3.2 characters per token for `clef-flash` and 2.46 for `laya`. The model also never emitted a "hold" answer. An empty input returned HTTP 400, and nonsense came back as "disapproved". So "hold" has to come from a confidence threshold, not from the model's answer.

The guard changed with these facts. A rejection now means the item failed closed and never counts as a decision.

## Routing: one fixed model for F2 and F4, a size cut inside F1

My first routing idea tied the generative model to the decision model. If F1 runs on `laya`, F2 and F4 run on Gemma, and if F1 runs on `clef-flash`, F2 and F4 run on a larger model. The larger model did not fit the GPU cap, and `laya` does not cause the choice of Gemma. F2 and F4 are the heavy phases, so they run on Gemma regardless of what F1 used.

Inside F1 the choice is per item, not per phase. The script picks the profile from the size of the cleaned input: a short item goes to the light profile (`laya`), a longer one to the full profile (`clef-flash`). Coupling the models across phases would make the shadow hard to read, because a drop in quality could not be assigned to one phase. The routing never asks a model to choose.

## Where the measurements broke the design

The plan put the size cut at 350 tokens, computed as characters divided by four. That is 1400 characters. At the probe's 2.46 characters per token, 1400 characters come to about 570 tokens, which is over the 447 that `laya` accepts. The cut moved to 1000 characters.

The first real round then showed that 1000 is not safe either. Items of 877 to 997 characters reached 448 to 497 tokens against the 512-token window, and the guard marked them as truncated. The safe limit sits below 1000 characters. Without the guard those items would have been scored as if the model had read them in full, and the error would have looked like a model error.

## What the first round said

The first round used a fixed prompt and a labeled corpus. `clef-flash` matched the label on 370 of 588 decided items, 62.9%. Always answering "approved" matched 62.1%, so the model was 0.8 points above a predictor that never thinks. It caught 25 of 223 disapproved items, 11.2%. The gate failed. `laya` was worse, with 57 of 107 decided items, 53.3%.

The next articles in this series go into the numbers: how the gate was built, what it caught, and how a second round narrowed the claim. Here the point is smaller. The limits came first, and they changed the design before any result existed.

## The trade-off

The shadow code lives in a plan folder under `07-QUEUE`, not in `04-SYSTEM`, where the vault keeps its scripts. That was deliberate. The experiment should not look like part of the system, and nothing was merged into the routine. The cost is that someone looking for the shadow scripts in the usual place will not find them.

The next article covers the plan I wrote for this test, and why its checks had to fail before any code existed: [plans that fail before they run](/posts/plans-that-fail-before-they-run/).

## What I still don't know

How the Gemma profile behaves in F2 and F4, since I measured only F1. And how a cold load changes the latency, because the probe ran on a warm model.
