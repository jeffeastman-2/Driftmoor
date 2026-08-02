"""Load authoritative runtime Things from place-local ``CONTENTS.md`` files."""

from __future__ import annotations

import re
from pathlib import Path

from models.thing import Thing


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text, re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group("body") if match else ""


def _table(section: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    for start in range(len(lines) - 1):
        if lines[start].startswith("|") and re.match(r"^\|[\s:|\-]+\|$", lines[start + 1]):
            headers = [c.strip().lower() for c in lines[start].strip("|").split("|")]
            rows = []
            for line in lines[start + 2:]:
                if not line.startswith("|"):
                    break
                cells = [c.strip() for c in line.strip("|").split("|")]
                rows.append({h: cells[i] if i < len(cells) else "" for i, h in enumerate(headers)})
            return rows
    return []


def _affordances(raw: str) -> set[str]:
    return {v.strip().lower() for v in re.split(r"[,;/]", raw or "") if v.strip()}


def _details(text: str) -> dict[str, dict[str, str]]:
    body = _section(text, "Runtime Thing Details")
    out: dict[str, dict[str, str]] = {}
    matches = list(re.finditer(r"^### (?!#)(.+?)\s*$", body, re.MULTILINE))
    for i, match in enumerate(matches):
        tid = match.group(1).strip()
        block = body[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(body)]
        att = re.search(r"^\*\*Attunement:\*\*\s*(.+)$", block, re.MULTILINE)
        advertised = re.search(
            r"^#### Advertised Properties\s*$\n(?P<v>.*?)(?=^#### |\Z)",
            block, re.MULTILINE | re.DOTALL,
        )
        dm = re.search(
            r"^#### DM Properties\s*$\n(?P<v>.*?)(?=^#### |\Z)",
            block, re.MULTILINE | re.DOTALL,
        )
        out[tid] = {
            "attunement": att.group(1).strip() if att else "",
            "properties": advertised.group("v").strip() if advertised else "",
            "dm_properties": dm.group("v").strip() if dm else "",
        }
    return out


def load_place_things(places_root: Path) -> list[Thing]:
    """Load every row under ``## Runtime Things`` below ``places_root``."""
    things: list[Thing] = []
    seen: set[str] = set()
    for path in sorted(places_root.rglob("CONTENTS.md")):
        text = path.read_text(encoding="utf-8")
        rows = _table(_section(text, "Runtime Things"))
        details = _details(text)
        if not rows:
            continue
        location_id = path.parent.relative_to(places_root).as_posix()
        for row in rows:
            tid = row.get("id", "").strip()
            if not tid:
                continue
            if tid in seen:
                raise ValueError(f"duplicate runtime Thing id {tid!r} in {path}")
            seen.add(tid)
            thing = Thing(
                id=tid,
                name=row.get("name", "").strip(),
                emoji=row.get("emoji", "").strip(),
                category=row.get("category", "mundane").strip() or "mundane",
                price=row.get("price", "").strip(),
                vendor_id=row.get("owner", "").strip(),
                location_id=location_id,
                container_id=row.get("container", "").strip(),
                availability=row.get("availability", "public").strip() or "public",
                affordances=_affordances(row.get("affordances", "")),
                description=row.get("effect", "").strip(),
                properties=row.get("effect", "").strip(),
                attunement=details.get(tid, {}).get("attunement", ""),
                dm_properties=details.get(tid, {}).get("dm_properties", ""),
            )
            if details.get(tid, {}).get("properties"):
                thing.properties = details[tid]["properties"]
            things.append(thing)
    return things
