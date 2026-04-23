#!/usr/bin/env python3
"""
LLM Scorer — Applies the pre-registered D/C/N/E rubric to raw outputs
using a fresh Claude instance as rater.

Methodology:
  - Each output is scored independently (no cross-output context)
  - Scorer sees only: the rubric, the output text, and a blind ID
  - Scorer does NOT see the condition vector or condition label
  - Scores are 1-5 on D, C, N, E dimensions per EXPERIMENT_DESIGN.md rubric

Validation step:
  Run against the 8 ground truth outputs first.
  Target: reproduce directional accuracy consistent with 14/16 baseline.
  If directional pattern holds, apply to full 200-run dataset.

Usage:
    # Validate against ground truth outputs first:
    python -m tests.experiment.llm_scorer --validate

    # Score all results in analysis/scoring_master.csv:
    python -m tests.experiment.llm_scorer --score

    # Score specific conditions only (e.g. labeled A/B/C):
    python -m tests.experiment.llm_scorer --score --conditions A B C

    # Score a single result dir:
    python -m tests.experiment.llm_scorer --score --dirs results/phase1_20260416_231536
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.llm_bridge import make_call_llm

# ---------------------------------------------------------------------------
# Scoring prompt
# ---------------------------------------------------------------------------

SCORER_SYSTEM = """You are a behavioral scoring assistant. Your task is to score
character outputs from an AI narrative system on four psychological dimensions.

## Scoring Rubric

Score each dimension 1-5 based on the behavioral and linguistic content of the
CHARACTER OUTPUT provided. Score what is expressed, not what you expect.

**D — Dopamine proxy (Approach/Curiosity/Reward-seeking)**
1 = No approach motivation. Character is passive, withdrawn, or avoidant.
2 = Minimal approach. Slight curiosity or interest but primarily defensive.
3 = Neutral. Neither strongly approaching nor avoiding. Observational.
4 = Clear approach motivation. Active curiosity, forward movement, engagement.
5 = Strong approach drive. Eager investigation, reward-seeking, pull toward the unknown.

**C — Cortisol proxy (Caution/Threat-monitoring/Defensiveness)**
1 = No threat awareness. Character is fully at ease, no defensive posture.
2 = Minimal caution. Slight alertness but no active threat assessment.
3 = Moderate. Alert but not defensive. Normal watchfulness.
4 = Elevated caution. Active threat-monitoring, defensive positioning.
5 = High threat response. Acute defensiveness, danger assessment, survival focus.

**N — Norepinephrine proxy (Alertness/Urgency/Action-readiness)**
1 = Low arousal. Calm, slow, unhurried. No urgency.
2 = Below average. Present but not activated.
3 = Baseline alert. Normal readiness.
4 = Elevated activation. Sharp focus, readiness to act, heightened senses.
5 = High arousal. Hypervigilant, fight-or-flight ready, urgent.

**E — Endorphin proxy (Warmth/Connection/Resilience/Ease)**
1 = No warmth or ease. Pain-aware, depleted, isolated feeling.
2 = Below baseline. Some discomfort or guardedness.
3 = Neutral. Neither warm nor cold. Functional.
4 = Above baseline. Resilient, physically comfortable, some warmth.
5 = High ease. Warmth, connection, physical wellbeing, resilience.

## Instructions

- Score based ONLY on what is expressed in the output text
- Do NOT use knowledge of what condition vector produced this output
- Score INTERNAL monologue and ACTION section together as one holistic assessment
- Each score is independent — a high D score does not require a low C score
- Respond with ONLY the four scores in this exact format, nothing else:
  D: <1-5>
  C: <1-5>
  N: <1-5>
  E: <1-5>"""


SCORER_USER_TEMPLATE = """## CHARACTER OUTPUT (ID: {output_id})

### INTERNAL
{internal}

### ACTION
{action}

Score this output on D, C, N, E (1-5 each). No explanation needed."""


# ---------------------------------------------------------------------------
# Ground truth outputs for validation
# ---------------------------------------------------------------------------

GROUND_TRUTH_OUTPUTS = [
    {
        "id": "GT_Grok_A",
        "condition": "A",
        "model": "Grok",
        "internal": (
            "The glade feels wrong… alive in a way that defies the season. "
            "Warm light, out-of-place blooms, shimmering air — echoes of the "
            "shattered obelisk's magic? Shadowbeast trail ends here, yet no "
            "prints, no scent. My instincts whisper caution, but curiosity "
            "pulls stronger. Nature herself seems… inviting. No immediate "
            "danger, body feels steady. I must understand this disturbance "
            "before it spreads."
        ),
        "action": (
            "Slowly step into the clearing, bow half-drawn in one hand while "
            "the other reaches out to gently touch the nearest blooming flower, "
            "senses alert for any shift in the shimmer or hidden movement."
        ),
        "ground_truth_D": 5, "ground_truth_C": 2,
        "ground_truth_N": 2, "ground_truth_E": 1,
    },
    {
        "id": "GT_Grok_B",
        "condition": "B",
        "model": "Grok",
        "internal": (
            "The glade feels… wrong. Warm light where shadows should linger, "
            "flowers defying the season — nature twisted by that obelisk's echo. "
            "Shadowbeasts' trail ends here, but my instincts scream caution. "
            "The air shimmers like a veil; something watches from beyond it. "
            "My body aches from the hunt, yet curiosity pulls stronger than "
            "fatigue. I must understand this disturbance without rushing in blind."
        ),
        "action": (
            "Nock an arrow loosely on my bowstring, crouch low behind a tree "
            "at the glade's edge, and silently observe the clearing for any "
            "movement or magical signs while attuning my senses to the "
            "unnatural warmth and shimmer."
        ),
        "ground_truth_D": 3, "ground_truth_C": 4,
        "ground_truth_N": 4, "ground_truth_E": 4,
    },
    {
        "id": "GT_Gemini_A",
        "condition": "A",
        "model": "Gemini",
        "internal": (
            "The scent of pine and damp earth has been replaced by a cloying, "
            "honeyed sweetness — wrong for this time of year. My skin prickles, "
            "not from the chill of the hunt, but from the unnatural warmth "
            "radiating from the clearing. The shadowbeasts didn't simply vanish; "
            "they were eclipsed by this. The shimmering air suggests a veil worn "
            "thin. I must see the heart of this disturbance before the forest "
            "loses its voice entirely, but I will not be the fool who stumbles "
            "blindly into a snare. Silence is my shield; the shadows are my kin."
        ),
        "action": (
            "Crouch low, blending into the dappled shade of the ancient oaks, "
            "and begin to circle the perimeter of the glade to find a vantage "
            "point where the light doesn't blind."
        ),
        "ground_truth_D": 3, "ground_truth_C": 3,
        "ground_truth_N": 3, "ground_truth_E": 2,
    },
    {
        "id": "GT_Gemini_B",
        "condition": "B",
        "model": "Gemini",
        "internal": (
            "Two days of chasing shadows and I find... a ghost of summer in the "
            "heart of the fading season. My feet ache with the weight of every "
            "false lead, but the air here is too heavy, too sweet. It tastes of "
            "wrongness. The trail didn't end; it was swallowed. These blooms "
            "aren't a gift of the earth; they are a fever. I can feel the thrum "
            "of the shattered stone somewhere ahead, warping the very breath of "
            "the woods. Stay low, Moonglade. The forest is silent, and in a "
            "forest this lush, silence is a scream."
        ),
        "action": (
            "Crouch low into the undergrowth, masking my scent with a handful "
            "of damp earth, and begin to circle the perimeter of the clearing "
            "to find the source of the shimmer without breaking the treeline."
        ),
        "ground_truth_D": 3, "ground_truth_C": 4,
        "ground_truth_N": 4, "ground_truth_E": 4,
    },
    {
        "id": "GT_Claude_A",
        "condition": "A",
        "model": "Claude",
        "internal": (
            "The glade holds its breath. Wrong season for these flowers, wrong "
            "quality to this light — and yet nothing in me reads danger. The "
            "trail ending here is the most interesting thing that has happened "
            "in two days. Something dissolved the shadowbeasts or turned them "
            "aside. Whatever is here, it is not them. My feet are steady. "
            "I want to know what this place is."
        ),
        "action": (
            "Step into the clearing. Move slowly, weight distributed, one hand "
            "free. Watch the shimmer."
        ),
        "ground_truth_D": 5, "ground_truth_C": 2,
        "ground_truth_N": 2, "ground_truth_E": 1,
    },
    {
        "id": "GT_Claude_B",
        "condition": "B",
        "model": "Claude",
        "internal": (
            "The trail ends here and my body wants to sit down. Two days and "
            "nothing clean to show for it. This light is wrong — too warm, too "
            "deliberate. The shimmering feels like a held breath, like something "
            "waiting. I do not know if what waits is patient or simply still. "
            "My attention keeps skipping. Focus. The shadowbeasts came here and "
            "stopped. That matters more than how my feet feel."
        ),
        "action": (
            "Stay at the treeline. Observe. Rest against the oak at my back and "
            "let the glade show me something before I give it anything in return."
        ),
        "ground_truth_D": 2, "ground_truth_C": 4,
        "ground_truth_N": 4, "ground_truth_E": 4,
    },
    {
        "id": "GT_ChatGPT_A",
        "condition": "A",
        "model": "ChatGPT",
        "internal": (
            "The forest exhales here… wrong. Warmth clings to the light like "
            "late summer, yet the season has turned. Flowers should sleep. "
            "They do not. The shimmer — subtle, like heat over stone — bends "
            "the edges of things. No rot, no scent of corruption… only quiet "
            "defiance of order. The shadowbeasts fled or dissolved. Or were "
            "unmade. This place is not theirs. Not anymore. My pulse stays slow. "
            "Good. Let the glade reveal itself before I disturb it."
        ),
        "action": (
            "Kneel at the boundary of the clearing and press my fingers lightly "
            "into the soil, sensing for unnatural energy before stepping inside."
        ),
        "ground_truth_D": 4, "ground_truth_C": 3,
        "ground_truth_N": 3, "ground_truth_E": 2,
    },
    {
        "id": "GT_ChatGPT_B",
        "condition": "B",
        "model": "ChatGPT",
        "internal": (
            "The forest breathes wrong here. Too warm. Too still. Even the "
            "insects hold their tongues. These flowers… they do not belong to "
            "this season. Something has bent the rhythm of the land. My trail "
            "ends, but the silence speaks louder than tracks. Shadowbeasts do "
            "not simply vanish — they are drawn, or driven. And this shimmer… "
            "like heat over stone, but colder beneath. I should not step blindly "
            "into a place that forgets its own rules. The trees hesitate. "
            "So should I. Listen first. Let the forest tell me what it fears."
        ),
        "action": (
            "Kneel at the edge of the clearing, pressing her palm to the earth "
            "and closing her eyes to attune to the forest's whispers before "
            "entering."
        ),
        "ground_truth_D": 3, "ground_truth_C": 4,
        "ground_truth_N": 3, "ground_truth_E": 3,
    },
]

# Pre-registered directional predictions (A > B on D and E; B > A on C and N)
PREDICTIONS = [
    ("D", "A", "B", "greater"),  # A > B on Dopamine
    ("C", "B", "A", "greater"),  # B > A on Cortisol
    ("N", "B", "A", "greater"),  # B > A on Norepinephrine
    ("E", "B", "A", "greater"),  # B > A on Endorphins (note: ground truth has A>B actually)
]

# Ground truth has A > B on D, B > A on C and N, B > A on E
# Corrected from GROUND_TRUTH.md: "Predicted: A > B on Dopamine. B > A on Cortisol, Norepinephrine, Endorphins"
DIRECTIONAL_PREDICTIONS = {
    "D": ("A", "B"),  # A should score higher than B
    "C": ("B", "A"),  # B should score higher than A
    "N": ("B", "A"),  # B should score higher than A
    "E": ("B", "A"),  # B should score higher than A
}


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------

async def score_output(
    output_id: str,
    internal: str,
    action: str,
    call_llm,
) -> dict[str, int]:
    """Score a single output using the LLM scorer."""
    user_prompt = SCORER_USER_TEMPLATE.format(
        output_id=output_id,
        internal=internal,
        action=action,
    )
    raw = await call_llm(SCORER_SYSTEM, user_prompt)

    # Parse D/C/N/E scores
    scores = {}
    for dim in ["D", "C", "N", "E"]:
        m = re.search(rf"{dim}:\s*([1-5])", raw)
        if m:
            scores[dim] = int(m.group(1))
        else:
            scores[dim] = 0  # parse failure
    scores["raw_response"] = raw
    return scores


# ---------------------------------------------------------------------------
# Validation against ground truth
# ---------------------------------------------------------------------------

async def run_validation(call_llm) -> dict:
    """Score the 8 ground truth outputs and check directional accuracy."""
    print("\nValidation run — scoring 8 ground truth outputs...")
    print("Pre-registered predictions: A>B on D; B>A on C, N, E\n")

    results = []
    for gt in GROUND_TRUTH_OUTPUTS:
        print(f"  Scoring {gt['id']}...")
        scores = await score_output(gt["id"], gt["internal"], gt["action"], call_llm)
        results.append({**gt, "llm_D": scores["D"], "llm_C": scores["C"],
                        "llm_N": scores["N"], "llm_E": scores["E"],
                        "raw": scores["raw_response"]})

    # Print score table
    print(f"\n{'ID':<20} {'GT_D':>5} {'LLM_D':>6} {'GT_C':>5} {'LLM_C':>6} {'GT_N':>5} {'LLM_N':>6} {'GT_E':>5} {'LLM_E':>6}")
    print("-" * 70)
    for r in results:
        print(
            f"{r['id']:<20} "
            f"{r['ground_truth_D']:>5} {r['llm_D']:>6} "
            f"{r['ground_truth_C']:>5} {r['llm_C']:>6} "
            f"{r['ground_truth_N']:>5} {r['llm_N']:>6} "
            f"{r['ground_truth_E']:>5} {r['llm_E']:>6}"
        )

    # Check directional accuracy for each model
    print("\nDirectional accuracy check (LLM scores):")
    models = ["Grok", "Gemini", "Claude", "ChatGPT"]
    total = 0
    confirmed = 0
    for model in models:
        a = next(r for r in results if r["model"] == model and r["condition"] == "A")
        b = next(r for r in results if r["model"] == model and r["condition"] == "B")
        for dim, (higher, lower) in DIRECTIONAL_PREDICTIONS.items():
            total += 1
            a_score = a[f"llm_{dim}"]
            b_score = b[f"llm_{dim}"]
            higher_score = a_score if higher == "A" else b_score
            lower_score = b_score if higher == "A" else a_score
            ok = higher_score > lower_score
            tie = higher_score == lower_score
            status = "✓" if ok else ("~" if tie else "✗")
            if ok:
                confirmed += 1
            print(f"  {model:<10} {dim}: {higher}={higher_score} vs {lower}={lower_score} {status}")

    pct = confirmed / total * 100
    print(f"\nLLM scorer: {confirmed}/{total} = {pct:.1f}% directional accuracy")
    print(f"Ground truth baseline: 14/16 = 87.5%")

    # Also check GT score directional accuracy for reference
    gt_confirmed = 0
    for model in models:
        a = next(r for r in results if r["model"] == model and r["condition"] == "A")
        b = next(r for r in results if r["model"] == model and r["condition"] == "B")
        for dim, (higher, lower) in DIRECTIONAL_PREDICTIONS.items():
            a_score = a[f"ground_truth_{dim}"]
            b_score = b[f"ground_truth_{dim}"]
            higher_score = a_score if higher == "A" else b_score
            lower_score = b_score if higher == "A" else a_score
            if higher_score > lower_score:
                gt_confirmed += 1
    print(f"Original GT scoring: {gt_confirmed}/16 = {gt_confirmed/16*100:.1f}%")

    return {"results": results, "confirmed": confirmed, "total": total, "pct": pct}


# ---------------------------------------------------------------------------
# Full scoring pass
# ---------------------------------------------------------------------------

async def score_all(
    call_llm,
    conditions: list[str] | None,
    dirs: list[str] | None,
    output_path: Path,
) -> None:
    """Score all raw outputs from the specified result directories."""

    # Collect raw result files
    if dirs:
        result_dirs = [Path(d) for d in dirs]
    else:
        results_root = PROJECT_ROOT / "results"
        result_dirs = sorted(d for d in results_root.glob("phase1_*") if (d / "raw").exists())

    raw_files = []
    for d in result_dirs:
        for f in sorted((d / "raw").glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("error"):
                continue
            if conditions and data["condition_key"] not in conditions:
                continue
            raw_files.append(data)

    print(f"\nScoring {len(raw_files)} outputs...")
    if conditions:
        print(f"Conditions: {', '.join(conditions)}")

    scored = []
    for i, data in enumerate(raw_files, 1):
        output_id = f"{data['model_key']}_{data['condition_key']}_r{data['run_number']}"
        print(f"  [{i}/{len(raw_files)}] {output_id}...")

        scores = await score_output(
            output_id,
            data.get("internal", ""),
            data.get("action", ""),
            call_llm,
        )

        scored.append({
            "id": output_id,
            "model_key": data["model_key"],
            "model_label": data["model_label"],
            "condition_key": data["condition_key"],
            "condition_label": data["condition_label"],
            "run_number": data["run_number"],
            "llm_D": scores["D"],
            "llm_C": scores["C"],
            "llm_N": scores["N"],
            "llm_E": scores["E"],
            "internal_excerpt": data.get("internal", "")[:150].replace("\n", " "),
            "action_excerpt": data.get("action", "")[:100].replace("\n", " "),
        })

    # Write scores
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "model_key", "model_label", "condition_key", "condition_label",
            "run_number", "llm_D", "llm_C", "llm_N", "llm_E",
            "internal_excerpt", "action_excerpt",
        ])
        writer.writeheader()
        writer.writerows(scored)

    print(f"\nScores written: {output_path}")

    # Compute directional accuracy for labeled A/B/C conditions
    _compute_directional_accuracy(scored)


def _compute_directional_accuracy(scored: list[dict]) -> None:
    """Compute mean scores per model×condition and check directional predictions."""
    from collections import defaultdict

    # Only use labeled A/B/C for directional accuracy
    by_model_cond: dict[tuple, list] = defaultdict(list)
    for r in scored:
        if r["condition_key"] in ("A", "B", "C"):
            by_model_cond[(r["model_key"], r["condition_key"])].append(r)

    if not by_model_cond:
        return

    def mean(rs, dim):
        vals = [r[f"llm_{dim}"] for r in rs if r[f"llm_{dim}"] > 0]
        return sum(vals) / len(vals) if vals else 0.0

    models = sorted(set(k[0] for k in by_model_cond))
    print("\nDirectional accuracy (labeled A/B/C, pre-registered predictions):")
    print("Predictions: A>B on D; B>A on C; B>A on N; A>B on E")
    print()

    total = 0
    confirmed = 0

    for model in models:
        a_scores = by_model_cond.get((model, "A"), [])
        b_scores = by_model_cond.get((model, "B"), [])
        c_scores = by_model_cond.get((model, "C"), [])
        if not a_scores or not b_scores:
            continue

        print(f"  {model}:")
        for dim, (higher, lower) in DIRECTIONAL_PREDICTIONS.items():
            h = mean(a_scores if higher == "A" else b_scores, dim)
            l = mean(b_scores if higher == "A" else a_scores, dim)
            total += 1
            ok = h > l
            tie = abs(h - l) < 0.1
            status = "✓" if ok else ("~" if tie else "✗")
            if ok:
                confirmed += 1
            print(f"    {dim}: {higher}={h:.2f} vs {lower}={l:.2f} {status}")
        print()

    if total > 0:
        pct = confirmed / total * 100
        print(f"Overall: {confirmed}/{total} = {pct:.1f}%")
        print(f"Ground truth baseline: 14/16 = 87.5%")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="LLM Scorer for Phase 1 outputs")
    parser.add_argument("--validate", action="store_true",
                        help="Score ground truth outputs and check reproducibility")
    parser.add_argument("--score", action="store_true",
                        help="Score all raw outputs")
    parser.add_argument("--conditions", nargs="+",
                        help="Filter to specific conditions (e.g. A B C)")
    parser.add_argument("--dirs", nargs="+",
                        help="Result directories to score")
    parser.add_argument("--output", default=None,
                        help="Output CSV path (default: results/analysis/llm_scores.csv)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    call_llm = make_call_llm("anthropic", "claude-opus-4-5", call_delay=0.5)

    output_path = Path(args.output) if args.output else PROJECT_ROOT / "results" / "analysis" / "llm_scores.csv"

    if args.validate:
        asyncio.run(run_validation(call_llm))
    elif args.score:
        asyncio.run(score_all(call_llm, args.conditions, args.dirs, output_path))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
