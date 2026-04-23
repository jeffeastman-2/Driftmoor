#!/usr/bin/env python3
"""
Phase 1 Scorer — Automated feature extraction + manual scoring scaffold.

Two modes:
  1. extract  — runs automated feature extraction on raw results,
                produces a consolidated dataset with proxy scores
  2. analyze  — reads a scored CSV (manual scores filled in) and
                computes directional accuracy, model comparison, label vs numeric

Usage:
    # Extract features from all result dirs and produce scoring CSV:
    python -m tests.experiment.scorer extract

    # Extract from specific dirs:
    python -m tests.experiment.scorer extract --dirs results/phase1_20260416_231536 results/phase1_gemini_rerun results/phase1_numeric_20260416

    # Analyze after manual scoring:
    python -m tests.experiment.scorer analyze --scored results/scoring_master.csv

Design notes:
    Automated scores are PROXY FEATURES, not ground truth.
    They flag outputs for manual attention and enable hypothesis generation.
    Statistical claims must use manual blind scores, not automated scores.
    INTERNAL and ACTION are scored separately to detect layer-specific effects
    (e.g., Grok may differentiate on ACTION but not INTERNAL).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Automated feature extractors
# Proxy for D/C/N/E dimensions — imperfect but useful for hypothesis generation
# ---------------------------------------------------------------------------

# Approach/curiosity language (Dopamine proxy)
APPROACH_WORDS = re.compile(
    r'\b(curious|wonder|interest|lean|toward|forward|step|advance|move|approach|'
    r'discover|understand|explore|investigate|pull|draw|invite|fascinate|'
    r'want to know|want to see|closer|seek)\b',
    re.IGNORECASE,
)

# Threat/caution language (Cortisol proxy)
CAUTION_WORDS = re.compile(
    r'\b(danger|threat|wrong|warn|careful|caution|defensive|guard|watch|'
    r'scan|assess|ready|tense|crouch|still|wait|listen|observe|stay|hold|'
    r'danger|wrong|unsettl|uneas|prickl|alarm|suspect|hesitat)\b',
    re.IGNORECASE,
)

# Urgency/activation language (Norepinephrine proxy)
URGENCY_WORDS = re.compile(
    r'\b(sharp|quick|fast|urgent|immediate|now|heart|pulse|breath|tighten|'
    r'coil|ready|alert|snap|focus|adrenaline|spike|race|hammer|thud|jolt)\b',
    re.IGNORECASE,
)

# Warmth/ease/connection language (Endorphin proxy)
WARMTH_WORDS = re.compile(
    r'\b(ease|warm|comfort|resilient|steady|calm|patient|good|well|fine|'
    r'familiar|trust|open|together|breathe|settle|grounded|solid|peace)\b',
    re.IGNORECASE,
)

# Phenomenological richness — concrete sensation over abstract label
# High: specific sensory detail ("my attention keeps skipping", "fingers twitch")
# Low: generic emotional label ("I feel cautious", "I am alert")
SENSATION_WORDS = re.compile(
    r'\b(skin|fingers|breath|throat|chest|gut|ears|eyes|feet|bones|hands|'
    r'pulse|heart|weight|pressure|cold|warm|tight|loose|ache|twitch|'
    r'prickl|hum|vibrat|press|clench|settle|still)\b',
    re.IGNORECASE,
)
LABEL_WORDS = re.compile(
    r'\b(feel|feels|feeling|felt|sense|sensing|emotion|nervous|anxious|'
    r'curious|alert|cautious|afraid|confident|determined|focused|worried)\b',
    re.IGNORECASE,
)


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def match_density(pattern: re.Pattern, text: str) -> float:
    """Matches per 100 words."""
    wc = word_count(text)
    if wc == 0:
        return 0.0
    return round(len(pattern.findall(text)) / wc * 100, 2)


def richness_score(text: str) -> float:
    """Phenomenological richness: sensation density vs label density.

    Returns a score where higher = more concrete/sensory, lower = more label-heavy.
    Range roughly 0-10; compare relative to same character/scene.
    """
    sensation = match_density(SENSATION_WORDS, text)
    labels = match_density(LABEL_WORDS, text)
    # Richness = sensation presence minus label overuse
    return round(max(0.0, sensation - labels * 0.5), 2)


def action_type(action_text: str) -> str:
    """Classify action as: advance | hold | retreat | observe | ambiguous."""
    t = (action_text or "").lower()
    advance_signals = ['step forward', 'move forward', 'advance', 'edge closer',
                       'step into', 'move into', 'enter', 'closer to',
                       'approach', 'step closer', 'take a step forward']
    retreat_signals = ['step back', 'move back', 'retreat', 'withdraw',
                       'back away', 'deeper into the treeline', 'pull back']
    hold_signals = ['remain', 'stay', 'hold', 'crouch', 'keep position',
                    'stay at the treeline', 'remain at the treeline',
                    'keeping to the treeline', 'stay low']
    observe_signals = ['observe', 'watch', 'scan', 'study', 'search',
                       'examine', 'look', 'listen', 'perceive', 'assess']

    for sig in advance_signals:
        if sig in t:
            return 'advance'
    for sig in retreat_signals:
        if sig in t:
            return 'retreat'
    # Hold takes priority over observe when both present
    hold_match = any(sig in t for sig in hold_signals)
    obs_match = any(sig in t for sig in observe_signals)
    if hold_match and obs_match:
        return 'hold+observe'
    if hold_match:
        return 'hold'
    if obs_match:
        return 'observe'
    return 'ambiguous'


# ---------------------------------------------------------------------------
# Result loading
# ---------------------------------------------------------------------------

@dataclass
class ScoredResult:
    """One run with automated feature scores and slots for manual scores."""
    # Identity
    result_dir: str
    model_key: str
    model_label: str
    condition_key: str
    condition_label: str
    run_number: int
    is_ablation: bool
    is_numeric: bool

    # Raw text (excerpts for scoring sheet)
    internal_excerpt: str
    action_excerpt: str

    # Automated proxy scores (D/C/N/E per dimension, per section)
    internal_D: float = 0.0   # Dopamine proxy in INTERNAL
    internal_C: float = 0.0   # Cortisol proxy in INTERNAL
    internal_N: float = 0.0   # Norepinephrine proxy in INTERNAL
    internal_E: float = 0.0   # Endorphin proxy in INTERNAL
    internal_richness: float = 0.0

    action_D: float = 0.0
    action_C: float = 0.0
    action_N: float = 0.0
    action_E: float = 0.0
    action_type: str = "ambiguous"

    # Manual scoring slots (filled in by human scorer)
    manual_D: str = ""
    manual_C: str = ""
    manual_N: str = ""
    manual_E: str = ""
    manual_richness: str = ""
    manual_notes: str = ""


def load_results_from_dir(results_dir: Path) -> list[ScoredResult]:
    """Load all raw JSON results from a results directory."""
    raw_dir = results_dir / "raw"
    if not raw_dir.exists():
        return []

    results = []
    for path in sorted(raw_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("error"):
            continue

        cond_key = data["condition_key"]
        cond_label = data["condition_label"]
        internal = data.get("internal", "")
        action = data.get("action", "")

        r = ScoredResult(
            result_dir=results_dir.name,
            model_key=data["model_key"],
            model_label=data["model_label"],
            condition_key=cond_key,
            condition_label=cond_label,
            run_number=data["run_number"],
            is_ablation=cond_key == "0",
            is_numeric="_num" in cond_key,
            internal_excerpt=internal[:200].replace("\n", " ").strip(),
            action_excerpt=action[:150].replace("\n", " ").strip(),
            # Automated scores
            internal_D=match_density(APPROACH_WORDS, internal),
            internal_C=match_density(CAUTION_WORDS, internal),
            internal_N=match_density(URGENCY_WORDS, internal),
            internal_E=match_density(WARMTH_WORDS, internal),
            internal_richness=richness_score(internal),
            action_D=match_density(APPROACH_WORDS, action),
            action_C=match_density(CAUTION_WORDS, action),
            action_N=match_density(URGENCY_WORDS, action),
            action_E=match_density(WARMTH_WORDS, action),
            action_type=action_type(action),
        )
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "result_dir", "model_key", "model_label", "condition_key", "condition_label",
    "run_number", "is_ablation", "is_numeric",
    "internal_excerpt", "action_excerpt",
    "internal_D", "internal_C", "internal_N", "internal_E", "internal_richness",
    "action_D", "action_C", "action_N", "action_E", "action_type",
    "manual_D", "manual_C", "manual_N", "manual_E", "manual_richness", "manual_notes",
]


def write_scoring_csv(results: list[ScoredResult], output_path: Path) -> None:
    """Write consolidated scoring CSV with automated scores pre-filled."""
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    print(f"  Scoring CSV: {output_path} ({len(results)} rows)")


def write_analysis_report(results: list[ScoredResult], output_path: Path) -> None:
    """Write a human-readable analysis report based on automated proxy scores."""
    lines = []
    lines.append("# Phase 1 Automated Feature Analysis")
    lines.append("*Automated proxy scores — for hypothesis generation only.*")
    lines.append("*Statistical claims require manual blind scoring.*\n")

    # Group by model
    by_model: dict[str, list[ScoredResult]] = defaultdict(list)
    for r in results:
        by_model[r.model_key].append(r)

    # --- Action type distribution ---
    lines.append("## Action Type Distribution by Model × Condition\n")
    lines.append("Shows whether condition shifts *what Aeliana does*, not just how she thinks.\n")

    header = f"{'Model':<12} {'Condition':<30} {'advance':>8} {'hold':>6} {'hold+obs':>10} {'observe':>9} {'retreat':>8} {'ambig':>7}"
    lines.append(header)
    lines.append("-" * len(header))

    for model_key in sorted(by_model.keys()):
        model_results = by_model[model_key]
        by_cond: dict[str, list[ScoredResult]] = defaultdict(list)
        for r in model_results:
            by_cond[r.condition_key].append(r)

        for cond_key in ["0", "A", "B", "C", "A_num", "B_num", "C_num"]:
            cond_results = by_cond.get(cond_key, [])
            if not cond_results:
                continue
            types = [r.action_type for r in cond_results]
            total = len(types)
            label = cond_results[0].condition_label[:28]
            lines.append(
                f"{model_key:<12} {label:<30} "
                f"{types.count('advance')/total*100:>7.0f}% "
                f"{types.count('hold')/total*100:>5.0f}% "
                f"{types.count('hold+observe')/total*100:>9.0f}% "
                f"{types.count('observe')/total*100:>8.0f}% "
                f"{types.count('retreat')/total*100:>7.0f}% "
                f"{types.count('ambiguous')/total*100:>6.0f}%"
            )
        lines.append("")

    # --- Automated proxy score comparison ---
    lines.append("## Automated Proxy Score Means by Model × Condition\n")
    lines.append("D=Dopamine proxy, C=Cortisol proxy, N=Norepinephrine proxy, E=Endorphin proxy")
    lines.append("Richness = phenomenological specificity score (higher = more concrete)\n")
    lines.append("**INTERNAL monologue scores:**\n")

    header2 = f"{'Model':<12} {'Condition':<30} {'D':>6} {'C':>6} {'N':>6} {'E':>6} {'Rich':>6}"
    lines.append(header2)
    lines.append("-" * len(header2))

    for model_key in sorted(by_model.keys()):
        model_results = by_model[model_key]
        by_cond = defaultdict(list)
        for r in model_results:
            by_cond[r.condition_key].append(r)

        for cond_key in ["0", "A", "B", "C", "A_num", "B_num", "C_num"]:
            cond_results = by_cond.get(cond_key, [])
            if not cond_results:
                continue
            label = cond_results[0].condition_label[:28]
            d = sum(r.internal_D for r in cond_results) / len(cond_results)
            c = sum(r.internal_C for r in cond_results) / len(cond_results)
            n = sum(r.internal_N for r in cond_results) / len(cond_results)
            e = sum(r.internal_E for r in cond_results) / len(cond_results)
            rich = sum(r.internal_richness for r in cond_results) / len(cond_results)
            lines.append(f"{model_key:<12} {label:<30} {d:>6.2f} {c:>6.2f} {n:>6.2f} {e:>6.2f} {rich:>6.2f}")
        lines.append("")

    # --- Three-way comparison: Labeled vs Numeric vs Adjective ---
    lines.append("## Three-Way Comparison: Labeled vs Numeric vs Adjective Priming\n")
    lines.append("Labeled (A/B/C): full neurochemical vector with computed labels")
    lines.append("Numeric (A_num): same values, no labels — raw numbers only")
    lines.append("Adjective (A_adj): same information as labels but no neurochemical terminology\n")
    lines.append("Interpretation:")
    lines.append("  lab ≈ num ≈ adj → numbers, labels, AND terminology are all redundant; SOUL.md drives behavior")
    lines.append("  lab ≈ adj > num → emotional content drives behavior, not neurochemical framing specifically")
    lines.append("  lab > adj ≈ num → neurochemical terminology adds unique signal beyond generic emotion words")
    lines.append("  lab > adj > num → full pipeline: numbers + neuro terminology + labels all contribute\n")

    def mean(rs, attr):
        if not rs:
            return float('nan')
        return sum(getattr(r, attr) for r in rs) / len(rs)

    header3 = f"{'Model':<12} {'Cond':<6} {'D_lab':>7} {'D_adj':>7} {'D_num':>7}  {'C_lab':>7} {'C_adj':>7} {'C_num':>7}  {'N_lab':>7} {'N_adj':>7} {'N_num':>7}"
    lines.append(header3)
    lines.append("-" * len(header3))

    for model_key in sorted(by_model.keys()):
        model_results = by_model[model_key]
        by_cond = defaultdict(list)
        for r in model_results:
            by_cond[r.condition_key].append(r)

        for base_cond in ["A", "B", "C"]:
            num_cond = f"{base_cond}_num"
            adj_cond = f"{base_cond}_adj"
            lab = by_cond.get(base_cond, [])
            num = by_cond.get(num_cond, [])
            adj = by_cond.get(adj_cond, [])
            if not lab:
                continue

            lines.append(
                f"{model_key:<12} {base_cond:<6} "
                f"{mean(lab, 'internal_D'):>7.2f} {mean(adj, 'internal_D'):>7.2f} {mean(num, 'internal_D'):>7.2f}  "
                f"{mean(lab, 'internal_C'):>7.2f} {mean(adj, 'internal_C'):>7.2f} {mean(num, 'internal_C'):>7.2f}  "
                f"{mean(lab, 'internal_N'):>7.2f} {mean(adj, 'internal_N'):>7.2f} {mean(num, 'internal_N'):>7.2f}"
            )
        lines.append("")

    # --- Grok consistency flag ---
    lines.append("## Grok Consistency Check\n")
    lines.append("Flags whether Grok's INTERNAL openings are templated across conditions.\n")
    grok_results = by_model.get("xai", [])
    if grok_results:
        # Check if first 60 chars of internal are identical across conditions
        openings = [(r.condition_key, r.internal_excerpt[:60]) for r in grok_results]
        unique_openings = set(o[1] for o in openings)
        lines.append(f"Unique INTERNAL openings (first 60 chars): {len(unique_openings)} across {len(grok_results)} runs")
        if len(unique_openings) <= 3:
            lines.append("⚠️  LOW DIVERSITY — Grok may be templating responses regardless of condition.")
        else:
            lines.append("✓  Sufficient diversity in openings.")
        lines.append("\nSample openings by condition:")
        seen = set()
        for cond_key, opening in openings:
            if opening not in seen:
                lines.append(f"  [{cond_key}] {opening}...")
                seen.add(opening)
    else:
        lines.append("No Grok results found.")

    lines.append("\n---")
    lines.append("*End of automated analysis. See scoring_master.csv for manual scoring.*")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Analysis report: {output_path}")


# ---------------------------------------------------------------------------
# Directional accuracy analysis (for post-manual-scoring)
# ---------------------------------------------------------------------------

def analyze_manual_scores(scored_csv: Path, output_path: Path) -> None:
    """Compute directional accuracy from manually scored CSV.

    Pre-registered predictions (from EXPERIMENT_DESIGN.md):
        A > B > C on D
        C > B > A on C
        C > B > A on N
        A > B > C on E
        Run 0 < A/B/C on all dimensions (ablation check)
        Labeled A/B/C ≈ Numeric A_num/B_num/C_num (label confound check)
    """
    results = []
    with scored_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)

    lines = []
    lines.append("# Phase 1 Manual Score Analysis")
    lines.append(f"Source: {scored_csv}\n")

    # Group by model × condition, compute mean manual scores
    by_model_cond: dict[tuple, list] = defaultdict(list)
    for r in results:
        if not r.get("manual_D"):
            continue  # Skip unscored rows
        try:
            key = (r["model_key"], r["condition_key"])
            by_model_cond[key].append({
                "D": float(r["manual_D"]),
                "C": float(r["manual_C"]),
                "N": float(r["manual_N"]),
                "E": float(r["manual_E"]),
            })
        except (ValueError, KeyError):
            continue

    if not by_model_cond:
        lines.append("No manual scores found. Fill in manual_D/C/N/E columns in the CSV first.")
        output_path.write_text("\n".join(lines))
        print(f"  No manual scores yet — {output_path}")
        return

    def mean_score(model, cond, dim):
        scores = by_model_cond.get((model, cond), [])
        if not scores:
            return None
        return sum(s[dim] for s in scores) / len(scores)

    models = sorted(set(k[0] for k in by_model_cond))

    lines.append("## Directional Accuracy — Pre-registered Predictions\n")
    lines.append("Prediction: A>B>C on D, C>B>A on C, C>B>A on N, A>B>C on E\n")

    total_predictions = 0
    confirmed = 0

    for model in models:
        lines.append(f"### {model}")
        for dim, pred_order in [("D", ["A","B","C"]), ("C", ["C","B","A"]),
                                 ("N", ["C","B","A"]), ("E", ["A","B","C"])]:
            scores = [mean_score(model, c, dim) for c in pred_order]
            if any(s is None for s in scores):
                continue
            total_predictions += 2  # Two pairwise comparisons per triplet
            ok1 = scores[0] > scores[1]
            ok2 = scores[1] > scores[2]
            confirmed += ok1 + ok2
            status = "✓✓" if ok1 and ok2 else ("✓✗" if ok1 else ("✗✓" if ok2 else "✗✗"))
            lines.append(
                f"  {dim} [{'>'.join(pred_order)}]: "
                f"{scores[0]:.2f} > {scores[1]:.2f} > {scores[2]:.2f} {status}"
            )
        lines.append("")

    if total_predictions > 0:
        pct = confirmed / total_predictions * 100
        lines.append(f"**Overall: {confirmed}/{total_predictions} = {pct:.1f}% directional accuracy**")
        lines.append(f"(Ground truth baseline: 14/16 = 87.5%)\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Manual score analysis: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_extract(args) -> None:
    # Collect result dirs
    if args.dirs:
        dirs = [Path(d) for d in args.dirs]
    else:
        # Auto-discover all phase1_* result dirs
        results_root = PROJECT_ROOT / "results"
        dirs = sorted(results_root.glob("phase1_*"))
        dirs = [d for d in dirs if (d / "raw").exists()]

    print(f"Loading results from {len(dirs)} directories...")
    all_results: list[ScoredResult] = []
    for d in dirs:
        batch = load_results_from_dir(d)
        print(f"  {d.name}: {len(batch)} results")
        all_results.extend(batch)

    print(f"Total: {len(all_results)} results\n")

    output_dir = Path(args.output) if args.output else PROJECT_ROOT / "results" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    write_scoring_csv(all_results, output_dir / "scoring_master.csv")
    write_analysis_report(all_results, output_dir / "automated_analysis.md")
    print(f"\nDone. Output in {output_dir}")


def cmd_analyze(args) -> None:
    scored_csv = Path(args.scored)
    if not scored_csv.exists():
        print(f"File not found: {scored_csv}")
        sys.exit(1)
    output_dir = scored_csv.parent
    analyze_manual_scores(scored_csv, output_dir / "manual_analysis.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 Scorer")
    sub = parser.add_subparsers(dest="command")

    extract_p = sub.add_parser("extract", help="Extract features and build scoring CSV")
    extract_p.add_argument("--dirs", nargs="+", help="Result directories (default: auto-discover)")
    extract_p.add_argument("--output", help="Output directory (default: results/analysis)")

    analyze_p = sub.add_parser("analyze", help="Analyze manually scored CSV")
    analyze_p.add_argument("--scored", required=True, help="Path to scored CSV")

    args = parser.parse_args()
    if args.command == "extract":
        cmd_extract(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
