# Phase 1b — Selfsame vs. Cross-Model Scoring

**Date:** 2026-04-27
**Inputs:**
- Cross-model (leave-one-out): `results/phase1b_20260426_060324/scoring/combined_scores_20260426_082942.csv` (816 scores)
- Selfsame (all-vs-all): `results/phase1b_20260426_060324/scoring_self/combined_scores_20260427_095357.csv` (1088 scores: 272 self + 816 cross)
- Analysis script: `tests/experiment/analyze_self_vs_cross.py`

**Question:** The original Phase 1 ground-truth methodology used the same LLM to generate and score (selfsame LLM gen+score) and produced 14/16 = 87.5% directional confirmation. Does the same selfsame methodology, applied to the Phase 1b stimulus set, reproduce that result — and does it correlate better with the underlying "this NT was switched on" signal than cross-model scoring?

## Headline result

**No — selfsame scoring is *worse* at directional confirmation than cross-model.**

| Methodology | Cells where NT-on raised that dim's score |
|---|---|
| Cross-model (orig run, 04-26) | **13/16 = 81.2%** |
| Cross-model (re-run inside scoring_self) | 13/16 = 81.2% (same; see test-retest) |
| **Selfsame** (gen-model = score-model) | **9/16 = 56.2%** |

Cross-model is ~25 percentage points more reliable at recovering "we switched this NT on."

## Aggregate NT-on minus NT-off deltas (1-5 scale)

```
mode             D       C       N       E
cross (orig)   -0.18   +0.19   +0.14   +0.41
cross (re)     +0.05   +0.29   +0.26   +0.41
selfsame       -0.09   +0.25   +0.06   +0.47
```

Endorphins (E) and Cortisol (C) hold up under either methodology. Dopamine (D) and Norepinephrine (N) are weaker and direction-unstable across modes — consistent with the original Phase 1b finding that D is model-specific and reverses for Grok/Gemini.

## Per-model breakdown (cells positive out of 4)

```
model       self    cross
anthropic   4/4     3/4
gemini      0/4     3/4    <-- selfsame totally fails
openai      2/4     4/4
xai         3/4     3/4
```

**Key observation:** Anthropic is the only model where self-scoring beats cross-scoring (4/4 vs 3/4) — and it does so by *amplifying* deltas (e.g., D=+0.50 self vs +0.12 cross, C=+0.88 self vs +0.29 cross). This looks like Claude is unusually willing to "see what it intended to put there" when scoring its own output.

Gemini collapses to 0/4 under selfsame — scoring its own outputs, it produces no positive directional signal at all. The Phase 1b finding that Gemini reverses on D and reads NT-stack as "arousal" not "approach" gets *worse* when Gemini is the only voice, not better.

OpenAI also drops (2/4 vs 4/4) — self-scoring is noisy for it.

Grok is roughly equivalent (3/4 either way).

## Test-retest: scorer self-consistency

The scoring_self/ run produced an independent second pass of the same 816 cross-model pairings as the original scoring/ run. Comparing them directly:

- **Matched pairs:** 816
- **Pearson r:** 0.804
- **Exact-score match:** 81.6%
- **Within 1 point:** 96.3%
- Means almost identical (3.12 vs 3.25)

Scorer LLMs are highly stable on re-runs of the same prompt. So the ~25-point drop in directional confirmation under selfsame is **not** noise — it's a real methodology effect.

## Self-score vs. mean cross-score correlation

Within scoring_self/, for each (output, dimension) we have one self-score and three cross-scores. Correlating the self-score against the mean of the three cross-scores:

- **Overall:** n=272, Pearson r=0.866 (high agreement on absolute level)
- Per dimension:
  - D (dopamine): r=0.42
  - C (cortisol): r=0.29
  - N (norepinephrine): r=0.54
  - E (endorphins): r=0.59

The high overall r=0.87 is largely driven by *between-dimension* differences (E is rated low for everything, C is rated high). Within-dimension agreement (0.29–0.59) is much weaker. Self-scorers and cross-scorers don't strongly agree on which *outputs* express a given dimension — they mainly agree on which dimensions the corpus is loaded for overall.

## Interpretation

The Phase 1 ground-truth (14/16 directional) was itself **selfsame LLM gen+score** — same model generated and scored. We expected this re-run to reproduce that result on the Phase 1b stimulus set. It did not: selfsame on Phase 1b drops to 9/16 = 56%, while cross-model holds at 13/16 = 81%.

This is a real methodology puzzle, not a human-vs-LLM artifact. Findings:

1. Selfsame loses directional reliability vs. cross-model on Phase 1b (56% vs 81%).
2. The effect is highly model-dependent: Anthropic over-amplifies (4/4), Gemini collapses (0/4), OpenAI drops (2/4), Grok unchanged (3/4).
3. The gap is not noise: test-retest of cross-model scoring is r=0.80, exact-match 81.6%.

## Why doesn't this reproduce Phase 1's 14/16?

Candidate explanations to investigate before drawing conclusions:

- **Stimulus design.** Phase 1 used 4-level conditions per NT (low / med-low / med-high / high), giving graded signal. Phase 1b uses **binary on/off** per NT, which compresses the signal and may not move scorers off the midpoint as readily. The selfsame run's scores cluster heavily (e.g., E mean = 1.74 self / 1.53 cross; C mean = 4.29 both), suggesting compression.
- **Cross-model contamination of intuition.** Phase 1's 14/16 was on a single model, generating and scoring. Phase 1b runs four models and aggregates. Per-model variance is huge (Anthropic 4/4, Gemini 0/4 under selfsame). Phase 1's result may have been a single-model success that doesn't generalize.
- **Prompt / rubric drift.** The Phase 1b scorer prompt / rubric may differ from whatever Phase 1 used. Worth diffing before blaming the methodology.
- **Different stimulus count.** Phase 1: 16 conditions. Phase 1b: 17 conditions (16 binary perms + ablation) × 4 models = 68 outputs. Different scoring scale, different scoring load.

**Recommendation:** Until the Phase 1 / Phase 1b selfsame gap is explained, treat cross-model (leave-one-out) as the safer methodology for Phase 1b. But do **not** dismiss selfsame as broken — it worked in Phase 1 and the per-model variance here suggests the issue may be model-mix or stimulus-design, not the methodology itself.

**Useful follow-on:** Anthropic's amplified self-deltas (D=+0.50 self vs +0.12 cross, C=+0.88 vs +0.29) deserve a closer look. Either Claude is unusually self-aware about which condition it was given, or its scorer is anchored to its own generation in a way the others aren't.
