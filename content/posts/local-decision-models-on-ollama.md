---
description: "I surveyed seven decision models on Ollama and ran four of them on my own triage data. None beats the lazy baseline on accuracy at the default rule. What separates d3 and kev from d1 is ranking and order stability, laya ranks at chance in this Portuguese-prompt setup, and the vendor pages report neither. One role showed signal in an exploratory, unregistered check: approving locally the clippings a model finds least suspicious."
tags: ["local-llm", "ollama", "decision-models", "evals", "benchmarks", "model-routing"]
slug: "local-decision-models-on-ollama"
title: "Seven local decision models surveyed, four tested: none beats answering approved at the default rule"
date: "2026-10-24T13:12:13-04:00"
draft: false
summary: "I surveyed seven decision models on Ollama and ran four of them on my own triage data. None beats the lazy baseline on accuracy at the default rule. What separates d3 and kev from d1 is ranking and order stability, laya ranks at chance in this Portuguese-prompt setup, and the vendor pages report neither. One role showed signal in an exploratory, unregistered check: approving locally the clippings a model finds least suspicious."
cover:
  image: "/og/local-decision-models-on-ollama.png"
  alt: "Seven local decision models surveyed, four tested: none beats answering approved at the default rule"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Seven local decision models surveyed, four tested: none beats answering approved at the default rule

None of the local decision models I tested beats the laziest classifier there is: answer "approved" every time. On my data that classifier is right 89.8% of the time. The most accurate model I ran, at its default decision rule, is right 87.7% of the time. The models differ in two other ways. One is how well they rank the rare bad item above the common good one. The other is how much their answer changes when I only reorder the options. On the seven Ollama library pages I read, I found neither reported as a number. One use did show signal: letting the model approve the clippings it finds least suspicious, which I cover near the end.

This article is the long version of that claim. It covers what a decision model is, which seven I surveyed, what each vendor measured, what I measured, and where the two disagree. It is long because the short version ("model X is best") would be false in a way I can show.

## What a decision model is

A decision model does not write text. You send it a piece of text, called the state, and a set of named questions. Each question lists the answers you allow. The model returns a probability for each allowed answer, in one forward pass, with zero generated tokens. Ollama exposes this through a dedicated endpoint, `/v1/systemone`. Its request shape follows the Jev API from TypeSafe, a hosted service for the same kind of call, and the "System One" name in the docs refers to that family of models. Models that support it carry a `decision` capability that `ollama show` prints.

There are three question types. A `choice` question maps option names to descriptions and returns a probability per option. A `noul` question is a yes/no and returns the probability of true. A `score` question takes an ordered list of levels and returns a probability-weighted level. A request can carry up to 64 questions about the same state, and they share one pass.

My triage call looks like this. The real prompt is in Portuguese, so the text below is my translation of it:

```json
{
  "model": "kev:4b-q4_K_M",
  "state": "<the clipping text>",
  "questions": {
    "decision": {
      "type": "choice",
      "instructions": "Triage for a personal vault about AI agents, software engineering and productivity. ...",
      "criteria": {
        "approved": "at least one reusable idea, technique, datum or method ...",
        "disapproved": "only promotion, announcement, link lists, or off-domain ...",
        "hold": "text cut off, unreadable, or too short to decide ..."
      }
    }
  }
}
```

The answer comes back as a chosen option plus `probabilities` for all three. That output is the reason to use these models. A chat model gives you a sentence you have to parse. A decision model gives you a number you can threshold, and a threshold is something you can check against your own data.

The seven models reach that number by different mechanisms, which matters later:

- Laya is a ModernBERT-large encoder with a decision head. It scores every option at its own `[MASK]` marker and applies a softmax over that question's options. There is no decoder at all.
- Nimble v3 is fine-tuned from Qwen3.5-9B and, per its page, scores the candidate answer tokens directly, with no reasoning trace.
- Strands Decider puts a trained decision head on Qwen3.5-2B-Base.
- Kev merges publisher adapters into Qwen3.5 bases and keeps a pointer head in FP32.
- d1 is built on Liquid AI's LFM2.5-VL-3B, so its state can mix text and images.
- Tev1 is a Qwen3.5 fine-tune from Together AI. d3 comes from the vLLM Semantic Router project, and I did not read which base it uses.

One caveat travels with all of them. Kev's page says its reported confidence "describes how concentrated the choices are, not the chance that the answer is correct." That sentence applies to the whole category. A probability from these models is a score, not a frequency, until you check it against labels.

## The seven

Seven is the number I surveyed, not a census. Kev's page itself mentions two more decision models on the platform, and Laya has sibling checkpoints. Its readme says they do not ship with the Ollama model, yet the tag list shows a 322M multilingual tag, which I did not run. For each model I took what the library page and `ollama show` said.

| Model | Publisher | Size | Base | License | Input |
|---|---|---|---|---|---|
| d1 | Liquid AI | 3B (2.7B in `ollama show`) | LFM2.5-VL-3B | LFM Open License v1.0 | text, image |
| laya | Convai Innovations | 421M | ModernBERT-large | Apache-2.0 | text, English only |
| tev1 | Together AI | 0.8B, 4B | Qwen3.5 | training scripts MIT; model license not read | text |
| d3 | vLLM Semantic Router | 2B to 27B | not read | Apache 2.0 | text, image |
| kev | Jared Palmer | 0.8B to 27B | Qwen3.5 (0.8B, 4B, 9B) | Apache-2.0 | text |
| nimble-v3 | Bespoke Labs | 9B | Qwen3.5-9B | CC BY-NC 4.0, noncommercial | text |
| strands-decider | Strands Agents | 2B | Qwen3.5-2B-Base | Apache 2.0 | text |

The context window deserves its own table, because the pages disagree with themselves. The tag list on several pages shows 256K, the readme says something much smaller, and for some models `ollama show` reports yet another value. The `ollama show` column comes from the outputs I saved next to the results.

| Model | Tag list | Readme | `ollama show` on my pull |
|---|---|---|---|
| d1 | 32K | not stated | 32,768 (`num_ctx` 16,384) |
| laya | 8K for the tag I pulled | 512-token budget per question, longer states "are truncated" | context length 8,192; `num_ctx` 512 |
| tev1 | 256K | about 2K ("Keep inputs short") | not pulled |
| d3 | 256K | 4,096-token packages | context length 262,144; `num_ctx` 4,096 |
| kev | 256K | `num_ctx` 73,728 | context length 262,144 on the 4B |
| nimble-v3 | 32K | 32K | not pulled |
| strands-decider | 4K | 4K | not pulled |

My inputs are web clippings cut to 8,000 characters, which is about 2,000 tokens in English and more in other languages, plus a prompt of a couple of hundred tokens. Tev1's roughly 2K cannot hold that comfortably. Strands-decider's 4K is the same window as d3's, and d3 rejected only 2% to 4% of my items, so the window alone does not rule strands-decider out. I did not test either model because I ran out of time on this round, not because the evidence excluded them.

Two more constraints show up outside the benchmarks. Nimble v3 is the only model in the set under CC BY-NC 4.0, and its page says this is a change from the earlier Nimble release. For a personal vault that does not matter. For anything you ship, it eliminates the model before you read a score. Strands Decider ships MLX variants only and requires an Apple silicon Mac. Kev's default tags use the MLX runner too, but it also publishes GGUF tags, and those are the ones I ran.

## What the vendors measured

Every vendor reports a number, and the numbers come from at least four different instruments. Three terms first. Jev is TypeSafe's hosted decision service. The Decision Index is a scored suite of decision tasks that several vendors cite, in versioned releases. JevBench is a separate public set of 231 tasks, 111 of them marked hard, that two vendors and the Ollama pages run locally.

| Model | Reported number | What it is |
|---|---|---|
| d1 | 48.57 on Decision Index 0.2.1 | Liquid AI's report. Liquid AI calls it the best score for a decision model under 10B, ahead of a 35B-A3B Decider at 47.11 |
| nimble-v3 | 56.88 on Decision Index 0.2.1; 201/231 on JevBench (MLX), 198/231 (GGUF Q4_K_M) | Bespoke Labs' index report; JevBench measured on an M5 Max |
| d3 | Decision Index 0.3.2, text: 38.9, 52.6, 55.8, 66.3 for 2B, 4B, 9B, 27B | Publisher's original checkpoints, not the Ollama quantized packages |
| kev | 175/231 (4B BF16), 184/231 (9B BF16), 183/231 (9B NVFP4), 202/231 (27B BF16) on JevBench | Reported on the Ollama page, MLX builds |
| strands-decider | 180/231 on JevBench by the publisher; 182 to 183/231 on Ollama | Two measurers, same public set |
| tev1 | 73.3% (4B), 63.5% (0.8B) | Mean accuracy over Bespoke Labs' 13 public datasets with human labels, 3,880 decisions |
| laya | 83.8% macro in-task; 65.1% held-out zero-shot | Convai's own test sets for the shipped checkpoint |

Five readings come out of this table.

The indexes are not one scale. d1 and nimble-v3 both cite Decision Index 0.2.1, so those two are comparable, and nimble-v3 is ahead, 56.88 against 48.57. Liquid AI's "best under 10B" is Liquid AI's claim about decision models it compared, and nimble-v3 is a 9B model with a higher number on the same version. D3 cites 0.3.2. I have no conversion between versions, so d3's 4B score of 52.6 is not "better than d1's 48.57." It is a different ruler, and I cannot say how different.

JevBench is the closest thing to a shared bench, and three pages quote it. In raw terms the 231-task numbers are: nimble-v3 201 (87.0%), kev 9B 184 (79.7%), strands-decider 2B 180 (77.9%), kev 4B 175 (75.8%). On the hard subset, kev's 0.8B gets 39 of 111 (35.1%), the 4B gets 60 (54.1%), the 9B gets 66 (59.5%), and the 27B gets 83 (74.8%). A 2B model from Strands landing within five tasks of a 4B from Kev is not what parameter counts predict. Nimble's 9B is about 20 tasks ahead of both. I did not run strands-decider or nimble-v3, so I cannot say whether any of these gaps hold on my data.

The nimble-v3 page also contains the most direct evidence about the quantization question I face. Its GGUF Q4_K_M build, the format I used for kev, scores 198 against 201 for MLX BF16, three tasks lower on one machine. That is small and it is one model. Kev's page warns separately that "quantization changed some individual answers and probabilities even where aggregate accuracy was close."

Some of these numbers are development numbers. Tev1's page says its 88.0% on a 1,000-item main set used "the same eval mix ... while the model was being built, so it isn't an independent benchmark." I respect the disclosure. It also means the strongest-looking tev1 figure, 100% on policy transfer, should carry no weight. The comparable tev1 figure is 73.3% on Bespoke's 13 public datasets, run on Ollama, next to Nimble (the earlier release) at 75.7% and Jev 1.13 at 76.0%. A 4B model within three points of the hosted service it takes its inspiration from is a sober result.

Laya's numbers answer a different question from mine. Convai reports 99.1% on intent and routing and 96.7% on moderation, on the checkpoint's own in-task test sets. It reports 65.1% with calibration error 0.207 on held-out task families, zero-shot. My task, deciding whether a clipping belongs in a knowledge vault, is not one of its five trained families, so the held-out figure is the closer description of my situation and the weakest number on the page. My own notes record the model card calling it "a fast base to specialise, not a zero-shot decision engine." I took that quote from the note, not from the live card.

Laya's page also publishes the closest thing to an order or reliability metric I found: gating on confidence of 0.85 or higher automates half the decisions at 92.2% accuracy, on Convai's own setup. That is a selective-automation number, not a stability number, and it is Convai's measurement on Convai's data.

## My test

### The task

My vault ingests web clippings. A triage step decides whether each one enters the vault (approved) or is dropped (disapproved), with a third option, hold, for texts that cannot be judged. Wrongly dropping a clipping is a loss I do not see. Wrongly approving one costs a little attention.

### The labels

The labels are not human. They are the decisions a Claude model made in my production triage. A model's "accuracy" here is its agreement with that triage, and the triage has its own error rate. Every number below inherits that. Whether the Claude decision is right about each clipping is a separate question that I did not measure.

The dataset has 1,632 decided items. Items with the same content hash or the same normalized title form a group, and a hash of the group assigns it to one of four parts, so duplicates never straddle two splits: dev (650 items), select (334), confirm (227) and test (421). The classes are heavily skewed. Select has 300 approved and 34 disapproved. Confirm has 204 and 23.

### The language of the test

This matters more than I first treated it, so it goes before the results. The prompt I sent is in Portuguese, both the instructions and the three option descriptions, and so is the one-line prefix that marks the clipping as untrusted data. The clippings are mostly English. With a rough stopword and script heuristic, select has about 306 English items, 17 Japanese or Chinese and 11 Portuguese, and confirm has about 213, 10 and 4. The heuristic is approximate and I did not run a language detector.

So every request mixes a Portuguese prompt with, mostly, English text. Laya's page says "English only," Kev's says its evaluations focus on English, and Tev1's says Together AI has not fully tested languages other than English. A Portuguese prompt is a confound for those three, and for Laya it is a simpler explanation of a null result than anything I say below. D1's page lists Portuguese among its supported languages, so it is less exposed. I did not run an English-prompt version.

### The floor

That class skew produces the baseline for this article. A classifier that always answers approved is right 89.8% of the time on select and 89.9% on confirm. I call that the majority floor. It is useless as a classifier, since it never rejects anything. It is the reference for overall agreement, not a requirement for usefulness in every role. It is also the wrong yardstick for my costs. Accuracy weighs both mistakes equally, while wrongly dropping a clipping costs me more than wrongly keeping one. So I report the floor and judge usefulness by what the model could do in three different roles: sort a review queue, approve the safe clippings locally so fewer go to the remote model, or drop clippings on its own. Each role needs its own metric, and I report the first two below.

### The protocol

I used the harness that already runs my shadow tests, where a local model classifies items alongside the production triage without changing it. Three properties matter.

- The prompt is fixed before the run and hashed. I used the version called V2. It was chosen on the select split, with a different model, a retired 9.5B one called clef-flash, in an earlier round. So select is not a clean holdout for this prompt, and the prompt was tuned for another model.
- The harness rotates the option order. The criteria go out as `approved, disapproved, hold`, then `disapproved, hold, approved`, then `hold, approved, disapproved`. A model that answers by position rather than meaning shows up as a model whose answers move.
- It records the full probability vector, and it marks inputs the server rejects for exceeding the context as `truncated`, rather than scoring a cut-off text as if it were whole.

I ran the select split first, then confirm for the three finalists. I did not consult the test split in this round. An earlier round already used it for the retired model, so I would not call it untouched.

### The hardware

Everything ran on one MacBook Pro 14-inch with an M5 Pro chip and 24 GB of unified memory. The runs were sequential, one request at a time, so latencies are single-stream medians as the runner logged them, including HTTP overhead. They are not throughput numbers, and they move between runs of the same model: d3:4b measured 1.5 s, 2.8 s and 2.8 s in three runs, kev:4b 2.3 s, 1.5 s and 1.9 s. Read latency as a rough order of magnitude.

The 24 GB fits every model I ran. It rules out the 27B tier of d3 and kev, whose pages quote 28.6 GB and 25.6 GB loaded. The vendors measured on other machines: Kev's page on an M5 Max with 128 GB, Strands Decider's on an M5 Pro with 64 GB. Latencies copied between machines do not transfer, so I only compare the ones I measured myself.

### The metrics

Accuracy at the default decision rule, meaning whichever option has the highest probability, is the headline number and the one that meets the floor. A `hold` answer counts as a miss for both classes, and I say so because it changes the recall columns.

AUROC of P(disapproved) is the ranking measure. Pick one random disapproved item and one random approved item. AUROC is the chance the model gives the disapproved one the higher P(disapproved). A value of 0.5 means no signal and 1.0 is a perfect ranking. It does not depend on where you cut the probability, which makes it the right number for "does this model carry information," separate from "is it good at 0.5."

Recall on each class says what the default rule does in practice. With 10% disapproved, a model can reach 90% accuracy by never rejecting. Recall on disapproved is the check against that.

Confidence intervals come from a bootstrap of 1,000 resamples with seed 0, drawing items with replacement within each class, using my own short script. The resampling is by item, not by duplicate group, so if near-duplicates survive inside a group the intervals are a little too narrow. With 34 disapproved items in select and 23 in confirm, they are wide. For differences between two models I resampled the same items for both and took the AUROC difference, 2,000 times.

### Deviations from the vendor setups

Quantization. I ran kev as `kev:4b-q4_K_M` and `kev:9b-q4_K_M`, the GGUF builds. Kev's own table measures MLX BF16 and NVFP4 builds. Treat my kev numbers as Q4 GGUF numbers.

The laya window. The pull defaults to `num_ctx` 512. With that default, every one of the 334 select items came back invalid. I made a local alias, `laya-8k`, from the same weights with `num_ctx` set to 8,192. I need to be careful about what that means. Laya's page says each question gets a 512-token budget and longer states are truncated. My `laya-8k` requests had a median of about 2,080 tokens. The server accepted them, and the model may have cut them internally to its budget without telling me. The only clean laya run is the control, with the text cut to 700 characters so prompt and state fit in 512 tokens (median input 397). I report both.

Server versions. d3 needs Ollama 0.40.9 and my desktop app server was 0.40.6. I started a second server from the Homebrew build of 0.40.9 on another port and ran d3, kev's 9B, the three-order runs and the confirm runs there. As a sanity check, d1 and kev 4B gave the same select AUROC on both servers to three decimals, 0.665 and 0.734.

## The results

### One option order, select split

Select has 334 items. D3 rows cover 326, because the server rejected 8 inputs for exceeding its 4,096-token window. Laya 8K covers 333, because one request came back invalid. Recall on approved counts a `hold` answer as a miss.

| Model | AUROC | Accuracy | Recall disapproved | Recall approved | Median latency |
|---|---|---|---|---|---|
| d3:9b | 0.791 | 82.8% | 60.6% | 85.3% | 8.5 s |
| d3:4b | 0.756 | 78.2% | 60.6% | 80.2% | 1.5 s |
| kev:9b q4_K_M | 0.738 | 87.7% | 38.2% | 93.3% | 4.3 s |
| kev:4b q4_K_M | 0.734 | 87.7% | 35.3% | 93.7% | 2.3 s |
| d1:3b | 0.665 | 67.7% | 44.1% | 70.3% | 1.1 s |
| laya, 8K alias | 0.449 | 83.2% | 0% | 92.6% | 0.23 s |
| laya, text cut to fit 512 | 0.500 | 84.4% | 0% | 94.0% | 0.06 s |
| always approved | n/a | 89.8% | 0% | 100% | n/a |

For reference, the retired clef-flash on the same select split with the same V2 prompt gives an AUROC of 0.745 and 61.4% accuracy. It is not part of the comparison because it no longer exists in my setup.

### Three option orders, select split

| Model | AUROC per order | Mean over 3 orders | 95% interval | Items whose decision changes across orders |
|---|---|---|---|---|
| d3:4b | 0.756 / 0.745 / 0.759 | 0.753 | 0.654 to 0.843 | 3.1% |
| kev:4b | 0.734 / 0.748 / 0.729 | 0.740 | 0.645 to 0.827 | 3.9% |
| d1:3b | 0.665 / 0.650 / 0.670 | 0.664 | 0.567 to 0.766 | 16.5% |

The mean over orders is computed per item, then ranked. The last column counts items whose chosen option is not the same under all three orders.

### The confirm split

Confirm has 227 items, 23 of them disapproved, one order. The d3:4b row covers 218 items, since 9 were rejected for length.

| Model | AUROC | 95% interval | Accuracy | Recall disapproved | Recall approved | Median latency |
|---|---|---|---|---|---|---|
| kev:4b | 0.761 | 0.640 to 0.858 | 86.3% | 39.1% | 91.7% | 1.9 s |
| d3:4b | 0.721 | 0.600 to 0.832 | 74.3% | 57.1% | 76.1% | 2.8 s |
| d1:3b | 0.649 | 0.532 to 0.760 | 62.6% | 43.5% | 64.7% | 0.8 s |
| always approved | n/a | n/a | 89.9% | 0% | 100% | n/a |

## What the numbers say

### Nothing beats the floor at the default rule, or outside the sample

On select the most accurate model reaches 87.7% against a floor of 89.8%. On confirm the best is 86.3% against 89.9%. The two kev models get their accuracy by behaving like the floor: kev 4B answers approved for 303 of 334 select items, so it gains from the majority class and gives some back on wrong rejections.

The obvious reply is that the default rule is a poor operating point and a tuned threshold would do better. I checked in two ways. First, I swept every threshold on P(disapproved) and took the best accuracy on the same split. That is in-sample, so it is optimistic by construction.

| Split | Model | Floor | Best accuracy, threshold tuned on the same data |
|---|---|---|---|
| select | kev:4b | 89.8% | 91.9% |
| select | d3:4b | 89.9% | 91.4% |
| select | d3:9b | 89.9% | 91.4% |
| select | kev:9b | 89.8% | 91.0% |
| select | d1:3b | 89.8% | 91.0% |
| select | laya | 89.8% | 89.8% (no threshold helps) |
| confirm | d3:4b | 90.4% | 90.8% |
| confirm | d1:3b | 89.9% | 90.3% |
| confirm | kev:4b | 89.9% | 89.9% (no threshold helps) |

Second, I did what I would have to do in practice: pick the threshold on select and apply it to confirm.

| Model | Threshold from select | Confirm accuracy | Confirm floor |
|---|---|---|---|
| kev:4b | 0.51 | 89.0% | 89.9% |
| d3:4b | 0.836 | 90.4% | 90.4% |
| d1:3b | 0.804 | 87.7% | 89.9% |

Tuned on the same data, the models gain up to 2.1 points. Tuned on one split and applied to the next, kev and d1 lose to the floor and d3 ties it. That is the claim the title makes, and I measured it for three models on one split pair: a threshold buys somewhere between nothing and two points of accuracy over a classifier that never reads the text, and out of sample it bought nothing. I have not shown that it could never transfer, only that it did not here.

### Ranking is the real product

If accuracy is the wrong lens, AUROC and recall at a fixed review budget are the right ones. Suppose I do not trust a model to reject anything alone, and only want it to put the likeliest rejects at the top of a review queue. Take the top 20% of items by P(disapproved), with k as the floor of 0.2 times the number of items, and ask what fraction of all disapproved items lands there.

| Split | d3:9b | d3:4b | kev:9b | kev:4b | d1:3b | laya |
|---|---|---|---|---|---|---|
| select, top 20% | 54.5% | 54.5% | 50.0% | 44.1% | 41.2% | 8.8% |
| confirm, top 20% | n/a | 52.4% | n/a | 52.2% | 30.4% | n/a |

A random ranking would put about 20% of the rejects in the top 20%. The better models put roughly half there: a review queue a fifth the size that catches about half the noise. That is useful for triage and it is not an automated decision. Read operationally, the numbers are less generous: for kev:4b on confirm the top 45 items hold 12 of the 23 rejects, a precision of 26.7% against a base rate near 10%, so I would review about four items to find one reject, and nearly three quarters of that queue would still be approved items. On select the same cut gives 15 rejects in 66 items (22.7%), and d3:4b gives 27.7% and 25.6%. Laya's 8.8% is three of 34, no better than random. Its scores are not constant, which would have explained a flat ranking: the cut-text control produced 331 distinct values between 0.107 and 0.505. Constant output therefore does not explain the chance-level AUROC. That does not rule out every interface effect, and the test does not separate prompt language, context length and fit to the task.

### Approving locally is where the signal is

I had only looked at the reject side. The cheaper mistake in my setting is the other one: approving a clipping the production triage would have dropped. So I turned the question around. Rank items by P(disapproved) from lowest, approve locally the lowest fraction, and measure how many of those the production triage would have rejected. I picked the cut on select and applied it to confirm.

| Model | Local approval coverage on confirm | Locally approved items the production triage rejected | Base rate on confirm |
|---|---|---|---|
| kev:4b | 17.6% (40 items) | 5.0% (2 of 40) | 10.1% |
| kev:4b | 26.0% (59 items) | 3.4% (2 of 59) | 10.1% |
| kev:4b | 52.4% (119 items) | 2.5% (3 of 119) | 10.1% |
| d3:4b | 43.6% (95 items) | 5.3% (5 of 95) | 9.6% |

The cuts are the P(disapproved) at 20%, 30% and 50% coverage on select: 0.176, 0.197 and 0.245 for kev:4b, and 0.280 for d3:4b at 50%. On select they left 1.5%, 4.0% and 4.8% rejected among the locally approved items, against a base of 10.2%. From select to confirm the rejected share moved in both directions (1.5% to 5.0%, 4.0% to 3.4%, 4.8% to 2.5%), and d3:4b went from 4.3% to 5.3%.

At about half the traffic, kev:4b approves a set whose rejected share is roughly four times below the base rate on confirm. On select, where I chose the cut, the same cut gives 4.8% against a base of 10.2%, about half. That is the only role in this article where a local model shows something I would call useful, and the evidence is thin: three of the 119 locally approved items had been rejected by the production triage, on one split and one prompt. Those are disagreements, not confirmed errors, since the reference is Claude's own decision. With only 2 or 3 rejects among 40 to 119 locally approved items, the intervals are wide: a 95% Wilson interval is 0.9% to 7.2% for 3 of 119, 0.9% to 11.5% for 2 of 59 and 1.4% to 16.5% for 2 of 40. I chose the coverage cuts on select without registering them first, so the three kev rows are an exploration, not a frozen policy. This is a candidate for a prospective pilot. If the goal is fewer calls to the remote model, the next test is whether the rate holds on new clippings under one frozen cut, and what those three items were.

### What separates the models, and what does not

Here the intervals matter, so I use paired differences, where both models score the same items and I bootstrap the AUROC gap.

| Comparison | AUROC difference | 95% interval |
|---|---|---|
| d3:4b minus d1, select | +0.100 | 0.010 to 0.195 |
| d3:4b minus d1, confirm | +0.098 | 0.008 to 0.198 |
| kev:4b minus d1, confirm | +0.113 | 0.025 to 0.197 |
| kev:4b minus d1, select | +0.069 | -0.022 to 0.164 |
| d3:4b minus kev:4b, select | +0.028 | -0.071 to 0.136 |
| kev:4b minus d3:4b, confirm | +0.031 | -0.084 to 0.138 |
| d3:9b minus d3:4b, select | +0.035 | -0.019 to 0.091 |
| kev:9b minus kev:4b, select | +0.003 | -0.047 to 0.051 |

Three things come out of that table. D1 is behind d3:4b on both splits and behind kev:4b on confirm, with intervals whose lower bounds are only about 0.01 and that I did not correct for the eight comparisons. D3 and kev are not separable from each other. And size shows no reliable gain in either family: d3's point estimate rises by 0.035 from 4B to 9B and kev's by 0.003, and both intervals include no change. The vendor tables show size as a quality dial. In my sample, with 33 or 34 negatives, I cannot confirm the dial for d3 and I see none for kev. Kev's own JevBench table shows 9 more tasks correct for the 9B over the 4B (184 against 175, 3.9 points), a gap my sample is too small to detect either way.

### Order sensitivity is the clearest signal

The three-order table has the number that changes how I think about a model. 16.5% of d1's decisions change when I only permute the options. For d3:4b it is 3.1% and for kev:4b it is 3.9%. The meaning of an option does not change when its position does, so a changed answer shows sensitivity to presentation order. The test does not isolate positional bias from other serialization effects or small shifts near the decision boundary. Kev's page lists reordered options among the conditions where accuracy can fall. It publishes no number for it.

For a pipeline, order sensitivity is cheap to measure and expensive to ignore. I would run it on any candidate before reading its accuracy table. It costs two extra passes.

### Where the vendor numbers and my data meet

I do not want to make the lazy move and say "the benchmarks are wrong." They answer other questions. Two comparisons show how little they would have told me.

Liquid AI reports a Decision Index of 48.57 for d1 and in my data it is the weakest finalist, with the order instability above. The index tells me d1 does well on the index's tasks.

Laya's in-task accuracy is 99.1% on intent and routing, and in my data it is at chance. The held-out figure on its own page, 65.1% with a calibration error of 0.207, was the warning. A Portuguese prompt, a 512-token budget and an unfamiliar task type all point the same way, and I cannot separate them with this data.

## What the vault already knew

This is not my first look at local decision models in this pipeline, and earlier rounds agree with the new ones where they overlap.

The previous round measured the retired clef-flash on the locked test split, 421 items, with the same V2 prompt. It found an AUROC of 0.719 with a 95% interval of 0.639 to 0.793, a calibration error of 0.098 against a null of 0.050, and no operating point where the model could reject anything at 5% risk. That report is about clef-flash, not d1. The clef-flash number sits next to the new ones: 0.745 on select here, in the same range as d3 and kev. A clef-flash result of 0.72 to 0.75 is what the round-two report called a modest ordering signal, not a usable classifier, and the current finalists land in the same place.

Laya had already left the shadow test after its first round. That round measured it on short items under a 512-token window. It agreed with the label on 53.3% of the 107 items it decided, against a majority floor of 52.3%. I will not repeat the AUROC of about 0.53 that appears in the second-round plan: when I traced it, the plan attributes it to the first round of the retired clef-flash with an earlier prompt, not to laya. The new laya runs, 0.449 with the 8K alias and 0.500 with the text cut to fit, point the same way as the first round, but they are not independent confirmations. Round one used distilled source pages in mixed Portuguese and English, not raw clippings, so the corpus differs between the two runs. The Portuguese prompt is the confound they share.

## Trade-offs

The case for running one of these anyway is that the cost is small. The 4B models are 2.7 GB (kev Q4_K_M) and about 5.6 GB (d3 4B), and they answer in one to three seconds on a laptop. Nothing leaves the machine. For a review queue, where the model sorts and a person decides, half the rejects in the top fifth is real value.

The cost is that none of them is safe as the only gate. The vendors say so. Kev's page says "Do not use these models as the sole control for consequential decisions," and tev1's says "Don't let it be the only check on a high-stakes decision." My data agrees and adds a specific warning: a model that looks reasonable on accuracy can be answering the majority class.

Two costs are structural. D3's 4,096-token window rejected 8 of 334 select items and 9 of 227 confirm items. By my rough language check, most of the rejected select items were Japanese, which tokenizes long, and one was Portuguese. The server returned an error for them, and the runner recorded them. A pipeline that ignores errors would drop 2% to 4% of its input without a record, and one that handles them needs a fallback for those items. The second structural cost is language. The Portuguese items in my splits are disproportionately disapproved, 5 of 11 on select and 3 of 4 on confirm. A model could be rewarded for a language shortcut, and I did not test for that.

## How I would choose

For the review-queue role I would shortlist kev:4b and d3:4b and treat them as tied on ranking. Kev:4b has the better accuracy and the lower false-reject rate, with an 6% to 8% error on approved items, 2.7 GB of disk and 3.9% order sensitivity. D3:4b catches more rejects at the default rule, at the price of rejecting 20% to 24% of approved items. Those two comparisons differ: at the default rule each model flags a different number of items, while a fixed review budget makes them compete for the same human time. For a queue, the fixed-budget comparison is the fair one, and at a 20% budget the two catch nearly the same share of rejects on confirm (52.4% against 52.2%), although d3:4b is ahead on select (54.5% against 44.1%). So d3:4b's higher recall at the default rule does not show it gives more value for the same review work. Neither model has a measured result on a downstream task, and I do not read any of this as permission to drop items automatically.

The process I would follow for any new model is short.

1. Write the floor first: the majority-class accuracy of your own split.
2. Run three option orders and report how many decisions move.
3. Report AUROC with an interval, and recall at a fixed review budget.
4. Choose the threshold on one split and measure it on another.
5. Treat the vendor benchmark as a hint about which models to try, not as a reason to choose one.

## What I would do next

Freeze one local-approval policy for kev:4b: one prompt, one cut, written down before new data. Inspect the three disagreements and a sample of the other approved items. Then validate on new clippings and measure coverage, disagreement rate, remote calls avoided and total latency. This is the step with a concrete saving behind it, so it comes before widening the catalog.

Next, the English-versus-Portuguese prompt ablation on the current candidates, with the same checkpoint. Add the multilingual laya tag only after that, because changing language and checkpoint together would hide which change helped.

Then widen the catalog: run the three models I surveyed and did not test: tev1, nimble-v3 and strands-decider. Below the 27B tier, nimble-v3 has the strongest published JevBench number in the group, and it holds the higher of the two Decision Index 0.2.1 scores, but its license rules it out for anything commercial. Strands-decider is the one I most want to see, because a 2B model within five tasks of a 4B is the claim that would change which size I deploy. For tev1 and strands-decider I would shorten the text to a few hundred tokens and measure what the cut costs on a model that handles the long version.

Get human labels for a few hundred items, so I can ask whether the Claude triage or the local model is closer to the truth. Right now I measure agreement with a reference, and the reference has errors I have not counted.

Compare the models on the intersection of items every candidate answered, and report the end-to-end result including a fallback for the rejected ones. The two views answer different questions, and production only gets the second. Then repeat select with a second prompt. Every number here comes from one prompt, and that prompt was tuned on select for a different model.

## What I still don't know

I do not know how much of the gap between these models and the floor is the models, and how much is the labels. The reference decisions come from a model, not a person, and I did not audit them here.

I do not know what an English prompt does. Every request had Portuguese instructions around mostly English text, and that may hurt the English-focused models in a way I did not measure, laya most of all.

I have no calibration numbers from this round. I measured ranking, accuracy and stability, not whether a P(disapproved) of 0.8 means 80%, so I cannot read the scores as risks. Whether a cut holds up outside the sample is a separate question, and I measured it on one split pair only. The accuracy thresholds did not transfer. The local-approval cuts kept their coverage within about six points but moved the rejected share in both directions. One pair cannot tell me they will hold on new clippings.

I do not know whether the Q4 GGUF builds behave like the MLX builds the vendors measured. The nimble-v3 page suggests a small loss, and I did not test it for kev.

The samples are small and each configuration ran once. Select has 34 disapproved items and confirm has 23. The d3 and kev results are not separable, and d3's base is 326 items rather than 334. Kev 4B on d3's base scores 0.728 against 0.734, so I expect that effect to be small.

I did not test three of the seven models. I did not check whether the Portuguese and Japanese items give some models a shortcut, and I only have a rough language count to work from.
