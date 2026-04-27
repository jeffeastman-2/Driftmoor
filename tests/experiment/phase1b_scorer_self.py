#!/usr/bin/env python3
"""
Phase 1b Scorer (SELFSAME variant) — All-vs-all dimension scoring.

Mirror of phase1b_scorer.py with one change: the leave-one-out exclusion
is REMOVED. Each scorer model rates every output, including the ones it
generated itself. This is for comparison vs. the cross-model (leave-one-out)
results, since the original ground-truth methodology used the same LLM to
generate and score.

Outputs are written to a separate scoring_self/ subdirectory so cross-model
results are not overwritten.

Usage:
    python -m tests.experiment.phase1b_scorer_self
    python -m tests.experiment.phase1b_scorer_self --input results/phase1b_<ts>
    python -m tests.experiment.phase1b_scorer_self --dry-run

Dimensions: D, C, N, E (1-5 scale), same rubric as phase1b_scorer.
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Reuse all the building blocks from the cross-model scorer.
from tests.experiment.phase1b_scorer import (  # noqa: E402
    SCORERS,
    DIMENSIONS,
    OutputRecord,
    ScoreRecord,
    load_outputs,
    score_output_with_retry,
    load_api_keys_from_file,
)


async def main():
    load_api_keys_from_file()

    parser = argparse.ArgumentParser(
        description="Phase 1b Scorer (selfsame: each model scores all outputs incl. its own)"
    )
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

    if args.input:
        input_dir = Path(args.input)
    else:
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

    # Separate output dir to preserve the cross-model results.
    scoring_dir = input_dir / "scoring_self"
    scoring_dir.mkdir(exist_ok=True)

    all_scores: list[ScoreRecord] = []
    # Every scorer scores every output × every dimension (no leave-one-out).
    total_tasks = len(SCORERS) * len(outputs) * len(DIMENSIONS)
    completed = 0

    print(
        f"\nSelfsame mode: {len(SCORERS)} scorers × {len(outputs)} outputs × "
        f"{len(DIMENSIONS)} dimensions = {total_tasks} scores"
    )

    for scorer_key in SCORERS:
        scorer_config = SCORERS[scorer_key]
        scorer_label = scorer_config["label"]

        print(f"\nScoring with {scorer_label} (incl. its own outputs)...")

        for output in outputs:
            for dimension in DIMENSIONS:
                score_record = await score_output_with_retry(
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

        # Per-scorer CSV
        csv_file = scoring_dir / f"scores_{scorer_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        scorer_scores = [s for s in all_scores if s.scorer_key == scorer_key]

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "output_id", "model_key", "condition_key", "dimension",
                "score", "confidence", "reasoning",
                "is_self",
            ])
            for score in scorer_scores:
                writer.writerow([
                    score.output_id,
                    score.model_key,
                    score.condition_key,
                    score.dimension,
                    score.score,
                    f"{score.confidence:.2f}",
                    score.reasoning[:100],
                    "1" if score.model_key == score.scorer_key else "0",
                ])

        print(f"  Saved: {csv_file.name}")

    combined_file = scoring_dir / f"combined_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(combined_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "output_id", "model_key", "condition_key", "scorer_key", "dimension",
            "score", "confidence", "is_self",
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
                "1" if score.model_key == score.scorer_key else "0",
            ])

    print(f"\nComplete: {completed} scores generated")
    print(f"Output: {scoring_dir}")


if __name__ == "__main__":
    asyncio.run(main())
