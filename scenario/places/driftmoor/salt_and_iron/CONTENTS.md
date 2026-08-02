# CONTENTS.md — Salt & Iron Mercantile

## Common Items for Sale
| Item | Price | Notes |
|------|-------|-------|
| Rope (50 ft, hempen) | 1 gp | |
| Lantern (hooded) | 5 gp | 30-ft radius, can be shuttered |
| Climber's Kit | 25 gp | Pitons, gloves, harness |
| Waterskin | 2 gp | 4 pints |
| Fishing Net | 4 gp | 5-ft net |
| Barrel of Salt | 10 gp | Food preservation or wound treatment |
| Grain Sack (20 lbs) | 2 sp | |

## Adventurer Items
| Item | Price | Notes |
|------|-------|-------|
| Dagger | 2 gp | |
| Shortsword | 10 gp | |
| Arrows (20) | 1 gp | |
| Tent (2-person) | 2 gp | |
| Iron Spikes (10) | 1 gp | |
| Signal Whistle | 5 sp | |
| Map of Driftmoor and surroundings | 5 gp | Rough but useful |

## Rare / Imported Goods
| Item | Price | Notes |
|------|-------|-------|
| Silk Rope (50 ft) | 10 gp | Stronger and lighter |
| Fine Wine (bottle) | 25 gp | Southern import |
| Small Spyglass | 100 gp | |
| Exotic Spices (pouch) | 15 sp | |
| Folding Chair | 8 gp | |

## Services
- Basic repairs (non-magical weapons, armor, tools): 2-5 gp
- Appraisal of trade goods or treasure: 1 gp/item
- Credit extended to trusted individuals

## Notes for DM
- Jorgen will reward a genuinely interesting traveler's story with a small discount
- The Map of Driftmoor is a good early purchase for the party — worth pointing out

---

## Runtime Containers

These containers are authoritative for stock placement and access.

| id | name | owner | access | affordances |
|---|---|---|---|---|
| merchant_stock | Merchant stock displays | jorgen | public | container |

## Runtime Things

This table is the authoritative runtime inventory for this place.

| id | name | emoji | container | owner | price | category | affordances | availability | effect |
|---|---|---|---|---|---|---|---|---|---|
| rope_hempen_50_ft | Rope, hempen (50 ft) |  | merchant_stock | jorgen | 1 gp | mundane | holdable | public | Standard climbing and securing rope |
| lantern_hooded | Lantern, hooded |  | merchant_stock | jorgen | 5 gp | mundane | holdable | public | 30-ft radius light; shuttered for stealth |
| climber_s_kit | Climber's Kit |  | merchant_stock | jorgen | 25 gp | mundane | holdable | public | Pitons, gloves, harness |
| waterskin | Waterskin |  | merchant_stock | jorgen | 2 gp | mundane | holdable | public | Holds 4 pints |
| fishing_net | Fishing Net |  | merchant_stock | jorgen | 4 gp | mundane | holdable | public | 5-ft net; can restrain small creatures |
| barrel_of_salt | Barrel of Salt |  | merchant_stock | jorgen | 10 gp | mundane | holdable | public | Food preservation or wound treatment |
| grain_sack_20_lbs | Grain Sack (20 lbs) |  | merchant_stock | jorgen | 2 sp | mundane | holdable | public | Basic food supply |
| dagger | Dagger |  | merchant_stock | jorgen | 2 gp | mundane | holdable | public | 1d4 piercing, finesse, light, thrown |
| shortsword | Shortsword |  | merchant_stock | jorgen | 10 gp | mundane | holdable | public | 1d6 piercing, finesse, light |
| arrows_20 | Arrows (20) |  | merchant_stock | jorgen | 1 gp | mundane | holdable | public | Standard arrows |
| bolts_20 | Bolts (20) |  | merchant_stock | jorgen | 1 gp | mundane | holdable | public | Standard crossbow bolts |
| tent_2_person | Tent, 2-person |  | merchant_stock | jorgen | 2 gp | mundane | holdable | public | Simple canvas shelter |
| iron_spikes_10 | Iron Spikes (10) |  | merchant_stock | jorgen | 1 gp | mundane | holdable | public | Securing ropes, barricading doors |
| signal_whistle | Signal Whistle |  | merchant_stock | jorgen | 5 sp | mundane | holdable | public | Loud; alerts allies or startles animals |
| map_of_driftmoor_and_surroundings | Map of Driftmoor and surroundings |  | merchant_stock | jorgen | 5 gp | mundane | holdable | public | Rough but accurate; shows key locations |
| silk_rope_50_ft | Silk Rope (50 ft) |  | merchant_stock | jorgen | 10 gp | mundane | holdable | public | Stronger and lighter than hempen |
| fine_wine_bottle | Fine Wine (bottle) |  | merchant_stock | jorgen | 25 gp | mundane | consumable, drinkable, holdable | public | Southern import; social lubricant |
| small_spyglass | Small Spyglass |  | merchant_stock | jorgen | 100 gp | mundane | holdable | public | Distant objects viewed clearly |
| exotic_spices_pouch | Exotic Spices (pouch) |  | merchant_stock | jorgen | 15 sp | mundane | holdable | public | High value among wealthy buyers |
| folding_chair | Folding Chair |  | merchant_stock | jorgen | 8 gp | mundane | holdable | public | Practical comfort; surprisingly rare |
| basic_repairs_weapons_armor_tools | Basic repairs (weapons, armor, tools) |  |  | jorgen | 2-5 gp | service |  | public | Non-magical only |
| appraisal | Appraisal |  |  | jorgen | 1 gp/item | service |  | public | Approximate market value |
| credit | Credit |  |  | jorgen | Negotiated | service |  | public | Extended to trusted individuals only; failure to repay earns a bounty |
