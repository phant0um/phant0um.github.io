---
date: "2026-11-01T09:00:00-05:00"
description: "I tested thinking-capable local models on a rule-resolution task with planted answers. With thinking off, seven models scored between 21% and 42%, and an eighth scored 0 because it leaked its thinking tags. With thinking on, three of them reached 75-96% on a held-out set, at a cost of far more generated tokens and latency."
tags: ["local-llm", "ollama", "thinking-models", "evals", "benchmark", "apple-silicon"]
slug: "thinking-mode-local-models-adr"
title: "Thinking on vs. off in a local ADR benchmark: screening 14 models on a 24 GB laptop"
draft: false
summary: "I tested thinking-capable local models on a rule-resolution task with planted answers. With thinking off, seven models scored between 21% and 42%, and an eighth scored 0 because it leaked its thinking tags. With thinking on, three of them reached 75-96% on a held-out set, at a cost of far more generated tokens and latency."
cover:
  image: "/og/thinking-mode-local-models-adr.png"
  alt: "Thinking on vs. off in a local ADR benchmark: screening 14 models on a 24 GB laptop"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Thinking on vs. off in a local ADR benchmark: screening 14 models on a 24 GB laptop

On a rule-resolution task with planted answers, none of the seven models that answered in the right format with thinking off clearly beat the simple baselines: they scored 21% to 42%, against 24% for a random pick and 37.5% for always answering `indeterminado`. With thinking on, three models reached 75% to 96% on a sealed set of 24 items, opened first after I froze the protocol and then again in a separately authorized second stage. In this sample, parameter count alone did not predict which models could finish thinking within the budget I allowed, and the immediate cost of thinking was generated tokens and latency: about 100 times more output for gemma4:e4b, and about 900 times more for qwen3.5:4b.

I ran this on a MacBook Pro with 24 GB of memory, over about three days, using Ollama. This article reports what I measured, how I made the measurement hard to fool, and what went wrong along the way.

## What I wanted to know

I keep a notes vault that runs a maintenance pipeline. Some of its steps are decisions: should this clipping enter the knowledge base, which of these architecture decision records (ADRs) is the one in force today. Those decisions were designed to run on Claude. I wanted to know whether a small model on my own machine, with its thinking mode switched on, could take over decisions of that kind.

Ollama exposes an explicit `think` flag on `/api/chat`. The question was narrow: for a model that supports thinking, does `think=true` buy verifiable accuracy over `think=false`, at the same resource ceiling and with the practical setting of each mode? I also wanted the cost, in tokens and in seconds, because a model that wins by burning an hour per answer is not an answer.

A benchmark that shows capability does not authorize moving a production workflow, and every table below carries that limit.

## The machine and the software

| Item | Value |
|---|---|
| Machine | MacBook Pro, model identifier Mac17,9 |
| Chip | Apple M5 Pro, 15 cores (5 super, 10 performance) |
| Memory | 24 GB unified |
| OS | macOS 27.0.1 (build 26A434) |
| Server | Ollama 0.40.13, desktop app, llama.cpp runner |
| Swap in use during runs | varied by run, recorded, not a gate |

The memory number is the one that shapes everything. On unified memory the model weights, the key-value cache and the operating system share the same 24 GB. A large model with a 16k context is already uncomfortable next to a browser and an editor. That is why I pulled nothing larger than 6.7 GiB.

I tested fourteen models. Five were already on the machine and nine I pulled for this test, about 35 GiB of downloads. 

| Model | Download size (pulled models) |
|---|---|
| nemotron-3.5-bolt:e4b-mxfp8 | already installed |
| ornith-1.5:9b | already installed |
| granite4.2:8b and granite4.2:3b | already installed |
| lfm3:1.7b-q4_K_M | already installed |
| nemotron-3-nano:4b-q4_K_M | 2.64 GiB |
| qwen3.5:4b-q4_K_M | 3.10 GiB |
| qwen3.5:9b-q4_K_M | 6.10 GiB |
| qwen3-vl:4b-thinking | 3.11 GiB |
| lfm3-vl:2b-q4_K_M | 1.38 GiB |
| bonsai-2:4b | 1.47 GiB |
| lfm2.5:8b-a1b-q4_K_M | 4.80 GiB |
| gemma4:12b-it-qat | 6.66 GiB |
| gemma4:e4b-it-qat | 5.72 GiB |

I used each model as a text model. Several of them also accept images, and that part sat unused.

## The task

The task is resolving an ADR. The model receives a set of ADR documents, each with a status and links such as "supersedes" or "reinstates", and a question: which decision is in force for this scope today? The answer must be one ADR identifier from a closed list, or the word `indeterminado` when the documents do not settle it.

I did not write these items by hand. A generator builds them, so the correct answer is planted and known. It produces ten situation types, among them `chain` (A is replaced by B, B by C), `reinstate` (a replaced decision is brought back), `revocation`, `insufficient_conflict` (two documents disagree and nothing settles it), `status_stale` and `proposed_later`. Each item belongs to a story, and one story can produce several items. The generator wrote 24 items for a development split (15 stories) and 24 for a sealed split, with no story shared between the splits. The sealed file is read-only and I did not open it while building and tuning anything.

Here is one development item, translated from Portuguese. The prompt gives seven rules (only an `accepted` ADR counts, a replacement ends the replaced one, an `accepted` ADR that restores another brings it back, and so on) and then the documents:

> ADR-307, scope "key rotation", 2026-01-18, status: superseded.
> ADR-299, scope "key rotation", 2026-06-30, status: accepted. Takes effect in place of ADR-372. Restores the decision of ADR-307. It sets no new rule of its own.
> ADR-039, scope "team training", 2026-09-15, status: accepted.
> ADR-372, scope "key rotation", 2026-03-29, status: accepted. Takes effect in place of ADR-307.
>
> Question: which ADR is in force today for the decision on "key rotation"? Answer: an ADR ID or `indeterminado`.

The correct answer is ADR-307. ADR-372 replaced it, ADR-299 then replaced ADR-372 and restored ADR-307, and ADR-299 introduces no rule of its own. The type is `reinstate`, the one that thinking-off models missed 8 times out of 8 in gemma4:e4b and qwen3.5:4b.

The generator also computes baselines, which are the accuracy of dumb rules on the same items. Always answering `indeterminado` gets 37.5% on the development set. Picking the most recent ADR gets 8%. A random pick gets about 24%: for each item, a uniform choice among that item's 3 to 5 allowed answers (the candidate ADR IDs plus `indeterminado`), averaged over the 24 items. These numbers matter because they tell me what "better than nothing" means. A model that scores 33% is not meaningfully better than a rule that fits in one line.

The scoring is strict. The verifier reads only `message.content`. Whatever the model wrote in `thinking` is auxiliary. A correct answer that appears only in the thinking text counts as wrong. A response that stops with `done_reason=length` counts as wrong, even if it was heading to the right answer. Invalid format, leaked thinking tags and errors all count as errors in the denominator, and no item is ever dropped.

## The protocol, and why it is heavy

A benchmark on one laptop has an obvious weakness: anything else running on the machine changes the result. I wrote the protocol around that weakness before I ran any model, and I froze it in files with their hashes.

**Fixed request.** Every call is a single `user` message to `/api/chat`, with no `system` message, `temperature=0`, `stream=false`, a fixed `num_ctx`, an explicit `think` boolean, and an explicit `num_predict`. The prompt file has a recorded hash. The server digest of every model must match the digest I recorded, and the runner refuses to start if it does not.

**Calibrate the token budget first (T1).** Thinking models need a ceiling on output tokens. If the ceiling is too low the model runs out before it answers, and the test measures the ceiling, not the model. So before any accuracy run, each model goes through a ladder of ceilings: 1500, 3000, 6000, and then the largest value that still fits the context: the context size minus the measured prompt length minus a 256-token margin, rounded down to a multiple of 100. At 16,384 context and a prompt of about 500 tokens, that is about 15,500. A level passes only if the first 15 items finish without hitting the ceiling and with enough headroom left. Headroom means the longest of the 15 answers used at most two thirds of the ceiling (`eval_count` ≤ 0.67 × `num_predict`). The model gets a label: either `np_escolhido:N` (the lowest ceiling that works) or `nao_avaliavel`. A separate level checks `think=false` with a ceiling of 64 tokens, which I call D4.

**Isolation checks on every call.** Before each call the runner checks that `/api/ps` shows only the model under test, that `lsof` shows no new client on port 11434, and that the model was not reloaded. After each arm it counts the requests in the Ollama server log inside the time window and requires the count to equal the runner's own calls. Any mismatch invalidates the arm. The runner records the event and stops. It does not kill anything.

**Freeze files.** A `FREEZE.json` holds the SHA-256 of the pre-registration and of the artifacts: the runner, the adapter, the scoring code, the generator, the development file, the prompt. The runner refuses to start if one of them changed after the freeze. The freeze also carries a flag, `inference_authorized`, that only I can flip.

**Pre-registration.** The analysis plan for the sealed set was written before I saw any sealed result. A comparison meets the criterion only if the gain of `think=true` is at least 5 points and the 95% confidence interval excludes zero. The interval is a bootstrap that resamples whole stories (10,000 resamples, a fixed seed), because items from one story are not independent. I also planned an exact McNemar test on the discordant pairs. Anything else is "inconclusive", and inconclusive does not mean `think=false` won.

The protocol cost me days.

## Result 1: most models cannot think inside the budget

I ran the calibration at two context sizes. The first round used `num_ctx=8192`. Four of the five models in that round could not finish thinking, so I raised the context to 16384 and reran the other models, plus the nine new ones.

| Model | `think=true` at 8192 | `think=true` at 16384 | D4 (`think=false`, 64) |
|---|---|---|---|
| nemotron-3.5-bolt:e4b-mxfp8 | ceiling 1500 | not rerun | passes |
| gemma4:e4b-it-qat | not run | ceiling 1500 | passes |
| lfm2.5:8b-a1b-q4_K_M | not run | ceiling 3000 | invalid |
| qwen3.5:4b-q4_K_M | not run | ceiling 15500 | passes |
| qwen3.5:9b-q4_K_M | not run | ceiling 15500 (ran in a forbidden time window, see the daylight saving section) | passes |
| ornith-1.5:9b | not evaluable | not evaluable | passes |
| granite4.2:8b | not evaluable | not evaluable | passes |
| granite4.2:3b | not evaluable | not evaluable | passes |
| lfm3:1.7b-q4_K_M | not evaluable | not evaluable | invalid (`length`) |
| nemotron-3-nano:4b-q4_K_M | not run | not evaluable | passes |
| qwen3-vl:4b-thinking | not run | not evaluable | invalid |
| lfm3-vl:2b-q4_K_M | not run | not evaluable | passes |
| bonsai-2:4b | not run | not evaluable | passes |
| gemma4:12b-it-qat | not run | not evaluable | passes |

"Not evaluable" means the model failed the pre-registered calibration criteria within the tested context and ceilings. Most failures were truncation: the first item overran every ceiling, up to about 15,500 tokens. For ornith the model kept thinking and never produced `content`, even at the largest ceiling.

Two things surprised me. First, parameter count alone was not a reliable selection rule in this sample. gemma4:e4b finished in 1500 tokens. The 12B model from the same family overran at every level. ornith (9B) overran, and granite (8B) answered but did not qualify. qwen3.5 at 4B and 9B finished, but only with a 15,500-token ceiling.

Second, some models, granite4.2:3b among them, failed in a different way at the last level. They did answer, but they broke the headroom rule. The runner labels this `folga_violada`, and the pre-registered rule keeps the model "not evaluable". I did not bend the rule to include it.

## Result 2: without thinking, no model clearly beat the simple baselines

Here is the development set, 24 items. Each cell is the number of correct answers.

| Model | `think=true` | `think=false`, same ceiling | `think=false`, ceiling 64 |
|---|---|---|---|
| nemotron-3.5-bolt | 24 | 6 | 6 |
| gemma4:e4b | 23 | 8 | 8 |
| qwen3.5:4b | 23 (1 `length`) | 7 | 7 |
| qwen3.5:9b | 24 (isolation violated, see below) | 10 | 10 |
| lfm2.5:8b-a1b | 9 (3 `length`, 1 invalid) | 0 (23 tag leaks) | no arm |
| ornith-1.5:9b | not evaluable | not run | 7 (6 invalid format) |
| granite4.2:8b | not evaluable | not run | 7 |
| granite4.2:3b | not evaluable | not run | 5 |

Seven models scored between 5 and 10 correct answers out of 24 with thinking off, which is 21% to 42% (ornith is one of them, with six invalid formats among its 24 answers). An eighth, lfm2.5, scored 0 of 24, with thinking tags leaked in 23 answers. The random baseline is about 24%, and the "always `indeterminado`" baseline is 37.5%. Only qwen3.5:9b with thinking off beats the second one, and it does so by one item (10 of 24 against 9).

The ceiling made no difference to `think=false`. Allowing 1500 or 15,500 tokens gave exactly the same count as allowing 64, in the four models where I ran both (nemotron, gemma4:e4b, qwen3.5:4b, qwen3.5:9b), because a model with thinking off answers in about five tokens. This is useful in practice: the practical `think=false` configuration is also the cheap one.

The errors have a pattern. With thinking off, the models get the short situations right (`partial`, `status_stale`, `insufficient_deprecated`) and miss the types that need several documents held in mind: `reinstate` (0 of 8 for gemma4:e4b and qwen3.5:4b) and `insufficient_conflict` (0 of 4 for gemma, 1 of 4 for qwen). With thinking on, `reinstate` goes from 0 of 8 to 8 of 8 in gemma4:e4b and to 7 of 8 in qwen3.5:4b. The biggest gains appear in situations that require several document relationships to be resolved. That is consistent with thinking helping there, but the experiment does not isolate the mechanism. I did not inspect the thinking text item by item.

The lfm2.5 result is a format failure, not a reasoning result. With thinking off it leaked the thinking tag into the answer in 23 of 24 items, so the verifier scored zero. I did not investigate why.

## Result 3: the sealed set shows the same gap

I opened the sealed set in two stages. Nemotron went first, before gemma4:e4b and qwen3.5:4b had any development result. After their development runs, a second opening, authorized separately, evaluated those two on the same set. qwen3.5:9b scored 24 of 24 in development but stayed out of the sealed set, because its thinking arm broke isolation and I had no authorization for another opening. The second opening is not a clean first read of the sealed set. I changed nothing in the prompt or the verifier between the two, and I wrote the arms down before the second read, but the file was no longer unseen.

| Model | `think=true` | `think=false` | Gain (percentage points) | 95% interval (by story, points) | Meets pre-specified gain and interval criterion |
|---|---|---|---|---|---|
| nemotron-3.5-bolt | 23/24 (96%) | 8/24 (33%) | +62 | 36 to 82 | yes |
| gemma4:e4b | 22/24 (92%) | 8/24 (33%) | +58 | 33 to 78 | yes |
| qwen3.5:4b | 18/24 (75%) | 8/24 (33%) | +42 | 23 to 61 | yes |

Nemotron ran with a context of 8192 and the other two with 16384, so the rows are not strictly comparable. The best baseline on the sealed set is 37.5%, and the `think=false` arms sit below it. The sealed split has 24 items from 15 stories, like the development split.

The paired counts show where the gain comes from. For gemma4:e4b, 14 items were right only with thinking, 0 only without, 8 right in both and 2 wrong in both. For qwen3.5:4b the counts are 10, 0, 8 and 6, and for nemotron 15, 0, 8 and 1. In no model was there an item right only without thinking.

The pre-registered criterion is a gain of at least 5 points with a story-level interval that excludes 0. I also ran an exact McNemar test, which gave p = 0.0001 for nemotron and gemma4:e4b and p = 0.002 for qwen3.5:4b. That test treats the 24 items as independent pairs, which they are not, so I do not use it as evidence. The bootstrap resamples whole stories with replacement and compares item-level accuracy.

qwen3.5:4b dropped from 96% on the development set to 75% on the sealed set, and most of the drop comes from truncation: five of its 24 sealed answers ran into the 15,500-token ceiling and counted as errors, and one more was wrong. The main limit I observed was finishing inside the budget. I did not raise the ceiling after seeing this. The pre-registration says a length stop is an error, and a retry with a bigger ceiling would be an adjustment the sealed set exists to forbid.

## What thinking costs

The accuracy is not free, and the cost differs by a lot between the models that win.

| Model | Mean output tokens per item (`think=true`) | Total time, 24 items | Same with `think=false` (dev split) |
|---|---|---|---|
| nemotron-3.5-bolt | about 645 | 203 s (dev), 121 s (sealed) | about 6 tokens, 17 s |
| gemma4:e4b | about 653 (dev), 723 (sealed) | 404 s (dev), 286 s (sealed) | about 7 tokens, 19 s |
| qwen3.5:4b | about 4,460 (dev), 6,076 (sealed) | 2,474 s (dev), 3,738 s (sealed) | about 5 tokens, 11 s |
| qwen3.5:9b (thinking arm: isolation violated) | about 4,110 | 3,689 s (dev) | about 5 tokens, 18 s |

Nemotron and gemma4:e4b reach 92% to 96% on the sealed set in 2 to 5 minutes for 24 items (121 s to 286 s). qwen3.5:4b needs roughly 41 to 62 minutes (2,474 s on the development set, 3,738 s on the sealed set) for similar or lower accuracy. On this machine, with this task, the small thinking budget of gemma4:e4b and nemotron is the better deal: total time for qwen3.5:4b is 6 to 13 times gemma4:e4b's and 12 to 31 times nemotron's, depending on the split.

All the numbers above come from one machine, with one quantization per model; times are wall-clock for the 24 items and tokens are the `eval_count` Ollama reports per item, which includes thinking. Median throughput with thinking on ranged from about 39 tokens per second (qwen3.5 4b and 9b) to 88 (lfm2.5), and I did not tune anything for speed.

## What broke

This section is longer than it should be, and I include it because the failures shaped the numbers.

**Two calibrations at once.** The ornith T1 was launched twice. One run ended incomplete and the other ended with `espera_teto`. I kept both on disk, left them out of every result, and relied on the run that passed every check.

**The swap gate.** My first protocol interrupted an arm when swap use passed a fixed limit, and an arm stopped on it. I decided that swap should be recorded, not used as a gate, and I wrote that as an amendment instead of quietly raising the number.

**A client that polls Ollama.** The qwen3.5:9b calibration failed in two attempts with `server_log_diverge`: the server log showed more requests than the runner made. The extra ones were `GET /v1/models` calls from some other client on the machine. In another attempt the runner reported a new client that I could not identify. The counting rule includes `/v1/`, so a harmless model listing invalidates a long arm. I did not relax the rule. The fourth attempt, with nothing else touching Ollama, passed. Another interruption with the same cause stopped the qwen3.5:9b thinking arm in the development set, after 24 of 24 correct answers. I kept it as an observation with an "isolation violated" flag, and it does not count in any verdict.

**Daylight saving time.** On 1 November the clock moved back one hour. The Ollama log wrote its timestamps one hour behind my runner's clock, so the window in which the runner counted server requests matched nothing, and an arm that had made 24 calls counted zero. The pre-registration forbade runs between 01:00 and 02:00 that day, and I did not guard against the mismatch outside that window. The qwen3.5:9b calibration run that supports the 15,500 ceiling ran inside the forbidden window. It passed every isolation check, and I did not repeat it, so I keep its result and flag it as a protocol deviation. The fix for the clock was an environment variable, `TZ=Etc/GMT+5`, set for the runner process only. I did not touch the runner code or restart the server, and I wrote the change down in an addendum before repeating the two qwen3.5:9b `think=false` development arms that the mismatch had interrupted.

**Freeze after every change.** Each time I touched the runner, even to add a model's digest, the artifact hashes changed and the old freeze became invalid. I rebuilt a new folder for each round and kept the previous freezes. It looks slow, but it is the reason I can say that the numbers in the table came from the code in the folder next to them.

**Tests tied to a constant.** My runner tests assumed a context of 8192. When I moved to 16384 they broke, so I made most of them relative to the `NUM_CTX` constant. Tests with planted negatives (a correct answer that appears only in the thinking text, a `length` stop, a leaked tag) are what let me trust that the verifier fails when it should.

## The trade-off

If your task has a verifier, a long budget and a human who can wait, the price of thinking is good. These runs and this task do not establish that thinking suits a workflow with a one-second deadline.

The result also depends on the setup in ways that matter. Four of the five models in the first round failed at 8192, and raising the context to 16384 rescued none of those four. The models that passed at 16384 had never been tested at 8192. I had to measure the ceiling for each model, and I could not assume it from the name or the size.

## What I still don't know

I do not know if the gap holds for other tasks. This is one task family, with 24 items in each split from 15 stories, and the intervals are wide: the lower bound of the nemotron gain is 36 points, and the lower bound of the qwen3.5:4b gain is 23. These numbers say that thinking helps here. They do not say how much it helps on tasks I did not test.

I also do not know whether the models I labeled "not evaluable" would do well with a bigger context. ornith and gemma4:12b overran every ceiling at 16,384 context, and granite answered but broke the headroom rule. A 32k or 64k context might let them finish, at a cost in memory I did not want to pay. And the comparison between nemotron (tested at 8192) and the others (16384) is not clean.

Finally, I did not look at the thinking text itself. I scored only the final answer. A model could be right for the wrong reason, and a wrong answer could hide a nearly right chain of reasoning. Reading a sample of the thinking is the first thing I would add.
