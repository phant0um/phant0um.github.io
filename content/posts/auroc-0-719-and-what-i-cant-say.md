---
date: "2026-10-13T01:30:00-04:00"
description: "A local model orders my pipeline's approve and disapprove decisions a little better than chance. The honest claim is narrower than the number, and a reviewer, not the metric, is what narrowed it."
tags: ["ai-agents", "evals", "llm-as-judge", "pipeline", "calibration", "claude"]
slug: "auroc-0-719-and-what-i-cant-say"
title: "AUROC 0.719, and the list of things I'm not allowed to say"
draft: false
summary: "A local model orders my pipeline's approve and disapprove decisions a little better than chance. The honest claim is narrower than the number, and a reviewer, not the metric, is what narrowed it."
cover:
  image: "/og/auroc-0-719-and-what-i-cant-say.png"
  alt: "AUROC 0.719, and the list of things I'm not allowed to say"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# AUROC 0.719, and the list of things I'm not allowed to say

The previous article in this series was about a gate; this one is about the claims I had to drop after the numbers came in. The honest result of round two is the narrowest version I have: a modest ordering signal, and nothing wider.

The setup is a notes vault whose ingest pipeline asks a model whether a web clipping should be approved or disapproved. Round one was the first look. Round two I wrote down before running anything, then sent to an Opus reviewer at each stage. The metric throughout is agreement with Claude F1, the decision the production pipeline already recorded. Agreement is not accuracy, because the teacher is not ground truth, and its own ceiling was never measured.

## 1. Design without a human

The teacher is the decision Claude F1 already wrote into the pipeline state. The state has 2532 entries: 1452 approved, 338 disapproved and 742 with no decision, which I left out. Of the 338 disapproved, 310 have a null `reason_code`. So most of the labels arrive without the explanation that would let me audit them.

Splits are by group, not by item. The 1744 groups mean a near-duplicate clipping cannot sit on both sides of a split. Dev has 573 approved and 77 disapproved. Select has 300 and 34, confirm 204 and 23, and test 375 and 46. Another 158 disapproved had no file on disk. I excluded them and counted them, instead of dropping them silently.

Select was the only split the loop could look at. Confirm and test stayed frozen, and I opened the test set once.

## 2. The 8000-character cut, and the long arm

The production triage reads at most 8000 characters of a clipping, with `head -c 8000`. My first plan sent the model the whole body. The cut was a fidelity fix: the model should see what the teacher saw. I strip the YAML frontmatter before cutting, not after. That is a deliberate choice, because the frontmatter can carry the decision field, and a model that reads a `decision:` line is not measuring anything about the clipping.

Then I asked whether a local model could simply read more, since local tokens are free. Only partly. Reading more costs time and memory, and the server ignores the context-size setting. The ceiling is 16384 tokens, and anything over 64 KiB is rejected. A latency probe on 20 items took 62 seconds, 3.1 s per call. The full run predicts 3200 calls, 2.76 hours, against a 4-hour limit.

So 8000 characters became the primary arm. A 40000-character version of V1, called V1-long, ran only on dev, and only descriptively. It cannot decide the verdict.

The result: V1-long scored 0.696 against 0.736 for V1. The paired difference is −0.054 with interval [−0.088; −0.023], n=390, because 10 items were truncated. What I can say is that on dev, more text was worse for this model. I am not claiming that reading less is better in general. It is one model, one dev split and one prompt family.

## 3. Ablation: the model follows the description

The ablation ran on 400 dev items, 54 of them disapproved. V0 is the only clean variant. It scored 0.682 with interval [0.601; 0.765] at 95%. V1 scored 0.736 and V2 scored 0.785, both at the 97.5% level the rule uses for the deciding lines. C-label, which shows only the category names, scored 0.561. C-swap, which swaps the category descriptions, scored 0.321.

C-swap is almost the mirror of V0, and the two sum to about 1.00. The model reads the description of the criterion, not the name on the label.

| Paired difference (dev, AUROC) | Difference | 95% interval | n |
|---|---|---|---|
| V1 − V0 | +0.054 | [−0.043; 0.156] | 400 |
| V2 − V1 | +0.049 | [−0.007; 0.111] | 400 |
| V1-long − V1 | −0.054 | [−0.088; −0.023] | 390 |
| C-swap − V0 | −0.361 | [−0.519; −0.206] | 400 |

The first two rows include zero, so the prompt effect is not established. Moving from V0 to V1 or V2 is not a difference I can defend. The ablation ran the options in three orders for V1 and C-swap. The probabilities were identical across orders, so the flip rate and divergence measure nothing on this server.

The planted failures check the gate itself. An empty body gave 100 invalid results. A body truncated at 50 characters gave 100 holds.

## 4. The loop that kept V2

The loop took V2 as its base, fixed in writing before any select prediction. It tried four candidates on select, with 334 usable items. The rule needed a gain of at least 0.02, a paired interval that excludes zero, and a margin over the length floor. The candidate set was cut from five to four after round-two review.

Candidate 1 scored 0.746 against 0.745 for the base. That is a gain of 0.002 with interval [−0.048; 0.061]. Candidates 2 to 4 scored lower. None was eligible, so V2 stayed.

Keeping V2 was the expected outcome, and I wrote it down in advance. With only 34 disapproved items in select the power is low, so a loop that finds nothing is not a broken loop. The more useful part of the loop is the pre-registration itself. It fixed the base before the select numbers existed, so the choice of V2 could not be reopened after the fact to fit a result.

The dev ablation had already shown a pattern in the base's errors: approved items were over-rejected at every length, with recall of 0.572 on dev. Candidate prompts were not expected to fix that. The fix for over-rejection belongs to the thresholds in the cascade, and that is where I tried to put it.

## 5. The test

The test ran once, on 421 items, 46 of them disapproved. AUROC was 0.719 with interval [0.639; 0.793]. The length floor on the same items was 0.526, and the model's margin over it has a lower bound above zero, at 0.088.

Recall was 0.512 for approved and 0.783 for disapproved, so the argmax rejects about half of the approved items. That is the same over-rejection I saw on dev, now on data the loop never touched. Calibration is weak. Expected calibration error is 0.098 against 0.050 for the null, a ratio of 1.96. Coverage at 5% risk is zero. The hold rate was 0.005.

I read these numbers as a statement about the scoring, not about the clippings. A model can rank items reasonably and still be unusable as a decision maker, because its probabilities do not mean what a threshold needs them to mean. The cascade I built on top of it then had to choose its thresholds on select and hope they held on test. They did not hold cleanly, which is the subject of the next section.

## 6. What the reviewer took back

The reviewer recomputed the main numbers and got the same AUROC. What it took back was the scope of the claim.

- **Batches.** The 54 dev positives come from about five triage batches. Recomputed per batch, the lower bound falls under 0.60 for both V1 and V2 (the reviewer's figures: 0.543 and 0.593). On test, the batches score 0.817 with n=15, 0.550 with n=6, 0.708 with n=21, and 0.663 for four items with no date. A bootstrap by batch has a lower bound of 0.590. The plan did not pre-register that analysis, so it is a sensitivity check.
- **Suspect labels.** Seven of the 54 dev positives come from the `fiap` material, with no found date. The reviewer flagged those labels as suspect. I have not checked them.
- **The cascade.** The approval threshold is the smallest probability among items predicted approved on select. So it accepts every item the model calls approved and escalates the rest: 222 of 421, or 53%. The block side is empty, with 4 items on select and none on test. The 0.976 agreement counts escalated items as correct, because the fallback is the teacher. The reviewer's null, approving everything at the same budget, leaks about 22 items against 10 observed. Its agreement is 0.948 against 0.976. The 0.193 gain over random escalation measures over-rejection, not confidence.
- **The allow violation.** Leakage on the allow side was 10 of 199, or 0.0503, above the 0.05 limit. The Wilson interval is [0.028; 0.090]. Agreement drifted from 0.962 on select to 0.953 on confirm to 0.950 on test. Five of the ten leaks come from the 09-26 batch, and two are near-duplicates in different groups.
- **The cost sign.** The cost function uses the opposite sign to the plan. The plan made rejecting a good item the costly mistake. The code made letting a disapproved item through the costly one. Under the plan's sign, approving everything wins at every cost ratio tested. Under the code's sign, the argmax beats the Bayes policy at every ratio, which points to miscalibration. It was an undeclared deviation in the code, and the final report records it now.
- **The test is not fresh for V2.** Round one used all the disapproved items and reviewed the largest false positives and negatives before V1 and V2 existed. Only V0 is clean, and V0 was not measured on test. Whether V1 or V2 leaked against the test body was not measured either.

## 7. Floors and selftests

The plan brought three floors: majority, length and random escalation. The majority floor is 0.891 on test. The length floor is the AUROC of text length, oriented either way: 0.565 on dev and 0.526 on test. The reviewer added an era floor of 0.589 on test. Within each era the model still scores 0.755 for post and 0.713 for pre. The random-escalation floor gives 0.782 agreement on test, and the oracle gives 1.000.

The gate was tested against planted cases. A perfect predictor scored 1.000 and was labelled signal. Random scores gave 0.5145, with interval [0.4715; 0.5627], and were labelled no-signal. Always-approved gave 0.500 and was also labelled no-signal. These are synthetic predictions over the 1632 real dataset items, 180 of them disapproved. They prove the gate can say no. They say nothing about the model.

## 8. The sentence I can say

This is the sentence I am willing to sign:

> modest ordering signal, AUROC 0.719 [0.639; 0.793] on the test set, agreement with Claude F1.

The reviewer's list of what the final step may not claim is longer, so I'll write it out in plain words. The final step may not claim:

- that the model is usable for triage
- savings above 47% of calls
- a guarantee of a 5% violation rate
- that `max_p` is useful
- any gain in cost
- generalization beyond the three batches
- any effect of the prompt
- a recommendation to promote the model

A confidence interval above the floor does not make a model useful. This interval is for an ordering measure over 46 disapproved items, 42 from three batches and 4 undated, and its lower bound drops to 0.590 when the bootstrap resamples by batch.

The next article in the series, [how Clef-Flash behaves as a typed judge](/posts/how-clef-flash-behaves-as-a-typed-judge/), looks at the model itself: what its probabilities and its reading of the criterion can and cannot carry. How far the teacher can be trusted waits for the last article. In this round the claim narrowed because the reviewer kept checking it, not because I was careful on my own.

## What I still don't know

- The teacher's ceiling. I have not measured how often Claude F1 agrees with itself, so every agreement number is against a reference of unknown quality.
- V0 on the test set, and whether V1 or V2 leaked against the test body.
- The label quality of the 09-26 batch and of the `fiap` items.
