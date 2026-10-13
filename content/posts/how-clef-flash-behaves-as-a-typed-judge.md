---
date: "2026-10-13T01:40:00-04:00"
description: "Clef-Flash ranks items by the criterion text it receives, not by the label name, and its probabilities are not confidence I can use. Treating it as a calibrated judge is a mistake."
tags: ["ai-agents", "evals", "llm-as-judge", "calibration", "local-llm", "pipeline"]
slug: "how-clef-flash-behaves-as-a-typed-judge"
title: "How Clef-Flash behaves as a typed judge"
draft: false
summary: "Clef-Flash ranks items by the criterion text it receives, not by the label name, and its probabilities are not confidence I can use. Treating it as a calibrated judge is a mistake."
cover:
  image: "/og/how-clef-flash-behaves-as-a-typed-judge.png"
  alt: "How Clef-Flash behaves as a typed judge"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# How Clef-Flash behaves as a typed judge

Clef-Flash ranks items by the description of the criterion it receives, not by the name on the label, and its probabilities are not confidence I can use, so treating it as a calibrated judge is a mistake. The previous article in this series ended with a modest ordering signal. This one checks what that signal is made of, and what it is not.

A typed judge does three things at once. It picks one option from a fixed list, it returns a distribution over the options, and it returns a number it calls confidence. My pipeline reads all three. Each part can look fine on its own and still fail the job the pipeline needs. This article goes through the parts one at a time.

Every number here is agreement with Claude F1, the decision the pipeline already recorded. It is not accuracy, because the teacher was never measured against ground truth.

## What it is and what it was asked

`clef-flash` is a 9.5B-parameter model from Cloudflare. On my machine it takes 12 GB on disk, and its default context window is 16384 tokens. The vault calls it through a typed endpoint, `/v1/systemone`, which answers with a `choice`, a `probabilities` map and a `confidence` value. The question offers two options, approved and disapproved. In the probes the model never produced a `hold`, so that outcome has to come from a confidence threshold.

The pipeline uses the answer in one place. An approved item moves on to ingest, and a disapproved one stays out of the knowledge base. The model gives no reasons I can audit, so every test in this article is a comparison with the teacher.

My notes on the vendor lineage of these decision models (the Jev line, not Cloudflare) say that `confidence` is not the probability of the winning option. I did not check that claim myself, so I treat it as a claim about that lineage and not as a measurement of mine.

## It follows the description, not the name

The cleanest test swaps the text. In the C-swap variant, each category keeps its label but receives the description that belongs to another category. On 400 dev items, 54 of them disapproved, C-swap scored an AUROC of 0.321. The control that shows only the label names (C-label) scored 0.561. The baseline V0 scored 0.682.

Put the two extremes side by side. V0 and C-swap sum to 1.003, which I calculated from the two scores. If the model read the label names, swapping the descriptions would change almost nothing. Instead the ranking flipped to nearly its mirror image. The paired difference, C-swap minus V0, is −0.361 with an interval of [−0.519; −0.206], n=400.

So the model is reading what the criterion says. That is the strongest result in this series, and its scope is narrow: dev only, 400 items, one prompt family, one ordering of the options.

The practical reading is this. The criterion text is what a prompt author actually edits, so it is the part of the setup that moves the output. A label list is not enough to define the decision, and a change to the description should be treated as a change to the judge, not as wording. That reading is mine, and the test supports it only for this model and this corpus.

## The prompt effect is not established

Three prompt variants were scored. V0 reached 0.682, V1 reached 0.736 and V2 reached 0.785. The steps look like progress, and they are not. V1 minus V0 is +0.054 with interval [−0.043; 0.156]. V2 minus V1 is +0.049 with interval [−0.007; 0.111]. Both intervals include zero.

V0 is the only clean variant. The reviewer suspected that V1 and V2 were shaped by the review of round one's errors. The reviewer put it plainly: the prompt effect is not established, and 0.785 is not a headline number. Across the three variants, the sensitivity I can report is a median of 0.736 with a range from 0.682 to 0.785.

## The order of the options

The ablation also asked whether the answer changes when the options are listed in a different order. The probabilities were identical across orders. On V1 the flip rate was 0.0050, and the mean divergence was 0.0000 over 400 items.

That does not show the model is robust to order. A server that ignores the order would give these same numbers, and so would a model that is truly invariant. The reviewer's verdict was that the test is degenerate on this server, so it cannot measure robustness at all. I will not claim order invariance from this result.

The question matters for a practical reason. A judge whose answer depends on where an option sits in the list will not give the same decision twice for the same clipping. This test could not show whether that happens here, so the question stays open, and I would want it answered before any run that treats the answer as stable.

## Confidence is not something I can use

This section changed the design more than any other. The idea I had to drop was that the model's confidence tells you when it is right.

In round one I binned the confidence values on 588 decided items. Every bin had an accuracy between 61% and 67%. The bins were 82 items at 67%, 110 at 61%, 267 at 63% and 129 at 61%, and none reached 0.8. A value that does not separate right answers from wrong ones cannot serve as a threshold. A rule that held every item below 0.6 would have held 459 of the 588, which is 78%.

In round two, on the 421 test items, expected calibration error was 0.098 against 0.050 for a null, a ratio of 1.96. Coverage at 5% risk was zero, so no subset of the decisions met that risk level. The reviewer recorded that the top probability did not show usefulness, and I have no measurement that says otherwise.

The argmax is the failure a reader will feel most. On test, the model rejects about half of the approved items. Recall for approved was 0.512 on 375 items, so 183 approved items were rejected. On dev, the reviewer found the argmax of V2 rejecting 49% of all items, when the disapproved base rate is 13.5%. An AUROC of 0.719 is a statement about ordering. It says nothing about whether the top choice is safe to act on, and here the top choice sends about half the wanted items to the reject pile.

## Limits and what they cost

The probes found three limits that matter for anyone who would run this model in a loop.

The first is the context setting. The server ignores it: the same 20000-character text produced 6059 tokens under three different settings. Bodies above 64 KiB are rejected with HTTP 413, and a 58000-character body was accepted at 16358 tokens. At about 3.2 characters per token, with an overhead of roughly 173 tokens for the question, that puts the practical ceiling for this prompt near 58000 characters.

The second is `hold`. An empty state returned HTTP 400, and nonsense input came back as disapproved. So any `hold` has to come from a confidence threshold, and the confidence section above showed that threshold cannot be trusted.

These limits set one rule for the guard. A rejected call is not a decision. It counts as no decision, and the item stays out of the automatic path. That costs throughput, and I accept the cost. A quiet fallback to approved would turn a server error into a claim about the clipping, and nobody reading the state later could tell the two apart.

The third is latency, and this one was my mistake. The probe on a warm model took 11 ms per call, using 1200 characters. I read that as the cost of a call. A 20-item run then took 62 seconds, which is 3.1 seconds per call. Extrapolated to 3200 calls, that is 2.76 hours against a four-hour limit. The round-one run reported a median of 852 ms and a 95th percentile of 2110 ms over 700 items. I have not reconciled these figures. They measure different inputs under different conditions, and the cold-load cost was never measured at all, because the first call to each model was a rejected empty input that returned before the model loaded.

## The longer input was worse

Round two also tried a long arm: V1 with up to 40000 characters instead of 8000. It ran only on dev, and only descriptively. It scored 0.696 against 0.736 for V1. The paired difference is −0.054 with interval [−0.088; −0.023], n=390, because 10 items were marked truncated and dropped from the pair.

On this dev split, more text was worse for this model. I do not generalize that. It is one split, one model and one prompt family, and the test set was never run with the long arm. The 8000-character cut stays as the primary arm, and the reason is the measurement, not a belief that shorter is always better.

## Where I would use it (opinion)

This section is my opinion, not a result.

My untested hypothesis is that the model is more useful as a sorter than as a decider. A ranking that puts the likely approvals first helps a person who reads the top of a list, and it is cheap to check against the teacher. This series did not test that use, and it is not a recommendation.

What the data do not support is deciding alone. Its probabilities do not support a threshold, its argmax rejects about half of the items that should pass, and its `hold` never came out of the probes. Any decision that changes what enters the knowledge base should not rest on it.

The next article in the series is [Laya vs Clef-Flash](/posts/laya-vs-clef-flash/). It sets this judge next to `laya`, the 421M model from the same probes, on the same items.

## What I still don't know

- The cost of a cold load, since every latency number here was taken on a warm model.
- Whether a different corpus would change the ordering result, since all of it comes from one vault.
- How V0 scores on the test set, which was never run.
