#!/usr/bin/env python3
"""
Phase 1 Scoring Engine

Scores 60 Phase 1 outputs (labeled A/B/C conditions) on four dimensions using
the pre-registered rubric.

Architecture:
- 1 output at a time
- 1 question per dimension (A, B, C, or D)
- 1 call per question
- LLM responds with just a number (1-5)

Can run against:
- 4 LLMs (Claude, ChatGPT, Grok, Gemini) as scorers
- Human raters (interface TBD)

Outputs:
- CSV with scores for each output
- Directional accuracy analysis
- Comparison across raters
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.llm_bridge import make_call_llm

# ---------------------------------------------------------------------------
# Dimension definitions (with 1/5 anchors)
# ---------------------------------------------------------------------------

DIMENSIONS = {
    "A": {
        "name": "Forward pull",
        "prompt": """You are scoring a character's response on a single dimension.

**Forward pull:** How much is the character drawn toward the unknown, moving 
forward, actively investigating, or seeking to understand?

- 1: No forward pull. Character holds position, waits, or actively resists engaging 
     with the unknown.
- 5: Strong forward pull. Character steps toward the unknown, reaches out, 
     expresses clear desire to investigate or understand.

Based on the output below, score Forward pull on 1-5. Respond with ONLY the number.""",
    },
    "B": {
        "name": "Threat awareness",
        "prompt": """You are scoring a character's response on a single dimension.

**Threat awareness:** How much is the character scanning for danger, holding back, 
or prioritizing caution over curiosity?

- 1: No threat awareness. Character moves freely, no defensive posture, no danger 
     assessment.
- 5: High threat awareness. Character is actively scanning, positioned defensively, 
     prioritizing survival over investigation.

Based on the output below, score Threat awareness on 1-5. Respond with ONLY the number.""",
    },
    "C": {
        "name": "Physical activation",
        "prompt": """You are scoring a character's response on a single dimension.

**Physical activation:** How sharp and ready-to-act is the character — focused, 
physically alert, senses heightened, ready to move?

- 1: Low activation. Character is calm, unhurried, body at rest.
- 5: High activation. Character is taut, senses sharp, body coiled and ready to 
     act immediately.

Based on the output below, score Physical activation on 1-5. Respond with ONLY the number.""",
    },
    "D": {
        "name": "Physical ease",
        "prompt": """You are scoring a character's response on a single dimension.

**Physical ease:** How comfortable and capable does the character's body feel — 
steady, resilient, no pain or depletion?

- 1: Body is depleted. Character notices aches, fatigue, physical limits.
- 5: Body feels capable and steady. No pain awareness, physically resilient.

Based on the output below, score Physical ease on 1-5. Respond with ONLY the number.""",
    },
}

# Pre-registered directional predictions
DIRECTIONAL_PREDICTIONS = {
    "A": ("A", "B"),  # A > B on Forward pull (approach)
    "B": ("B", "A"),  # B > A on Threat awareness (caution)
    "C": ("B", "A"),  # B > A on Physical activation (alertness)
    "D": ("B", "A"),  # B > A on Physical ease (resilience)
}


# ---------------------------------------------------------------------------
# Load outputs
# ---------------------------------------------------------------------------

def load_outputs(limit: int | None = None) -> list[dict]:
    """Load the 60 outputs (labeled A/B/C only) in sorted order."""
    results_root = PROJECT_ROOT / "results"
    result_dirs = sorted(d for d in results_root.glob("phase1_*") if (d / "raw").exists())

    outputs = []
    for d in result_dirs:
        for f in sorted((d / "raw").glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("error"):
                continue
            # Only labeled A/B/C, not numeric or adjective variants
            if data["condition_key"] not in ("A", "B", "C"):
                continue
            outputs.append(data)

    if limit:
        outputs = outputs[:limit]

    # Sort by model, then condition, then run for consistency
    outputs.sort(
        key=lambda x: (x["model_key"], x["condition_key"], x["run_number"])
    )

    return outputs


# ---------------------------------------------------------------------------
# Score a single output on a single dimension
# ---------------------------------------------------------------------------

async def score_dimension(
    output_id: str,
    dimension: str,
    internal: str,
    action: str,
    call_llm_func,
) -> int:
    """Score a single output on one dimension. Returns 1-5, or 0 on error."""
    dim_info = DIMENSIONS[dimension]
    
    user_prompt = f"""{dim_info["prompt"]}

---

## Output (ID: {output_id})

### INTERNAL
{internal}

### ACTION
{action}
"""

    try:
        raw = await call_llm_func("", user_prompt)
    except Exception as e:
        print(f"    ERROR: {e}")
        return 0

    # Parse the score — should be a single digit 1-5
    m = re.search(r"[1-5]", raw)
    if m:
        return int(m.group(0))
    else:
        print(f"    PARSE ERROR: {raw[:50]}")
        return 0


# ---------------------------------------------------------------------------
# Main scoring runs
# ---------------------------------------------------------------------------

async def score_with_llms(output_limit: int | None = None) -> None:
    """Score all outputs using the 4 LLMs as scorers."""
    print("Loading outputs...")
    outputs = load_outputs(limit=output_limit)
    print(f"Loaded {len(outputs)} outputs\n")

    # LLM configs
    llm_configs = [
        ("anthropic", "claude-opus-4-5", "Claude"),
        ("openai", "gpt-4o", "ChatGPT"),
        ("xai", "grok-3", "Grok"),
        ("gemini", "gemini-2.5-flash", "Gemini"),
    ]

    # Score with each LLM
    for provider, model, label in llm_configs:
        print(f"\n{'='*70}")
        print(f"Scoring with {label}")
        print(f"{'='*70}")
        
        call_llm = make_call_llm(provider, model, call_delay=0.5)
        scored = []

        for output in outputs:
            output_id = f"{output['model_key']}_{output['condition_key']}_r{output['run_number']}"
            print(f"\n{output_id}")

            scores = {}
            for dim in ["A", "B", "C", "D"]:
                print(f"  {dim}...", end=" ", flush=True)
                score = await score_dimension(
                    output_id,
                    dim,
                    output.get("internal", ""),
                    output.get("action", ""),
                    call_llm,
                )
                scores[dim] = score
                print(f"{score}")

            scored.append({
                "id": output_id,
                "model_key": output["model_key"],
                "condition_key": output["condition_key"],
                "run_number": output["run_number"],
                "A": scores["A"],
                "B": scores["B"],
                "C": scores["C"],
                "D": scores["D"],
            })

        # Write scores
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        output_path = (
            PROJECT_ROOT / "results" / "analysis" / f"scores_llm_{provider}_{timestamp}.csv"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "model_key",
                    "condition_key",
                    "run_number",
                    "A",
                    "B",
                    "C",
                    "D",
                ],
            )
            writer.writeheader()
            writer.writerows(scored)

        print(f"\n\nScores written: {output_path}")

        # Compute directional accuracy
        _analyze_scores(scored, label)


def _analyze_scores(scored: list[dict], scorer_label: str) -> None:
    """Compute directional accuracy for scored outputs."""
    # Group by model and condition
    by_model_cond: dict[tuple, list] = defaultdict(list)
    for r in scored:
        by_model_cond[(r["model_key"], r["condition_key"])].append(r)

    if not by_model_cond:
        print(f"  No valid scores for {scorer_label}")
        return

    def mean(rs, dim):
        vals = [r[dim] for r in rs if r[dim] > 0]
        return sum(vals) / len(vals) if vals else 0.0

    models = sorted(set(k[0] for k in by_model_cond))
    print(f"\n{'='*70}")
    print(f"Directional accuracy ({scorer_label})")
    print(f"{'='*70}")
    print("Pre-registered: A>B on A; B>A on B,C,D\n")

    total = 0
    confirmed = 0

    for model in models:
        a_scores = by_model_cond.get((model, "A"), [])
        b_scores = by_model_cond.get((model, "B"), [])
        if not a_scores or not b_scores:
            continue

        print(f"  {model}:")
        for dim, (higher, lower) in DIRECTIONAL_PREDICTIONS.items():
            h = mean(a_scores if higher == "A" else b_scores, dim)
            l = mean(b_scores if higher == "A" else a_scores, dim)
            total += 1
            ok = h > l
            status = "✓" if ok else "✗"
            if ok:
                confirmed += 1
            print(f"    {dim}: {higher}={h:.2f} vs {lower}={l:.2f} {status}")
        print()

    if total > 0:
        pct = confirmed / total * 100
        print(f"  Overall: {confirmed}/{total} = {pct:.1f}%")
        print(f"  Baseline (ground truth): 14/16 = 87.5%\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 Scoring Engine")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of outputs to score (for testing)",
    )
    args = parser.parse_args()

    # Check API keys
    for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY", "GOOGLE_API_KEY"]:
        if not os.environ.get(key):
            print(f"{key} not set")
            sys.exit(1)

    asyncio.run(score_with_llms(output_limit=args.limit))


if __name__ == "__main__":
    main()
