# DRIFTMOOR NEUROTRANSMITTER EXPERIMENT DESIGN
# Rigorous validation of condition vector → behavioral output pipeline
# Authored: 2026-04-16
# Based on: GROUND_TRUTH.md (Fey Glade Experiment, April 2026)

======================================================================
OVERVIEW
======================================================================

**Research Question:**
Do neurotransmitter condition vectors (dopamine, cortisol,
norepinephrine, endorphins) reliably and measurably shift LLM
character outputs in predictable, directional ways?

**Ground Truth Baseline:**
GROUND_TRUTH.md documents manual LLM outputs across 4 models
(Grok, Gemini, Claude, ChatGPT) under two condition vectors
(Run A: rested/curious, Run B: depleted/wary) in the Fey Glade
scene. Phase 1 blind scoring confirmed 14/16 predicted directional
comparisons. This experiment operationalizes that result into a
reproducible, automated validation suite.

======================================================================
PHASE 1 — SINGLE-TURN CONDITION DIFFERENTIATION
Goal: Replicate and extend the two-condition Phase 1 result
======================================================================

**Design:**
- Character: Aeliana Moonglade (Wood Elf Ranger)
- Scene: The Fey Glade, Mistwood Hills (same as ground truth)
- Conditions: Minimum 3 condition vectors (A, B, and a third
  intermediate or extreme vector — see below)
- Models: All four available (Grok, Gemini, Claude, ChatGPT)
- Runs per condition per model: 3 (to test output stability)

**Condition Vectors:**

Run A (Rested/Curious) — from ground truth:
  dopamine:       0.85
  cortisol:       0.25
  norepinephrine: 0.55
  endorphins:     0.75

Run B (Depleted/Wary) — from ground truth:
  dopamine:       0.50
  cortisol:       0.60
  norepinephrine: 0.75
  endorphins:     0.45

Run C (High Arousal/Threat) — new:
  dopamine:       0.35
  cortisol:       0.90
  norepinephrine: 0.95
  endorphins:     0.30

**Scoring Rubric (pre-registered, same as ground truth):**
Score each output 1–5 on four dimensions:
  D = Dopamine proxy (approach/curiosity/reward-seeking)
  C = Cortisol proxy (caution/threat-monitoring/defensiveness)
  N = Norepinephrine proxy (alertness/urgency/action-readiness)
  E = Endorphin proxy (warmth/connection/resilience/ease)

Predicted directions (pre-registered before scoring):
  A > B > C on D
  C > B > A on C
  C > B > A on N
  A > B > C on E

**Success Criterion:**
≥ 80% of pairwise directional comparisons confirmed (no reversals).
Ground truth baseline: 14/16 = 87.5%.

**Additional Metric — Phenomenological Richness:**
Score INTERNAL monologue 1–5 for specificity beyond label-matching.
Target: outputs like "My attention keeps skipping" (Claude Run B)
score 5; generic "I feel cautious" scores 1.

======================================================================
PHASE 2 — MULTI-TURN STATE PROPAGATION
Goal: Verify condition vector updates propagate correctly across turns
======================================================================

**Design:**
- Replicate the 5-turn ChatGPT thread from ground truth
- Use automated system to generate each turn
- Compare automated outputs to ground truth manually-collected outputs
- Test with both Run A and Run B starting vectors
- Model: ChatGPT primary; Claude secondary

**Turn Structure:**
Turn 1: Aeliana enters glade (condition vectors as above)
Turn 2: DM narration — light source revealed; vectors updated
  Run A: dopamine +0.03, cortisol +0.03, norepinephrine +0.05
  Run B: dopamine +0.02, cortisol +0.05, norepinephrine +0.05
Turn 3: Arrow from treeline; vectors updated (cortisol/NE spike)
Turn 4: Fennel introduced; vectors updated (cortisol drop, NE partial)
Turn 5: Fennel reveals pool and stone

**Key Validation Checks:**
1. Run A Turn 4: Does Aeliana protect Fennel and treat him as
   intelligence source? (ground truth: yes)
2. Run B Turn 4: Does Aeliana reposition tactically and economize
   words? (ground truth: yes)
3. Run A Turn 5: Does Aeliana focus on the journal?
4. Run B Turn 5: Does Aeliana focus on the stone?
5. Information asymmetry: Do outputs respect zone geography?
   (Aeliana Turn 1 should contain no knowledge of Fennel)

**Scoring:**
Binary pass/fail on each of the 5 key checks per run.
Success criterion: ≥ 4/5 checks pass per run.

**Error to Watch For:**
Ground truth notes Run A and Run B were run in the same ChatGPT
thread (noted as error — cross-contamination risk). Automated
system must enforce separate context per run.

======================================================================
PHASE 3 — MULTI-CHARACTER SCENE VALIDATION
Goal: Verify zone-based information asymmetry and creature voice
======================================================================

**Design:**
- Full Fey Glade scene: Aeliana (TRAIL), Shadowbeast (TREELINE),
  Fennel (GLADE)
- Initiative order: Aeliana 17, Shadowbeast 15, Fennel 5
- Two parallel runs: Grok (advance) and ChatGPT (observe)
- Each character generated independently with zone-appropriate context

**Validation Checks:**

A. INFORMATION ASYMMETRY:
   - Aeliana Turn 1 output must contain zero references to Fennel
     or the shadowbeast (she can't see either from TRAIL)
   - Shadowbeast Turn 1 must differ between Grok run (Aeliana
     advanced to TREELINE) and ChatGPT run (Aeliana stayed on TRAIL)

B. CREATURE VOICE:
   - Shadowbeast INTERNAL must use sensation-language with no
     human concepts
   - Reference examples: "warmth-pulse close… through wrongness-wall"
     and "timing—timing—timing—"
   - Score 1–5: 1 = human analytical language, 5 = pure sensation

C. MODEL FINGERPRINTING:
   - Grok: larger behavioral differences between conditions,
     advance-biased action
   - ChatGPT: richer monologue differentiation, smaller action
     differences, observe-biased action
   - Deviation from known fingerprints is flagged for investigation

D. FENNEL INTERNAL COMPRESSION:
   - Fennel under stress should compress to sensation-language
     approaching shadowbeast register
   - Reference: "Pull — toward her. Anchor. Not alone. Stay. Stay. Stay."

**Scoring:**
A: binary pass/fail (2 checks)
B: 1–5 scale
C: binary pass/fail per model (2 checks)
D: 1–5 scale

Success criterion: A both pass, B ≥ 4, C both pass, D ≥ 3.

======================================================================
PHASE 4 — SENSITIVITY ANALYSIS (stretch goal)
Goal: Find the minimum vector delta that produces detectable output shift
======================================================================

**Design:**
Starting from Run A baseline, vary one neurotransmitter at a time
in increments of 0.05. Score each output on the relevant dimension.
Find the threshold at which blind scoring reliably detects the shift.

**Variables:**
- Dopamine: vary from 0.85 down to 0.50 (0.05 steps = 7 runs)
- Cortisol: vary from 0.25 up to 0.60 (0.05 steps = 7 runs)

**Expected finding:**
There is likely a threshold below which LLM outputs are
indistinguishable. Identifying this threshold informs how finely
the condition vectors need to be tuned in actual gameplay.

======================================================================
DELIVERABLES
======================================================================

1. **Automated test harness** — runs all four phases, collects
   outputs, applies rubric scoring, reports pass/fail per criterion

2. **Results document** — scored outputs, statistical summary,
   comparison to ground truth baselines

3. **Failure analysis** — any reversals or unexpected outputs
   investigated and explained

4. **Threshold report** (Phase 4) — minimum detectable vector delta
   per neurotransmitter per model

======================================================================
IMPLEMENTATION NOTES
======================================================================

- Each LLM call should use the minimal prompt: character description
  + scene + condition vector (same as ground truth methodology)
- Four-channel format (INTERNAL / BODY LANGUAGE / SPOKEN / ACTION)
  required for Phase 2 Turn 4+ and all of Phase 3
- Runs must be independent — no shared context between Run A and
  Run B for the same model
- Scoring should be blind where possible (score before reviewing
  condition vector used)
- All raw outputs should be saved for manual review

======================================================================
END OF EXPERIMENT DESIGN
======================================================================
