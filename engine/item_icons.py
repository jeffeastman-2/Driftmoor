"""Small presentation helper for item emoji used by inventory and maps."""

from __future__ import annotations

import re


ITEM_ICONS = (
    ("torch", "🔥"), ("crossbow", "🏹"), ("bow", "🏹"), ("dagger", "🗡️"),
    ("rapier", "🗡️"), ("sword", "🗡️"), ("blade", "🗡️"), ("axe", "🪓"),
    ("mace", "🔨"), ("hammer", "🔨"), ("shield", "🛡️"), ("staff", "🪄"),
    ("wand", "🪄"), ("potion", "🧪"), ("vial", "🧪"), ("scroll", "📜"),
    ("letter", "✉️"), ("parchment", "📜"), ("key", "🗝️"), ("gem", "💎"),
    ("shard", "💎"), ("crystal", "💎"), ("coin", "🪙"), ("gold", "🪙"),
    ("book", "📖"), ("tome", "📖"), ("rope", "🪢"), ("bone", "🦴"),
    ("skull", "💀"), ("ring", "💍"), ("pack", "🎒"), ("bag", "🎒"),
    ("chalk", "✏️"), ("charcoal", "✏️"), ("armor", "🛡️"),
    ("leather", "🛡️"), ("tools", "🛠️"), ("kit", "🧰"),
    ("bracelet", "💍"), ("amulet", "🔱"), ("cloak", "🧥"), ("boots", "🥾"),
    ("pemmican", "🥩"), ("tack", "🍪"), ("ration", "🍖"), ("bread", "🍞"),
    ("waterskin", "💧"), ("water", "💧"), ("mead", "🍺"), ("ale", "🍺"),
    ("wine", "🍷"), ("flask", "🍶"),
)


def item_icon(label: str) -> str:
    """Choose an icon using whole tokens and compound-word suffixes."""
    tokens = re.findall(r"[a-z0-9]+", (label or "").lower())
    for keyword, icon in ITEM_ICONS:
        if any(token == keyword or token.endswith(keyword) for token in tokens):
            return icon
    return "📦"
