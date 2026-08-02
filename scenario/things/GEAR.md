# Gear

Mundane non-weapon, non-armor possessions — tools, trinkets, wearables, and
containers — as Thing templates. A character's IDENTITY references these by `id`
in the flat `## Equipment` list (e.g. `- thieves_tools`), optionally overriding
the display name for that character's instance (`- bracelet: Wooden vine-carved
bracelet`).

`affordances` declares capabilities (comma-separate several):
- `tool` — holdable, usable (`use the ...`); may `produce` another Thing
- `wearable` — occupies a body slot (`wear`/`remove`)
- `shield` — HAND-held (holdable), not worn; its AC comes from an `ac +N` effect

`effects` is the comma-separated grammar from CONSUMABLES.md (usually empty; a
ring or shield carries `ac +N`). Containers (packs, bags, chests) live in their
own catalog — see CONTAINERS.md.

| id | price | name | affordances | effects |
|----|-------|------|------|---------|
| shield | 10 gp | Shield | shield | ac +2 |
| bracelet |  | Bracelet | wearable | |
| ring | 5 gp | Ring | wearable | |
| amulet | 10 gp | Amulet | wearable | |
| cloak | 10 gp | Cloak | wearable | |
| holy_symbol | 5 gp | Holy Symbol | wearable | |
| talisman | 10 gp | Talisman | wearable | |
| thieves_tools | 25 gp | Thieves' Tools | tool | |
| disguise_kit | 25 gp | Disguise Kit | tool | |
| healers_kit | 5 gp | Healer's Kit | tool | |
| torch | 1 cp | Torch | tool | |
| prayer_book | 25 gp | Prayer Book | tool | |
| incense | 5 cp | Incense | tool | |
| smiths_tools | 20 gp | Smith's Tools | tool | |
| spellbook | 50 gp | Spell Book | tool | |
| notebook | 25 gp | Notebook | tool | |
| instrument | 30 gp | Musical Instrument | tool | |
| wand | 10 gp | Wand | tool | |
| rope | 1 gp | Hempen Rope (50 ft) | tool | |
| bedroll | 1 gp | Bedroll | tool | |
| tinderbox | 5 sp | Tinderbox | tool | |
| mess_kit | 2 sp | Mess Kit | tool | |
| candle | 1 cp | Candle | tool | |
| crowbar | 2 gp | Crowbar | tool | |
| hammer | 1 gp | Hammer | tool | |
| piton | 5 cp | Piton | tool | |
| lantern | 5 gp | Hooded Lantern | tool | |
| oil | 1 sp | Flask of Oil | tool | |
| ball_bearings | 1 gp | Ball Bearings | tool | |
| string | 1 cp | String (10 ft) | tool | |
| bell | 1 gp | Bell | tool | |
| book_of_lore | 25 gp | Book of Lore | tool | |
| ink | 10 gp | Ink (1 oz bottle) | tool | |
| ink_pen | 2 cp | Ink Pen | tool | |
| parchment | 1 sp | Parchment | tool | |
| bag_of_sand | 1 cp | Bag of Sand | tool | |
| small_knife | 2 sp | Small Knife | tool | |
| costume | 5 gp | Costume | wearable | |
| flint_steel | 5 sp | Flint & Steel | tool |  |
