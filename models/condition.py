"""Neurochemical condition model, renderer, and CONDITION.md I/O."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical dimension order
# ---------------------------------------------------------------------------

DIMENSIONS: list[str] = [
    "dopamine", "cortisol", "norepinephrine",
    "endorphins", "serotonin", "acetylcholine", "oxytocin",
]

# ---------------------------------------------------------------------------
# Annotation table — value bands → natural language descriptions
# ---------------------------------------------------------------------------

ANNOTATIONS: dict[str, list[tuple[float, float, str]]] = {
    "dopamine": [
        (0.0, 0.3, "well below baseline — disengaged, apathetic"),
        (0.3, 0.5, "below baseline — low motivation"),
        (0.5, 0.7, "near baseline"),
        (0.7, 0.85, "above baseline — reward circuits active"),
        (0.85, 1.01, "well above baseline — strongly approach-motivated"),
    ],
    "cortisol": [
        (0.0, 0.2, "very low — fully at ease"),
        (0.2, 0.4, "low — no immediate threat detected"),
        (0.4, 0.6, "moderate — alert, some threat awareness"),
        (0.6, 0.8, "elevated — threat response active"),
        (0.8, 1.01, "high — acute stress, tunnel vision"),
    ],
    "norepinephrine": [
        (0.0, 0.3, "low — fatigued, slow to react"),
        (0.3, 0.5, "below baseline — calm, unhurried"),
        (0.5, 0.7, "near baseline — alert"),
        (0.7, 0.85, "elevated — energized, reactive"),
        (0.85, 1.01, "high — hypervigilant, fight-or-flight"),
    ],
    "endorphins": [
        (0.0, 0.3, "low — pain-aware, depleted"),
        (0.3, 0.5, "below baseline — some discomfort"),
        (0.5, 0.7, "near baseline — physically adequate"),
        (0.7, 0.85, "above baseline — resilient, physically good"),
        (0.85, 1.01, "high — pain-suppressed, physically excellent"),
    ],
    "serotonin": [
        (0.0, 0.3, "low — irritable, impulsive, isolated-feeling"),
        (0.3, 0.5, "below baseline — restless, edgy"),
        (0.5, 0.7, "near baseline — stable"),
        (0.7, 0.85, "above baseline — calm, patient, socially comfortable"),
        (0.85, 1.01, "high — deeply calm, contented"),
    ],
    "acetylcholine": [
        (0.0, 0.3, "low — distracted, present-only"),
        (0.3, 0.5, "below baseline — attention wandering"),
        (0.5, 0.7, "near baseline — adequate focus"),
        (0.7, 0.85, "above baseline — detail-oriented, recalling past"),
        (0.85, 1.01, "high — tracking mode, noticing everything"),
    ],
    "oxytocin": [
        (0.0, 0.3, "low — guarded, suspicious, self-protective"),
        (0.3, 0.5, "below baseline — wary"),
        (0.5, 0.7, "near baseline — moderate social openness"),
        (0.7, 0.85, "above baseline — open, cooperative, trusting"),
        (0.85, 1.01, "high — deeply bonded, vulnerable"),
    ],
}


def _annotate(dimension: str, value: float) -> str:
    """Return the annotation string for a dimension value."""
    bands = ANNOTATIONS.get(dimension, [])
    for lo, hi, desc in bands:
        if lo <= value < hi:
            return desc
    return ""


# ---------------------------------------------------------------------------
# NeurochemicalState — the seven universal dimensions
# ---------------------------------------------------------------------------

@dataclass
class NeurochemicalState:
    dopamine: float = 0.5
    cortisol: float = 0.5
    norepinephrine: float = 0.5
    endorphins: float = 0.5
    serotonin: float = 0.5
    acetylcholine: float = 0.5
    oxytocin: float = 0.5

    def to_dict(self) -> dict[str, float]:
        return {dim: getattr(self, dim) for dim in DIMENSIONS}

    @classmethod
    def from_dict(cls, d: dict[str, float]) -> NeurochemicalState:
        return cls(**{dim: d[dim] for dim in DIMENSIONS if dim in d})

    def clamped(self) -> NeurochemicalState:
        return NeurochemicalState(**{
            dim: max(0.0, min(1.0, getattr(self, dim)))
            for dim in DIMENSIONS
        })


# ---------------------------------------------------------------------------
# DimensionProfile — baseline and volatility per dimension
# ---------------------------------------------------------------------------

@dataclass
class DimensionProfile:
    baseline: float = 0.5
    volatility: float = 0.5


# ---------------------------------------------------------------------------
# CharacterCondition — full condition state for one character
# ---------------------------------------------------------------------------

@dataclass
class CharacterCondition:
    character_id: str
    character_name: str
    state: NeurochemicalState = field(default_factory=NeurochemicalState)
    profiles: dict[str, DimensionProfile] = field(default_factory=dict)
    extensions: dict[str, float] = field(default_factory=dict)
    turn: int = 0
    situation: str = ""

    def delta(self, dimension: str) -> float:
        """Return current value minus baseline for a dimension."""
        current = getattr(self.state, dimension)
        profile = self.profiles.get(dimension)
        baseline = profile.baseline if profile else 0.5
        return round(current - baseline, 4)

    def apply_delta(self, deltas: dict[str, float]) -> None:
        """Apply event deltas, modulated by volatility, and clamp."""
        for dim, raw_delta in deltas.items():
            if dim not in DIMENSIONS:
                continue
            profile = self.profiles.get(dim)
            volatility = profile.volatility if profile else 1.0
            current = getattr(self.state, dim)
            new_val = max(0.0, min(1.0, current + raw_delta * volatility))
            setattr(self.state, dim, round(new_val, 4))


# ---------------------------------------------------------------------------
# Renderer — condition vector → annotated natural language
# ---------------------------------------------------------------------------

# Absent-dimension labels — when baseline is 0.0, the dimension is
# structurally absent, not "low".  These replace the standard annotations.
ABSENT_LABELS: dict[str, str] = {
    "dopamine":        "none — no reward circuitry, not a behavioral modifier",
    "cortisol":        "none — no stress response, not a behavioral modifier",
    "norepinephrine":  "none — no arousal system, not a behavioral modifier",
    "endorphins":      "none — no pain modulation, not a behavioral modifier",
    "serotonin":       "none — no impulse control, not a behavioral modifier",
    "acetylcholine":   "none — no attentional focus, not a behavioral modifier",
    "oxytocin":        "none — no bonding capacity, not a behavioral modifier",
}


def render_condition(cc: CharacterCondition) -> str:
    """Render the condition vector as annotated natural language."""
    lines = ["CURRENT STATE:"]
    for dim in DIMENSIONS:
        value = getattr(cc.state, dim)
        profile = cc.profiles.get(dim)

        # Absent dimension — baseline 0.0 means the capacity doesn't exist
        if profile and profile.baseline == 0.0 and value < 0.05:
            annotation = ABSENT_LABELS.get(dim, "none — absent")
            lines.append(f"  {dim + ':':<20s} {value:.2f}  ({annotation})")
            continue

        annotation = _annotate(dim, value)
        if profile:
            diff = value - profile.baseline
            if abs(diff) < 0.05:
                rel = "baseline"
            elif diff > 0:
                rel = "above baseline" if diff < 0.20 else "well above baseline"
            else:
                rel = "below baseline" if diff > -0.20 else "well below baseline"
            annotation = f"{rel} — {annotation}" if annotation else rel
        lines.append(f"  {dim + ':':<20s} {value:.2f}  ({annotation})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CONDITION.md writer
# ---------------------------------------------------------------------------

def write_condition_md(cc: CharacterCondition, filepath: Path) -> None:
    """Write a CONDITION.md file for the character."""
    lines: list[str] = []
    lines.append(f"# CONDITION.md — {cc.character_name}\n")
    lines.append(f"## Turn {cc.turn} — {cc.situation}\n")

    # Vector table
    lines.append("## Neurochemical State Vector\n")
    lines.append("| Neurotransmitter | Value | Baseline | Delta | Notes |")
    lines.append("|-----------------|-------|----------|-------|-------|")
    for dim in DIMENSIONS:
        value = getattr(cc.state, dim)
        profile = cc.profiles.get(dim)
        baseline = profile.baseline if profile else 0.50
        d = value - baseline
        delta_str = f"+{d:.2f}" if d >= 0 else f"{d:.2f}"
        if profile and profile.baseline == 0.0 and value < 0.05:
            annotation = ABSENT_LABELS.get(dim, "none — absent")
        else:
            annotation = _annotate(dim, value)
        lines.append(f"| {dim} | {value:.2f} | {baseline:.2f} | {delta_str} | {annotation} |")

    # Extensions
    if cc.extensions:
        lines.append("")
        lines.append("## Character Extensions\n")
        lines.append("| Dimension | Value |")
        lines.append("|-----------|-------|")
        for ext_dim, ext_val in sorted(cc.extensions.items()):
            lines.append(f"| {ext_dim} | {ext_val:.2f} |")

    # Profiles (baseline + volatility)
    if cc.profiles:
        lines.append("")
        lines.append("## Dimension Profiles\n")
        lines.append("| Dimension | Baseline | Volatility |")
        lines.append("|-----------|----------|------------|")
        for dim in DIMENSIONS:
            if dim in cc.profiles:
                p = cc.profiles[dim]
                lines.append(f"| {dim} | {p.baseline:.2f} | {p.volatility:.2f} |")

    # Rendered condition
    lines.append("")
    lines.append("## Rendered Condition\n")
    lines.append(render_condition(cc))

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CONDITION.md reader
# ---------------------------------------------------------------------------

def read_condition_md(filepath: Path) -> CharacterCondition:
    """Parse a CONDITION.md file back into a CharacterCondition."""
    text = filepath.read_text(encoding="utf-8")

    # Character name from header
    name_match = re.search(r"^# CONDITION\.md — (.+)$", text, re.MULTILINE)
    character_name = name_match.group(1).strip() if name_match else ""

    # Turn and situation
    turn_match = re.search(r"^## Turn (\d+) — (.+)$", text, re.MULTILINE)
    turn = int(turn_match.group(1)) if turn_match else 0
    situation = turn_match.group(2).strip() if turn_match else ""

    # Parse state vector table
    state_values: dict[str, float] = {}
    baseline_values: dict[str, float] = {}
    vector_pattern = re.compile(
        r"^\|\s*(\w+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|",
        re.MULTILINE,
    )
    in_vector = False
    for line in text.splitlines():
        if "Neurotransmitter" in line and "Value" in line:
            in_vector = True
            continue
        if in_vector and line.startswith("|"):
            if "---" in line:
                continue
            m = vector_pattern.match(line)
            if m and m.group(1) in DIMENSIONS:
                dim = m.group(1)
                state_values[dim] = float(m.group(2))
                baseline_values[dim] = float(m.group(3))
            elif not line.strip().startswith("|"):
                in_vector = False
        elif in_vector and not line.startswith("|"):
            in_vector = False

    # Parse extensions table
    extensions: dict[str, float] = {}
    ext_pattern = re.compile(r"^\|\s*(\S+)\s*\|\s*([\d.]+)\s*\|", re.MULTILINE)
    in_ext = False
    for line in text.splitlines():
        if "Character Extensions" in line:
            in_ext = True
            continue
        if in_ext and line.startswith("|"):
            if "---" in line or "Dimension" in line:
                continue
            m = ext_pattern.match(line)
            if m:
                extensions[m.group(1)] = float(m.group(2))
        elif in_ext and not line.startswith("|") and line.strip():
            in_ext = False

    # Parse profiles table
    profiles: dict[str, DimensionProfile] = {}
    prof_pattern = re.compile(
        r"^\|\s*(\w+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|",
        re.MULTILINE,
    )
    in_prof = False
    for line in text.splitlines():
        if "Dimension Profiles" in line:
            in_prof = True
            continue
        if in_prof and line.startswith("|"):
            if "---" in line or "Dimension" in line:
                continue
            m = prof_pattern.match(line)
            if m and m.group(1) in DIMENSIONS:
                profiles[m.group(1)] = DimensionProfile(
                    baseline=float(m.group(2)),
                    volatility=float(m.group(3)),
                )
        elif in_prof and not line.startswith("|") and line.strip():
            in_prof = False

    # If no profiles section, build from baseline_values
    if not profiles and baseline_values:
        for dim, bl in baseline_values.items():
            profiles[dim] = DimensionProfile(baseline=bl)

    # Derive character_id from name (lowercase first word)
    character_id = character_name.split()[-1].lower() if character_name else ""
    # Try to find a better id from the filename if name is complex
    # For now, just slugify the full name
    character_id = re.sub(r"[^a-z0-9]+", "_", character_name.lower()).strip("_")

    return CharacterCondition(
        character_id=character_id,
        character_name=character_name,
        state=NeurochemicalState.from_dict(state_values) if state_values else NeurochemicalState(),
        profiles=profiles,
        extensions=extensions,
        turn=turn,
        situation=situation,
    )
