---
date: "2026-10-13T01:50:00-04:00"
description: "Laya, a 421M model, left the shadow test. The size cut meant to protect it did not hold, and its first round showed no signal, so speed was never the reason."
tags: ["local-llm", "ollama", "evals", "shadow-testing", "model-routing"]
slug: "laya-vs-clef-flash"
title: "Laya vs Clef-Flash: why the smaller model left"
draft: false
summary: "Laya, a 421M model, left the shadow test. The size cut meant to protect it did not hold, and its first round showed no signal, so speed was never the reason."
cover:
  image: "/og/laya-vs-clef-flash.png"
  alt: "Laya vs Clef-Flash: why the smaller model left"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Laya vs Clef-Flash: why the smaller model left

The previous article in this series looked at how clef-flash behaves as a typed judge. This one covers the other model in the test, laya, and why it left: the size cut that was meant to protect it did not, and its first round showed no signal. The tempting bet is that a smaller, faster model pays off when the item is short. My data never gave it that chance, and speed was never the problem.

## Two models, side by side

The larger model is clef-flash, 9.5B parameters with a 16384-token context. The smaller one is laya, 421M parameters with a 512-token context. Laya ships open weights under Apache-2.0, according to the note on the model in my vault.

That note also records the vendor's language claims. The vendor describes laya as English-first. It has a multilingual checkpoint that the vendor says covers more than 100 languages, but the vault records that the checkpoint does not improve Portuguese. In the vendor's table, as I noted it, Portuguese scores 0.450 on the multilingual checkpoint and 0.470 on the English one, against 0.820 on English. I did not measure those numbers. They are the vendor's. My corpus is mostly Portuguese, so that gap alone was enough to make me doubt the small model before any run.

## Speed

On the general set, laya had a median of 26 ms and a p95 of 30 ms. Clef-flash had a median of 852 ms and a p95 of 2110 ms. The gap is real, and it is large. It did not decide anything, because the question was never how fast the answer comes. The question was whether the answer agrees with the label and whether the model read the whole item.

## The cut that did not protect it

The probe measured laya at 2.46 characters per token. My plan had first set the size cut at 350 tokens, computed as characters divided by four. That is 1400 characters. At the probe's ratio, 1400 characters is about 570 tokens, which is over the 447 that laya accepts with the question included. So the cut moved to 1000 characters.

The first round then showed that 1000 was not safe either. Items of 877 to 997 characters reached 448 to 497 tokens against the 512 window. The 64-token guard marked them as truncated. That happened to 7 of the 116 short items in the main set, and to 10 of the 178 short items across the whole sample. Without the guard, those items would have been scored as if the model had read them in full, and the result would have looked like a model error. The cut was wrong twice. The second error only showed up on real items, after the probe had already been run.

## Round one

Laya agreed with the Claude F1 label on 57 of 107 decided items, 53.3%. The always-approved predictor scored 52.3% on the same 107. That is a margin of one point. Its disapproved recall was 16 of 56, or 28.6%. Its disapproved precision was 16 of 26, or 61.5%. The report marked the accuracy-above-baseline row as a pass, and it marked the recall row and the truncation row as failures. The one-point margin did not decide the gate.

The two models were also compared on the items both had decided. That set has 106 items. They agreed on 75 of them, 70.8%. Against the label, clef-flash scored 57.5% and laya scored 50.0%, both on the same 106. The eval script produced a second opinion as well. It gave laya 103 of 164, or 62.8%, against a majority baseline of 65.9%, so it does not beat the majority either. Only 164 items matched, below the 200 the script targets. Items in the 250-to-450-token band, the one that matters for the limit, number exactly one. One item says nothing. I cannot conclude anything about where the real limit sits.

## Why it left

The round-two plan has a section 0 that lists its assumptions. Item 4 is titled "Laya out": round one and the vendor's external numbers show no signal, so only clef-flash stays. The reason is written in the plan, not left to memory. The same plan records that the round-one re-score, with the first prompt, gave an AUROC of about 0.53 and a kappa between 0.07 and 0.09. That AUROC belongs to the plan's re-score, and I am citing it, not measuring it again here.

The Opus advisor review was blunter. In the notes of that review, the first cut is laya, because round one showed no signal. The AUROC near 0.53 comes from the round-two plan's re-score of round one with the first prompt, not from laya alone.

Leaving is not a verdict on the small model's design. It is a choice about where the next round's effort goes. I read it this way: with laya out, every remaining question about the prompt and the labels has one model to answer for.

The limit of this decision matters. It holds for this corpus, which is mostly Portuguese and built from source pages that were already distilled, and it holds for this prompt. I did not test laya on English text. Nothing here says laya is a weak model in general. It says that on my data, with this cut, it could not earn a second round.

## A guess, not a result

I suspect a 421M model is worth testing when four things hold together. The item is short. The text is in English. The label is stable. The context is controlled, so nothing gets cut silently. This is my opinion, based on the vendor's English numbers and on my own round-one failure. It has no measurement behind it. The first test I would run is a short English set under the cut, with a cold-load run, because I have not measured a cold load for either model. I would also keep the cut as a rejection, never as a silent shortening, so that a failed item shows up in the count instead of in the score.

The next article in the series, [Claude as teacher, a 9.5B model as student](/posts/claude-as-teacher/), takes the larger model as the only one left and asks what role the expensive models play around it.

## What I still don't know

Whether laya does better on English text, whether the multilingual checkpoint helps Portuguese on this vault, and how either model behaves from a cold start.
