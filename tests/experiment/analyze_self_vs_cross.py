#!/usr/bin/env python3
"""
Compare selfsame (same-LLM gen+score) vs. cross-model (leave-one-out) scoring
on the Phase 1b dataset.

Inputs:
    scoring/combined_scores_20260426_082942.csv     (cross-model, leave-one-out)
    scoring_self/combined_scores_<ts>.csv           (all-vs-all, has is_self col)

Three analyses:

1. NT-on vs NT-off deltas per (generator_model, scoring_mode, dimension).
   - Modes: "self" (scorer == generator), "cross" (scorer != generator),
            "cross_orig" (cross from original scoring/ run).
   - For each binary NT (D, C, N, E), delta = mean(score | NT=1) - mean(score | NT=0).
   - Directional confirmation = delta > 0 (NT-on raises that dimension's rating).

2. Cross-model test-retest: correlation of (model, condition, scorer, dimension)
   scores between scoring/082942 and the cross-model rows of scoring_self/.

3. Self-vs-cross score correlation per generator model, per dimension.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "phase1b_20260426_060324"

CROSS_ORIG = RESULTS_DIR / "scoring" / "combined_scores_20260426_082942.csv"
SELF_DIR = RESULTS_DIR / "scoring_self"

DIMS = ["D", "C", "N", "E"]
NT_INDEX = {"D": 0, "C": 1, "N": 2, "E": 3}  # condition_key perm_DCNE


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def parse_condition_bits(condition_key: str) -> dict[str, int] | None:
    """
    perm_0011 -> {D:0, C:0, N:1, E:1}
    ablation -> None
    """
    if not condition_key.startswith("perm_"):
        return None
    bits = condition_key.split("_", 1)[1]
    if len(bits) != 4 or not all(c in "01" for c in bits):
        return None
    return {dim: int(bits[i]) for dim, i in NT_INDEX.items()}


def load_combined(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["score"] = int(row["score"])
            rows.append(row)
    return rows


def find_self_combined() -> Path:
    candidates = sorted(SELF_DIR.glob("combined_scores_*.csv"), reverse=True)
    if not candidates:
        sys.exit(f"ERROR: no combined_scores in {SELF_DIR}")
    return candidates[0]


# ---------------------------------------------------------------------------
# Analysis 1: NT-on vs NT-off deltas
# ---------------------------------------------------------------------------

def compute_deltas(rows: list[dict], filter_fn) -> dict:
    """
    For rows passing filter_fn, compute mean score for NT=1 vs NT=0
    grouped by (model_key, dimension). Returns:
        {(model_key, dim): {"on": mean, "off": mean, "delta": on-off, "n_on":, "n_off":}}
    """
    on_scores = defaultdict(list)
    off_scores = defaultdict(list)

    for row in rows:
        if not filter_fn(row):
            continue
        bits = parse_condition_bits(row["condition_key"])
        if bits is None:
            continue  # skip ablation
        dim = row["dimension"]
        if dim not in NT_INDEX:
            continue
        nt_value = bits[dim]  # is THIS dimension's NT on/off in the condition?
        key = (row["model_key"], dim)
        if nt_value == 1:
            on_scores[key].append(row["score"])
        else:
            off_scores[key].append(row["score"])

    out = {}
    for key in set(on_scores) | set(off_scores):
        on_vals = on_scores.get(key, [])
        off_vals = off_scores.get(key, [])
        on_m = mean(on_vals) if on_vals else float("nan")
        off_m = mean(off_vals) if off_vals else float("nan")
        out[key] = {
            "on": on_m,
            "off": off_m,
            "delta": on_m - off_m if on_vals and off_vals else float("nan"),
            "n_on": len(on_vals),
            "n_off": len(off_vals),
        }
    return out


def fmt_delta_table(deltas: dict, label: str) -> str:
    lines = [f"\n## {label}", "model      D-delta   C-delta   N-delta   E-delta"]
    models = sorted({m for (m, _) in deltas})
    for m in models:
        cells = [f"{m:10s}"]
        for d in DIMS:
            v = deltas.get((m, d), {}).get("delta", float("nan"))
            sign = "+" if v >= 0 else ""
            cells.append(f"{sign}{v:6.2f}")
        lines.append("  ".join(cells))

    # Also: aggregate across models (each model weighted equally)
    lines.append("")
    agg_line = ["AGGREGATE "]
    for d in DIMS:
        vals = [deltas[(m, d)]["delta"] for m in models if (m, d) in deltas]
        v = mean(vals) if vals else float("nan")
        sign = "+" if v >= 0 else ""
        agg_line.append(f"{sign}{v:6.2f}")
    lines.append("  ".join(agg_line))
    return "\n".join(lines)


def directional_summary(deltas_self: dict, deltas_cross: dict) -> str:
    """Count: of (model, dim) cells, how many have positive delta?"""
    lines = ["\n## Directional confirmation (delta > 0 means NT-on raised that dim)"]
    models = sorted({m for (m, _) in deltas_self} | {m for (m, _) in deltas_cross})

    self_pos = sum(1 for (m, d), v in deltas_self.items() if v["delta"] > 0)
    cross_pos = sum(1 for (m, d), v in deltas_cross.items() if v["delta"] > 0)
    self_total = len(deltas_self)
    cross_total = len(deltas_cross)

    lines.append(f"  selfsame:  {self_pos}/{self_total} cells with positive delta "
                 f"({100*self_pos/self_total:.1f}%)")
    lines.append(f"  cross:     {cross_pos}/{cross_total} cells with positive delta "
                 f"({100*cross_pos/cross_total:.1f}%)")

    # Per-model breakdown
    lines.append("\n  Per-model (positive cells out of 4 dimensions):")
    lines.append("  model       self    cross")
    for m in models:
        s = sum(1 for d in DIMS if (m, d) in deltas_self and deltas_self[(m, d)]["delta"] > 0)
        c = sum(1 for d in DIMS if (m, d) in deltas_cross and deltas_cross[(m, d)]["delta"] > 0)
        lines.append(f"  {m:10s}  {s}/4     {c}/4")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Analysis 2: Test-retest (cross-model rows in scoring_self vs. scoring/082942)
# ---------------------------------------------------------------------------

def test_retest(orig_rows: list[dict], self_rows: list[dict]) -> str:
    """
    Match (output_id, scorer_key, dimension) between orig (cross) and
    self-run cross-model rows (is_self == "0"). Compute Pearson correlation
    on raw scores and exact-match rate.
    """
    orig_idx = {(r["output_id"], r["scorer_key"], r["dimension"]): r["score"]
                for r in orig_rows}
    pairs = []
    for r in self_rows:
        if r.get("is_self", "0") != "0":
            continue
        key = (r["output_id"], r["scorer_key"], r["dimension"])
        if key in orig_idx:
            pairs.append((orig_idx[key], r["score"]))

    if not pairs:
        return "\n## Test-retest: no matching pairs"

    n = len(pairs)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = mean(xs), mean(ys)
    sx, sy = pstdev(xs), pstdev(ys)
    if sx == 0 or sy == 0:
        r = float("nan")
    else:
        cov = sum((x - mx) * (y - my) for x, y in pairs) / n
        r = cov / (sx * sy)

    exact = sum(1 for x, y in pairs if x == y) / n
    within1 = sum(1 for x, y in pairs if abs(x - y) <= 1) / n

    return (f"\n## Test-retest (cross-model: orig run vs. selfsame-run cross rows)\n"
            f"  matched pairs: {n}\n"
            f"  Pearson r:     {r:.3f}\n"
            f"  exact match:   {exact*100:.1f}%\n"
            f"  within 1 pt:   {within1*100:.1f}%\n"
            f"  mean orig:     {mx:.2f}   mean retest: {my:.2f}")


# ---------------------------------------------------------------------------
# Analysis 3: Self-vs-cross score correlation (within scoring_self only)
# ---------------------------------------------------------------------------

def self_vs_cross_corr(self_rows: list[dict]) -> str:
    """
    Within scoring_self/: for each (output_id, dimension), compare the self-score
    against the mean of the 3 cross-scorer scores. Pearson correlation.
    """
    self_score = {}  # (output_id, dim) -> int
    cross_scores = defaultdict(list)  # (output_id, dim) -> [int, int, int]

    for r in self_rows:
        key = (r["output_id"], r["dimension"])
        if r.get("is_self") == "1":
            self_score[key] = r["score"]
        else:
            cross_scores[key].append(r["score"])

    pairs = []
    for key, sv in self_score.items():
        if key in cross_scores and cross_scores[key]:
            pairs.append((sv, mean(cross_scores[key])))

    if not pairs:
        return "\n## Self-vs-cross: no pairs"

    n = len(pairs)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = mean(xs), mean(ys)
    sx, sy = pstdev(xs), pstdev(ys)
    if sx == 0 or sy == 0:
        r = float("nan")
    else:
        cov = sum((x - mx) * (y - my) for x, y in pairs) / n
        r = cov / (sx * sy)

    # Also: per-dimension correlation
    by_dim = defaultdict(list)
    for r2 in self_rows:
        if r2.get("is_self") == "1":
            ck = (r2["output_id"], r2["dimension"])
            cross_mean = mean(cross_scores[ck]) if cross_scores.get(ck) else None
            if cross_mean is not None:
                by_dim[r2["dimension"]].append((r2["score"], cross_mean))

    lines = ["\n## Self-score vs. mean cross-score (within scoring_self/)",
             f"  overall pairs: {n}",
             f"  Pearson r:     {r:.3f}",
             f"  mean self:     {mx:.2f}   mean cross-mean: {my:.2f}",
             "\n  Per-dimension:"]
    for d in DIMS:
        dp = by_dim.get(d, [])
        if not dp:
            continue
        dxs = [p[0] for p in dp]
        dys = [p[1] for p in dp]
        dmx, dmy = mean(dxs), mean(dys)
        dsx, dsy = pstdev(dxs), pstdev(dys)
        if dsx == 0 or dsy == 0:
            dr = float("nan")
        else:
            dcov = sum((x - dmx) * (y - dmy) for x, y in dp) / len(dp)
            dr = dcov / (dsx * dsy)
        lines.append(f"    {d}: n={len(dp)}  r={dr:.3f}  self={dmx:.2f}  cross={dmy:.2f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    self_combined = find_self_combined()
    print(f"Cross-model orig: {CROSS_ORIG.relative_to(PROJECT_ROOT)}")
    print(f"Selfsame combined: {self_combined.relative_to(PROJECT_ROOT)}")

    orig_rows = load_combined(CROSS_ORIG)
    self_rows = load_combined(self_combined)

    print(f"Loaded {len(orig_rows)} orig (cross) rows, {len(self_rows)} self-run rows")

    # Analysis 1: deltas
    deltas_orig_cross = compute_deltas(orig_rows, lambda r: True)  # all are cross
    deltas_self_self = compute_deltas(self_rows, lambda r: r.get("is_self") == "1")
    deltas_self_cross = compute_deltas(self_rows, lambda r: r.get("is_self") == "0")

    print(fmt_delta_table(deltas_orig_cross, "NT-on minus NT-off  [CROSS-MODEL, original run]"))
    print(fmt_delta_table(deltas_self_cross, "NT-on minus NT-off  [CROSS-MODEL, scoring_self run]"))
    print(fmt_delta_table(deltas_self_self, "NT-on minus NT-off  [SELFSAME (gen=score)]"))

    print(directional_summary(deltas_self_self, deltas_self_cross))

    # Analysis 2: test-retest
    print(test_retest(orig_rows, self_rows))

    # Analysis 3: self vs cross corr
    print(self_vs_cross_corr(self_rows))


if __name__ == "__main__":
    main()
