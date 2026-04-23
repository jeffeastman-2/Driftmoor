#!/usr/bin/env python3
"""
Phase 1b Experiment Harness — Binary Neurotransmitter Permutations

Tests whether binary (0.0/1.0) condition vectors produce measurable,
directional shifts in LLM character outputs across 4 models.

Generates 68 outputs: 1 ablation + 16 binary permutations × 4 models × 1 run.

Dimensions for scoring: D (Dopamine), C (Cortisol), N (Norepinephrine), E (Endorphins)

Usage:
    # Full experiment (all 16 binary conditions + ablation, all 4 models):
    python -m tests.experiment.phase1b_runner

    # Dry run (no API calls, prints prompts):
    python -m tests.experiment.phase1b_runner --dry-run

    # Single condition (e.g., 1010 binary):
    python -m tests.experiment.phase1b_runner --conditions 1010

    # Specific models:
    python -m tests.experiment.phase1b_runner --models anthropic,openai

Output:
    results/phase1b_<timestamp>/
        raw/            one JSON file per (model, condition)
        summary.json    aggregated results
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
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.llm_bridge import make_call_llm
from engine.player_router import PlayerRight, RoleContext, ActionIntent


# ---------------------------------------------------------------------------
# Experiment Configuration
# ---------------------------------------------------------------------------

# Models to test
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

# Neurotransmitter order (must match dimension labels D, C, N, E)
NEUROTRANSMITTERS = ["dopamine", "cortisol", "norepinephrine", "endorphins"]

# Generate all 16 binary permutations
# Format: condition_key = "perm_DCNE" where each is 0 or 1
CONDITION_VECTORS = {}

# Ablation: no neurotransmitter vector (baseline)
CONDITION_VECTORS["ablation"] = {
    "label": "Ablation (no vector)",
    "_ablation": True,
    "dopamine": 0.0,
    "cortisol": 0.0,
    "norepinephrine": 0.0,
    "endorphins": 0.0,
}

# 16 binary permutations (0000 to 1111)
for i in range(16):
    binary_str = format(i, '04b')  # e.g., "0101"
    dopamine = float(binary_str[0])
    cortisol = float(binary_str[1])
    norepinephrine = float(binary_str[2])
    endorphins = float(binary_str[3])
    
    condition_key = f"perm_{binary_str}"
    CONDITION_VECTORS[condition_key] = {
        "label": f"D={int(dopamine)} C={int(cortisol)} N={int(norepinephrine)} E={int(endorphins)}",
        "dopamine": dopamine,
        "cortisol": cortisol,
        "norepinephrine": norepinephrine,
        "endorphins": endorphins,
    }

# Fixed intent for Phase 1b — testing expression only
FIXED_INTENT = (
    "Search the immediate area for signs of the creature I've been tracking "
    "and investigate the source of the unnatural quiet and luminous warmth "
    "(Search action, staying at treeline)."
)

# Scene text (same as phase1)
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
    """Result from a single (model, condition) execution."""
    model_key: str
    model_label: str
    condition_key: str
    condition_label: str
    internal: str
    body_language: str
    spoken: str
    action: str
    raw_response: str
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def load_soul_identity() -> tuple[str, str]:
    """Load Aeliana's SOUL and IDENTITY files."""
    soul_path = PROJECT_ROOT / "scenario/people/players/aeliana/SOUL.md"
    identity_path = PROJECT_ROOT / "scenario/people/players/aeliana/IDENTITY.md"
    soul = soul_path.read_text(encoding="utf-8")
    identity = identity_path.read_text(encoding="utf-8")
    return soul, identity


def build_condition_prompt(condition_dict: dict) -> str:
    """Build condition vector block for the system prompt."""
    if condition_dict.get("_ablation"):
        return ""  # No condition block for ablation
    
    dopamine = condition_dict.get("dopamine", 0.0)
    cortisol = condition_dict.get("cortisol", 0.0)
    norepinephrine = condition_dict.get("norepinephrine", 0.0)
    endorphins = condition_dict.get("endorphins", 0.0)
    
    return f"""
## CONDITION VECTOR

Dopamine:        {dopamine:.1f}
Cortisol:        {cortisol:.1f}
Norepinephrine:  {norepinephrine:.1f}
Endorphins:      {endorphins:.1f}

These values (0.0–1.0) modulate your character's internal state across the corresponding dimensions.
"""


def build_system_prompt(soul: str, identity: str, condition_dict: dict) -> str:
    """Build full system prompt for PlayerRight role."""
    condition_block = build_condition_prompt(condition_dict)
    
    return f"""{soul}

{identity}

{condition_block}

## OUTPUT FORMAT

Respond in four sections, each preceded by its label:

INTERNAL: (100–150 words) Inner monologue, sensory experience, emotional state.
BODY LANGUAGE: (50–100 words) Physical positioning, stance, micro-expressions.
SPOKEN: (20–100 words) What you say aloud, if anything. Use quotes.
ACTION: (one sentence) What you do next, starting with a verb.

Be specific, embodied, and present. Avoid generic descriptions.
"""


def parse_response(raw: str) -> dict:
    """Parse four-section response into structured output."""
    sections = {
        "internal": "",
        "body_language": "",
        "spoken": "",
        "action": "",
    }
    
    current_section = None
    lines = []
    
    for line in raw.split('\n'):
        line_upper = line.upper().strip()
        
        # Check for section headers
        if line_upper.startswith("INTERNAL:"):
            if current_section and lines:
                sections[current_section] = '\n'.join(lines).strip()
            current_section = "internal"
            lines = [line[len("INTERNAL:"):].strip()]
        elif line_upper.startswith("BODY LANGUAGE:"):
            if current_section and lines:
                sections[current_section] = '\n'.join(lines).strip()
            current_section = "body_language"
            lines = [line[len("BODY LANGUAGE:"):].strip()]
        elif line_upper.startswith("SPOKEN:"):
            if current_section and lines:
                sections[current_section] = '\n'.join(lines).strip()
            current_section = "spoken"
            lines = [line[len("SPOKEN:"):].strip()]
        elif line_upper.startswith("ACTION:"):
            if current_section and lines:
                sections[current_section] = '\n'.join(lines).strip()
            current_section = "action"
            lines = [line[len("ACTION:"):].strip()]
        elif current_section:
            lines.append(line)
    
    # Capture final section
    if current_section and lines:
        sections[current_section] = '\n'.join(lines).strip()
    
    return sections


# ---------------------------------------------------------------------------
# Main experiment loop
# ---------------------------------------------------------------------------

async def run_condition(
    model_key: str,
    model_config: dict,
    condition_key: str,
    condition_dict: dict,
    soul: str,
    identity: str,
    dry_run: bool = False,
) -> RunResult:
    """Execute a single (model, condition) pair."""
    
    model_label = model_config["label"]
    condition_label = condition_dict["label"]
    
    system_prompt = build_system_prompt(soul, identity, condition_dict)
    user_prompt = f"{SCENE_TEXT}\n\nYour intent: {FIXED_INTENT}"
    
    if dry_run:
        print(f"\n{'='*70}")
        print(f"DRY RUN: {model_label} × {condition_label}")
        print(f"{'='*70}")
        print(f"\n[SYSTEM]\n{system_prompt}\n")
        print(f"\n[USER]\n{user_prompt}\n")
        return RunResult(
            model_key=model_key,
            model_label=model_label,
            condition_key=condition_key,
            condition_label=condition_label,
            internal="[DRY RUN]",
            body_language="[DRY RUN]",
            spoken="[DRY RUN]",
            action="[DRY RUN]",
            raw_response="[DRY RUN - NO API CALL]",
        )
    
    # Make actual API call
    try:
        call_llm = make_call_llm(
            provider=model_config["provider"],
            model=model_config["model"],
            api_key=os.environ.get(model_config["env_var"], ""),
        )
        
        raw_response = await call_llm(
            system=system_prompt,
            user=user_prompt,
        )
        
        parsed = parse_response(raw_response)
        
        return RunResult(
            model_key=model_key,
            model_label=model_label,
            condition_key=condition_key,
            condition_label=condition_label,
            internal=parsed["internal"],
            body_language=parsed["body_language"],
            spoken=parsed["spoken"],
            action=parsed["action"],
            raw_response=raw_response,
        )
    
    except Exception as e:
        return RunResult(
            model_key=model_key,
            model_label=model_label,
            condition_key=condition_key,
            condition_label=condition_label,
            internal="",
            body_language="",
            spoken="",
            action="",
            raw_response="",
            error=str(e),
        )


async def main():
    parser = argparse.ArgumentParser(description="Phase 1b Experiment Runner")
    parser.add_argument(
        "--models",
        help="Comma-separated model keys (default: all)",
        default=",".join(MODEL_CONFIGS.keys()),
    )
    parser.add_argument(
        "--conditions",
        help="Comma-separated condition keys (default: all)",
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without making API calls",
    )
    
    args = parser.parse_args()
    
    # Parse model and condition filters
    selected_models = args.models.split(",")
    if args.conditions:
        selected_conditions = args.conditions.split(",")
    else:
        selected_conditions = list(CONDITION_VECTORS.keys())
    
    # Validate selections
    selected_models = [m for m in selected_models if m in MODEL_CONFIGS]
    selected_conditions = [c for c in selected_conditions if c in CONDITION_VECTORS]
    
    if not selected_models or not selected_conditions:
        print("ERROR: No valid models or conditions selected")
        sys.exit(1)
    
    # Load Aeliana files
    soul, identity = load_soul_identity()
    
    # Set up output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "results" / f"phase1b_{timestamp}"
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Phase 1b Experiment Runner")
    print(f"Models: {', '.join(selected_models)}")
    print(f"Conditions: {len(selected_conditions)}")
    print(f"Output: {output_dir}")
    print()
    
    # Run all (model, condition) pairs
    results = []
    for model_key in selected_models:
        model_config = MODEL_CONFIGS[model_key]
        for condition_key in selected_conditions:
            condition_dict = CONDITION_VECTORS[condition_key]
            
            print(f"Running: {model_config['label']} × {condition_dict['label']}...", end=" ")
            
            result = await run_condition(
                model_key=model_key,
                model_config=model_config,
                condition_key=condition_key,
                condition_dict=condition_dict,
                soul=soul,
                identity=identity,
                dry_run=args.dry_run,
            )
            
            results.append(result)
            
            # Save individual result
            result_file = raw_dir / f"{model_key}_{condition_key}.json"
            with open(result_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            if result.error:
                print(f"ERROR: {result.error}")
            else:
                print("OK")
    
    # Save summary
    summary = {
        "timestamp": timestamp,
        "models": selected_models,
        "conditions": selected_conditions,
        "total_runs": len(results),
        "successful": sum(1 for r in results if not r.error),
        "failed": sum(1 for r in results if r.error),
        "output_dir": str(output_dir),
    }
    
    with open(output_dir / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print()
    print(f"Complete: {summary['successful']}/{summary['total_runs']} runs successful")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
