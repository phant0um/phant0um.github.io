---
date: "2026-10-13T02:00:00-04:00"
description: "In this vault a local decision model orders work but does not decide it. The expensive model's value moved from doing the work to teaching the local model and reviewing the plan, and the reviews caught errors the tests did not."
tags: ["ai-agents", "model-routing", "evals", "local-models", "claude", "review"]
slug: "claude-as-teacher"
title: "Claude as teacher, a 9.5B model as student"
draft: false
summary: "In this vault a local decision model orders work but does not decide it. The expensive model's value moved from doing the work to teaching the local model and reviewing the plan, and the reviews caught errors the tests did not."
cover:
  image: "/og/claude-as-teacher.png"
  alt: "Claude as teacher, a 9.5B model as student"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Claude as teacher, a 9.5B model as student

The previous article in this series compared the two local models and ended with only `clef-flash` left. This one argues that the useful lesson is about roles: in this vault the local decision model orders, it does not decide, and the expensive models earned their place by teaching the local one and by reviewing the plan. The tempting claim, that the local model replaces the expensive one in triage, is the claim this vault does not support.

## Why Laya left and clef-flash stayed

Round 1 compared two local candidates. The first was `clef-flash`, which the reviewer's correction note attributes to Cloudflare. The second was Laya, an open-weights model (421M parameters, Apache-2.0) that the vault's system note describes as English-first. The vault's note on Laya's model card also reports lower numbers for Portuguese than for English, and this corpus is mostly Portuguese.

The round 1 numbers were close to the floor. `clef-flash` got 370 of 588 decisions right (62.9%), against 62.1% for always answering "approved". Laya got 57 of 107 (53.3%), against a 52.3% baseline. Laya also had a context problem: clippings of 877 to 997 characters reached 448 to 497 tokens against a 512-token context, so the guard marked them as truncated. Across Laya's 178 short items, 10 were truncated.

The round 2 plan cut Laya in its section 0.4, with the reason written down: round 1 and the external sources showed no signal, so only `clef-flash` stays. That reason is limited to this corpus and this prompt. It says nothing about Laya in general. It also means I did not test Laya on an English corpus, so I cannot say whether the problem was the model or the fit.

## Claude as teacher, and why agreement is not truth

Round 2 uses the expensive model as the answer key. The labels are the decisions Claude F1 already wrote into the state. That gives free labels, and it also gives a trap: a system that is scored against its teacher learns the teacher's habits, not the truth.

The orchestrator named the trap before any run. Self-improvement without an independent truth is circular, so it set three locks. The first is a frozen test set that stays outside the loop; the prompt generator never sees it. The second is a split by group rather than by item, so near-duplicate clippings cannot sit on both sides. The vault's two eras appear as strata inside every split. The third is a rule in the report: the metric is "agreement with Claude F1", never "accuracy", and the limit of that claim is written next to every number.

The number the round 2 report allows is: modest ordering signal, AUROC 0.719 [0.639; 0.793] on the test set (46 positives, 375 negatives), agreement with Claude F1. Those locks limit the damage, but they do not measure the ceiling. Nobody measured how much Claude F1 agrees with itself, so I cannot say how much of the agreement is signal and how much is the teacher's own noise. The orchestrator also offered a second-family judge, the local Gemma, to vote on the disagreements. I did not authorize it, so the judge is not in the data and no result depends on it.

## Opus as advisor, before the plan

Before any wave was written, an Opus advisor reviewed the plan. The plan's log records the verdict twice: first redo, with 16 findings, then approve with corrections, with 12. One assumption carries most of the weight, called Porta 0. The triage skill says there is no Ollama dependency (ADR-003), and it puts the F1 classifier under HR1, the rule that locks the F1 model because of prompt-injection risk on untrusted input. Promoting a local F1 would therefore need both amended, and that is a human decision. A passing shadow does not get around that policy, so the shadow cannot change what runs by itself.




## Opus as reviewer, four rounds

The reviewer's numbers are the reviewer's claims. I read each figure back against the report files, but I did not recompute them myself. What the reviewer changed is the point of this section.

Round 1 reviewed the ablation on the 400-item sample. It returned twelve findings and asked for corrections. It recomputed the AUROCs by counting pairs. It found that the 54 positives came from about five batches, so a per-batch check widened the V1 interval to [0.543; 0.866], and the plan had not pre-registered that check. It found that the order test was degenerate: the probabilities were identical across the three orders, so every "flip" was an exact tie, and the plan stopped spending on that test. It also found that the argmax of V2 rejected 49% of items against a 13.5% base rate, so an AUROC is not a classifier, and that the prompt effect, V1 minus V0 at +0.054 with interval [−0.043; 0.156], was too small to call a result.

Rounds 2 and 2b reviewed the candidate batch and then the code diff, with nine findings each. The base variant was ambiguous, because the ablation script broke ties by order, so the base was fixed in writing before the lock. The `choose` rule that the plan cited did not exist, and it was implemented. One candidate rested on a domain policy that the canonical policy does not have, and it was removed. The planted test isolated one of five clauses, so it was rewritten to carry one negative per clause, and mutating any clause now fails a test.

Round 3 reviewed the frozen evaluation, which was run once against the test set. It returned eight findings, and two of them mattered most. The cost function used the opposite sign to the plan's section 0.9. Under the code's sign, the Bayes rule rejects everything at C=10, which matches the majority floor of 375 of 421, and under the plan's sign approving everything beats every policy. Second, the cascade's "passes" claim was loose. The 0.976 agreement counted escalated items as correct, and the null comparison, approving everything at the same budget, gave about 22 leaks against 10 observed, with agreement 0.948 against 0.976 and no interval on either. The auto-approved side also violated its own rule: 10 of 199 leaked, a rate of 0.0503 against a declared 0.05, with a Wilson interval of [0.028; 0.090]. The lot-level AUROCs were 0.817 for 19 September (n=15), 0.550 for 23 September (n=6), 0.708 for 26 September (n=21), and 0.663 for the undated items (n=4).

Round 4 reviewed the written documents. It returned seven corrections. The most useful was a tag: the calibration claim belonged to the vendor lineage, not to our measurement, so the tag was reassigned, and the normative sentence became a labelled proposal. The reviewer also checked that the routing file was unchanged, using its blob hash.

None of these failures showed up as a red test. The tests were green, and the reviewer found a reversed sign, a leak above the declared rate, and a claim filed under the wrong source. That is the part I would defend: the review read the code and the arithmetic, and the suite did not.

## The orchestrator orchestrates, the executor executes, and practice diverged

The plan's frontmatter names the roles: orchestrator `claude-sonnet-5-5@medium`, executor `claude-haiku-5-5@low`, advisor `opus@high`, with the orchestrator as writer. I do not claim which model ran the main session. The practice diverged in two places.

In round 1, the code for W3 was written by the local 12B Gemma under the orchestrator's supervision, with three corrections; the round 1 report says so directly. The executor role did not stay with Haiku in that run.

In round 2, the orchestrator ran the W3, W4 and W5 inference itself instead of handing it to Haiku executors. The inference is a local script, a mechanical step. The session notes say the executor choice was inherited from routing and was never reconsidered for the shadow run. A separate mistake showed up in the estimate: I read the 11 ms of a warm probe as the cost of a call. The probe measured 3.1 s per call across 20 items (62 seconds total), about 280 times slower. The 11 ms figure came from a hot probe with 1,200 characters, and that input length was far from the real clippings. A latency estimate needs a probe on real inputs, not a memory of a warm call.

## Gemma 12B in F2 and F4: a map without measurements

The drain's routine now names the local 12B Gemma as the model for the heavy phases F2 and F4, called through `/api/chat`. Nothing measures that choice yet. The round 2 report says plainly that F2 and F4 were not measured, and the drain itself says the gold standard and the promotion criterion for F2 and F4 do not exist yet.

The orchestrator proposed a way to start: compare the local outputs against the Claude outputs already saved, and add mechanical checks for cited provenance, valid schema, and links that do not exist. It would stay in shadow with no promotion, the same as F1. The proposal accepts the limit that agreement with Claude is not proof of quality. It has not been authorized, and I have not run it.

## What the economy looks like, and what is not measured

The drain's budget comment puts a Claude `claude -p` call for F1 or F2 at about US$0.086 per call, which is the vault's own estimate and a fixed cap line. The real saving from F1 is not measured. F1 is one batch call per drain, so the number depends on how many calls a drain makes, and the orchestrator proposed measuring that offline from the pipeline log at no cost. That has not been done, so I am not putting a dollar saving on this.

## Opinion: decision models in this vault

This section is my opinion, not a result. A local decision model belongs in an ordering queue, not in a gate that acts without review, until the vault can promote it by a rule the model can fail. The reviews did more for trust than any local score did, because they caught a reversed sign and a leak above the declared rate by reading the code. My hypothesis, untested here, is that the expensive model is better spent on teaching and review while a cheap one only orders. I may be wrong if the cost of a local run is the only number that matters. The vault does not yet know that number.

## What I still don't know

Whether Claude F1 agrees with itself, which decides how much of the agreement is signal. Whether a judge from another model family would change the AUROC on the contested items. Whether the local F1 pays off once you count one Claude call per drain.

This closes the series. The first article, [Probe the limits first](/posts/shadow-testing-a-local-model/), set the physical limits of the local models. The roles in this article only mean something inside those limits.
