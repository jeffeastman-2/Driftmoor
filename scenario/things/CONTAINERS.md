# Containers

Packs, bags, and chests — things whose job is to *hold other things*. They live
in their own catalog because their attributes diverge from plain gear:

- `contents` — a comma list of catalog ids with optional quantities
  (`torch x10, rations x10, rope`), expanded into the holder's possessions at
  load so the items are usable.
- `capacity` — free-text carry limit (e.g. `30 lb`); informational for now,
  the home for a future encumbrance check.

`kind` is usually `wearable, container` (a pack is worn on the back and holds
things) — or just `container` for a chest that isn't worn. Referenced by `id`
in a character's IDENTITY `## Equipment` list, same as any other Thing.

| id | name | kind | capacity | contents |
|----|------|------|----------|----------|
| explorers_pack | Explorer's Pack | wearable, container | 30 lb | torch x10, rations x10, rope, bedroll, tinderbox, mess_kit, water |
| burglars_pack | Burglar's Pack | wearable, container | 30 lb | ball_bearings, string, bell, candle x5, crowbar, hammer, piton x10, lantern, oil x2, rations x5, tinderbox, water, rope |
| gils_pack | Gil's Pack | wearable, container | 30 lb | string, gils_pouch, candle x5, lantern, oil x2, rations x5, tinderbox, mess_kit, water, thieves_tools, disguise_kit|
| scholars_pack | Scholar's Pack | wearable, container | 30 lb | book_of_lore, ink, ink_pen, parchment x10, bag_of_sand, small_knife |
| musicians_pack | Musician's Pack | wearable, container | 30 lb | bedroll, costume x2, candle x5, rations x5, water, disguise_kit |
| gils_pouch | Old leather pouch | container | 3 lb | |
| pouch | Pouch | wearable, container | 6 lb | |
| sachel | Satchel | wearable, container | 10 lb | |
| fennels_sachel | Fennel's Sachel | wearable, container | 2 lb | moonlace, mistwood_herbs x3, collection_vials x4, journal |
