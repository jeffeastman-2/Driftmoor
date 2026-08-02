# CONTENTS.md — The Gilded Trinket

## Practical Goods for Sale
| Item | Price | Notes |
|------|-------|-------|
| Iron Lock with Key | 15 gp | Sturdy |
| Lantern, Bullseye | 8 gp | Focused beam |
| Tinker's Tools (used) | 50 gp | Complete set |
| Spyglass | 100 gp | Excellent condition |
| Fishing Tackle | 1 gp | Simple but functional |

## Curios and Oddities
| Item | Price | Notes |
|------|-------|-------|
| Strange Stone Amulet | 25 gp | Hums faintly when held |
| Cracked Compass | 10 gp | Points somewhere other than north |
| Ornate Dagger | 35 gp | Inscription in unknown language |
| Porcelain Music Box | 20 gp | Haunting melody, slightly chipped |
| Mysterious Map Fragment | 15 gp | Island coastline, partial |

## Weapons and Armor
| Item | Price | Notes |
|------|-------|-------|
| Rusty Longsword | 12 gp | Needs polishing |
| Reinforced Buckler | 20 gp | Extra iron bands |
| War Pick | 25 gp | Excellent condition |
| Half-Plate Armor (used) | 375 gp | Battle-worn but reliable |

## Hidden / Locked
- Large safe (DC 18 Thieves' Tools): Tav's ledger, coin reserve, items not for sale
- **Obelisk Shard Ring** (received from villager, currently in the locked glass display case): A small obelisk shard fragment set into a tarnished silver ring. The villager who pawned it reported recurring nightmares and a growing compulsion to walk north toward the Shattered Obelisk after wearing it for weeks. The ring hums faintly — the glass case muffles but does not fully contain the sound. Tavian recognized the stone from his smuggling days and locked it away. He knows it is dangerous but also potentially very valuable. Not priced — he has not decided what to do with it.
- **Tav's medallion**: on his person, not in the shop

## Services
- Appraisal: 1 gp (may lowball to buy)
- Short-term loans: steep interest, forfeiture on late repayment
- Rare item search: 5 gp upfront, uses contacts

## Notes for DM
- The cracked compass and strange stone amulet are genuinely magical — Tav knows and is not telling
- The obelisk shard ring is tied to the central campaign MacGuffin — see `scenario/things/obelisk_shards.md` for full lore
- Characters with latent arcane ability may sense the shard's resonance even through the glass
- The mysterious map fragment shows part of the Drowned Isle coastline

---

## Runtime Containers

These containers are authoritative for stock placement and access.

| id | name | owner | access | affordances |
|---|---|---|---|---|
| merchant_stock | Merchant stock displays | tavian | public | container |

## Runtime Things

This table is the authoritative runtime inventory for this place.

| id | name | emoji | container | owner | price | category | affordances | availability | effect |
|---|---|---|---|---|---|---|---|---|---|
| iron_lock_with_key | Iron Lock with Key |  | merchant_stock | tavian | 15 gp | mundane | holdable | public | Sturdy, reliable |
| lantern_bullseye | Lantern, Bullseye |  | merchant_stock | tavian | 8 gp | mundane | holdable | public | Focused beam; useful for caves |
| tinker_s_tools_used | Tinker's Tools (used) |  | merchant_stock | tavian | 50 gp | mundane | holdable | public | Complete set, minor wear |
| spyglass | Spyglass |  | merchant_stock | tavian | 100 gp | mundane | holdable | public | Excellent condition |
| fishing_tackle | Fishing Tackle |  | merchant_stock | tavian | 1 gp | mundane | holdable | public | Simple, functional |
| mysterious_map_fragment | Mysterious Map Fragment |  | merchant_stock | tavian | 15 gp | mundane | holdable | public | Shows partial island coastline (Drowned Isle) |
| rusty_longsword | Rusty Longsword |  | merchant_stock | tavian | 12 gp | mundane | holdable | public | Serviceable; needs polishing; -1 to attack until cleaned (1 hour, DC 10 Maintenance) |
| reinforced_buckler | Reinforced Buckler |  | merchant_stock | tavian | 20 gp | mundane | holdable | public | Small shield with extra iron bands; +2 AC |
| war_pick | War Pick |  | merchant_stock | tavian | 25 gp | mundane | holdable | public | Excellent condition; 1d8 piercing, versatile |
| half_plate_armor_used | Half-Plate Armor (used) |  | merchant_stock | tavian | 375 gp | mundane | holdable | public | Battle-worn; AC 15; shows history |
| appraisal_gilded_trinket | Appraisal |  |  | tavian | 1 gp/item | service |  | public | May lowball to buy |
| short_term_loan | Short-term loan |  |  | tavian | Item as collateral | service |  | public | Steep interest; forfeiture if late |
| rare_item_search | Rare item search |  |  | tavian | 5 gp upfront | service |  | public | Uses contacts; days to weeks |
| strange_stone_amulet | Strange Stone Amulet |  | merchant_stock | tavian | 25 gp (as curio) | magical | holdable, wearable | public | Hums faintly when held. |
| cracked_compass | Cracked Compass |  | merchant_stock | tavian | 10 gp (as oddity) | magical | holdable | public | Points to something other than north — Tav claims it's magical. |
| ornate_dagger_gilded_trinket | Ornate Dagger (Gilded Trinket) |  | merchant_stock | tavian | 35 gp | magical | holdable | public | Beautifully crafted with an inscription in an unknown language. |
| porcelain_music_box | Porcelain Music Box |  | merchant_stock | tavian | 20 gp | magical | holdable | public | Plays a haunting melody when wound, slightly chipped. |

## Runtime Thing Details

### strange_stone_amulet

#### Advertised Properties

Hums faintly when held.

#### DM Properties

Hums more strongly within 60 ft of an obelisk shard — functions as a proximity detector (louder = closer) Created by the same civilization as the obelisk — predates Driftmoor by centuries Elyssa Moonglow will immediately recognize it as significant if she sees it (DC 10 for her; DC 17 Arcana for anyone else) Attunement not required for the proximity detection — it works for anyone holding it Extended attunement (1 week worn): the attuned user begins to perceive the obelisk's passive emanation as a directional sense — they always know which direction the nearest shard is

### cracked_compass

#### Advertised Properties

Points to something other than north — Tav claims it's magical.

#### DM Properties

Points toward the nearest concentration of the obelisk civilization's artifacts or structures Currently points roughly northeast — toward the Obelisk Reach, because the shattered obelisk is the largest concentration in the region If brought to the Drowned Isle (which has the altar), it will redirect — pointing toward whichever concentration is larger The crack appeared when the obelisk shattered — it was whole before that event Tav acquired it from an estate sale; the previous owner died at sea near the Drowned Isle

### ornate_dagger_gilded_trinket

#### Advertised Properties

Beautifully crafted with an inscription in an unknown language.

#### DM Properties

The inscription is in the same language as the obelisk base carvings Translated (DC 16 Arcana, or Elyssa with time): "Given in trust. Return in need." Not magical — but the inscription suggests it was a ceremonial object from the obelisk civilization, passed between individuals as a bond of obligation Worth 200 gp to Elyssa as a research artifact; Tav has no idea

### porcelain_music_box

#### Advertised Properties

Plays a haunting melody when wound, slightly chipped.

#### DM Properties

The melody it plays changes subtly depending on who winds it — it plays a variation of a tune significant to that person's past (DC 13 Insight to notice the melody is personalized) Non-harmful but deeply unsettling to some — Chaotic Neutral or darker characters may find it appealing; Lawful Good characters may find it disturbing Source of magic is unknown even to a thorough Arcana check — it simply is what it is The chip appeared recently; before that the melody was always the same
