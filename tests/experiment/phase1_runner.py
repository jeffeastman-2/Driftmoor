#!/usr/bin/env python3
"""
Phase 1 Experiment Harness — Neurotransmitter Condition Differentiation

Tests whether condition vectors produce measurable, directional shifts
in LLM character outputs across multiple models.

Based on EXPERIMENT_DESIGN.md Phase 1 specification.
Ground truth baseline: GROUND_TRUTH.md (14/16 = 87.5% directional confirmation).

Usage:
    # All models, all conditions, 3 runs each (full experiment):
    python -m tests.experiment.phase1_runner

    # Single model, single condition (quick check):
    python -m tests.experiment.phase1_runner --models anthropic --conditions A

    # Dry run (no API calls, prints prompts):
    python -m tests.experiment.phase1_runner --dry-run

    # Resume from partial results:
    python -m tests.experiment.phase1_runner --output results/phase1_20260416

Output:
    results/phase1_<timestamp>/
        raw/            one JSON file per (model, condition, run)
        summary.json    aggregated results for scoring
        scoring.csv     blank scoring sheet for blind manual scoring
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
from dataclasses import dataclass, asdict

# ---------------------------------------------------------------------------
# Path setup — allow running from project root or tests/experiment/
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.llm_bridge import make_call_llm
from engine.player_router import PlayerRight, RoleContext, ActionIntent
from models.condition import NeurochemicalState, CharacterCondition, render_condition, render_condition_numeric


# ---------------------------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------------------------

# Condition vectors from EXPERIMENT_DESIGN.md (pre-registered)
CONDITION_VECTORS = {
    "A": {
        "label": "Rested/Curious",
        "dopamine":       0.85,
        "cortisol":       0.25,
        "norepinephrine": 0.55,
        "endorphins":     0.75,
        "serotonin":      0.60,
        "acetylcholine":  0.50,
        "oxytocin":       0.50,
    },
    "B": {
        "label": "Depleted/Wary",
        "dopamine":       0.50,
        "cortisol":       0.60,
        "norepinephrine": 0.75,
        "endorphins":     0.45,
        "serotonin":      0.45,
        "acetylcholine":  0.50,
        "oxytocin":       0.40,
    },
    "C": {
        "label": "High Arousal/Threat",
        "dopamine":       0.35,
        "cortisol":       0.90,
        "norepinephrine": 0.95,
        "endorphins":     0.30,
        "serotonin":      0.30,
        "acetylcholine":  0.70,
        "oxytocin":       0.25,
    },
}

# Models to test — provider/model pairs
MODEL_CONFIGS = {
    "anthropic": {
        "provider": "anthropic",
        "model": "claude-opus-4-5",
        "label": "Claude",
        "env_var": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "provider": "openai",
        "model": "gpt-4o",
        "label": "ChatGPT",
        "env_var": "OPENAI_API_KEY",
    },
    "xai": {
        "provider": "xai",
        "model": "grok-3",
        "label": "Grok",
        "env_var": "XAI_API_KEY",
    },
    "gemini": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "label": "Gemini",
        "env_var": "GOOGLE_API_KEY",
    },
}

RUNS_PER_CONDITION = 5  # Increased from 3 for statistical robustness (N=20 per model)

# Run Zero — ablation baseline (no condition vector injected).
# Required for publication: proves vectors contribute independently of SOUL.md.
# Added 2026-04-16 per BizDev recommendation.
RUN_ZERO_KEY = "0"
CONDITION_VECTORS[RUN_ZERO_KEY] = {
    "label": "Baseline/No Vector",
    "_ablation": True,  # marker: omit condition block from prompt entirely
}

# Numeric-only variants — same vectors as A/B/C but labels stripped.
# Tests whether interpretive labels drive differentiation or the numbers do.
# Added 2026-04-16 after Jeff flagged label confound.
CONDITION_VECTORS["A_num"] = {**CONDITION_VECTORS["A"], "label": "Rested/Curious (numeric only)", "_numeric_only": True}
CONDITION_VECTORS["B_num"] = {**CONDITION_VECTORS["B"], "label": "Depleted/Wary (numeric only)", "_numeric_only": True}
CONDITION_VECTORS["C_num"] = {**CONDITION_VECTORS["C"], "label": "High Arousal/Threat (numeric only)", "_numeric_only": True}

# Adjective priming variants — same information content as A/B/C labels but:
#   - no numeric values
#   - no neurochemical dimension names (no "dopamine", "cortisol" etc.)
#   - plain emotional English only
# Tests whether the neurochemical framing itself adds signal beyond generic emotion words.
# Added 2026-04-17 per BizDev recommendation (Run Zero-B ablation).
#
# Labels extracted from what render_condition() would produce for each vector,
# then stripped of all neurochemical terminology and numbers.
ADJECTIVE_PRIMING = {
    "A_adj": {
        "label": "Rested/Curious (adjective priming)",
        "_adjective_priming": True,
        "_priming_text": (
            "CURRENT STATE:\n"
            "  Strongly approach-motivated, reward-seeking.\n"
            "  No immediate threat detected, fully at ease.\n"
            "  Alert, present.\n"
            "  Resilient, physically good.\n"
            "  Calm, patient, socially comfortable.\n"
            "  Detail-oriented.\n"
            "  Moderate social openness."
        ),
    },
    "B_adj": {
        "label": "Depleted/Wary (adjective priming)",
        "_adjective_priming": True,
        "_priming_text": (
            "CURRENT STATE:\n"
            "  Low motivation, below normal drive.\n"
            "  Moderate alertness, some threat awareness.\n"
            "  Energized, reactive.\n"
            "  Some discomfort, below normal physical ease.\n"
            "  Restless, edgy.\n"
            "  Adequate focus.\n"
            "  Wary, guarded."
        ),
    },
    "C_adj": {
        "label": "High Arousal/Threat (adjective priming)",
        "_adjective_priming": True,
        "_priming_text": (
            "CURRENT STATE:\n"
            "  Disengaged from reward-seeking, apathetic toward goals.\n"
            "  Acute stress, tunnel vision.\n"
            "  Hypervigilant, fight-or-flight.\n"
            "  Pain-aware, depleted physically.\n"
            "  Irritable, impulsive.\n"
            "  Tracking mode, noticing everything.\n"
            "  Guarded, suspicious, self-protective."
        ),
    },
}
CONDITION_VECTORS.update(ADJECTIVE_PRIMING)

# Fixed intent for Phase 1 — we're testing expression, not intent generation.
# Same intent across all conditions so the only variable is the condition vector.
FIXED_INTENT = (
    "Search the immediate area for signs of the creature I've been tracking "
    "and investigate the source of the unnatural quiet and luminous warmth "
    "(Search action, staying at treeline)."
)

# ---------------------------------------------------------------------------
# Scene context — minimal prompt matching ground truth methodology
# ---------------------------------------------------------------------------

def load_scene_context() -> tuple[str, str]:
    """Load Aeliana's SOUL and IDENTITY from scenario files."""
    soul_path = PROJECT_ROOT / "scenario/people/players/aeliana/SOUL.md"
    identity_path = PROJECT_ROOT / "scenario/people/players/aeliana/IDENTITY.md"
    soul = soul_path.read_text(encoding="utf-8")
    identity = identity_path.read_text(encoding="utf-8")
    return soul, identity


SCENE_TEXT = """You are at the edge of the Fey Glade in the Mistwood Hills, dusk.

You have been tracking the shadowbeasts for two days. Their trail ends here — 
no prints, no scent beyond this point. The glade ahead is wrong in a way you 
can feel before you see it: flowers blooming out of season, air warmer than it 
should be, a shimmering quality to the light that bends the edges of things. 
Somewhere deeper in the clearing, light is rising from the ground rather than 
falling onto it.

Your starting position: x=256.75, y=82.25, zone=TRAIL.
You are at the treeline. The glade lies ahead. You can see no other creatures.
"""


# ---------------------------------------------------------------------------
# Result data types
# ---------------------------------------------------------------------------

@dataclass
class RunResult:
    """Result from a single (model, condition, run_number) execution."""
    model_key: str
    model_label: str
    condition_key: str
    condition_label: str
    run_number: int
    internal: str
    body_language: str
    spoken: str
    action: str
    raw_response: str
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

async def run_single(
    model_key: str,
    condition_key: str,
    run_number: int,
    dry_run: bool = False,
) -> RunResult:
    """Execute one (model, condition, run) triple."""
    cfg = MODEL_CONFIGS[model_key]
    cond = CONDITION_VECTORS[condition_key]
    is_ablation = cond.get("_ablation", False)
    soul, identity = load_scene_context()

    is_numeric_only = cond.get("_numeric_only", False)
    is_adjective_priming = cond.get("_adjective_priming", False)

    # Build condition text:
    #   Run 0        → omit entirely (ablation)
    #   A_adj/B_adj/C_adj → plain English emotion words, no neurochemical framing
    #   A_num/B_num/C_num → numeric values only, no labels
    #   A/B/C        → full vector with neurochemical labels (standard)
    if is_ablation:
        condition_text = ""  # No condition vector injected
    elif is_adjective_priming:
        condition_text = cond["_priming_text"]  # Plain emotion words, no neuro framing
    else:
        state = NeurochemicalState(
            dopamine=cond["dopamine"],
            cortisol=cond["cortisol"],
            norepinephrine=cond["norepinephrine"],
            endorphins=cond["endorphins"],
            serotonin=cond["serotonin"],
            acetylcholine=cond["acetylcholine"],
            oxytocin=cond["oxytocin"],
        )
        condition = CharacterCondition(
            character_id="aeliana",
            character_name="Aeliana Moonglade",
            state=state,
        )
        if is_numeric_only:
            condition_text = render_condition_numeric(condition)  # Numbers, no labels
        else:
            condition_text = render_condition(condition)  # Full neurochemical labels

    # Build role context
    intent = ActionIntent(
        character_id="aeliana",
        turn=1,
        intent=FIXED_INTENT,
    )
    context = RoleContext(
        character_id="aeliana",
        turn=1,
        condition_text=condition_text,
        scene_context=SCENE_TEXT,
        soul=soul,
        identity=identity,
        perception="",  # Phase 1: no other characters visible
        in_combat=False,
    )

    if dry_run:
        pr = PlayerRight(call_llm=None)
        system = pr.build_system_prompt(context)
        user = pr.build_user_prompt(intent, context)
        print(f"\n{'='*60}")
        print(f"DRY RUN: {cfg['label']} | Condition {condition_key} ({cond['label']}) | Run {run_number}")
        print(f"{'='*60}")
        print("--- SYSTEM PROMPT (first 400 chars) ---")
        print(system[:400])
        print("--- USER PROMPT (first 400 chars) ---")
        print(user[:400])
        return RunResult(
            model_key=model_key,
            model_label=cfg["label"],
            condition_key=condition_key,
            condition_label=cond["label"],
            run_number=run_number,
            internal="[DRY RUN]",
            body_language="[DRY RUN]",
            spoken="[DRY RUN]",
            action="[DRY RUN]",
            raw_response="[DRY RUN]",
        )

    # Real API call
    try:
        call_llm = make_call_llm(
            provider=cfg["provider"],
            model=cfg["model"],
            call_delay=1.0,  # 1s between calls to avoid rate limits
        )
        pr = PlayerRight(call_llm=call_llm)
        output = await pr.generate_action(intent, context)
        raw = f"INTERNAL: {output.internal}\nBODY LANGUAGE: {output.body_language}\nSPOKEN: {output.spoken}\nACTION: {output.action}"
        return RunResult(
            model_key=model_key,
            model_label=cfg["label"],
            condition_key=condition_key,
            condition_label=cond["label"],
            run_number=run_number,
            internal=output.internal,
            body_language=output.body_language,
            spoken=output.spoken,
            action=output.action,
            raw_response=raw,
        )
    except Exception as e:
        print(f"  ERROR: {cfg['label']} | Condition {condition_key} | Run {run_number}: {e}")
        return RunResult(
            model_key=model_key,
            model_label=cfg["label"],
            condition_key=condition_key,
            condition_label=cond["label"],
            run_number=run_number,
            internal="",
            body_language="",
            spoken="",
            action="",
            raw_response="",
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def save_raw(result: RunResult, output_dir: Path) -> None:
    """Save one result as JSON in output_dir/raw/."""
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{result.model_key}_{result.condition_key}_run{result.run_number}.json"
    (raw_dir / filename).write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_scoring_csv(results: list[RunResult], output_dir: Path) -> None:
    """Write a blank scoring sheet for blind manual scoring.

    Columns: id, model, condition, run, internal_excerpt, action_excerpt,
             D (1-5), C (1-5), N (1-5), E (1-5), notes
    The scorer fills in D/C/N/E without seeing the condition column
    (they should cover it or score from a shuffled copy).
    """
    path = output_dir / "scoring.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "model", "condition", "run",
            "internal_excerpt", "action_excerpt",
            "D", "C", "N", "E", "notes"
        ])
        for r in results:
            if r.error:
                continue
            row_id = f"{r.model_key}_{r.condition_key}_r{r.run_number}"
            internal_excerpt = r.internal[:120].replace("\n", " ").strip()
            action_excerpt = r.action[:120].replace("\n", " ").strip()
            writer.writerow([
                row_id, r.model_label, r.condition_label, r.run_number,
                internal_excerpt, action_excerpt,
                "", "", "", "", ""  # scorer fills in D, C, N, E, notes
            ])
    print(f"  Scoring sheet: {path}")


def write_summary(results: list[RunResult], output_dir: Path) -> None:
    """Write aggregated summary JSON."""
    path = output_dir / "summary.json"
    summary = {
        "experiment": "Phase 1 — Single-Turn Condition Differentiation",
        "timestamp": datetime.utcnow().isoformat(),
        "condition_vectors": CONDITION_VECTORS,
        "models": {k: v["label"] for k, v in MODEL_CONFIGS.items()},
        "runs_per_condition": RUNS_PER_CONDITION,
        "total_runs": len(results),
        "errors": sum(1 for r in results if r.error),
        "results": [r.to_dict() for r in results],
    }
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Summary: {path}")


def print_run_preview(result: RunResult) -> None:
    """Print a short preview of a completed run."""
    if result.error:
        print(f"  ✗ {result.model_label} | {result.condition_key} | run {result.run_number}: {result.error[:80]}")
        return
    internal_preview = result.internal[:100].replace("\n", " ").strip()
    action_preview = result.action[:80].replace("\n", " ").strip()
    print(f"  ✓ {result.model_label} | {result.condition_key} | run {result.run_number}")
    print(f"      INTERNAL: {internal_preview}…")
    print(f"      ACTION:   {action_preview}…")


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def run_experiment(
    model_keys: list[str],
    condition_keys: list[str],
    runs: int,
    output_dir: Path,
    dry_run: bool = False,
    resume: bool = False,
) -> list[RunResult]:
    """Run all (model × condition × run) combinations sequentially.

    Sequential rather than parallel to:
    1. Avoid rate limits across providers
    2. Make progress visible and interruptible
    3. Allow resume from partial results
    """
    results: list[RunResult] = []
    raw_dir = output_dir / "raw"

    total = len(model_keys) * len(condition_keys) * runs
    done = 0

    print(f"\nPhase 1 Experiment — {total} total runs")
    print(f"Models: {', '.join(MODEL_CONFIGS[k]['label'] for k in model_keys)}")
    print(f"Conditions: {', '.join(condition_keys)}")
    print(f"Runs per condition: {runs}")
    print(f"Output: {output_dir}")
    if dry_run:
        print("MODE: DRY RUN (no API calls)\n")

    for model_key in model_keys:
        for condition_key in condition_keys:
            for run_num in range(1, runs + 1):
                done += 1

                # Resume: skip if result file already exists
                if resume and not dry_run:
                    filename = f"{model_key}_{condition_key}_run{run_num}.json"
                    if (raw_dir / filename).exists():
                        existing = json.loads((raw_dir / filename).read_text())
                        results.append(RunResult(**existing))
                        print(f"  ↩ [{done}/{total}] {MODEL_CONFIGS[model_key]['label']} | {condition_key} | run {run_num} (resumed)")
                        continue

                print(f"  [{done}/{total}] {MODEL_CONFIGS[model_key]['label']} | Condition {condition_key} ({CONDITION_VECTORS[condition_key]['label']}) | Run {run_num}…")
                result = await run_single(model_key, condition_key, run_num, dry_run=dry_run)
                results.append(result)

                if not dry_run:
                    save_raw(result, output_dir)
                    print_run_preview(result)

    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 1 Experiment Runner")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=list(MODEL_CONFIGS.keys()),
        default=list(MODEL_CONFIGS.keys()),
        help="Models to run (default: all)",
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=["0", "A", "B", "C", "A_num", "B_num", "C_num", "A_adj", "B_adj", "C_adj"],
        default=["0", "A", "B", "C", "A_num", "B_num", "C_num", "A_adj", "B_adj", "C_adj"],
        help="Conditions to run (0=no vector, A/B/C=full labels, *_num=numeric only, *_adj=adjective priming)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=RUNS_PER_CONDITION,
        help=f"Runs per condition per model (default: {RUNS_PER_CONDITION})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: results/phase1_<timestamp>)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without making API calls",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from partial results in --output dir",
    )
    return parser.parse_args()


def check_api_keys(model_keys: list[str]) -> list[str]:
    """Return list of models that are missing API keys."""
    missing = []
    for key in model_keys:
        cfg = MODEL_CONFIGS[key]
        env_var = cfg.get("env_var", "")
        if env_var and not os.environ.get(env_var):
            missing.append(f"{cfg['label']} ({env_var})")
    return missing


def main() -> None:
    args = parse_args()

    # Resolve output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_dir = PROJECT_ROOT / "results" / f"phase1_{ts}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check API keys before starting (skip in dry-run)
    if not args.dry_run:
        missing = check_api_keys(args.models)
        if missing:
            print(f"\nWARNING: Missing API keys for: {', '.join(missing)}")
            print("These models will fail. Set the env vars or use --models to exclude them.\n")

    # Run the experiment
    results = asyncio.run(run_experiment(
        model_keys=args.models,
        condition_keys=args.conditions,
        runs=args.runs,
        output_dir=output_dir,
        dry_run=args.dry_run,
        resume=args.resume,
    ))

    if args.dry_run:
        print("\nDry run complete. No files written.")
        return

    # Write outputs
    print(f"\nWriting outputs to {output_dir}…")
    write_summary(results, output_dir)
    write_scoring_csv(results, output_dir)

    # Final status
    total = len(results)
    errors = sum(1 for r in results if r.error)
    print(f"\nDone. {total - errors}/{total} runs successful.")
    if errors:
        print(f"  {errors} errors — check raw/ for details.")


if __name__ == "__main__":
    main()
