"""Guardrail tests for keeping specs/SPELLS.md aligned with resolver spell book."""

from __future__ import annotations

import re
from pathlib import Path

from engine.spell_resolver import _SPELL_BOOK


def _spec_spell_headings(spec_text: str) -> set[str]:
    pattern = r"^###\s+(.+?)\n- Engine type:"
    return {m.group(1).strip() for m in re.finditer(pattern, spec_text, flags=re.MULTILINE)}


def test_spells_spec_lists_all_implemented_spells() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    spec_path = repo_root / "specs" / "SPELLS.md"
    spec_text = spec_path.read_text(encoding="utf-8")

    resolver_spells = {spell_def.name for spell_def in _SPELL_BOOK.values()}
    spec_spells = _spec_spell_headings(spec_text)

    missing = sorted(resolver_spells - spec_spells)
    extra = sorted(spec_spells - resolver_spells)

    assert not missing, (
        "SPELLS.md is missing implemented spells: " + ", ".join(missing)
    )
    assert not extra, (
        "SPELLS.md has spell headings not present in resolver spell book: " + ", ".join(extra)
    )
