#!/usr/bin/env python3
"""LATN acceptance replay: compare the LATN resolver against the shallow one
on real logged intents, bucketed into a taxonomy.

This is the gate for flipping DRIFTMOOR_LATN_RESOLVER on (phase 2a cutover):
it replays the ``intent`` strings recorded in session checkpoints
(``character_results[*].intent``) through BOTH resolvers against the scene's
real items/characters, and categorizes each outcome:

  agree         - both resolve to the same item (or both decline)
  latn_only     - LATN resolved, shallow didn't  (usually a LATN win:
                  inflection / negation / role syntax shallow misses)
  shallow_only  - shallow resolved, LATN didn't, split by why:
      grammar_gap   - LATN produced no dispatchable verb phrase (parse gap)
      grounding_miss- LATN parsed a verb but grounded no item (adapter/lexicon)
  disagree      - both resolved, but to different items (needs review)

Headless: feeds intent strings through the resolver; no async turn loop, no
LLMs. Run:  .venv/bin/python -m tools.latn_acceptance
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable, Optional

from engine.md_loader import configure_from_md
from engine.latn_lexicon import build_driftmoor_lexicon
from engine.latn_adapter import DriftmoorSceneAdapter
from engine import latn_resolver
from engine import verb_resolver

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "runtime" / "state"
SCENES_DIR = ROOT / "scenes"


def _iter_logged_intents(state_dir: Path):
    """Yield (scene, character_id, turn, intent_text, interaction_target, zone)
    from every checkpoint, de-duplicated on (scene, char, turn, text)."""
    seen = set()
    for ckpt in sorted(state_dir.rglob("day1_*.json")):
        scene = ckpt.parent.name
        try:
            data = json.loads(ckpt.read_text())
        except Exception:
            continue
        positions = data.get("current_positions", {}) or {}
        for cr in data.get("character_results", []) or []:
            intent = (cr or {}).get("intent") or {}
            text = intent.get("intent")
            if not text:
                continue
            cid = intent.get("character_id", "")
            turn = intent.get("turn", 0)
            key = (scene, cid, turn, text)
            if key in seen:
                continue
            seen.add(key)
            pos = positions.get(cid) or {}
            # positions are serialized as {'x','y','zone'}
            zone = (pos.get("zone") if isinstance(pos, dict) else "") or ""
            yield scene, cid, turn, text, intent.get("interaction_target"), zone


def _shallow_item(text, target, items, zone) -> Optional[str]:
    """Item id the shallow resolver would land on, mirroring the turn loop:
    infer a target when none was given, then resolve."""
    t = target or verb_resolver.infer_interaction_target(text or "", items, zone)
    if not t:
        return None
    res = verb_resolver.resolve_item_interaction(
        intent_text=text or "", interaction_target=t, items=items, character_zone=zone,
    )
    return res[0].id if res else None


def _latn_outcome(text, lexicon, adapter):
    """Return (item_id_or_None, parsed_a_verb: bool) from the LATN resolver."""
    actions = latn_resolver.resolve_actions(text or "", lexicon=lexicon, adapter=adapter)
    parsed = bool(actions)
    for a in actions:
        if a.item is not None:
            return a.item.id, parsed
    return None, parsed


def run(scene_md: Path, state_dir: Path, show: int = 25) -> Counter:
    cfg = configure_from_md(scene_md)
    items, characters = cfg.items, cfg.characters
    geo = getattr(cfg, "scene_geometry", None)
    zones = list(getattr(geo, "zones", {}) or {}) if geo is not None else []
    lexicon = build_driftmoor_lexicon(
        list(characters.values()), list(items.values()), zones=zones,
    )

    # A character is "human" when it isn't LLM-driven (typed via a transport).
    human_ids = {
        cid for cid, cs in characters.items()
        if (getattr(cs, "player_transport", "llm") or "llm") != "llm"
    }

    tally: Counter = Counter()
    examples: dict[str, list[str]] = {}
    parsed_count = 0
    grp_total: Counter = Counter()   # 'human' / 'npc'
    grp_parsed: Counter = Counter()

    for scene, cid, turn, text, target, zone in _iter_logged_intents(state_dir):
        adapter = DriftmoorSceneAdapter(items=items, characters=characters, actor_zone=zone)
        shallow = _shallow_item(text, target, items, zone)
        latn, parsed = _latn_outcome(text, lexicon, adapter)
        parsed_count += int(parsed)
        grp = "human" if cid in human_ids else "npc"
        grp_total[grp] += 1
        grp_parsed[grp] += int(parsed)

        if shallow == latn:
            bucket = "agree_item" if shallow is not None else "agree_none"
        elif latn is not None and shallow is None:
            bucket = "latn_only"
        elif shallow is not None and latn is None:
            bucket = "grounding_miss" if parsed else "grammar_gap"
        else:
            bucket = "disagree"

        tally[bucket] += 1
        if not bucket.startswith("agree"):
            examples.setdefault(bucket, []).append(
                f"  [{cid} t{turn} z={zone or '-'}] {text[:80]!r}\n"
                f"      shallow={shallow}  latn={latn}  parsed_verb={parsed}"
            )

    total = sum(tally.values())
    print(f"\nLATN acceptance replay — {total} logged intents from {state_dir}\n" + "=" * 64)
    for b in ("agree_item", "agree_none", "latn_only", "grounding_miss", "grammar_gap", "disagree"):
        n = tally.get(b, 0)
        pct = (100.0 * n / total) if total else 0.0
        print(f"  {b:14} {n:4}  ({pct:4.1f}%)")
    print("-" * 64)
    pr = (100.0 * parsed_count / total) if total else 0.0
    item_total = tally.get("agree_item", 0) + tally.get("grammar_gap", 0) + \
        tally.get("grounding_miss", 0) + tally.get("disagree", 0)
    item_ok = tally.get("agree_item", 0)
    print(f"  parse rate     {parsed_count:4}/{total}  ({pr:4.1f}%)  "
          f"— LATN produced a dispatchable verb phrase")
    print(f"  item coverage  {item_ok:4}/{item_total}  "
          f"— item-resolving intents LATN matches shallow on")
    for grp in ("human", "npc"):
        gt, gp = grp_total.get(grp, 0), grp_parsed.get(grp, 0)
        if gt:
            print(f"  parse rate [{grp:5}] {gp:4}/{gt}  ({100.0*gp/gt:4.1f}%)")
    print("=" * 64)
    print("Cutover read: agree+latn_only is the safe-or-better set; grammar_gap +"
          "\n  grounding_miss + disagree are the triage backlog (shallow fallback"
          "\n  covers them live, so they don't regress).")
    for b in ("disagree", "grounding_miss", "grammar_gap", "latn_only"):
        ex = examples.get(b, [])
        if ex:
            print(f"\n--- {b} ({len(ex)}) — first {min(show, len(ex))} ---")
            print("\n".join(ex[:show]))
    return tally


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default=str(SCENES_DIR / "echoing_caverns.md"))
    ap.add_argument("--state", default=str(STATE_DIR))
    ap.add_argument("--show", type=int, default=25, help="examples per non-agree bucket")
    args = ap.parse_args()
    run(Path(args.scene), Path(args.state), show=args.show)


if __name__ == "__main__":
    main()
