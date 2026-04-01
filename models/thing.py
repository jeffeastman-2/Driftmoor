"""Thing model for the Driftmoor RPG engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Thing:
    """An item in the game world.

    Covers mundane shop goods, magical items, obelisk shards, and
    shadowbeast parts.  The *category* field distinguishes them.
    """

    id: str
    name: str
    category: str = ""              # "mundane", "magical", "obelisk_shard", "shadowbeast_part"
    price: str = ""                 # kept as string: "5 gp", "2-5 gp", "Varies"
    description: str = ""
    vendor_id: str = ""             # character ID of seller
    location_id: str = ""           # place ID where item currently is
    properties: str = ""            # advertised / player-visible properties
    dm_properties: str = ""         # true / hidden properties (DM only)
    attunement: str = ""            # e.g. "Required (1 hour in dim light)"
    raw: str = ""                   # original markdown source
