---
date: "2026-10-13T01:20:00-04:00"
description: "A local model agreed with my triage labels on 62.9% of a stratified sample, a number that said almost nothing. The rare-class recall and the majority baseline are what failed it, and the gate was right to fail it."
tags: ["ai-agents", "triage", "evals", "classification", "local-models"]
slug: "the-gate-was-right"
title: "The gate was right: round one of a local triage model"
draft: false
summary: "A local model agreed with my triage labels on 62.9% of a stratified sample, a number that said almost nothing. The rare-class recall and the majority baseline are what failed it, and the gate was right to fail it."
cover:
  image: "/og/the-gate-was-right.png"
  alt: "The gate was right: round one of a local triage model"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# The gate was right: round one of a local triage model

The previous article in this series ended with a plan, and this one reports what the plan found: the 62.9% agreement a local model reached on my stratified sample said almost nothing, and the gate that rejected the model was right to reject it.

I keep a notes vault that runs an ingest pipeline. One of its steps, which the pipeline calls F1, decides whether a clipping is approved or disapproved and attaches a reason code. F1 is a stage name here, not the F1 score. Until now the stage has run on Claude. I wanted to know whether a small model on my own machine could take it over. Before the test I wrote down the rule: promote nothing unless the model passes a gate I set in advance.

## The corpus is 97% approved

The labeled corpus has 8048 files. 7819 are approved, 228 are disapproved, and one is neither. Disapproved is 2.8% of the data. I read the labels from the `decision:` field of each source page, and the counts come from the plan's baseline section.

At 2.8%, a random sample of 800 would hold about 22 disapproved items. That is too few to measure a rare class with any care. So I drew a stratified sample of 700 items: all 228 disapproved, 372 random approved, and 100 short approved items. The main set of 600 is the first two strata, which puts 38% of its items in the disapproved class.

That changes what accuracy means. On a set that is 38% disapproved, a predictor that says "approved" to everything gets about 62% right. On the real corpus the same predictor gets about 97% right. So any accuracy I report on the sample has to be read against the sample's own baseline, never against the population.

## The probe disproved one of my premises

Before running the model on anything, I expected a particular failure. A local server with a small default context window reads the head of a long document, returns a plausible answer, and nobody notices the rest was never read. I had written that down as a risk, and the first probe was built to check it.

It did not happen. The server rejected the request outright. A body over 64 KiB came back as HTTP 413. For the smaller model, a request over its token limit came back as HTTP 400, and the limit was 447 tokens including my question. The context-size option I set was ignored: the same text produced the same token count under three settings. The measured ratio was about 3.2 characters per token for the larger model and 2.46 for the smaller one. The "hold" outcome that the pipeline depends on never came out of the model at all. It has to come from a confidence threshold, not from the answer.

So the guard changed. A rejection is a closed failure, never a decision, and the long-input problem became an explicit error instead of a quiet cut. I was wrong about the mechanism, and the probe is what caught it before it reached the numbers.

## The numbers, with denominators

The larger model is called clef-flash (9.5B). It answered 600 of 600 items in the main set without an invalid output. Twelve came back as hold, which leaves 588 decided items. Here is what the report measured on those 588.

| Measure | Value | Denominator |
|---|---|---|
| Agreement with the Claude F1 label | 62.9% (370) | 588 |
| Majority baseline (always approved) | 62.1% (365) | 588 |
| Disapproved recall | 11.2% (25) | 223 |
| Disapproved precision | 55.6% (25) | 45 |
| Approved recall | 94.5% (345) | 365 |

Read the last two rows together. The model is good at saying "approved" and poor at finding the rare class. Approved recall is high because most items are approved, and the model leans toward that answer. The 25 correct disapproved calls are the part of the result that matters for the gate, and there are only 25 of them.

Latency was fine. The median was 852 ms and the p95 was 2110 ms on the general set. The 700-item run took 11 minutes 3 seconds of wall time. The smaller model, laya (421M), was much faster at 26 ms median and 30 ms p95. Speed was never the problem.

## Laya and the 1000-character cut

The smaller model has a 512-token context. My first plan set the short-profile cut at 350 tokens, computed as characters divided by four, which is 1400 characters. The probe showed that ratio was wrong for this model, at 2.46 characters per token, so the cut moved to 1000 characters.

Items between 877 and 997 characters turned into 448 to 497 tokens, which is over the limit. The guard marked them as truncated. On the main set, 7 of 116 short items were truncated, and across the whole sample of 178 short items the count was 10. Laya's agreement was 57/107 = 53.3%, against a majority baseline of 52.3% on the same 107. Its disapproved recall was 16/56 = 28.6%. Those are small denominators, and the report says so.

The lesson is about the cut. The safe limit sits below 1000 characters, not at it. Without the guard, those truncated items would have been scored as if the model had read them in full, and the error would have looked like a model error.

## The confidence score does not sort anything

The model returns a confidence value. I had assumed the pipeline's threshold of 0.6 would catch the model's mistakes. It does not. I binned the 588 decided items by confidence and agreement was flat across the bins: 67% on 82 items below 0.2, 61% on 110 items between 0.2 and 0.4, 63% on 267 between 0.4 and 0.6, and 61% on 129 between 0.6 and 0.8.

A rule of "hold if confidence is below 0.6" would hold 459 of the 588 decided items, which is 78%. That is not a filter. It is a different way of keeping the same ~60% agreement. Confidence is not telling right answers from wrong ones here, so any threshold built on it is a guess.

## Two accounts, two baselines

This is the part I would most like readers to check on their own data.

The first account is the one in the report. On the 588 decided items, the model's 62.9% beats the majority baseline of 62.1%. The gate table has a row for "accuracy above baseline," and it reads PASS, with a margin of 0.8 points. Taken alone, that row says the model clears one of the bars.

The second account comes from running the evaluation script again over a different pairing of predictions to labels. That run had 683 items with a prediction. The same model scored 453 of 683, which is 66.3%. The majority baseline on those 683 items is 67.3%, and I can check it from the confusion matrix: 460 of the 683 are approved, and 460/683 is 67.3%. On this account the model does not beat a predictor that always says approved. The margin is negative.

The two accounts differ because the sets differ. The second set includes the 100-item short stratum and drops the holds, so both the numerator and the baseline move. Nothing in either calculation is broken. But the sign of the margin flipped when the set changed, and that alone is enough to stop trusting a 0.8-point margin.

The sentence I would have written without the second account is "accuracy above the baseline is already a signal." On this sample it is not, and it cannot be, because the margin is smaller than the change that a different set of items produces.

The gate was right for a simpler reason than either account. The rule I wrote down required disapproved recall of at least 0.50, a threshold I had marked as provisional. The model reached 0.112. Accuracy could never have carried the decision, because the common class is almost the whole game.

There is also a reweighting trap in the report. If I reweight the same predictions to the population's 2.8% disapproved rate, the score is 92.2%. That number looks like quality, and on a real inbox it would be dominated by approved items. The report flags it as inflated, and I do not treat it as evidence.

## A planted negative

A gate is only trustworthy if it fails something trivial. I ran a predictor that answers "approved" to every item on the same sample. Its disapproved recall is 0 of 228, and the gate returned FAIL. It also cannot beat the majority baseline, because it is the majority baseline. That negative is the reason I believe the gate catches the trivial case first. A gate that never failed anything would have been green for free.

## The proxy and the labels

Two things make this round weaker than it looks, and I do not know how much each one costs.

The first is that the corpus is not the input the pipeline sees. I used source pages, which are notes that already went through ingest and were condensed by an earlier model step. The real F1 step reads raw clippings. The round-two plan records a later re-score of this round: AUROC near 0.53 and kappa between 0.07 and 0.09, which means no signal. The Opus advisor I consulted argued that this result condemns the proxy, not the model, because condensing the source pages may have erased the signals that mark junk. I suspect the same. This round cannot tell the two apart.

The second is that the labels come from the pipeline itself. Some of the 228 disapproved items may be debatable, and I have not yet reviewed the top false negatives and false positives. So part of the 11.2% recall may be the label, not the model. The report makes the same point and asks for that review before anyone concludes the model is wrong.

Even with those caveats, the result is for this prompt. I wrote the instructions once and never varied them, so this round says nothing about the model in general.

## Options, and why B

The report ended with three options and recommended none. Option A was to adopt no local F1 and keep the current Claude step. Option B was to run a new shadow on real clippings from the inbox, with human labels, and test prompt variants before any decision. I took its direction but dropped the human labels: round two uses the Claude F1 decisions as the reference. Option C was to ship a version with everything on the local model behind a flag. Under the gate I had set, the numbers did not support C.

I chose B. A keeps the question open forever. C asks me to trust a number that has just failed its own gate. B measures on real inbox items and lets me vary the prompt. Without human labels it does not separate the label problem from the model problem, and I say so. Nothing gets promoted under B, and the routing file stays exactly as it was.

The next article covers what that second round produced: [AUROC 0.719, and the list of things I'm not allowed to say](/posts/auroc-0-719-and-what-i-cant-say/).

## What I still don't know

How much of the error is the label, and whether condensing the source pages erased the junk signal. Round one cannot answer either question.
