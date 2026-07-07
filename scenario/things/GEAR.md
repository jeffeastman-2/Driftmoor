# Gear

Mundane non-weapon, non-armor possessions — tools, trinkets, wearables, and
containers — as Thing templates. A character's IDENTITY references these by `id`
in the flat `## Equipment` list (e.g. `- thieves_tools`), optionally overriding
the display name for that character's instance (`- bracelet: Wooden vine-carved
bracelet`).

`kind` drives the affordance (comma-separate several):
- `tool` — holdable, usable (`use the ...`); may `produce` another Thing
- `wearable` — occupies a body slot (`wear`/`remove`)
- `shield` — HAND-held (holdable), not worn; its AC comes from an `ac +N` effect

`effects` is the comma-separated grammar from CONSUMABLES.md (usually empty; a
ring or shield carries `ac +N`). Containers (packs, bags, chests) live in their
own catalog — see CONTAINERS.md.

| id | name | kind | effects |
|----|------|------|---------|
| shield | Shield | shield | ac +2 |
| bracelet | Bracelet | wearable | |
| ring | Ring | wearable | |
| amulet | Amulet | wearable | |
| cloak | Cloak | wearable | |
| holy_symbol | Holy Symbol | wearable | |
| talisman | Talisman | wearable | |
| thieves_tools | Thieves' Tools | tool | |
| disguise_kit | Disguise Kit | tool | |
| healers_kit | Healer's Kit | tool | |
| torch | Torch | tool | |
| prayer_book | Prayer Book | tool | |
| incense | Incense | tool | |
| smiths_tools | Smith's Tools | tool | |
| spellbook | Spell Book | tool | |
| notebook | Notebook | tool | |
| instrument | Musical Instrument | tool | |
| wand | Wand | tool | |
| rope | Hempen Rope (50 ft) | tool | |
| bedroll | Bedroll | tool | |
| tinderbox | Tinderbox | tool | |
| mess_kit | Mess Kit | tool | |
| candle | Candle | tool | |
| crowbar | Crowbar | tool | |
| hammer | Hammer | tool | |
| piton | Piton | tool | |
| lantern | Hooded Lantern | tool | |
| oil | Flask of Oil | tool | |
| ball_bearings | Ball Bearings | tool | |
| string | String (10 ft) | tool | |
| bell | Bell | tool | |
| book_of_lore | Book of Lore | tool | |
| ink | Ink (1 oz bottle) | tool | |
| ink_pen | Ink Pen | tool | |
| parchment | Parchment | tool | |
| bag_of_sand | Bag of Sand | tool | |
| small_knife | Small Knife | tool | |
| costume | Costume | wearable | |
| rope | Hempen Rope (50 ft) | tool | | |
| bedroll | Bedroll | tool | | |
| tinderbox | Tinderbox | tool | | |
| mess_kit | Mess Kit | tool | | |
| candle | Candle | tool | | |
| crowbar | Crowbar | tool | | |
| hammer | Hammer | tool | | |
| piton | Piton | tool | | |
| lantern | Hooded Lantern | tool | | |
| oil | Flask of Oil | tool | | |
| ball_bearings | Ball Bearings | tool | | |
| string | String (10 ft) | tool | | |
| bell | Bell | tool | | |
| book_of_lore | Book of Lore | tool | | |
| ink | Ink (1 oz bottle) | tool | | |
| ink_pen | Ink Pen | tool | | |
| parchment | Parchment | tool | | |
| bag_of_sand | Bag of Sand | tool | | |
| small_knife | Small Knife | tool | | |
| costume | Costume | wearable | | |
