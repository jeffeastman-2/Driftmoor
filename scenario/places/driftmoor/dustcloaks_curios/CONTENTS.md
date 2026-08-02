# CONTENTS.md — Dustcloak's Curios (General / Exterior)

## Items Present (Yard)
- Rusty tools (various, low value)
- Wagon wheels (2, usable)
- Broken furniture (chairs, a table missing a leg)
- Rickety wooden fence

## Notes for DM
- The yard items are genuine junk but Kelem knows exactly what is there
- Nothing of value in the yard — it is atmosphere, not inventory

## Backroom

### Mundane
- Repair and appraisal tools
- Transaction ledger (comprehensive, coded in places)

### Notable
- Several obelisk fragments on the central table
- Research notes in untidy scrawl surrounding the fragments
- A small locked box beneath the worktable (DC 13 Thieves' Tools)

The ledger can reveal Kelem's outside buyers and smuggling connection. The
locked box may contain buyer correspondence or a map of fragment locations.

## Shopfront Inventory

The shopfront catalog and prices are authoritative for ordinary play.

### Non-Magical Items for Sale
1. Shadowbeast Claw Necklace — 15 gp (+2 Intimidation when worn)
2. Bone Dice Set — 2 gp (useful for bluffing or cheating)
3. Silent Grease — 20 gp/vial (silences a 5-foot area when applied)
4. Weighted Dice — 5 gp (advantage on Sleight of Hand to cheat at dice)
5. Obsidian Mirror — 25 gp (peek around corners or signal in dim light)
6. Pouch of Glowing Powder — 10 gp (clings to surfaces; dim light for 1 hour)
7. Iron False Key — 5 gp (advantage on Thieves' Tools to jam locks)
8. Traveler's Cloak — 8 gp (weather protection and hidden compartment)
9. Smoke Bomb — 15 gp (10-foot smoke cloud for 1 minute)
10. Boot Blades — 20 gp (concealed 1d4 piercing weapon; finesse, light)
11. Weighted Net — 15 gp (+2 to attack rolls when thrown)
12. Obelisk Fragment Replica — 50 gp (convincing fake)

### Haggling
- DC 13 Charisma (Persuasion or Deception): 10–20% reduction
- Barter, bundles, and a 10 gp mystery bag are available

Kelem will claim the replica is sold out if a customer already possesses a
real shard. His magical collection is secured privately in the living loft and
is not part of the initial public catalog.

---

## Runtime Containers

These containers are authoritative for stock placement and access.

| id | name | owner | access | affordances |
|---|---|---|---|---|
| merchant_stock | Merchant stock displays | kelem | public | container |

## Runtime Things

This table is the authoritative runtime inventory for this place.

| id | name | emoji | container | owner | price | category | affordances | availability | effect |
|---|---|---|---|---|---|---|---|---|---|
| shadowbeast_claw_necklace | Shadowbeast Claw Necklace | 📿 | merchant_stock | kelem | 15 gp | mundane | holdable, wearable | public | +2 bonus to CHA (Intimidation) checks when worn |
| bone_dice_set | Bone Dice Set | 🎲 | merchant_stock | kelem | 2 gp | mundane | holdable | public | Useful for bluffing or cheating in games |
| silent_grease_vial | Silent Grease (vial) | 🧴 | merchant_stock | kelem | 20 gp | mundane | holdable | public | No sound when applied; covers 5-ft area; oils hinges, creates slippery surface |
| weighted_dice | Weighted Dice | 🎲 | merchant_stock | kelem | 5 gp | mundane | holdable | public | Advantage on Sleight of Hand to cheat at dice games |
| obsidian_mirror | Obsidian Mirror | 🪞 | merchant_stock | kelem | 25 gp | mundane | holdable | public | Peek around corners; signal allies in dim light |
| pouch_of_glowing_powder | Pouch of Glowing Powder | ✨ | merchant_stock | kelem | 10 gp | mundane | holdable | public | Clings to surfaces; emits dim light 1 hour; reveals invisible creatures it coats |
| iron_false_key | Iron False Key | 🗝️ | merchant_stock | kelem | 5 gp | mundane | holdable | public | Advantage on Thieves' Tools checks to jam or sabotage simple locks |
| traveler_s_cloak | Traveler's Cloak | 🧥 | merchant_stock | kelem | 8 gp | mundane | holdable, wearable | public | Weather protection; hidden compartment in lining; advantage on Sleight of Hand to hide small items |
| smoke_bomb | Smoke Bomb | 💨 | merchant_stock | kelem | 15 gp each | mundane | holdable | public | Smash to create 10-ft radius thick smoke cloud; lasts 1 minute; provides obscurement |
| boot_blades | Boot Blades | 🥾 | merchant_stock | kelem | 20 gp | mundane | holdable, wearable | public | Concealed retractable blades; 1d4 piercing, finesse, light |
| weighted_net | Weighted Net | 🕸️ | merchant_stock | kelem | 15 gp | mundane | holdable | public | As standard net but +2 to attack rolls when thrown |
| obelisk_fragment_replica | Obelisk Fragment Replica | 💎 | merchant_stock | kelem | 50 gp | mundane | holdable | public | Convincing fake; advantage on CHA (Deception) checks re: obelisk lore |
| bundling_discount | Bundling discount |  |  | kelem |  | service |  | public | Buy 3 smoke bombs, get 1 free; similar deals available |
| mystery_bag | Mystery Bag |  |  | kelem |  | service |  | public | 10 gp for a grab bag of random items (1d4 mundane items, DM selects) |
| barter | Barter |  |  | kelem |  | service |  | public | Accepts trade for other rare items; will overpay in trade for obelisk shards |
| obelisk_shards | Obelisk shards |  |  | kelem | 300 gp+ | service |  | public | Overpays; will not explain why |
| shadowbeast_parts | Shadowbeast parts |  |  | kelem | Varies | service |  | public | Claws: 3 gp each; blood: 15 gp/vial; pelts: 6 gp |
| unusual_artifacts | Unusual artifacts |  |  | kelem | Varies | service |  | public | He will assess; legitimate interest |
| stolen_goods | Stolen goods |  |  | kelem | Varies | service |  | public | He will not ask questions; price accordingly |
