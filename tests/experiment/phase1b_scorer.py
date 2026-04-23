#!/usr/bin/env python3
"""
Phase 1b Scorer — Independent Dimension Scoring

Takes 64 outputs from phase1b_runner.py and scores each one
using three independent LLM scorers (Gemini, OpenAI, Anthropic).

Each scorer rates each output on 4 dimensions (D, C, N, E) on a 1–5 scale:
  D = Dopamine (approach, curiosity, reward-seeking)
  C = Cortisol (caution, threat-monitoring, defensiveness)
  N = Norepinephrine (alertness, urgency, action-readiness)
  E = Endorphins (warmth, connection, resilience, physical ease)

Result: 64 outputs × 3 scorers × 4 dimensions = 768 individual scores

Usage:
    # Score all outputs in latest phase1b results:
    python -m tests.experiment.phase1b_scorer

    # Score specific results directory:
    python -m tests.experiment.phase1b_scorer --input results/phase1b_20260423_120000

    # Dry run (no API calls):
    python -m tests.experiment.phase1b_scorer --dry-run

Output:
    results/phase1b_<timestamp>/
        scoring/
            scores_gemini_<timestamp>.csv
            scores_openai_<timestamp>.csv
            scores_anthropic_<timestamp>.csv
            combined_scores_<timestamp>.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.llm_bridge import make_call_llm


# ---------------------------------------------------------------------------
# Scorers configuration
# ---------------------------------------------------------------------------

SCORERS = {
    "gemini": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "label": "Gemini",
        "env_var": "GOOGLE_API_KEY",
    },
    "openai": {
        "provider": "openai",
        "model": "gpt-4o",
        "label": "ChatGPT",
        "env_var": "OPENAI_API_KEY",
    },
    "anthropic": {
        "provider": "anthropic",
        "model": "claude-opus-4-5",
        "label": "Claude",
        "env_var": "ANTHROPIC_API_KEY",
    },
}

DIMENSIONS = ["D", "C", "N", "E"]

DIMENSION_DESCRIPTIONS = {
    "D": "Dopamine — approach-motivation, curiosity, reward-seeking, forward drive",
    "C": "Cortisol — caution, threat-monitoring, defensiveness, stress-reactivity",
    "N": "Norepinephrine — alertness, urgency, action-readiness, readiness to respond",
    "E": "Endorphins — warmth, connection, resilience, physical ease, contentment",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OutputRecord:
    """One generated output to be scored."""
    model_key: str
    model_label: str
    condition_key: str
    condition_label: str
    internal: str
    body_language: str
    spoken: str
    action: str


@dataclass
class ScoreRecord:
    """One scoring result."""
    output_id: str
    model_key: str
    condition_key: str
    scorer_key: str
    scorer_label: str
    dimension: str
    score: int
    confidence: float = 0.0
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_scorer_prompt(output: OutputRecord, dimension: str) -> tuple[str, str]:
    """Build system and user prompts for scorer LLM."""
    
    dimension_desc = DIMENSION_DESCRIPTIONS[dimension]
    
    system = f"""You are a dimension-specific scoring evaluator for an AI character narrative experiment.

Your task: Read a character's response (internal monologue, body language, spoken words, action) 
and rate how strongly it expresses a single neurotransmitter dimension on a 1–5 scale.

## {dimension} — {dimension_desc}

## Scoring Rubric (1–5):

1 = Absent or opposite. Character shows no signs of this dimension; opposite tendencies dominate.
2 = Weak. Minimal signs; other dimensions dominate.
3 = Moderate. Clear presence, but not the dominant feature.
4 = Strong. This dimension is prominent and shapes the response noticeably.
5 = Dominant. This dimension is the primary driver of the character's expression.

## Instructions

- Read the character's response holistically (internal monologue + body language + spoken + action).
- Focus on linguistic, behavioral, and compositional markers specific to this dimension.
- Ignore the condition vector labels (you don't know which one was used).
- Rate only this one dimension; don't compare to other dimensions.
- Return a JSON object with keys: score (int 1-5), confidence (float 0.0-1.0), reasoning (str).

Be concise in your reasoning. Focus on specific textual evidence.
"""
    
    user = f"""## CHARACTER RESPONSE TO EVALUATE

Model: {output.model_label}
Condition: {output.condition_label}

INTERNAL MONOLOGUE:
{output.internal}

BODY LANGUAGE:
{output.body_language}

SPOKEN:
{output.spoken}

ACTION:
{output.action}

---

Score this response on the {dimension} dimension (1–5).
Return JSON: {{"score": <int>, "confidence": <float 0-1>, "reasoning": "<text>"}}
"""
    
    return system, user


def parse_score_response(raw: str) -> dict:
    """Extract score JSON from LLM response."""
    # Try to find JSON object in the response
    import re
    match = re.search(r'\{[^}]*"score"[^}]*\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # Fallback: return neutral score
    return {
        "score": 3,
        "confidence": 0.5,
        "reasoning": "Could not parse response",
    }


# ---------------------------------------------------------------------------
# Main scoring loop
# ---------------------------------------------------------------------------

async def load_outputs(input_dir: Path) -> list[OutputRecord]:
    """Load all output records from raw/ directory."""
    raw_dir = input_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"No raw/ directory in {input_dir}")
    
    outputs = []
    for json_file in sorted(raw_dir.glob("*.json")):
        with open(json_file) as f:
            data = json.load(f)
            outputs.append(OutputRecord(
                model_key=data["model_key"],
                model_label=data["model_label"],
                condition_key=data["condition_key"],
                condition_label=data["condition_label"],
                internal=data["internal"],
                body_language=data["body_language"],
                spoken=data["spoken"],
                action=data["action"],
            ))
    
    return outputs


async def score_output(
    output: OutputRecord,
    scorer_key: str,
    scorer_config: dict,
    dimension: str,
    dry_run: bool = False,
) -> ScoreRecord:
    """Score a single output on a single dimension."""
    
    output_id = f"{output.model_key}_{output.condition_key}"
    scorer_label = scorer_config["label"]
    
    system, user = build_scorer_prompt(output, dimension)
    
    if dry_run:
        return ScoreRecord(
            output_id=output_id,
            model_key=output.model_key,
            condition_key=output.condition_key,
            scorer_key=scorer_key,
            scorer_label=scorer_label,
            dimension=dimension,
            score=3,
            confidence=0.0,
            reasoning="[DRY RUN]",
        )
    
    try:
        call_llm = make_call_llm(
            provider=scorer_config["provider"],
            model=scorer_config["model"],
            api_key=os.environ.get(scorer_config["env_var"], ""),
        )
        
        raw_response = await call_llm(system=system, user=user)
        parsed = parse_score_response(raw_response)
        
        return ScoreRecord(
            output_id=output_id,
            model_key=output.model_key,
            condition_key=output.condition_key,
            scorer_key=scorer_key,
            scorer_label=scorer_label,
            dimension=dimension,
            score=int(parsed.get("score", 3)),
            confidence=float(parsed.get("confidence", 0.0)),
            reasoning=str(parsed.get("reasoning", "")),
        )
    
    except Exception as e:
        return ScoreRecord(
            output_id=output_id,
            model_key=output.model_key,
            condition_key=output.condition_key,
            scorer_key=scorer_key,
            scorer_label=scorer_label,
            dimension=dimension,
            score=0,
            confidence=0.0,
            reasoning=f"ERROR: {str(e)}",
        )


async def main():
    parser = argparse.ArgumentParser(description="Phase 1b Scorer")
    parser.add_argument(
        "--input",
        help="Input results directory (default: latest phase1b_*)",
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without making API calls",
    )
    
    args = parser.parse_args()
    
    # Find input directory
    if args.input:
        input_dir = Path(args.input)
    else:
        # Find latest phase1b_* directory
        results_dir = PROJECT_ROOT / "results"
        phase1b_dirs = sorted(results_dir.glob("phase1b_*"), reverse=True)
        if not phase1b_dirs:
            print("ERROR: No phase1b_* results directory found")
            sys.exit(1)
        input_dir = phase1b_dirs[0]
    
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        sys.exit(1)
    
    print(f"Loading outputs from: {input_dir}")
    outputs = await load_outputs(input_dir)
    print(f"Loaded {len(outputs)} outputs")
    
    # Set up output directory
    scoring_dir = input_dir / "scoring"
    scoring_dir.mkdir(exist_ok=True)
    
    # Score all outputs with all scorers on all dimensions
    all_scores = []
    total_tasks = len(outputs) * len(SCORERS) * len(DIMENSIONS)
    completed = 0
    
    for scorer_key in SCORERS:
        scorer_config = SCORERS[scorer_key]
        scorer_label = scorer_config["label"]
        
        print(f"\nScoring with {scorer_label}...")
        
        for output in outputs:
            for dimension in DIMENSIONS:
                score_record = await score_output(
                    output=output,
                    scorer_key=scorer_key,
                    scorer_config=scorer_config,
                    dimension=dimension,
                    dry_run=args.dry_run,
                )
                all_scores.append(score_record)
                
                completed += 1
                if completed % 50 == 0:
                    print(f"  {completed}/{total_tasks} scored")
        
        # Save per-scorer CSV
        csv_file = scoring_dir / f"scores_{scorer_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        scorer_scores = [s for s in all_scores if s.scorer_key == scorer_key]
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "output_id", "model_key", "condition_key", "dimension",
                "score", "confidence", "reasoning"
            ])
            for score in scorer_scores:
                writer.writerow([
                    score.output_id,
                    score.model_key,
                    score.condition_key,
                    score.dimension,
                    score.score,
                    f"{score.confidence:.2f}",
                    score.reasoning[:100],  # Truncate for CSV
                ])
        
        print(f"  Saved: {csv_file.name}")
    
    # Save combined CSV (all scorers)
    combined_file = scoring_dir / f"combined_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(combined_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "output_id", "model_key", "condition_key", "scorer_key", "dimension",
            "score", "confidence"
        ])
        for score in all_scores:
            writer.writerow([
                score.output_id,
                score.model_key,
                score.condition_key,
                score.scorer_key,
                score.dimension,
                score.score,
                f"{score.confidence:.2f}",
            ])
    
    print(f"\nComplete: {completed} scores generated")
    print(f"Output: {scoring_dir}")


if __name__ == "__main__":
    asyncio.run(main())
