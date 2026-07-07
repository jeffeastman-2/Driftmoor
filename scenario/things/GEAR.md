# Gear

Mundane non-weapon, non-armor possessions — tools, trinkets, wearables, and
containers — as Thing templates. A character's IDENTITY references these by `id`
in the flat `## Equipment` list (e.g. `- thieves_tools`), optionally overriding
the display name for that character's instance (`- bracelet: Wooden vine-carved
bracelet`).

`kind` drives the affordance (comma-separate several, e.g. `wearable, container`):
- `tool` — holdable, usable (`use the ...`); may `produce` another Thing
- `wearable` — occupies a body slot (`wear`/`remove`)
- `shield` — HAND-held (holdable), not worn; its AC comes from an `ac +N` effect
- `container` — can hold other Things (see `contents`)

`effects` is the comma-separated grammar from CONSUMABLES.md (usually empty; a
ring or shield carries `ac +N`). `contents` (containers only) is a comma list of
catalog ids with optional quantities — `torch x10, rations x10, rope` — expanded
into the holder's possessions at load so the items are usable.

| id | name | kind | effects | contents |
|----|------|------|---------|----------|
| shield | Shield | shield | ac +2 | |
| bracelet | Bracelet | wearable | | |
| ring | Ring | wearable | | |
| amulet | Amulet | wearable | | |
| cloak | Cloak | wearable | | |
| holy_symbol | Holy Symbol | wearable | | |
| talisman | Talisman | wearable | | |
| explorers_pack | Explorer's Pack | wearable, container | | torch x10, rations x10, rope, bedroll, tinderbox, mess_kit, water |
| burglars_pack | Burglar's Pack | wearable, container | | ball_bearings, string, bell, candle x5, crowbar, hammer, piton x10, lantern, oil x2, rations x5, tinderbox, water, rope |
| scholars_pack | Scholar's Pack | wearable, container | | book_of_lore, ink, ink_pen, parchment x10, bag_of_sand, small_knife |
| musicians_pack | Musician's Pack | wearable, container | | bedroll, costume x2, candle x5, rations x5, water, disguise_kit |
| thieves_tools | Thieves' Tools | tool | | |
| disguise_kit | Disguise Kit | tool | | |
| healers_kit | Healer's Kit | tool | | |
| torch | Torch | tool | | |
| prayer_book | Prayer Book | tool | | |
| incense | Incense | tool | | |
| smiths_tools | Smith's Tools | tool | | |
| spellbook | Spell Book | tool | | |
| pouch | Pouch | tool, container | | |
| sachel | Satchel | tool, container | | |
| notebook | Notebook | tool | | |
| instrument | Musical Instrument | tool | | |
| wand | Wand | tool | | |
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
