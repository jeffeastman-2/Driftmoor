#!/usr/bin/env python3
"""
Generate Things markdown files for the Driftmoor campaign.
Target: /Users/jeff/Python/Multi-LLM-Bridge/scenarios/DnD/things/
Run from anywhere: python3 generate_things.py
"""

import os

BASE_PATH = "/Users/jeff/Python/Multi-LLM-Bridge/scenarios/DnD/things"

files = {}

# ═════════════════════════════════════════════
# OBELISK SHARDS
# ═════════════════════════════════════════════

files["obelisk_shards.md"] = """\
# Obelisk Shards

## What They Are
Fragments of a once-towering stone spire — the Shattered Obelisk north of Driftmoor — that fractured in a magical event of unknown origin, likely decades ago. The dark stone is unlike any local rock formation. Each fragment retains a portion of the obelisk's original magical charge, which has been destabilizing since the shattering. The surface occasionally flickers with veins of glowing light. Holding a bare shard produces a low vibration felt in the palm and chest.

The shards are the campaign's central MacGuffin. Their individual properties are dangerous. What gathering them together might accomplish is unknown — and possibly catastrophic.

---

## Physical Properties
- Size range: thumbnail-sized chips to fragments the size of a fist; the embedded cliff fragments are much larger
- Color: dark, almost black stone with an iridescent quality in direct light
- Surface: smooth where fractured, rough where it was part of the original carved surface
- Weight: heavier than expected for their size
- Passive effect: a faint hum audible to anyone within 5 ft in silence; a low vibration felt on skin contact

---

## Magical Properties (Active)

### Standard Extractable Shard
*As sold by Kelem Dustcloak at 250 gp*

**Once per day (bonus action):** Channel the shard's power to deal an extra **1d6 necrotic damage** on the wielder's next melee or ranged weapon attack.

**Drawback:** Each use requires a **DC 12 Constitution saving throw**. On a failure, the wielder takes **1d6 psychic damage** and hears a faint whisper they cannot quite resolve into words.

**Passive accumulation:** A character who carries an uncontained shard for more than 24 hours must make a **DC 10 Wisdom saving throw** each subsequent dawn. On a failure, they feel a compulsion to keep the shard close and are reluctant to give it up (no mechanical effect yet — escalates with repeated failures).

---

## Containment
An uncontained shard is mildly hazardous to carry. Elyssa Moonglow uses a reinforced glass dome with chalk glyphs for her laboratory specimen. She can provide or describe:

- **Field containment:** A lead-lined pouch (Elyssa can provide one, cost 15 gp in materials) suppresses the passive hum and the dawn Wisdom save requirement
- **Laboratory containment:** Reinforced glass dome with chalk glyphs — full suppression of all passive effects, suitable for long-term study
- **No containment:** Passive effects active; other creatures within 10 ft at night may notice faint flickering light

---

## Known Shard Locations at Session Start

| Location | Description | Status |
|----------|-------------|--------|
| `places/driftmoor/elyssa_cottage/laboratory` | Full shard in reinforced dome | Present (until ransacking event) |
| `places/driftmoor/dustcloaks_curios/shopfront` | Standard extractable shard | For sale, 250 gp |
| `places/driftmoor/dustcloaks_curios/backroom` | Multiple fragments, various sizes | Kelem's research collection, not for sale |
| `places/obelisk_reach/shattered_obelisk` | Multiple cliff-embedded fragments | Extractable with tools, 10 min each |
| `places/obelisk_reach/echoing_caverns` | Large fragment embedded in cavern floor | Not removable without destroying surrounding stone |
| `places/azure_sea/drowned_isle` | Fragment embedded in altar stone | Not removable without destroying altar |

---

## Lore

### What Elyssa Knows
The obelisk predates any civilization currently documented in regional records. The symbols carved on its surface appear on cliff faces, cave walls, and — recently — on structures in Driftmoor itself, suggesting either active spread or a pre-existing pattern only now becoming visible. The shattering released contained energy that has been destabilizing the region ever since. The shadowbeasts appear to be drawn to or produced by this destabilization.

### What Kelem Knows (and Does Not Say)
Kelem's backroom notes suggest he believes the fragments can be recombined — not into the original obelisk, but into something new. His notes reference "the hunger beneath" (the same phrase partially translatable from the obelisk base inscription) without explanation. He values shards beyond their market price for reasons he has not disclosed.

### What the Inscriptions Say (Partial Translation)
The obelisk base inscription, partially translated by Elyssa (DC 16 Arcana/History for players; Elyssa can do it given time and rubbings):
- References a **binding** — something was being held in place
- References a **seal** — the obelisk was functional, not decorative
- References **"the hunger beneath"** — the entity or force being bound
- The Drowned Isle altar inscription is more complete and suggests the obelisk was one of **at least three** binding points in the region

### What Nobody Currently Knows
- The shattering was not an accident
- Gathering shards does not restore the binding — it accelerates the release of what was bound
- Kelem has been in contact with an outside party interested in exactly this outcome

---

## DM Escalation Notes
- Each shard the party carries increases the passive draw on shadowbeast attention (+1 to encounter frequency rolls per carried shard)
- Kelem's Wisdom save compulsion mechanic can be used to create party tension if multiple members carry shards
- The "hunger beneath" should remain unnamed and unseen for as long as possible — its nature is more frightening as an implication than as a revealed monster
- The Drowned Isle inscription is the pivot point — finding it should reframe the campaign from "monster problem" to "something was imprisoned here"
"""

# ═════════════════════════════════════════════
# SHADOWBEAST PARTS
# ═════════════════════════════════════════════

files["shadowbeast_parts.md"] = """\
# Shadowbeast Parts

## What Shadowbeasts Are
Creatures of shadow and dark energy connected to the shattered obelisk's destabilization. They are not natural animals and not undead — something in between, or something else entirely. Their physical form is partially substantial and partially shadow, which makes harvesting from them unusual: some parts solidify on death, others dissipate within minutes.

---

## Harvesting Rules

**Time window:** A shadowbeast's body begins dissipating 10 minutes after death. Harvesting must begin within this window.

**Skill check:** DC 12 Survival or Nature to harvest without damaging the parts. On a failure, the attempt yields half quantity or damaged goods (half value).

**Tools:** A sharp blade is sufficient. Lytha Varrow would prefer clean cuts — she will note sloppiness and adjust her payment accordingly.

**Aeliana Moonglade** succeeds on this check automatically due to her Outlander background and ranger training.

---

## Harvestable Parts

### Shadowbeast Pelt
**Harvest DC:** 12 (Survival or Nature)
**Yield:** 1 pelt per creature (if harvested within time window)
**Condition:** Fresh (within 1 hour) or cured

**Value:**
- To Lytha Varrow: 8 gp (fresh), 5 gp (cured)
- General market: 3 gp (decorative use, dye source)
- Kelem Dustcloak: 6 gp (for distilling Shadowbeast Pelt Dye — see mundane_items.md)

**Properties:**
- Absorbs some light — cloth dyed from it appears to drink in shadow
- Lytha uses it as a base material for the shadowbeast repellent poultice (requires pelt + fresh blood + Moonlace herb)
- Wilfred has a torn scrap of shadowbeast pelt at the tavern — proof of his sightings

---

### Shadowbeast Claws
**Harvest DC:** 10 (easier — claws are the most solid part)
**Yield:** 1d4+2 claws per creature
**Condition:** Remain solid indefinitely after death

**Value:**
- To Lytha Varrow: 2 gp per claw (component use)
- To Kelem Dustcloak: 3 gp per claw (for Shadowbeast Claw Necklace construction — see mundane_items.md)
- General market: 1 gp per claw (curiosity value)

**Properties:**
- Hard and cold to the touch, even in warm environments
- Retain a faint residual energy — DC 13 Arcana to detect
- Kelem's necklace grants +2 Intimidation because the energy is perceptible at a subconscious level

---

### Shadowbeast Blood
**Harvest DC:** 14 (blood partially dissipates — requires immediate collection)
**Yield:** 1 vial per creature (requires an empty vial, which must be on the party's person)
**Condition:** Fresh only — dissipates within 2 hours of collection; must be delivered to Lytha within this window or kept in a sealed alchemical vial (she can provide these for 2 gp each)

**Value:**
- To Lytha Varrow: 25 gp per vial (her priority purchase — needed for repellent research)
- No general market value — too unstable and dangerous for casual trade
- Kelem Dustcloak: 15 gp (interested but will not explain why)

**Properties:**
- Dark, almost black, slightly luminescent
- Corrosive to standard containers — requires glass or ceramic
- Lytha's repellent research: fresh blood + shadowbeast pelt + Moonlace herb = repellent potion (drives shadowbeasts away from a 30-ft area for 1 hour)
- Kelem's use: unknown

---

### Shadowbeast Eyes
**Harvest DC:** 16 (dissipate fastest — 5 minutes after death)
**Yield:** 2 eyes per creature
**Condition:** Fresh only — completely dissipate within 5 minutes; must be in alchemical preservative immediately (Lytha's sealed vials work)

**Value:**
- To Lytha Varrow: 20 gp per eye (rare component)
- To Elyssa Moonglow: 15 gp per eye (research specimen)
- No general market

**Properties:**
- Deep black with no visible iris or pupil — pure shadow
- In preservative, retain a faint visual property: looking into a preserved eye in darkness, one can sometimes see a dim image of where the shadowbeast was before it died (DC 14 Arcana to interpret; Elyssa can interpret reliably)
- Lytha's use: component for Potion of Shadow Sight (her own version, distinct from Kelem's stock)

---

## Lytha's Research Summary
Lytha Varrow's current research goals and what she needs:

| Research Goal | Parts Needed | Other Ingredients | Output |
|---------------|-------------|-------------------|--------|
| Shadowbeast Repellent | 1 fresh pelt + 1 vial fresh blood | Moonlace herb (from obelisk area) | Repellent potion — drives shadowbeasts from 30-ft area, 1 hour |
| Shadow Sight Potion | 2 preserved eyes | Glowcap spores + distilled starlight (rare) | Potion of Shadow Sight (her version, fewer side effects than Kelem's) |
| Pelt Dye (improved) | 2 fresh pelts | Mineral base | Improved Shadowbeast Pelt Dye — also grants advantage on Stealth in dim light |
| Antitoxin (shadow variant) | 1 vial fresh blood | Herbal poultice base | Grants advantage on saves vs. shadowbeast special abilities for 1 hour |

---

## DM Notes
- The 10-minute dissipation window creates urgency and decision-making after combat — reward players who think ahead and carry collection vials
- Lytha's payment rates make shadowbeast hunting economically viable as a side activity
- The eyes' retrospective vision property is a narrative tool — use it to show the party something they need to know about shadowbeast movement or behavior
- Kelem's interest in the blood should raise questions — he will not explain his use and will be slightly too casual about it
"""

# ═════════════════════════════════════════════
# MAGICAL ITEMS
# ═════════════════════════════════════════════

files["magical_items.md"] = """\
# Magical Items — DM Reference

## Overview
All magical items in the campaign, their true properties (including what vendors downplay or conceal), attunement requirements, and session-start locations. This file is the canonical DM reference. Player-facing descriptions may differ from what is listed here.

---

## Kelem Dustcloak's Inventory
*Location: `places/driftmoor/dustcloaks_curios/shopfront` (locked cabinet)*
*See also: `places/driftmoor/dustcloaks_curios/shopfront/CONTENTS.md`*

---

### Obelisk Shard (Unstable Fragment)
**Asking price:** 250 gp
**Attunement:** Not required
**Session-start location:** Dustcloak's shopfront (locked cabinet)

**Advertised properties:**
- Once/day bonus action: +1d6 necrotic on next attack
- Drawback: DC 12 CON save or take 1d6 psychic damage

**True properties (DM only):**
- The drawback whisper on a failed save is not random — it is a fragment of the entity bound beneath the obelisk, testing the carrier
- Repeated failed saves (3+) begin to produce specific whispered content: directions toward the obelisk, urgings to gather more shards
- Kelem knows this. He considers it a feature.
- See `obelisk_shards.md` for full lore and escalation mechanics

---

### Shadow Cloak
**Asking price:** 500 gp
**Attunement:** Required (1 hour in dim light or darkness)
**Session-start location:** Dustcloak's shopfront (locked cabinet)

**Advertised properties:**
- Advantage on Stealth in dim light or darkness
- Once/day reaction: impose disadvantage on one attack targeting wearer in dim light/darkness

**True properties (DM only):**
- Crafted from shadowbeast hide — attuning to it creates a subtle resonance with shadowbeasts
- After 1 week of attunement: shadowbeasts are 50% less likely to target the wearer as a primary target (they sense the resonance as kin)
- After 1 month: the wearer occasionally receives impressions — not thoughts, but feelings — of nearby shadowbeast presence (effective 60-ft passive detection in darkness)
- Kelem does not know these extended properties. He knows it is made from shadowbeast hide and suspects the resonance but has not tested it.

---

### Lantern of Revealing
**Asking price:** 400 gp
**Attunement:** Not required
**Session-start location:** Dustcloak's shopfront (locked cabinet)

**Advertised properties:**
- Reveals invisible creatures and objects in light radius (30-ft bright, 30-ft dim)
- Lasts 6 hours per pint of oil

**True properties (DM only):**
- Also reveals creatures of shadow that are not technically invisible but are partially phased — including shadowbeasts that have not yet fully manifested
- In the presence of an obelisk shard (within 30 ft), the lantern's light shifts slightly blue-white and the duration doubles
- Kelem claims it belonged to a famed hunter of invisible stalkers. This is true. The hunter died in the Echoing Caverns.

---

### Potion of Shadow Sight
**Asking price:** 100 gp per vial
**Attunement:** Not applicable (consumable)
**Session-start location:** Dustcloak's shopfront (locked cabinet, 3 vials)

**Advertised properties:**
- Darkvision 60 ft for 1 hour (or +30 ft if already has darkvision)
- Drawback: disadvantage on Perception in bright light for duration

**True properties (DM only):**
- The disadvantage in bright light is more severe than Kelem states — in direct sunlight, the drinker is effectively blinded for 1 round if they move from darkness into sunlight without closing their eyes first
- Brewed using shadowbeast eyes — the same retrovision property of the eyes (see `shadowbeast_parts.md`) is faintly present: the drinker occasionally perceives brief afterimages of where shadowbeasts have recently been in their field of vision
- Lytha Varrow could brew a version without the sunlight side effect given the right components

---

### Ring of Obfuscation
**Asking price:** 750 gp
**Attunement:** Required (worn for 24 hours)
**Session-start location:** Dustcloak's shopfront (locked cabinet)

**Advertised properties:**
- Cast Disguise Self once/day without spell slot
- Drawback: reflection slightly distorted while wearing

**True properties (DM only):**
- The distorted reflection is not a cosmetic quirk — it shows the wearer's true emotional state regardless of their Disguise Self appearance
- A creature that looks at the wearer's reflection in a mirror and makes a DC 14 Insight check perceives the emotional truth behind any deception the wearer is currently maintaining
- This makes it simultaneously useful (Disguise Self) and dangerous (reflections betray inner state)
- Kelem knows about the reflection property and uses it as a negotiating tool — he positions a mirror in his shopfront so he can observe customers' reflections

---

### Orb of Whispering Echoes
**Asking price:** 1,000 gp
**Attunement:** Required (meditate with orb for 1 hour)
**Session-start location:** Dustcloak's shopfront (locked cabinet)

**Advertised properties:**
- Once/day: cast Detect Thoughts
- Drawback: DC 13 WIS save or hear distracting whispers 1 hour (disadvantage on INT/WIS checks)

**True properties (DM only):**
- The whispers on a failed save are not random — they are fragments of thoughts the orb has previously absorbed from other users
- After 1 week of attunement: the attuned user can sometimes hear these echoed thoughts without using the active ability (passive, uncontrolled, DC 11 WIS save to suppress when unwanted)
- The orb was recovered from ruins connected to the same civilization that built the obelisk — Elyssa would pay 200 gp just to study it for a week, without purchasing it
- Kelem's claim that it came from a long-lost city is accurate

---

### Shadowbane Dagger
**Asking price:** 1,200 gp
**Attunement:** Required (spend a short rest with the dagger drawn)
**Session-start location:** Dustcloak's shopfront (locked cabinet)

**Advertised properties:**
- +1 to attack and damage rolls
- +1d4 radiant damage to shadow/darkness creatures
- Drawback: emits faint light when unsheathed (disadvantage on Stealth)

**True properties (DM only):**
- The faint light it emits is anathema to shadowbeasts specifically — they must make a DC 12 WIS save to willingly move within 10 ft of an unsheathed Shadowbane Dagger
- Forged by an order of clerics devoted to banishing shadow creatures — Father Elden Greybeard will recognize its origin if he sees it and become visibly affected (one of his lost companions in the Echoing Caverns carried one)
- The dagger's light brightens (to 10-ft bright, 10-ft dim) in the presence of a shadowbeast within 30 ft — functioning as an early warning system
- Kelem's dismissal of the clerics who made it ("speaks highly of its craftsmanship but lowly of its creators") is a tell — he dislikes what it represents

---

## The Gilded Trinket — Secretly Magical Items
*Location: `places/driftmoor/gilded_trinket`*
*Tav does not know these are magical. He suspects the compass and amulet but has not confirmed it.*

---

### Strange Stone Amulet
**Listed price:** 25 gp (as curio)
**True nature:** Magical
**Session-start location:** Gilded Trinket display case

**Advertised:** Hums faintly when held.

**True properties (DM only):**
- Hums more strongly within 60 ft of an obelisk shard — functions as a proximity detector (louder = closer)
- Created by the same civilization as the obelisk — predates Driftmoor by centuries
- Elyssa Moonglow will immediately recognize it as significant if she sees it (DC 10 for her; DC 17 Arcana for anyone else)
- Attunement not required for the proximity detection — it works for anyone holding it
- Extended attunement (1 week worn): the attuned user begins to perceive the obelisk's passive emanation as a directional sense — they always know which direction the nearest shard is

---

### Cracked Compass
**Listed price:** 10 gp (as oddity)
**True nature:** Magical
**Session-start location:** Gilded Trinket display case

**Advertised:** Points to something other than north — Tav claims it's magical.

**True properties (DM only):**
- Points toward the nearest concentration of the obelisk civilization's artifacts or structures
- Currently points roughly northeast — toward the Obelisk Reach, because the shattered obelisk is the largest concentration in the region
- If brought to the Drowned Isle (which has the altar), it will redirect — pointing toward whichever concentration is larger
- The crack appeared when the obelisk shattered — it was whole before that event
- Tav acquired it from an estate sale; the previous owner died at sea near the Drowned Isle

---

### Ornate Dagger (Gilded Trinket)
**Listed price:** 35 gp
**True nature:** Mundane (but significant)
**Session-start location:** Gilded Trinket display case

**Advertised:** Beautifully crafted with an inscription in an unknown language.

**True properties (DM only):**
- The inscription is in the same language as the obelisk base carvings
- Translated (DC 16 Arcana, or Elyssa with time): "Given in trust. Return in need."
- Not magical — but the inscription suggests it was a ceremonial object from the obelisk civilization, passed between individuals as a bond of obligation
- Worth 200 gp to Elyssa as a research artifact; Tav has no idea

---

### Porcelain Music Box
**Listed price:** 20 gp
**True nature:** Mildly magical
**Session-start location:** Gilded Trinket display case

**Advertised:** Plays a haunting melody when wound, slightly chipped.

**True properties (DM only):**
- The melody it plays changes subtly depending on who winds it — it plays a variation of a tune significant to that person's past (DC 13 Insight to notice the melody is personalized)
- Non-harmful but deeply unsettling to some — Chaotic Neutral or darker characters may find it appealing; Lawful Good characters may find it disturbing
- Source of magic is unknown even to a thorough Arcana check — it simply is what it is
- The chip appeared recently; before that the melody was always the same

---

## Elyssa Moonglow's Laboratory
*Location: `places/driftmoor/elyssa_cottage/laboratory`*

### Obelisk Shard (Contained Specimen)
**Not for sale**
**Session-start location:** Elyssa's laboratory (reinforced glass dome)
See `obelisk_shards.md` for full properties.

**DM note:** This is the shard stolen in the ransacking event. Its theft removes Elyssa's primary research specimen and triggers urgent need for party assistance.

---

## Items to Be Defined by DM Before Session

The following items are referenced in place/NPC files but deliberately left for DM determination:

| Item | Location | Reference |
|------|----------|-----------|
| Tess Malwin's hidden compartment contents | Broken Lantern storage room | `places/driftmoor/broken_lantern/storage_room/CONTENTS.md` |
| Suspicious guest's room contents | Broken Lantern upstairs | `places/driftmoor/broken_lantern/upstairs/CONTENTS.md` |
| Kelem's loft chest contents | Dustcloak's living loft | `places/driftmoor/dustcloaks_curios/living_loft/CONTENTS.md` |
| Kelem's locked box contents | Dustcloak's backroom | `places/driftmoor/dustcloaks_curios/backroom/CONTENTS.md` |
| Tav's mysterious medallion | On Tav's person | `people/npcs/tavian/IDENTITY.md` |
| The barnacle-covered chest contents | Drowned Isle | `places/azure_sea/drowned_isle/CONTENTS.md` |
| Watchtower hidden cache note | Old Watchtower | `places/mistwood_hills/old_watchtower/CONTENTS.md` |
| Aldren's portrait subject | Mayor's living quarters | `places/driftmoor/mayors_hall/living_quarters/CONTENTS.md` |

---

## DM Notes — Magical Item Distribution
- The party is level 1. The locked cabinet items are priced to be aspirational, not immediately accessible.
- The Gilded Trinket secretly magical items are the most accessible early finds — low price, no attunement required for core function.
- The Shadow Cloak's extended resonance properties and the Shadowbane Dagger's warning function are mid-campaign reveals — do not telegraph them early.
- The Ring of Obfuscation's mirror mechanic is most interesting if the party does not know about it — let them discover it through play.
- Elyssa will freely share the Lantern of Revealing with the party for the Echoing Caverns expedition if asked — she cannot go herself but wants the data.
"""

# ═════════════════════════════════════════════
# MUNDANE ITEMS
# ═════════════════════════════════════════════

files["mundane_items.md"] = """\
# Mundane Items — Master Reference

## Overview
Consolidated price list and item descriptions for all non-magical purchasable goods across Driftmoor. Cross-referenced to source locations. Prices are as listed by vendors; haggling rules apply where noted in individual NPC files.

---

## Salt & Iron Mercantile
*Proprietor: Jorgen Hallowtide*
*Location: `places/driftmoor/salt_and_iron`*
*Haggling: Not standard; Jorgen respects fair price. A good story may yield a small discount.*

### Common Goods
| Item | Price | Description |
|------|-------|-------------|
| Rope, hempen (50 ft) | 1 gp | Standard climbing and securing rope |
| Lantern, hooded | 5 gp | 30-ft radius light; shuttered for stealth |
| Climber's Kit | 25 gp | Pitons, gloves, harness |
| Waterskin | 2 gp | Holds 4 pints |
| Fishing Net | 4 gp | 5-ft net; can restrain small creatures |
| Barrel of Salt | 10 gp | Food preservation or wound treatment |
| Grain Sack (20 lbs) | 2 sp | Basic food supply |

### Adventurer Goods
| Item | Price | Description |
|------|-------|-------------|
| Dagger | 2 gp | 1d4 piercing, finesse, light, thrown |
| Shortsword | 10 gp | 1d6 piercing, finesse, light |
| Arrows (20) | 1 gp | Standard arrows |
| Tent, 2-person | 2 gp | Simple canvas shelter |
| Iron Spikes (10) | 1 gp | Securing ropes, barricading doors |
| Signal Whistle | 5 sp | Loud; alerts allies or startles animals |
| Map of Driftmoor and surroundings | 5 gp | Rough but accurate; shows key locations |

### Rare / Imported Goods
| Item | Price | Description |
|------|-------|-------------|
| Silk Rope (50 ft) | 10 gp | Stronger and lighter than hempen |
| Fine Wine (bottle) | 25 gp | Southern import; social lubricant |
| Small Spyglass | 100 gp | Distant objects viewed clearly |
| Exotic Spices (pouch) | 15 sp | High value among wealthy buyers |
| Folding Chair | 8 gp | Practical comfort; surprisingly rare |

### Services
| Service | Price | Notes |
|---------|-------|-------|
| Basic repairs (weapons, armor, tools) | 2-5 gp | Non-magical only |
| Appraisal | 1 gp/item | Approximate market value |
| Credit | Negotiated | Extended to trusted individuals only; failure to repay earns a bounty |

---

## The Bitter Remedy (Apothecary)
*Proprietor: Lytha Varrow*
*Location: `places/driftmoor/bitter_remedy`*
*Haggling: DC 14 CHA (Persuasion); Lytha responds better to bartered ingredients than coin reduction.*

| Item | Price | Effect |
|------|-------|--------|
| Healing Salve | 5 gp | Restores 1d4 HP when applied to wounds |
| Potion of Healing | 50 gp | Restores 2d4+2 HP |
| Antitoxin | 25 gp | Advantage on poison saving throws for 1 hour |
| Sleep Draught | 15 gp | Sleep 1d4 hours; DC 12 CON save to resist |
| Glowcap Spores (pouch) | 10 gp | Illuminates 5-ft radius for 1 hour when released; clings to surfaces |
| Herbal Poultices | 3 gp | Advantage on CON checks for illness recovery |
| Fire Oil | 25 gp | Coats weapons or functions as improvised explosive; 1d6 fire damage |
| Shadowbeast Pelt Dye | 10 gp | Stains clothing black; absorbs some light (minor stealth benefit at DM's discretion) |

### Lytha Buys
| Item | Price Paid | Condition Required |
|------|-----------|-------------------|
| Shadowbeast pelt | 8 gp (fresh) / 5 gp (cured) | See `shadowbeast_parts.md` |
| Shadowbeast blood (vial) | 25 gp | Fresh only (within 2 hours); alchemical vial required |
| Shadowbeast claws | 2 gp each | Any condition |
| Shadowbeast eyes | 20 gp each | Preserved in alchemical vial only |
| Moonlace herb (bunch) | 15 gp | Fresh from near obelisk |
| Unusual plants or monster parts | Varies | She will assess on sight |

### Custom Services
| Service | Cost | Time |
|---------|------|------|
| Custom remedy or potion | Ingredients + 10 gp labor | 1-2 days |
| Herbal knowledge consultation | 2 gp or a favor | Immediate |
| Monster part identification | 1 gp per part | Immediate |
| Alchemical collection vials (sealed) | 2 gp each | In stock |

---

## Ironhoof Forge
*Proprietors: Darrin Stonebrook (forge), Kara Stonebrook (stables)*
*Location: `places/driftmoor/ironhoof_forge`*
*Haggling: DC 13 CHA (Persuasion); Darrin respects quality work and may discount for demonstrated competence.*

### Forge Services and Goods
| Item / Service | Price | Notes |
|----------------|-------|-------|
| Horseshoes (set of 4) | 1 gp | Expertly crafted, durable |
| Weapon repairs | 2-5 gp | Based on damage severity |
| Tool repairs | 1 gp | Farming or adventuring tools |
| Arrowheads (20) | 2 gp | Steel tips, ready for fletching |
| Custom weapon order | Varies | Discuss with Darrin; 1d4 days |
| Custom armor order | Varies | Discuss with Darrin; 2d4 days |

### Stables Services and Goods
| Item / Service | Price | Notes |
|----------------|-------|-------|
| Horse boarding (1 week) | 5 gp | Feed and basic grooming included |
| Riding saddle | 10 gp | Sturdy leather |
| Cart rental | 10 gp/day | Basic transport |
| Wagon rental | 25 gp/day | Larger goods transport |
| Horse purchase | 75 gp | Healthy draft or riding horse |

---

## The Gilded Trinket (Pawnshop)
*Proprietor: Tavian "Tav" Drakescale*
*Location: `places/driftmoor/gilded_trinket`*
*Haggling: DC 14 CHA (Persuasion or Deception); Tav is a professional — he will not be easily moved.*
*Note: For secretly magical items in this inventory, see `magical_items.md`.*

### Practical Goods
| Item | Price | Notes |
|------|-------|-------|
| Iron Lock with Key | 15 gp | Sturdy, reliable |
| Lantern, Bullseye | 8 gp | Focused beam; useful for caves |
| Tinker's Tools (used) | 50 gp | Complete set, minor wear |
| Spyglass | 100 gp | Excellent condition |
| Fishing Tackle | 1 gp | Simple, functional |

### Curios and Oddities
| Item | Price | Notes |
|------|-------|-------|
| Strange Stone Amulet | 25 gp | *See magical_items.md — secretly magical* |
| Cracked Compass | 10 gp | *See magical_items.md — secretly magical* |
| Ornate Dagger | 35 gp | *See magical_items.md — significant inscription* |
| Porcelain Music Box | 20 gp | *See magical_items.md — mildly magical* |
| Mysterious Map Fragment | 15 gp | Shows partial island coastline (Drowned Isle) |

### Weapons and Armor
| Item | Price | Notes |
|------|-------|-------|
| Rusty Longsword | 12 gp | Serviceable; needs polishing; -1 to attack until cleaned (1 hour, DC 10 Maintenance) |
| Reinforced Buckler | 20 gp | Small shield with extra iron bands; +2 AC |
| War Pick | 25 gp | Excellent condition; 1d8 piercing, versatile |
| Half-Plate Armor (used) | 375 gp | Battle-worn; AC 15; shows history |

### Tav's Services
| Service | Price | Notes |
|---------|-------|-------|
| Appraisal | 1 gp/item | May lowball to buy |
| Short-term loan | Item as collateral | Steep interest; forfeiture if late |
| Rare item search | 5 gp upfront | Uses contacts; days to weeks |

### Tav Buys
- General goods at approximately 40% of listed value
- Unusual or rare items at his discretion — he may overpay for things that interest him
- He will not buy obelisk shards (he is aware of Kelem's interest and does not want the complication)

---

## Dustcloak's Curios
*Proprietor: Kelem Dustcloak*
*Location: `places/driftmoor/dustcloaks_curios`*
*Haggling: DC 13 CHA (Persuasion or Deception) for mundane items; DC 15 for magical. He enjoys the process.*
*For magical items, see `magical_items.md`.*

### Non-Magical Items for Sale
| Item | Price | Effect / Use |
|------|-------|-------------|
| Shadowbeast Claw Necklace | 15 gp | +2 bonus to CHA (Intimidation) checks when worn |
| Bone Dice Set | 2 gp | Useful for bluffing or cheating in games |
| Silent Grease (vial) | 20 gp | No sound when applied; covers 5-ft area; oils hinges, creates slippery surface |
| Weighted Dice | 5 gp | Advantage on Sleight of Hand to cheat at dice games |
| Obsidian Mirror | 25 gp | Peek around corners; signal allies in dim light |
| Pouch of Glowing Powder | 10 gp | Clings to surfaces; emits dim light 1 hour; reveals invisible creatures it coats |
| Iron False Key | 5 gp | Advantage on Thieves' Tools checks to jam or sabotage simple locks |
| Traveler's Cloak | 8 gp | Weather protection; hidden compartment in lining; advantage on Sleight of Hand to hide small items |
| Smoke Bomb | 15 gp each | Smash to create 10-ft radius thick smoke cloud; lasts 1 minute; provides obscurement |
| Boot Blades | 20 gp | Concealed retractable blades; 1d4 piercing, finesse, light |
| Weighted Net | 15 gp | As standard net but +2 to attack rolls when thrown |
| Obelisk Fragment Replica | 50 gp | Convincing fake; advantage on CHA (Deception) checks re: obelisk lore |

### Kelem's Special Deals
| Deal | Terms |
|------|-------|
| Bundling discount | Buy 3 smoke bombs, get 1 free; similar deals available |
| Mystery Bag | 10 gp for a grab bag of random items (1d4 mundane items, DM selects) |
| Barter | Accepts trade for other rare items; will overpay in trade for obelisk shards |

### Kelem Buys
| Item | Price Paid | Notes |
|------|-----------|-------|
| Obelisk shards | 300 gp+ | Overpays; will not explain why |
| Shadowbeast parts | Varies | Claws: 3 gp each; blood: 15 gp/vial; pelts: 6 gp |
| Unusual artifacts | Varies | He will assess; legitimate interest |
| Stolen goods | Varies | He will not ask questions; price accordingly |

---

## The Broken Lantern (Tavern)
*Proprietor: Tess Malwin*
*Location: `places/driftmoor/broken_lantern`*

### Food and Drink
| Item | Price |
|------|-------|
| Lamb Stew with bread | 2 sp |
| Roasted Fish with potatoes | 3 sp |
| Salted Pork with greens | 4 sp |
| Driftmoor Pie (seafood and vegetables) | 5 sp |
| Driftmoor Ale | 4 cp |
| Apple Cider | 6 cp |
| Fisherman's Delight (potent local spirit) | 1 sp |

### Lodging
| Option | Price |
|--------|-------|
| Private room (per night) | 5 sp |
| Shared room, 2 beds (per person) | 3 sp |
| Meeting room rental | A few silver; negotiable |

### Additional Services
| Service | Price |
|---------|-------|
| Bath | 2 sp |
| Laundry | 1 sp |

---

## The Weary Traveler (Rooming House)
*Proprietor: Martha Greaves*
*Location: `places/driftmoor/weary_traveler`*

| Item / Service | Price |
|----------------|-------|
| Basic room (per night) | 5 sp |
| Room with meals (per night) | 1 gp |
| Lamb Stew with bread | 2 sp |
| Fresh Baked Pie | 1 sp |
| Ale or Cider | 5 cp |
| Bath service | 2 sp |
| Laundry | 1 sp |
| Storage shed overflow (per night) | 2 sp |

---

## The Beacon Church
*Officiant: Father Elden Greybeard*
*Location: `places/driftmoor/beacon_church`*
*Payment is donation, not fee. Elden will not turn away those who cannot pay.*

| Service | Suggested Donation |
|---------|-------------------|
| Basic healing | 5 gp |
| Greater healing or curing disease | 25 gp |
| Blessing | Voluntary |
| Sanctuary | Free |
| Herbs and remedies from garden | Free or small donation |

---

## The Rusty Razor (Barbershop)
*Proprietor: Arlan Quickstep*
*Location: `places/driftmoor/rusty_razor`*

| Service / Item | Price |
|----------------|-------|
| Haircut | 5 sp |
| Shave | 2 sp |
| Pomade and grooming supplies | 1 gp |
| Old adventure map | Negotiable (sale or trade for a favor) |

---

## Simple Businesses — Basic Rates

### The Tannery (Boren Thatch)
| Item | Price |
|------|-------|
| Cured leather (per yard) | 5 sp |
| Leather scraps (bag) | 2 sp |
| Custom leather goods | 2-7 gp; 2-7 days |

### Carpenter's Workshop (Hilda Truebeam)
| Item | Price |
|------|-------|
| Standard furniture (chair, table) | 2-8 gp |
| Wagon repair | 5-15 gp |
| Custom orders | Varies; 3-10 days |

### The Fishmonger's Shack (Kessla Brinehook)
| Item | Price |
|------|-------|
| Fresh fish (per lb) | 2 cp |
| Salted fish (per lb) | 4 cp |
| Fishing tackle (simple) | 1 gp |
| Fish hooks (10) | 5 cp |

### The Weaver's Cottage (Eadric Spindle)
| Item | Price |
|------|-------|
| Sturdy cloth (per yard) | 3 sp |
| Simple garments | 5-8 sp |
| Heavy cloak | 1-2 gp |
| Custom work | Varies; 2-5 days |

### The Bakery (Maribel Crust)
| Item | Price |
|------|-------|
| Bread loaf | 2 cp |
| Meat pie | 5 cp |
| Sweet roll | 1 cp |
| Seasonal pastries | 3-6 cp |

### The Tailor's Shop (Vindra Goldneedle)
| Item | Price |
|------|-------|
| Simple repairs | 1-3 sp |
| Practical garments | 5 sp - 2 gp |
| Fine garments | 5-20 gp |
| Custom work | Varies; 3-7 days |

### The General Store (Jedrin Oakes)
| Item | Price |
|------|-------|
| Rope (50 ft) | 1 gp |
| Candles (10) | 5 cp |
| Preserved food (week's supply) | 5 sp |
| Basic tools (hammer, saw, etc.) | 2-5 sp each |

### The Cooper's Shed (Tomas Reed)
| Item | Price |
|------|-------|
| Standard barrel | 5 sp |
| Small cask | 3 sp |
| Crate (various sizes) | 1-3 sp |
| Custom orders | Varies; 1-3 days |

### The Cobbler's Shop (Marta Sole)
| Item | Price |
|------|-------|
| Boot repair | 2-8 sp |
| Standard boots | 1-2 gp |
| Custom footwear | 3-8 gp; 2-5 days |
| Beeswax polish | 2 cp |

### The Midwife's Home (Gran Lorie Wren)
| Item | Price |
|------|-------|
| Basic remedies and healing herbs | 1-5 sp |
| Medical consultation | Free |
| Emergency stabilization | Free |

---

## Currency Reference
| Coin | Abbreviation | Relative Value |
|------|-------------|---------------|
| Copper piece | cp | Base unit |
| Silver piece | sp | 10 cp |
| Gold piece | gp | 100 cp / 10 sp |
| Platinum piece | pp | 1,000 cp / 100 sp / 10 gp |

---

## DM Notes

### Price Consistency
These prices are internally consistent across all vendors. If the party attempts to arbitrage (buy cheap, sell elsewhere), apply common sense — Jorgen will not buy silk rope from the party at his own markup, and Kelem will not buy standard goods at all.

### Item Condition
The rusty longsword from the Gilded Trinket is the only item with a listed condition penalty. DM discretion applies to other used or damaged items the party acquires through play.

### Session Start Inventory
All listed items are assumed in stock at session start. As the session progresses, the monitor agent should track purchases and deplete inventory accordingly. Vendors do not have unlimited stock of rare or expensive items — a second spyglass, for instance, would require Jorgen to order one (1d4 weeks).

### Economy of the Region
Driftmoor is a small coastal town. 1 gp is a meaningful sum to most residents. The party's ability to spend freely on adventuring gear marks them as unusually wealthy by local standards, which should inform NPC reactions.
"""

# ═════════════════════════════════════════════
# WRITE FILES
# ═════════════════════════════════════════════

def write_files():
    created = []
    errors = []

    for relative_path, content in files.items():
        full_path = os.path.join(BASE_PATH, relative_path)
        dir_path = os.path.dirname(full_path)

        try:
            os.makedirs(dir_path, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            created.append(full_path)
        except Exception as e:
            errors.append((full_path, str(e)))

    print(f"\n✓ Written: {len(created)} files")
    for p in created:
        print(f"  {p}")

    if errors:
        print(f"\n✗ Errors: {len(errors)}")
        for p, e in errors:
            print(f"  {p}: {e}")

if __name__ == "__main__":
    write_files()
