# CONTENTS.md — Dustcloak's Living Loft

## Furnishings
- Narrow bed and rickety wardrobe
- Reinforced chest with multiple locks (DC 18 Thieves' Tools, or Kelem's keys)
- Locked cabinets containing Kelem's secured magical collection

## Secured Magical Collection
1. Obelisk Shard (Unstable Fragment) — 250 gp
2. Shadow Cloak — 500 gp
3. Lantern of Revealing — 400 gp
4. Potion of Shadow Sight — 100 gp/vial
5. Ring of Obfuscation — 750 gp
6. Orb of Whispering Echoes — 1,000 gp
7. Shadowbane Dagger — 1,200 gp

These objects may be offered selectively after trust, negotiation, or a
specific request. They are not advertised in the public shopfront catalog.
Their complete runtime properties are authored below.

---

## Runtime Containers

These containers are authoritative for stock placement and access.

| id | name | owner | access | affordances |
|---|---|---|---|---|
| locked_cabinet | Locked stock cabinet | kelem | selective, locked | container |

## Runtime Things

This table is the authoritative runtime inventory for this place.

| id | name | emoji | container | owner | price | category | affordances | availability | effect |
|---|---|---|---|---|---|---|---|---|---|
| obelisk_shard_unstable_fragment | Obelisk Shard (Unstable Fragment) |  | locked_cabinet | kelem | 250 gp | magical | holdable | selective | Once/day bonus action: +1d6 necrotic on next attack Drawback: DC 12 CON save or take 1d6 psychic damage |
| shadow_cloak | Shadow Cloak |  | locked_cabinet | kelem | 500 gp | magical | holdable, wearable | selective | Advantage on Stealth in dim light or darkness Once/day reaction: impose disadvantage on one attack targeting wearer in dim light/darkness |
| lantern_of_revealing | Lantern of Revealing |  | locked_cabinet | kelem | 400 gp | magical | holdable | selective | Reveals invisible creatures and objects in light radius (30-ft bright, 30-ft dim) Lasts 6 hours per pint of oil |
| potion_of_shadow_sight | Potion of Shadow Sight |  | locked_cabinet | kelem | 100 gp per vial | magical | holdable | selective | Darkvision 60 ft for 1 hour (or +30 ft if already has darkvision) Drawback: disadvantage on Perception in bright light for duration |
| ring_of_obfuscation | Ring of Obfuscation |  | locked_cabinet | kelem | 750 gp | magical | holdable, wearable | selective | Cast Disguise Self once/day without spell slot Drawback: reflection slightly distorted while wearing |
| orb_of_whispering_echoes | Orb of Whispering Echoes |  | locked_cabinet | kelem | 1,000 gp | magical | holdable | selective | Once/day: cast Detect Thoughts Drawback: DC 13 WIS save or hear distracting whispers 1 hour (disadvantage on INT/WIS checks) |
| shadowbane_dagger | Shadowbane Dagger |  | locked_cabinet | kelem | 1,200 gp | magical | holdable | selective | +1 to attack and damage rolls +1d4 radiant damage to shadow/darkness creatures Drawback: emits faint light when unsheathed (disadvantage on Stealth) |

## Runtime Thing Details

### obelisk_shard_unstable_fragment

**Attunement:** Not required

#### Advertised Properties

Once/day bonus action: +1d6 necrotic on next attack Drawback: DC 12 CON save or take 1d6 psychic damage

#### DM Properties

The drawback whisper on a failed save is not random — it is a fragment of the entity bound beneath the obelisk, testing the carrier Repeated failed saves (3+) begin to produce specific whispered content: directions toward the obelisk, urgings to gather more shards Kelem knows this. He considers it a feature. See `obelisk_shards.md` for full lore and escalation mechanics

### shadow_cloak

**Attunement:** Required (1 hour in dim light or darkness)

#### Advertised Properties

Advantage on Stealth in dim light or darkness Once/day reaction: impose disadvantage on one attack targeting wearer in dim light/darkness

#### DM Properties

Crafted from shadowbeast hide — attuning to it creates a subtle resonance with shadowbeasts After 1 week of attunement: shadowbeasts are 50% less likely to target the wearer as a primary target (they sense the resonance as kin) After 1 month: the wearer occasionally receives impressions — not thoughts, but feelings — of nearby shadowbeast presence (effective 60-ft passive detection in darkness) Kelem does not know these extended properties. He knows it is made from shadowbeast hide and suspects the resonance but has not tested it.

### lantern_of_revealing

**Attunement:** Not required

#### Advertised Properties

Reveals invisible creatures and objects in light radius (30-ft bright, 30-ft dim) Lasts 6 hours per pint of oil

#### DM Properties

Also reveals creatures of shadow that are not technically invisible but are partially phased — including shadowbeasts that have not yet fully manifested In the presence of an obelisk shard (within 30 ft), the lantern's light shifts slightly blue-white and the duration doubles Kelem claims it belonged to a famed hunter of invisible stalkers. This is true. The hunter died in the Echoing Caverns.

### potion_of_shadow_sight

**Attunement:** Not applicable (consumable)

#### Advertised Properties

Darkvision 60 ft for 1 hour (or +30 ft if already has darkvision) Drawback: disadvantage on Perception in bright light for duration

#### DM Properties

The disadvantage in bright light is more severe than Kelem states — in direct sunlight, the drinker is effectively blinded for 1 round if they move from darkness into sunlight without closing their eyes first Brewed using shadowbeast eyes — the same retrovision property of the eyes (see `shadowbeast_parts.md`) is faintly present: the drinker occasionally perceives brief afterimages of where shadowbeasts have recently been in their field of vision Lytha Varrow could brew a version without the sunlight side effect given the right components

### ring_of_obfuscation

**Attunement:** Required (worn for 24 hours)

#### Advertised Properties

Cast Disguise Self once/day without spell slot Drawback: reflection slightly distorted while wearing

#### DM Properties

The distorted reflection is not a cosmetic quirk — it shows the wearer's true emotional state regardless of their Disguise Self appearance A creature that looks at the wearer's reflection in a mirror and makes a DC 14 Insight check perceives the emotional truth behind any deception the wearer is currently maintaining This makes it simultaneously useful (Disguise Self) and dangerous (reflections betray inner state) Kelem knows about the reflection property and uses it as a negotiating tool — he positions a mirror in his shopfront so he can observe customers' reflections

### orb_of_whispering_echoes

**Attunement:** Required (meditate with orb for 1 hour)

#### Advertised Properties

Once/day: cast Detect Thoughts Drawback: DC 13 WIS save or hear distracting whispers 1 hour (disadvantage on INT/WIS checks)

#### DM Properties

The whispers on a failed save are not random — they are fragments of thoughts the orb has previously absorbed from other users After 1 week of attunement: the attuned user can sometimes hear these echoed thoughts without using the active ability (passive, uncontrolled, DC 11 WIS save to suppress when unwanted) The orb was recovered from ruins connected to the same civilization that built the obelisk — Elyssa would pay 200 gp just to study it for a week, without purchasing it Kelem's claim that it came from a long-lost city is accurate

### shadowbane_dagger

**Attunement:** Required (spend a short rest with the dagger drawn)

#### Advertised Properties

+1 to attack and damage rolls +1d4 radiant damage to shadow/darkness creatures Drawback: emits faint light when unsheathed (disadvantage on Stealth)

#### DM Properties

The faint light it emits is anathema to shadowbeasts specifically — they must make a DC 12 WIS save to willingly move within 10 ft of an unsheathed Shadowbane Dagger Forged by an order of clerics devoted to banishing shadow creatures — Father Elden Greybeard will recognize its origin if he sees it and become visibly affected (one of his lost companions in the Echoing Caverns carried one) The dagger's light brightens (to 10-ft bright, 10-ft dim) in the presence of a shadowbeast within 30 ft — functioning as an early warning system Kelem's dismissal of the clerics who made it ("speaks highly of its craftsmanship but lowly of its creators") is a tell — he dislikes what it represents
