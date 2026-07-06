# Gear

Mundane non-weapon, non-armor possessions — tools, trinkets, and other
wearables — as Thing templates. A character's IDENTITY references these by `id`
in an Equipment sub-list (e.g. `- thieves_tools`), optionally
overriding the display name for that character's instance
(`- bracelet: Wooden vine-carved bracelet`).

`kind` drives the affordance (comma-separate several, e.g. `wearable, container`):
- `tool` — holdable, usable (`use the ...`); may `produce` another Thing
- `wearable` — occupies a body slot (`wear`/`remove`)
- `shield` — HAND-held (holdable), not worn; its AC comes from an `ac +N` effect
- `container` — can hold other Things

`effects` is the same comma-separated grammar as CONSUMABLES.md (usually empty
for plain gear; e.g. a ring or shield carries `ac +N`).

| id | name | kind | effects |
|----|------|------|---------|
| shield | Shield | shield | ac +2 |
| bracelet | Bracelet | wearable | |
| ring | Ring | wearable | |
| amulet | Amulet | wearable | |
| cloak | Cloak | wearable | |
| holy_symbol | Holy Symbol | wearable |  |
| talisman | Talisman | wearable |  |
| explorers_pack | Explorer's Pack | wearable, container |  |
| burglars_pack | Burglar's Pack | wearable, container |  |
| scholars_pack | Scholar's Pack | wearable, container |  |
| musicians_pack | Musician's Pack | wearable, container |  |
| thieves_tools | Thieves' Tools | tool | |
| disguise_kit | Disguise Kit | tool | |
| healers_kit | Healer's Kit | tool | |
| torch | Torch | tool | |
| prayer_book | Prayer Book | tool |  |
| incense | Incense | tool |  |
| healers_kit | Healer's Kit | tool |  |
| smiths_tools | Smith's Tools | tool |  |
| spellbook | Spell Book | tool |  |
| pouch | Pouch | tool, container |  |
| sachel | Sachel | tool, container |  |
| notebook | Notebook | tool |  |
| instrument | Musical Instrument | tool |  |
| wand | Wand | tool |  |
