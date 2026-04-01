#!/usr/bin/env python3
"""
Generate PLACE.md and CONTENTS.md files for all Driftmoor locations.
Target: /Users/jeff/Python/Multi-LLM-Bridge/scenarios/DnD/places/
Run from anywhere: python3 generate_places.py
"""

import os

BASE_PATH = "/Users/jeff/Python/Multi-LLM-Bridge/scenarios/DnD/places"

files = {}

# ═════════════════════════════════════════════
# TOP LEVEL — The Land Around Driftmoor
# ═════════════════════════════════════════════

files["PLACE.md"] = """\
# PLACE.md — The Land Around Driftmoor

## Description and Atmosphere
A rocky coastal region where windswept plains meet jagged cliffs and cold grey sea. The Greywater River cuts through the land from the Mistwood Hills in the northeast down to the harbor at Driftmoor. The landscape is beautiful in a harsh way — isolation is its defining quality. Distances between settlements feel longer than they are. The sky is big and often threatening.

In recent months something has shifted. Animals behave strangely near the river banks. Farmers report livestock disappearing. Fisherfolk avoid certain waters after dark. The shadowbeasts are the visible symptom. The shattered obelisk to the north is the cause that nobody wants to examine too closely.

## Sub-Places
- `driftmoor/` — the town, population ~500, the heart of the region
- `obelisk_reach/` — jagged cliffs and plateaus north of town, source of the trouble
- `greywater_river/` — river corridor from Mistwood Hills to the harbor
- `mistwood_hills/` — fog-laden forested hills to the northeast
- `azure_sea/` — cold rocky coastline, Driftmoor's harbor, offshore features
- `plains_of_stonehearth/` — windswept grasslands southeast of town

## Who Is Normally Here
- Farmers moving goods between fields and town
- Fisherfolk on the coast and river
- The occasional traveling merchant
- Shadowbeasts, increasingly, after dark

## Connections
- The road north leads to the Obelisk Reach
- The river road northeast follows the Greywater toward the Mistwood Hills and Old Mill
- The coastal path south skirts the Plains of Stonehearth
- No major city within easy travel — Driftmoor is genuinely isolated

## Dynamic State
*(Updated by monitor agent)*

- **Current threat level:** Elevated — shadowbeast sightings increasing across all sub-regions
- **Weather:** Coastal, changeable — storms roll in from the Azure Sea with little warning
- **Recent events:** None yet — session not started
- **Active conditions:** None established
"""

files["CONTENTS.md"] = """\
# CONTENTS.md — The Land Around Driftmoor (Regional)

## Creatures and Threats

### Shadowbeasts
The primary regional threat. Creatures of shadow and dark energy, apparently connected to the shattered obelisk. Increasing in number and range.
- **Sighting locations:** Plains of Stonehearth (livestock predation), Greywater River banks, Obelisk Reach cliffs
- **Behavior:** Nocturnal, predatory, seemingly drawn to magical energy
- **Known weakness:** Light — radiant damage, bright light sources
- **Value:** Fresh shadowbeast blood useful to Lytha Varrow for repellent research

### Regional Wildlife (non-hostile baseline)
- Wolves (Mistwood Hills and plains)
- Giant crabs (coastal rocks)
- Trout, otters, kingfishers (Greywater River)
- Sheep and goats (Plains of Stonehearth, farmed)

## Environmental Hazards
- Coastal storms: fast-moving, heavy rain, dangerous travel conditions
- Obelisk Reach cliffs: crumbling edges, slippery surfaces, narrow paths
- Sea stacks: treacherous approach by water
- Mistwood Hills: paths that seem to vanish, disorientation reported by hunters

## Notes for DM
- Shadowbeast encounters should escalate in frequency as the session progresses
- Weather can be used as pacing tool — storms isolate locations and raise tension
- Regional wildlife behaves abnormally near obelisk fragment locations
"""

# ═════════════════════════════════════════════
# DRIFTMOOR TOWN
# ═════════════════════════════════════════════

files["driftmoor/PLACE.md"] = """\
# PLACE.md — Driftmoor Town

## Description and Atmosphere
A small coastal town of roughly 500 souls — mostly humans, with a scattering of halflings, dwarves, and elves. Perched where the Greywater River meets the Azure Sea, hemmed in by cliffs and windswept plains. The buildings are timber and stone, built to last against coastal weather. Nothing is ornate. Everything is functional.

The town has a self-contained quality — people here know each other's business and are suspicious of outsiders, not from hostility but from long practice. The harbor smells of fish and salt. The village center smells of woodsmoke and bread. At night the church lantern burns on the hill.

Something is wrong and most people know it without being able to say what.

## Sub-Places
- `mayors_hall/` — governance, records, Aldren Thorne
- `broken_lantern/` — the tavern, social hub, Tess Malwin
- `dustcloaks_curios/` — antiquities shop, Kelem Dustcloak
- `salt_and_iron/` — mercantile, Jorgen Hallowtide
- `bitter_remedy/` — apothecary, Lytha Varrow
- `beacon_church/` — church of Pelor, Father Elden Greybeard
- `ironhoof_forge/` — blacksmith and stables, Darrin and Kara Stonebrook
- `gilded_trinket/` — pawnshop, Tavian Drakescale
- `rusty_razor/` — barbershop, Arlan Quickstep
- `weary_traveler/` — rooming house, Martha Greaves
- `elyssa_cottage/` — scholar's residence, Elyssa Moonglow
- `tannery/` — Boren Thatch
- `carpenters_workshop/` — Hilda Truebeam
- `fishmongers_shack/` — Kessla Brinehook
- `weavers_cottage/` — Eadric Spindle
- `bakery/` — Maribel Crust
- `tailors_shop/` — Vindra Goldneedle
- `general_store/` — Jedrin Oakes
- `schoolhouse/` — Alina Finch
- `coopers_shed/` — Tomas Reed
- `midwifes_home/` — Gran Lorie Wren
- `watchtower/` — Darwin Cragg
- `cobblers_shop/` — Marta Sole

## Districts
- **Harbor District:** Piers, fishing boats, fisherfolk homes, fishmonger's shack, cooper's shed
- **Village Center:** Mayor's hall, tavern, mercantile, apothecary, barbershop, church on the hill
- **Outskirts:** Dustcloak's Curios (near Mistwood edge), Ironhoof Forge (road entrance), Elyssa's cottage (above river)

## Who Is Normally Here
Full NPC roster — see `people/npcs/` for individual files.
Population goes about its business: fishing, farming, trading, gossiping.

## Connections
- Road north → Obelisk Reach
- River road northeast → Greywater River, Old Mill, Mistwood Hills
- Coastal path → Azure Sea coastline, Plains of Stonehearth
- Harbor → Azure Sea trade routes (infrequent)

## Dynamic State
*(Updated by monitor agent)*

- **Current mood:** Uneasy. Rumors of shadowbeasts, missing people, strange lights
- **Recent events:** None yet — session not started
- **Active conditions:** None established
"""

files["driftmoor/CONTENTS.md"] = """\
# CONTENTS.md — Driftmoor Town (General)

## Public Resources
- Town well (village center)
- Public notice board near mayor's hall — bounties, missing persons, town announcements
- Harbor piers — fishing boats, occasional trade vessel

## Town-Level Items of Note
- Driftmoor's crest: fish and sheaf of grain crossed beneath a rising sun (appears on mayor's hall doors, town banner)
- The cracked, rusted lantern above The Broken Lantern tavern entrance — original, never replaced
- The church lantern on the hill — lit nightly, recently flickering with dark light

## Creatures
- No monsters within town proper (yet)
- Stray cats near the harbor
- Horses at Ironhoof Forge stables

## Notes for DM
- The notice board is a useful session tool — post bounties, missing person notices, or warnings as needed
- The church lantern's dark flickering is visible from anywhere in town at night
- Harbor has shadowy shapes beneath the water that fisherfolk avoid discussing
"""

# ─────────────────────────────────────────────
# MAYOR'S HALL
# ─────────────────────────────────────────────

files["driftmoor/mayors_hall/PLACE.md"] = """\
# PLACE.md — The Mayor's Hall

## Description and Atmosphere
The largest and most prominent building in Driftmoor — two stories of timber and stone built to withstand coastal weather and project quiet authority. Situated near the village square. Practical in design with small touches of civic pride: carved wooden trim along the eaves, a tended flower bed outside, the town crest on the double oak doors.

Inside it smells of old paper, woodsmoke, and the faint whiskey the mayor keeps in his office.

## Sub-Places
- `mayors_office/` — Aldren Thorne's working space
- `records_room/` — locked, town documents and historical ledgers
- `living_quarters/` — Aldren's modest upstairs suite
- Main Hall (covered in this file — no sub-directory needed)

## Main Hall
The heart of the building. Rows of simple wooden benches face a raised dais with a long table and high-backed chair. Walls adorned with maps of the surrounding region, fishing nets, and framed sketches of early Driftmoor. A weathered bronze bell near the back — used to call meetings or sound alarms.

## Exterior
- Wide double doors of dark oak, iron-banded, carved with Driftmoor's crest
- Flagpole with faded town banner
- Stone steps flanked by lanterns lit each evening

## Who Is Normally Here
- **Aldren Thorne** — mayor, usually in his office during the day
- **Elise Harper** — sharp-eyed clerk, manages the records room

## Connections
- Village square (outside)
- `mayors_office/` (left of main hall)
- `records_room/` (behind the office, locked)
- `living_quarters/` (upstairs)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Aldren Thorne (office), Elise Harper (records area)
- **Recent events:** None yet — session not started
- **Active conditions:** Records room ledger missing
"""

files["driftmoor/mayors_hall/CONTENTS.md"] = """\
# CONTENTS.md — The Mayor's Hall (Main Hall)

## Items Present

### Mundane
- Rows of simple wooden benches
- Long table and high-backed chair on raised dais
- Maps of the surrounding region (general, not detailed)
- Fishing nets (decorative)
- Framed sketches of early Driftmoor

### Notable
- Weathered bronze bell — functional alarm and meeting bell
- Town crest carving on the main doors

## Creatures
- None normally

## Notes for DM
- The bronze bell can be used as an alarm — ringing it will bring townsfolk
- The regional maps on the walls are rough but could orient players early in the session
"""

files["driftmoor/mayors_hall/mayors_office/PLACE.md"] = """\
# PLACE.md — Mayor's Office

## Description and Atmosphere
A smaller room to the left of the main hall. Cluttered in a way that suggests a busy man rather than a disorganized one — piles of papers, ledgers, and correspondence that Aldren knows the location of precisely. A large desk dominates the room. A window looks out toward the harbor.

Smells of paper, ink, and the whiskey kept discreetly in one corner.

## Who Is Normally Here
- **Aldren Thorne** — during working hours

## Connections
- Main hall (through door)
- `records_room/` (through rear door, locked from records side)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupant:** Aldren Thorne
- **Recent events:** None yet — session not started
- **Active conditions:** None
"""

files["driftmoor/mayors_hall/mayors_office/CONTENTS.md"] = """\
# CONTENTS.md — Mayor's Office

## Items Present

### Mundane
- Large desk
- Piles of papers, ledgers, correspondence
- Shelf of dusty legal texts
- Small collection of historical curios from Driftmoor's past
- Pair of glasses

### Notable
- Bottle of whiskey (tucked discreetly, not hidden)
- Current town correspondence — supply requests, farmer complaints, trade inquiries
- Aldren's personal notes on the shadowbeast situation (guarded, not for sharing)

## Notes for DM
- A successful Perception or Investigation check on the desk reveals Aldren's private notes on the shadowbeast escalation — more alarmed than his public manner suggests
- The legal texts are genuine but contain nothing plot-relevant unless DM decides otherwise
"""

files["driftmoor/mayors_hall/records_room/PLACE.md"] = """\
# PLACE.md — Records Room

## Description and Atmosphere
A small locked room behind the mayor's office. Meticulously organized — Elise Harper's work. Shelves of bound documents, property deeds, local laws, historical town records going back generations. The room smells of old paper and dust. A single lamp on the central table.

Locked from the inside when unoccupied. Elise Harper holds one key; Aldren holds the other.

## Who Is Normally Here
- **Elise Harper** — clerk, during working hours
- Otherwise locked and empty

## Connections
- Mayor's office (through locked door)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupant:** Elise Harper (working hours) / empty (otherwise)
- **Recent events:** The old town ledger referencing obelisk incidents is missing
- **Active conditions:** Missing ledger — unknown who took it or when
"""

files["driftmoor/mayors_hall/records_room/CONTENTS.md"] = """\
# CONTENTS.md — Records Room

## Items Present

### Mundane
- Bound volumes of town records (property deeds, local laws, census records)
- Correspondence files organized by year
- Lamp and writing materials on central table

### Notable
- Historical ledgers going back generations — most mundane, some contain references to unusual regional events
- **MISSING:** Old town ledger referencing strange incidents near the obelisk decades ago — removed by unknown party

### Locked / Hidden
- The room itself is locked (requires key or DC 15 Thieves' Tools)
- One ledger on the bottom shelf, spine unmarked, contains the earliest recorded sighting of the obelisk in town memory — not the missing one, but relevant

## Notes for DM
- The missing ledger is the primary plot item here — its absence is the hook
- The unmarked ledger on the bottom shelf is a secondary find requiring a DC 12 Investigation check
- Elise Harper will not leave the party alone in this room under any circumstances
"""

files["driftmoor/mayors_hall/living_quarters/PLACE.md"] = """\
# PLACE.md — Mayor's Living Quarters

## Description and Atmosphere
Aldren's modest upstairs suite. Sparse and functional — the quarters of a man who does not place much value on comfort for its own sake. A sturdy bed, a small writing desk, a trunk. One window facing the harbor. It lacks any real signs of luxury, which is either admirable or telling depending on your view of the man.

## Who Is Normally Here
- **Aldren Thorne** — sleeping hours, occasionally for private writing

## Connections
- Upstairs landing (staircase from main hall)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupant:** Empty during working hours
- **Recent events:** None
- **Active conditions:** None
"""

files["driftmoor/mayors_hall/living_quarters/CONTENTS.md"] = """\
# CONTENTS.md — Mayor's Living Quarters

## Items Present

### Mundane
- Sturdy bed
- Small writing desk with personal correspondence
- Trunk (personal belongings — clothing, documents)

### Notable
- Personal journal — private thoughts on the town's situation, more candid than anything in the office
- A small portrait of a woman — no label (DM's discretion on identity)

### Locked
- Trunk: simple lock (DC 10 Thieves' Tools or key on Aldren's person)

## Notes for DM
- The personal journal is the most candid source of Aldren's actual fears about the obelisk situation
- The portrait is deliberately unexplained — available as a character hook if desired
"""

# ─────────────────────────────────────────────
# THE BROKEN LANTERN
# ─────────────────────────────────────────────

files["driftmoor/broken_lantern/PLACE.md"] = """\
# PLACE.md — The Broken Lantern

## Description and Atmosphere
Driftmoor's only tavern and its social heart. A weathered timber structure with a sloping roof and ivy up one side. The cracked, rusted lantern above the door belonged to the founder and has never been replaced. Inside: warm, slightly shabby, full of competing smells — woodfire, roasted meat, ale, and something faintly briny from the harbor crowd.

The kind of place where everyone knows everyone, which means strangers are noticed immediately and assessed within minutes.

## Sub-Places
- `main_room/` — the public tavern space
- `upstairs/` — three guest rooms
- `storage_room/` — bar supplies, discreet meetings, hidden compartment
- `meeting_room/` — private room behind the kitchen, rentable

## Exterior
Weathered timber, sloping roof, ivy on one side. Faded sign depicting a broken lantern spilling light. Smoke from the chimney.

## Who Is Normally Here
- **Tess Malwin** — owner, behind the bar or moving through the room
- **Wilfred** — regular drunkard, claims to have seen shadow giants near the obelisk
- Fisherfolk, farmers, occasional travelers

## Connections
- Village center (outside)
- `main_room/` → `upstairs/` via creaky staircase
- `main_room/` → `storage_room/` and `meeting_room/` via door behind bar

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Tess Malwin, Wilfred, evening crowd
- **Recent events:** None yet — session not started
- **Active conditions:** Suspicious travelers in meeting room; strange noises reported from upstairs
"""

files["driftmoor/broken_lantern/CONTENTS.md"] = """\
# CONTENTS.md — The Broken Lantern (General)

## Items Present

### Mundane
- Cracked rusted lantern above the entrance (original, never replaced)
- Faded sign

## Creatures
- None

## Notes for DM
- The lantern is a landmark and a symbol — if it were ever destroyed or removed, the town would notice
"""

files["driftmoor/broken_lantern/main_room/PLACE.md"] = """\
# PLACE.md — The Broken Lantern: Main Room

## Description and Atmosphere
Large open space, sturdy wooden tables and mismatched chairs. The hearth on the far wall radiates heat, its mantle cluttered with fishing trophies, seashells, and faded maps. A long polished bar runs along one side, shelves behind it holding bottles, casks, and jars of questionable concoctions. A small raised stage platform in one corner, currently stacked with empty crates. A few shadowy booths along the walls for those who want privacy.

Noisy in the evenings. The kind of noise that covers private conversation if you choose the right booth.

## Who Is Normally Here
- **Tess Malwin** — behind the bar
- **Wilfred** — at his usual table, nursing ale
- Fisherfolk, farmers, occasional travelers in the evenings
- The party, when in town

## Connections
- Entrance (outside)
- Upstairs via creaky staircase
- Behind the bar: storage room and meeting room

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Tess, Wilfred, evening regulars
- **Recent events:** None yet — session not started
- **Active conditions:** None
"""

files["driftmoor/broken_lantern/main_room/CONTENTS.md"] = """\
# CONTENTS.md — Main Room

## Items Present

### Mundane
- Mismatched tables and chairs
- Hearth with fishing trophies, seashells, faded maps on mantle
- Bar with assorted bottles and casks
- Empty crates on stage platform

### Food and Drink Available
- Lamb stew with bread: 2 sp
- Roasted fish with potatoes: 3 sp
- Salted pork with greens: 4 sp
- Driftmoor Pie (seafood and vegetables): 5 sp
- Driftmoor Ale: 4 cp
- Apple Cider: 6 cp
- Fisherman's Delight (potent local spirit): 1 sp

## Notes for DM
- Wilfred has a torn scrap of shadowbeast pelt he will show the party if they engage him
- The faded maps on the mantle are decorative but one shows an older coastline with features no longer marked on current maps
"""

files["driftmoor/broken_lantern/upstairs/PLACE.md"] = """\
# PLACE.md — The Broken Lantern: Upstairs Rooms

## Description and Atmosphere
A creaky staircase leads to a small hallway with three guest rooms. Plain but functional. Each room has a sturdy wooden bed with straw mattress, a small writing desk, and a simple washbasin. Shuttered windows let in sea air and the distant sound of waves. Simple but serviceable locks on the doors.

Tess warns guests to keep valuables on them. This is not idle advice.

## Who Is Normally Here
- Paying guests
- Currently: a suspicious long-term guest (see adventure hooks)

## Connections
- Main room (via creaky staircase)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Suspicious long-term guest (one room), two rooms available
- **Recent events:** Strange sounds reported — scraping, whispers, thuds from unoccupied room
- **Active conditions:** One guest missing (left for Obelisk Reach, not returned); cryptic charcoal note in their room
"""

files["driftmoor/broken_lantern/upstairs/CONTENTS.md"] = """\
# CONTENTS.md — Upstairs Rooms

## Items Present

### Per Room (standard)
- Wooden bed, straw mattress
- Small writing desk
- Washbasin
- Simple lock (DC 8 Thieves' Tools)

### Notable (missing guest's room)
- Journal with cryptic entries about shadowy figures near the Obelisk Reach
- Cryptic note scrawled in charcoal mentioning the obelisk
- Personal belongings left behind — clothing, travel pack (no coin)

### Notable (suspicious guest's room — locked)
- Strange deliveries received late at night
- Contents of room unknown without access (DC 12 Thieves' Tools or Tess's key)

## Rates
- Private room: 5 sp per night
- Shared room (2 beds): 3 sp per person

## Notes for DM
- The missing guest's journal is the primary item of interest — contents at DM's discretion, should reference shadow creatures and obelisk
- The suspicious guest's room contains something the DM should decide on before session — connects to the shadowbeast or smuggler plotline
"""

files["driftmoor/broken_lantern/storage_room/PLACE.md"] = """\
# PLACE.md — The Broken Lantern: Storage Room

## Description and Atmosphere
Cramped, low-ceilinged. Barrels of ale, sacks of grain, crates of dried goods stacked to the rafters. Smells of wood, yeast, and old food. A single lamp on a hook. Used for supplies and, for the right coin, discreet meetings.

Tess has a hidden compartment under one of the floorboards. Only she knows about it.

## Who Is Normally Here
- Tess when restocking
- Anyone who has paid for privacy

## Connections
- Main room (through door behind bar)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Empty (unless rented)
- **Recent events:** None
- **Active conditions:** Hidden compartment undisturbed
"""

files["driftmoor/broken_lantern/storage_room/CONTENTS.md"] = """\
# CONTENTS.md — Storage Room

## Items Present

### Mundane
- Barrels of ale
- Sacks of grain
- Crates of dried goods
- Lamp on hook

### Hidden
- Floorboard compartment (DC 15 Perception or Investigation to locate without prior knowledge)
- Contents: DM's discretion — valuables and important documents belonging to Tess
- Rumored: a valuable relic hidden by a previous owner (may or may not be in the same compartment)

## Notes for DM
- The hidden compartment is Tess's most guarded secret
- The previous owner's relic rumor is a separate thread — DM should decide if it is in the compartment or elsewhere in the building
- Tess charges a few silver coins for use of this room as a meeting space
"""

files["driftmoor/broken_lantern/meeting_room/PLACE.md"] = """\
# PLACE.md — The Broken Lantern: Meeting Room

## Description and Atmosphere
A small, surprisingly well-kept room behind the kitchen. Round table, mismatched chairs, a single lamp. Soundproofed enough by the kitchen noise that conversations here are genuinely private. Tess rents it out to merchants, adventurers, and less reputable clients. She pretends not to know what is discussed. She always knows what is discussed.

## Who Is Normally Here
- Rented by various parties
- Currently: a group of nervous, secretive travelers (Tess suspects smugglers or spies)

## Connections
- Kitchen / back area (through door)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Suspicious travelers (evening rental)
- **Recent events:** Same group has rented multiple evenings, always nervous
- **Active conditions:** Tess has asked no questions; party may investigate
"""

files["driftmoor/broken_lantern/meeting_room/CONTENTS.md"] = """\
# CONTENTS.md — Meeting Room

## Items Present

### Mundane
- Round table
- Mismatched chairs
- Lamp

### Notable (if searched after suspicious travelers leave)
- Discarded parchment with partial figures or notations (DM's discretion — smuggling ledger fragment, map marking, coded message)

## Notes for DM
- The parchment left behind is the evidence thread connecting the meeting room to whatever the suspicious travelers are doing
- Contents should connect to either the harbor smuggler plotline or the obelisk shard trade
"""

# ─────────────────────────────────────────────
# DUSTCLOAK'S CURIOS
# ─────────────────────────────────────────────

files["driftmoor/dustcloaks_curios/PLACE.md"] = """\
# PLACE.md — Dustcloak's Curios

## Description and Atmosphere
A squat, crooked structure of mismatched wood and stone on the outskirts of Driftmoor, near the Mistwood Hills edge. Leans slightly to one side. The yard is organized chaos — rusty tools, wagon wheels, broken furniture, a rickety wooden fence with a gate that creaks ominously. The sign reads: "Dustcloak's Curios: Oddities & Antiquities" with an etched question mark.

Inside smells of incense masking mildew. Every surface is covered with something.

## Sub-Places
- `shopfront/` — main trading space
- `backroom/` — Kelem's workspace and research area
- `living_loft/` — his private quarters above the shop

## Who Is Normally Here
- **Kelem Dustcloak** — almost always present, usually in the shopfront or backroom

## Connections
- Outskirts road near Mistwood Hills edge
- `shopfront/` → `backroom/` (through curtained doorway)
- `backroom/` → `living_loft/` (narrow staircase)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Kelem Dustcloak
- **Recent events:** None yet — session not started
- **Active conditions:** Kelem actively collecting obelisk fragments; harbor smuggler contacts active
"""

files["driftmoor/dustcloaks_curios/CONTENTS.md"] = """\
# CONTENTS.md — Dustcloak's Curios (General / Exterior)

## Items Present (Yard)
- Rusty tools (various, low value)
- Wagon wheels (2, usable)
- Broken furniture (chairs, a table missing a leg)
- Rickety wooden fence

## Notes for DM
- The yard items are genuine junk but Kelem knows exactly what is there
- Nothing of value in the yard — it is atmosphere, not inventory
"""

files["driftmoor/dustcloaks_curios/shopfront/PLACE.md"] = """\
# PLACE.md — Dustcloak's Curios: Shopfront

## Description and Atmosphere
Dimly lit by oil lamps. Shelves, crates, and tables overflow with eclectic items — jars of preserved animals, ancient coins, dusty tomes in unreadable languages, peculiar trinkets that seem to hum faintly. A small counter near the entrance where Kelem conducts transactions. Behind the counter: a locked cabinet containing his most valuable wares.

Everything has a price. Most prices are negotiable. A few things are not for sale at any price, and Kelem will not always tell you which is which.

## Who Is Normally Here
- **Kelem Dustcloak** — behind the counter

## Connections
- Exterior yard (entrance)
- `backroom/` (curtained doorway behind counter)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Kelem Dustcloak
- **Recent events:** None yet — session not started
- **Active conditions:** Locked cabinet contains current magical inventory
"""

files["driftmoor/dustcloaks_curios/shopfront/CONTENTS.md"] = """\
# CONTENTS.md — Shopfront

## Non-Magical Items for Sale
1. Shadowbeast Claw Necklace — 15 gp (+2 Intimidation when worn)
2. Bone Dice Set — 2 gp (useful for bluffing/cheating)
3. Silent Grease — 20 gp/vial (no sound when applied, covers 5-ft area)
4. Weighted Dice — 5 gp (advantage on Sleight of Hand to cheat at dice games)
5. Obsidian Mirror — 25 gp (peek around corners, signal allies in dim light)
6. Pouch of Glowing Powder — 10 gp (clings to surfaces, dim light 1 hour)
7. Iron False Key — 5 gp (advantage on Thieves' Tools to jam locks)
8. Traveler's Cloak — 8 gp (weather protection, hidden compartment, advantage on Sleight of Hand to hide small items)
9. Smoke Bomb — 15 gp each (10-ft radius smoke cloud, 1 minute)
10. Boot Blades — 20 gp (concealed weapon, 1d4 piercing, finesse, light)
11. Weighted Net — 15 gp (+2 attack rolls when thrown)
12. Obelisk Fragment Replica — 50 gp (convincing fake, advantage on Deception re: obelisk lore)

## Magical Items for Sale (Locked Cabinet)
1. Obelisk Shard (Unstable Fragment) — 250 gp
   - Once/day bonus action: +1d6 necrotic on next attack
   - Drawback: DC 12 CON save or take 1d6 psychic damage
2. Shadow Cloak — 500 gp
   - Advantage on Stealth in dim light/darkness
   - Once/day reaction: impose disadvantage on one attack targeting wearer in dim light/darkness
3. Lantern of Revealing — 400 gp
   - Reveals invisible creatures/objects in light radius
   - Lasts 6 hours per pint of oil
4. Potion of Shadow Sight — 100 gp/vial
   - Darkvision 60 ft for 1 hour (or +30 ft if already has darkvision)
   - Drawback: disadvantage on Perception in bright light
5. Ring of Obfuscation — 750 gp
   - Cast Disguise Self once/day, no spell slot
   - Drawback: reflection in mirrors slightly distorted
6. Orb of Whispering Echoes — 1,000 gp
   - Attuned: cast Detect Thoughts once/day
   - Drawback: DC 13 WIS save or hear distracting whispers 1 hour (disadvantage on INT/WIS checks)
7. Shadowbane Dagger — 1,200 gp
   - +1 attack and damage
   - +1d4 radiant vs shadow/darkness creatures
   - Drawback: emits faint light when unsheathed (disadvantage on Stealth)

## Haggling
- DC 13 CHA (Persuasion or Deception): 10-20% price reduction
- DC 15 for magical items
- Barter accepted, especially obelisk shards (he overpays)
- Mystery Bag: 10 gp for random item
- Bundling discounts available

## Notes for DM
- The locked cabinet requires Kelem's key or DC 14 Thieves' Tools
- Kelem will not sell the obelisk shard replica to someone who already has a real shard — he will pretend he sold out
"""

files["driftmoor/dustcloaks_curios/backroom/PLACE.md"] = """\
# PLACE.md — Dustcloak's Curios: Backroom

## Description and Atmosphere
Kelem's workspace. Cluttered worktables with tools for repairing and appraising items. A ledger of transactions — meticulous beneath the apparent chaos. The smell of incense is strongest here. Several obelisk fragments on a central table, surrounded by notes in Kelem's untidy scrawl. More is happening in this room than Kelem admits.

## Who Is Normally Here
- **Kelem Dustcloak** — when working

## Connections
- Shopfront (curtained doorway)
- Living loft (narrow staircase)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Kelem when not serving customers
- **Recent events:** None yet — session not started
- **Active conditions:** Obelisk fragment research ongoing
"""

files["driftmoor/dustcloaks_curios/backroom/CONTENTS.md"] = """\
# CONTENTS.md — Backroom

## Items Present

### Mundane
- Repair and appraisal tools
- Transaction ledger (comprehensive, coded in places)

### Notable
- Several obelisk fragments on the central table
- Research notes in untidy scrawl surrounding the fragments
- A small locked box beneath the worktable (DC 13 Thieves' Tools)

### Locked Box Contents
- DM's discretion — suggested: correspondence with an unknown buyer for obelisk shards, or a map marking fragment locations

## Notes for DM
- The transaction ledger, if decoded (DC 14 Investigation), reveals Kelem has sold items to buyers in other towns — including at least one name connected to the smuggling network
- The obelisk fragment research notes suggest he understands more about their properties than he lets on — specifically that gathered fragments may combine to do something significant
- The locked box is the most sensitive item in the room
"""

files["driftmoor/dustcloaks_curios/living_loft/PLACE.md"] = """\
# PLACE.md — Dustcloak's Curios: Living Loft

## Description and Atmosphere
A narrow staircase leads to a small, dark loft. Low ceiling, cramped. A narrow bed, a rickety wardrobe, a chest locked with several reinforced mechanisms. Smells of incense and mildew. The incense is deliberate — the mildew is losing the battle. This is a space Kelem tolerates rather than inhabits.

## Who Is Normally Here
- **Kelem Dustcloak** — sleeping hours only

## Connections
- Backroom (narrow staircase)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Empty during shop hours
- **Recent events:** None
- **Active conditions:** Reinforced chest undisturbed
"""

files["driftmoor/dustcloaks_curios/living_loft/CONTENTS.md"] = """\
# CONTENTS.md — Living Loft

## Items Present

### Mundane
- Narrow bed
- Rickety wardrobe (clothing, nothing notable)

### Notable
- Reinforced chest with multiple lock mechanisms (DC 18 Thieves' Tools, or all three keys carried on Kelem's person)

### Chest Contents (DM's discretion — suggestions)
- His most prized possession — a genuine obelisk fragment of unusual size or clarity
- Correspondence revealing his connection to a larger organization interested in the obelisk
- Something personal that explains why he never removes his cloak

## Notes for DM
- The chest is the most secure object in the building — cracking it should feel like a significant achievement
- Whatever is inside should reframe Kelem's motivations when discovered
"""

# ─────────────────────────────────────────────
# SALT & IRON
# ─────────────────────────────────────────────

files["driftmoor/salt_and_iron/PLACE.md"] = """\
# PLACE.md — Salt & Iron Mercantile

## Description and Atmosphere
One of the town's largest and most solidly built structures — timber reinforced with iron bands. Practical and defensible. A swinging sign above the double doors depicts a sack of salt and crossed iron tongs. Inside: organized but crowded, shelves along the walls, barrels in corners, a long counter dominating the center where Jorgen is almost always found.

Smells of iron, grain, and rope. The smell of a working town.

## Who Is Normally Here
- **Jorgen Hallowtide** — behind the counter
- Townsfolk shopping for supplies

## Connections
- Village center (outside, near square)
- Upstairs living quarters (off-limits to customers)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Jorgen Hallowtide
- **Recent events:** None yet — session not started
- **Active conditions:** Supply caravan overdue
"""

files["driftmoor/salt_and_iron/CONTENTS.md"] = """\
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
"""

# ─────────────────────────────────────────────
# BITTER REMEDY
# ─────────────────────────────────────────────

files["driftmoor/bitter_remedy/PLACE.md"] = """\
# PLACE.md — The Bitter Remedy (Apothecary)

## Description and Atmosphere
A small weathered stone structure with a crooked chimney and green vines up the walls. Near the Greywater River — Lytha harvests many of her herbs from the riverbank. Inside: shelves crammed with jars, vials, and bundles of dried herbs. The air heavy with lavender, mint, and something faintly bitter. A wooden counter covered in mortars, pestles, scales, and open tomes.

A small back room holds personal experiments and more volatile ingredients. Its door is usually closed.

## Who Is Normally Here
- **Lytha Varrow** — almost always present
- The back room is off-limits to customers

## Connections
- Near Greywater River (outside)
- Back room (through closed door, customers not admitted)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Lytha Varrow
- **Recent events:** None yet — session not started
- **Active conditions:** Back room compromised by vine creature; Fennel (apprentice) missing in Mistwood Hills
"""

files["driftmoor/bitter_remedy/CONTENTS.md"] = """\
# CONTENTS.md — The Bitter Remedy

## Items for Sale
| Item | Price | Effect |
|------|-------|--------|
| Healing Salve | 5 gp | Restores 1d4 HP when applied |
| Potion of Healing | 50 gp | 2d4+2 HP |
| Antitoxin | 25 gp | Advantage on poison saves for 1 hour |
| Sleep Draught | 15 gp | Sleep 1d4 hours (DC 12 CON to resist) |
| Glowcap Spores | 10 gp | Illuminates 5-ft radius for 1 hour when released |
| Herbal Poultices | 3 gp | Advantage on CON checks for illness recovery |
| Fire Oil | 25 gp | Coat weapons or use as improvised explosive |
| Shadowbeast Pelt Dye | 10 gp | Stains clothing black, absorbs some light |

## Back Room (restricted)
- Living mass of writhing vines — Lytha's experiment gone wrong
- Volatile alchemical ingredients
- Personal research notes (not accessible without confronting the vine creature)
- Moonlace herb sample (small, reference only — she needs more from near the obelisk)

## Notes for DM
- The vine creature in the back room is a contained hazard — if the party helps clear it, Lytha's gratitude is significant
- Lytha will buy monster parts at fair prices — establish rates based on creature rarity
- Shadowbeast blood is her current priority purchase
"""

# ─────────────────────────────────────────────
# BEACON CHURCH
# ─────────────────────────────────────────────

files["driftmoor/beacon_church/PLACE.md"] = """\
# PLACE.md — The Beacon (Church of Pelor)

## Description and Atmosphere
A modest stone building on a small rise overlooking the village. Wooden steeple. At night its lantern burns as a symbol of hope — recently flickering with a wrong, dark light. Inside: simple and well-kept. Wooden pews, stone altar with sun symbols, tall narrow windows letting in natural light. Smells of beeswax and herbs from the garden behind.

The garden behind the church grows medicinal herbs and flowers. Elden tends it himself when his strength allows; Mira tends it most of the time.

## Who Is Normally Here
- **Father Elden Greybeard** — most hours, moving slowly
- **Mira** — all hours, managing the practical running of everything

## Connections
- Village rise (outside, visible from most of town)
- Garden behind (small, medicinal herbs)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Father Elden Greybeard, Mira
- **Recent events:** None yet — session not started
- **Active conditions:** Church lantern flickering with dark light at night
"""

files["driftmoor/beacon_church/CONTENTS.md"] = """\
# CONTENTS.md — The Beacon Church

## Items Present

### Mundane
- Wooden pews
- Stone altar with sun symbols
- Oak staff (Father Elden's walking aid)
- Beeswax candles throughout

### Services Available
- Basic healing: 5 gp donation
- Greater healing or curing disease: 25 gp donation
- Sanctuary: available to anyone
- Herbs and remedies from garden: freely or modest donation

### Notable
- The church lantern (exterior, on steeple) — currently flickering with dark light after dark
- Small garden behind: lavender, rosemary, medicinal herbs freely available

## Creatures
- None

## Notes for DM
- The dark lantern flickering is a visible signal of the obelisk's influence reaching into town
- Anyone investigating the lantern directly (climbing the steeple, examining the mechanism) finds no mundane explanation — the dark light has no physical source
- Mira has seen something near the lantern at night she has not told Elden
"""

# ─────────────────────────────────────────────
# IRONHOOF FORGE
# ─────────────────────────────────────────────

files["driftmoor/ironhoof_forge/PLACE.md"] = """\
# PLACE.md — Ironhoof Forge

## Description and Atmosphere
On the outskirts of Driftmoor near the road into town. The forge is built into one side of the stable — large anvil and roaring forge visible from the road, smoke and the ring of metal a constant presence. The stables are clean and well-maintained. Behind the stable, Thorgrim's lean-to occupies a sheltered corner against the rear wall.

Smells of hot iron, horse, and hay. The sounds of the hammer carry across the outskirts.

## Sub-Places
- `forge/` — the smithing area
- `stables/` — horse boarding and tack
- Thorgrim's lean-to (covered here — too simple for its own directory)

## Thorgrim's Lean-To
Canvas over wooden poles leaning against the stable's rear wall. Small fire pit ringed with stones. Bedroll, travel rations, whetstone, greatsword propped against the wall. Smells of hay, iron, and smoke. Thorgrim spends evenings here sharpening weapons and keeping to himself.

## Who Is Normally Here
- **Darrin Stonebrook** — at the forge
- **Kara Stonebrook** — in the stables
- **Thorgrim Stoneheart** — lean-to (evenings)

## Connections
- Road into Driftmoor (outside)
- `forge/` and `stables/` share the main building

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Darrin Stonebrook, Kara Stonebrook
- **Recent events:** None yet — session not started
- **Active conditions:** Strange shadowy symbols found on forge walls; one town horse missing with clawed tracks toward Mistwood
"""

files["driftmoor/ironhoof_forge/CONTENTS.md"] = """\
# CONTENTS.md — Ironhoof Forge (General)

## Items Present (General)
- Scrap metal barrels
- Half-finished metalwork
- Thorgrim's lean-to: bedroll, rations, whetstone, greatsword

## Notable
- Shadowy symbols carved into forge walls — unknown origin, unsettling
- Clawed tracks (now fading) near the stable door leading toward Mistwood

## Notes for DM
- The shadowy symbols are a plot thread — they match symbols found elsewhere near the obelisk's influence
- Darrin will not let anyone touch his tools or examine the symbols without a trust check first
"""

files["driftmoor/ironhoof_forge/forge/PLACE.md"] = """\
# PLACE.md — The Forge

## Description and Atmosphere
Hot, smoky, loud. The main anvil is large and well-used — the surface tells the history of decades of work. Tools hang on every available surface. Barrels of scrap metal in the corners. The fire is always burning during working hours.

Darrin works here in near-silence, communicating through the rhythm of his hammer.

## Who Is Normally Here
- **Darrin Stonebrook**

## Connections
- Road (open-fronted, visible from outside)
- Stables (through interior door)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Darrin Stonebrook
- **Active conditions:** Shadowy symbols on the walls (noted, unexplained)
"""

files["driftmoor/ironhoof_forge/forge/CONTENTS.md"] = """\
# CONTENTS.md — The Forge

## Items Present

### Mundane
- Large anvil
- Full set of smithing tools
- Barrels of scrap metal
- Coal and bellows

### For Sale / Service
- Horseshoes (set of 4): 1 gp
- Weapon repairs: 2-5 gp
- Tool repairs: 1 gp
- Arrowheads (20): 2 gp
- Custom orders: varies, discuss with Darrin

### Notable
- Shadowy symbols on the walls — appear to have been carved or burned in, not painted

## Notes for DM
- Custom orders take 1d4 days depending on complexity
- The symbols cannot be scrubbed off — Darrin has tried
"""

files["driftmoor/ironhoof_forge/stables/PLACE.md"] = """\
# PLACE.md — The Stables

## Description and Atmosphere
Clean and well-maintained — Kara's domain. Space for a dozen horses. Saddle racks and feed bins neatly organized. Smells of hay and horse. The animals here are calm around Kara and noticeably less so around strangers.

The horses near the Mistwood road stall have been spooked for weeks.

## Who Is Normally Here
- **Kara Stonebrook**
- Various horses (boarders and Darrin's stock)

## Connections
- Road (outside)
- Forge (interior door)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Kara Stonebrook
- **Active conditions:** Horses near Mistwood stall unsettled; one prize horse missing
"""

files["driftmoor/ironhoof_forge/stables/CONTENTS.md"] = """\
# CONTENTS.md — The Stables

## Items Present

### Mundane
- Saddle racks
- Feed bins
- Grooming tools
- Riding tack

### For Sale / Service
- Horse boarding (1 week): 5 gp (includes feed and grooming)
- Riding saddle: 10 gp
- Cart or wagon rental: 10-25 gp
- Horse purchase: 75 gp (healthy draft or riding horse)

### Notable
- Tracks near the rear door (fading) — clawed, leading toward Mistwood Forest
- One stall empty — the missing prize horse

## Notes for DM
- Kara can lend the party a horse in exchange for taking her along — Darrin will object
- The clawed tracks are the same type as shadowbeast tracks found elsewhere
"""

# ─────────────────────────────────────────────
# GILDED TRINKET
# ─────────────────────────────────────────────

files["driftmoor/gilded_trinket/PLACE.md"] = """\
# PLACE.md — The Gilded Trinket (Pawnshop)

## Description and Atmosphere
A narrow, weathered wooden building. Faded gold-painted sign above the door — a coin surrounded by sparkling trinkets. Small windows covered with metal grates. Inside: cluttered but carefully organized. Shelves of rusty tools, jewelry, old weapons, curios of uncertain value. A locked glass display case at the counter holds the most valuable wares. Behind it, a large safe and ledger. Dim oil lamp lighting.

Smells of dust and polish.

## Who Is Normally Here
- **Tavian "Tav" Drakescale** — behind the counter

## Connections
- Village (outside)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Tavian Drakescale
- **Recent events:** None yet — session not started
- **Active conditions:** Cursed artifact in inventory; mysterious medallion on Tav's person
"""

files["driftmoor/gilded_trinket/CONTENTS.md"] = """\
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
- **Cursed artifact** (received from villager, currently in the case): nature TBD by DM
- **Tav's medallion**: on his person, not in the shop

## Services
- Appraisal: 1 gp (may lowball to buy)
- Short-term loans: steep interest, forfeiture on late repayment
- Rare item search: 5 gp upfront, uses contacts

## Notes for DM
- The cracked compass and strange stone amulet are genuinely magical — Tav knows and is not telling
- The cursed artifact is the active plot item — decide its nature before session
- The mysterious map fragment shows part of the Drowned Isle coastline
"""

# ─────────────────────────────────────────────
# RUSTY RAZOR
# ─────────────────────────────────────────────

files["driftmoor/rusty_razor/PLACE.md"] = """\
# PLACE.md — The Rusty Razor (Barbershop)

## Description and Atmosphere
A small wooden building tucked into a corner near the village square. Red-and-white painted sign depicting a razor crossed with a comb. Inside: warm and inviting, potbelly stove, two sturdy customer chairs, wall lined with mirrors, scissors, razors, and brushes. Smells of pine soap and pomade.

The social hub for male townsfolk and the best source of current gossip in Driftmoor after the tavern.

## Who Is Normally Here
- **Arlan Quickstep** — almost always, scissors in hand or not
- One or two customers during the day

## Connections
- Village square corner (outside)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Arlan Quickstep
- **Recent events:** None yet — session not started
- **Active conditions:** Strange figures lurking near the shop at night
"""

files["driftmoor/rusty_razor/CONTENTS.md"] = """\
# CONTENTS.md — The Rusty Razor

## Items Present

### For Sale
- Haircut: 5 sp
- Shave: 2 sp
- Pomade and grooming supplies: 1 gp

### Notable
- Arlan's old adventure map — available for sale or trade for a favor
- Straight razors (functional weapons if needed: 1d4 slashing, light, finesse)

## Notes for DM
- The adventure map covers territory beyond Driftmoor — its accuracy and relevance is DM's discretion
- Arlan's steady hands and spatial awareness suggest his adventuring past is not entirely embellished
"""

# ─────────────────────────────────────────────
# WEARY TRAVELER
# ─────────────────────────────────────────────

files["driftmoor/weary_traveler/PLACE.md"] = """\
# PLACE.md — The Weary Traveler (Rooming House)

## Description and Atmosphere
A sturdy two-story timber building just off the main square, near the mercantile. A sign depicting a worn boot hangs above the entrance. The common room downstairs serves as dining area and gathering space — large hearth, mismatched wooden chairs and tables. Upstairs: small, clean guest rooms. Out back: a storage shed used as overflow housing.

Smells of lamb stew, almost always. Martha Greaves is almost always cooking.

## Who Is Normally Here
- **Martha Greaves** — managing everything
- Current guests (see dynamic state)

## Connections
- Main square area (outside, near mercantile)
- Upstairs guest rooms
- Storage shed out back (overflow)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Martha Greaves; one suspicious long-term guest
- **Recent events:** One previous guest missing after trip to Obelisk Reach
- **Active conditions:** Suspicious guest receiving strange late-night deliveries
"""

files["driftmoor/weary_traveler/CONTENTS.md"] = """\
# CONTENTS.md — The Weary Traveler

## Items Present

### Common Room
- Large hearth
- Mismatched tables and chairs

### Food and Drink
- Lamb stew with bread: 2 sp
- Fresh baked pie: 1 sp
- Ale or cider: 5 cp

### Guest Rooms (per room)
- Simple bed, washbasin, small chest
- Basic lock (DC 8 Thieves' Tools)

### Notable
- Missing guest's belongings (one room): journal with cryptic entries about shadowy figures near the Obelisk Reach
- Suspicious guest's deliveries: unknown contents, received after dark

## Rates
- Room per night: 5 sp (basic) or 1 gp (with meals)
- Bath service: 2 sp
- Laundry: 1 sp
- Storage shed overflow: negotiable (cheaper)

## Notes for DM
- Martha has quietly looked through the missing guest's journal — she will share it if the party seems trustworthy
- The suspicious guest's deliveries come from the harbor direction
"""

# ─────────────────────────────────────────────
# ELYSSA'S COTTAGE
# ─────────────────────────────────────────────

files["driftmoor/elyssa_cottage/PLACE.md"] = """\
# PLACE.md — Elyssa Moonglow's Cottage

## Description and Atmosphere
A simple stone building with slate roof and ivy up the walls on a low hill overlooking the Greywater River. A small chimney emits thin smoke — the fire in her study is almost never out. The front path is lined with overgrown lavender and rosemary. A side herb garden, less well-kept than her work inside. A weathered sign reads "E. Moonglow – Researcher" in Elvish script.

Inside: part library, part laboratory, part living space. Every surface serves a purpose.

## Sub-Places
- `study/` — main room, library and workspace
- `laboratory/` — side room, experiments and obelisk research
- Bedroom (covered here — too sparse for its own directory)

## Bedroom
Small, sparsely furnished. Narrow bed, wardrobe, table with single candle. Elyssa rarely uses it — she falls asleep at her desk more often than not.

## Who Is Normally Here
- **Elyssa Moonglow** — almost always, usually at her desk

## Connections
- Low hill above Greywater River (outside, outskirts of Driftmoor)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Elyssa Moonglow
- **Recent events:** None yet — session not started
- **Active conditions:** Cloaked visitor recently asked strange questions about the obelisk and disappeared; lab may be ransacked (event trigger)
"""

files["driftmoor/elyssa_cottage/CONTENTS.md"] = """\
# CONTENTS.md — Elyssa's Cottage (General)

## Items Present (Herb Garden)
- Lavender, rosemary (overgrown)
- Medicinal herbs (functional but less organized than church garden)

## Notes for DM
- The herb garden is a minor resource — Lytha Varrow occasionally trades with Elyssa for specimens
"""

files["driftmoor/elyssa_cottage/study/PLACE.md"] = """\
# PLACE.md — Elyssa's Study

## Description and Atmosphere
Shelves on every wall, overflowing with books, scrolls, and dusty tomes. Piles of papers on every flat surface, covered in hasty notes and diagrams. A large wooden desk near the window serves as primary workspace — cluttered with quills, ink bottles, and half-unrolled maps. The window looks toward the river.

The organized chaos of a working scholar. Everything is findable, to her.

## Who Is Normally Here
- **Elyssa Moonglow** — most waking hours

## Connections
- Front door (entrance)
- Laboratory (side room door)
- Bedroom (through back)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Elyssa Moonglow
- **Active conditions:** Notes on obelisk research visible on desk
"""

files["driftmoor/elyssa_cottage/study/CONTENTS.md"] = """\
# CONTENTS.md — Elyssa's Study

## Items Present

### Books and Documents
- Extensive library — history, arcane theory, regional geography
- Research notes: obelisk history, potential origins, current effects on the region
- Ancient hand-drawn maps of the region with obelisk marked as central point
- Half-unrolled current maps of Driftmoor and surroundings

### Notable
- Research notes (accessible on desk): contain the clearest organized account of what Elyssa knows about the obelisk — she will share these with serious allies
- Ancient maps: the obelisk-centric ones predate current town records and show features no longer present

### Rare Artifacts (on shelves and tables)
- Pottery shards from unknown civilization
- Carved stone glyphs (rusted)
- Rusted tools of unidentified design

## Notes for DM
- The ancient maps are a significant research resource — a DC 13 Investigation check reveals a symbol on the oldest map that matches the symbols appearing on Driftmoor buildings and the mill
- Elyssa will freely share her notes with the party once she trusts them
"""

files["driftmoor/elyssa_cottage/laboratory/PLACE.md"] = """\
# PLACE.md — Elyssa's Laboratory

## Description and Atmosphere
A smaller side room. Worn alchemical workbench covered in vials, beakers, and bubbling solutions. The air is different here — slightly charged. In the center of the table: a faintly glowing obelisk shard encased in a reinforced glass dome, surrounded by chalk glyphs. Several crates of excavation tools and partially cleaned artifacts. The glow from the dome provides the room's primary light.

## Who Is Normally Here
- **Elyssa Moonglow** — when experimenting

## Connections
- Study (side door)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Empty unless Elyssa is working
- **Active conditions:** Obelisk shard present and contained (until ransacking event)
"""

files["driftmoor/elyssa_cottage/laboratory/CONTENTS.md"] = """\
# CONTENTS.md — Elyssa's Laboratory

## Items Present

### Equipment
- Alchemical workbench (vials, beakers, solutions)
- Excavation tools (crates)
- Chalk and marking tools
- Partially cleaned artifacts

### Notable / Plot Items
- **Obelisk Shard** — in reinforced glass dome, surrounded by chalk glyphs
  - Faintly glowing, pulsing with dark energy
  - Elyssa's primary research specimen
  - TARGET: adventure hook — stolen if ransacking event triggers
- Research notes specific to the shard's behavior — stored in this room separately from study notes

### If Ransacked
- Dome broken, shard missing
- Notes scattered but recoverable (DC 11 Investigation to piece together key findings)
- Evidence of forced entry through the side window

## Notes for DM
- The shard in the dome is the most significant magical object the party will encounter early
- Its theft should feel urgent — Elyssa's fear when she discovers it missing is genuine
- The chalk glyphs are a containment measure — without them, the shard's energy is unshielded
"""

# ─────────────────────────────────────────────
# SIMPLE DRIFTMOOR BUILDINGS
# ─────────────────────────────────────────────

simple_buildings = {
    "tannery": {
        "name": "The Tannery",
        "npc": "Boren Thatch",
        "atmosphere": "A low stone building near the riverbank. The smell of leather and curing hides is unmistakable from twenty feet away. Wooden racks outside display stretched animal skins. Barrels of dyes and oils stacked against the walls. Inside: the work of rendering hide into leather in all its unsentimental stages.",
        "who": "Boren Thatch, working",
        "connections": "Riverbank (outside)",
        "contents": """\
## Items Present

### Mundane
- Stretched animal hides (various stages of curing)
- Barrels of dye and oil
- Tanning tools

### For Sale
- Cured leather (per yard): 5 sp
- Leather scraps (bag): 2 sp
- Custom leather goods: price by item and complexity, 2-7 days

## Notes for DM
- Boren knows which local farmers have been losing livestock — he processes what remains after predation
- He will share this information if asked directly; he does not volunteer it
"""
    },
    "carpenters_workshop": {
        "name": "Carpenter's Workshop",
        "npc": "Hilda Truebeam",
        "atmosphere": "Timber-framed with an open front. The smell of freshly cut wood and sawdust. Piles of lumber, half-finished furniture, the rhythmic sound of hammering. Hilda's apprentices work alongside her — she runs a tight shop. The finished pieces visible from the entrance are genuinely fine work.",
        "who": "Hilda Truebeam and apprentices",
        "connections": "Village (outside)",
        "contents": """\
## Items Present

### Mundane
- Lumber in various stages
- Woodworking tools (Hilda is protective of these)
- Half-finished furniture

### For Sale
- Standard furniture (chair, table): 2-8 gp
- Wagon repair: 5-15 gp depending on damage
- Custom orders: price by complexity, 3-10 days

## Notes for DM
- Hilda knows the structural condition of most buildings in Driftmoor
- She has noticed the mill's deterioration and has opinions about it
- She may need rare timber from the Mistwood Hills — a potential errand
"""
    },
    "fishmongers_shack": {
        "name": "The Fishmonger's Shack",
        "npc": "Kessla Brinehook",
        "atmosphere": "A small weathered shack near the harbor with a slanted roof and a sign shaped like a fish. Crates of fresh and salted fish stacked high inside. Nets and hooks hanging from the walls. Smells exactly like you would expect. Kessla's voice can be heard before the shack comes into view.",
        "who": "Kessla Brinehook, always",
        "connections": "Harbor (outside)",
        "contents": """\
## Items Present

### For Sale
- Fresh fish (per lb): 2 cp
- Salted fish (per lb): 4 cp
- Fishing tackle (simple): 1 gp
- Fish hooks (10): 5 cp

### Notable
- Kessla has seen shadowy shapes beneath the harbor water — she will describe them to anyone who asks
- She knows which fishing boats have been avoiding certain waters and why

## Notes for DM
- Kessla is the best source of harbor-specific intelligence
- The shadowy harbor shapes connect to the Drowned Isle plotline
"""
    },
    "weavers_cottage": {
        "name": "The Weaver's Cottage",
        "npc": "Eadric Spindle",
        "atmosphere": "A quaint stone-and-thatch cottage surrounded by colorful cloth drying on lines. The rhythmic clatter of the loom from inside. Bolts of finished fabric visible through the open door, in practical greens and browns alongside occasional surprising color. Eadric works continuously and talks while doing it.",
        "who": "Eadric Spindle",
        "connections": "Village outskirts (outside)",
        "contents": """\
## Items Present

### For Sale
- Sturdy cloth (per yard): 3 sp
- Simple garments (tunic, breeches): 5-8 sp
- Heavy cloak: 1-2 gp
- Custom work: price by complexity, 2-5 days

## Notes for DM
- Eadric trades with passing merchants — he knows the road conditions and recent traveler traffic
- Nothing plot-critical here unless DM develops it
"""
    },
    "bakery": {
        "name": "The Bakery",
        "npc": "Maribel Crust",
        "atmosphere": "A warm inviting building. The chimney perpetually wafts the smell of fresh bread and pastries across the surrounding street. The front counter displays loaves, meat pies, and sweet rolls. Maribel and her daughter Lottie work in near-constant motion. Entering feels like being welcomed.",
        "who": "Maribel Crust and daughter Lottie",
        "connections": "Village center (outside)",
        "contents": """\
## Items Present

### For Sale
- Bread loaf: 2 cp
- Meat pie: 5 cp
- Sweet roll: 1 cp
- Pastries (seasonal): 3-6 cp

## Notes for DM
- The bakery is a natural gathering point — townsfolk talk here while waiting
- Maribel knows who has been upset, worried, or acting strangely lately — she observes through the lens of who stops eating properly
"""
    },
    "tailors_shop": {
        "name": "The Tailor's Shop",
        "npc": "Vindra Goldneedle",
        "atmosphere": "A tidy building with a painted sign showing a needle and thread. Bolts of fabric line the walls, mannequins display garments ranging from practical to fine. Vindra is always impeccably dressed. The shop has a quiet, focused atmosphere — nothing is wasted, not a thread.",
        "who": "Vindra Goldneedle",
        "connections": "Village (outside)",
        "contents": """\
## Items Present

### For Sale
- Simple repairs: 1-3 sp
- Practical garments: 5 sp - 2 gp
- Fine garments (special occasions): 5-20 gp
- Custom work: price by complexity, 3-7 days

## Notes for DM
- Vindra knows who in town is spending beyond their means on appearance
- She will sometimes ask adventurers about their travels with genuine wistfulness — she has never left Driftmoor
"""
    },
    "general_store": {
        "name": "The General Store",
        "npc": "Jedrin Oakes",
        "atmosphere": "A simple stone-and-wood building crowded with everyday goods. Shelves overflow with tools, rope, candles, preserved food. Jedrin sits behind the small counter ready to barter. Behind the store, a large and surprisingly well-tended garden — Jedrin's quiet pride.",
        "who": "Jedrin Oakes; occasionally granddaughter Eliza",
        "connections": "Village (outside); garden behind",
        "contents": """\
## Items Present

### For Sale
- Rope (50 ft): 1 gp
- Candles (10): 5 cp
- Preserved food (week's supply): 5 sp
- Basic tools (hammer, saw, etc.): 2-5 sp each
- Miscellaneous household goods: various

### Garden (behind store)
- Carrots, turnips, cabbages, onions, radishes (fresh produce)
- Parsley, thyme, rosemary, mint (herbs)
- Marigolds and lavender (ornamental, pest-repelling)
- Wildflower patch (children may pick)
- Rain barrel, compost heap, seating under apple tree

### Notable
- Strange clawed tracks found in garden recently
- One herb patch showing unnatural growth rate with faint glow

## Notes for DM
- Jedrin is a good early-session contact — his store provides practical supplies and he has traveler road knowledge
- Eliza's disappearance (if triggered) is a family emergency that produces urgent motivation
"""
    },
    "schoolhouse": {
        "name": "The Schoolhouse",
        "npc": "Alina Finch",
        "atmosphere": "A one-room building with a bell on the roof. Chalkboard, rows of wooden desks. Chalk dust and ink are the primary smells. Alina's enthusiasm fills the room more than the furniture does. Used as a community meeting hall when school is not in session.",
        "who": "Alina Finch (during school hours); empty or community use otherwise",
        "connections": "Village (outside)",
        "contents": """\
## Items Present

### Mundane
- Chalkboard and chalk
- Rows of wooden desks
- Alina's reference books and teaching materials
- Bell (exterior, functional)

## Notes for DM
- Children talk to Alina. She is an excellent source of what the town's children have seen near the outskirts
- The schoolhouse doubles as a community meeting hall — could be used for a town assembly scene
"""
    },
    "coopers_shed": {
        "name": "The Cooper's Shed",
        "npc": "Tomas Reed",
        "atmosphere": "A utilitarian structure near the harbor. The yard is littered with wooden staves and iron hoops. The rhythmic pounding of mallet work. Tomas works in near-silence, preferring the sound of the wood. Small wooden toys are sometimes visible near the entrance — gifts for the town's children.",
        "who": "Tomas Reed",
        "connections": "Harbor (outside)",
        "contents": """\
## Items Present

### For Sale
- Standard barrel: 5 sp
- Small cask: 3 sp
- Crate (various sizes): 1-3 sp
- Custom orders: price by size and complexity, 1-3 days

## Notes for DM
- Tomas knows harbor logistics — who is shipping what, what has been ordered and not arrived
- His small wooden toys are given freely to children, which has made him quietly beloved
"""
    },
    "midwifes_home": {
        "name": "The Midwife's Home",
        "npc": "Gran Lorie Wren",
        "atmosphere": "A cozy cottage with a small herb garden and a cheery painted door. Inside: shelves of jarred remedies and bandages alongside the practical tools of her trade. Warm and welcoming in a different way than the tavern — more like being looked after than entertained. Gran Lorie has seen everything and judges nothing.",
        "who": "Gran Lorie Wren",
        "connections": "Village (outside)",
        "contents": """\
## Items Present

### Mundane
- Jarred herbal remedies (various)
- Bandages and basic medical supplies
- Midwifery tools

### For Sale / Service
- Basic remedies and healing herbs: 1-5 sp
- Medical consultation: free (she will not turn away anyone sick)
- Healer's assistance: she can stabilize a dying character without a roll

### Notable
- Healing from wounds sustained near the obelisk area is slower than normal — she has noticed and documented this
- She knows the medical history of nearly everyone in Driftmoor

## Notes for DM
- Gran Lorie is the party's backup healer if Lilar is down
- Her observation about slow healing near the obelisk is a useful piece of lore she will share freely if asked
"""
    },
    "watchtower": {
        "name": "The Watchtower",
        "npc": "Darwin Cragg",
        "atmosphere": "A squat stone tower in the center of town. Simple wooden door, a ladder ascending inside to the lookout platform. Darwin is almost always at the top, whatever the weather. From the platform: a clear view of the harbor, the road north toward the Obelisk Reach, the fields and river. He has been watching this view for years and knows it exactly.",
        "who": "Darwin Cragg (at the top, always)",
        "connections": "Village center (outside); ladder to lookout platform",
        "contents": """\
## Items Present

### Mundane
- Lookout platform with unobstructed view
- Darwin's logbook (movement records, sightings, weather)
- Signal horn (emergency use)

### Notable
- Darwin's logbook contains entries about strange lights near the Obelisk Reach at unusual hours
- He has logged these without reporting them — waiting to see if anyone else mentions them

## Notes for DM
- Darwin's logbook is a useful intelligence resource — DC 11 Persuasion to get him to share it
- He will share the obelisk lights information freely if the party mentions the obelisk first
- The signal horn can alert the whole town if sounded
"""
    },
    "cobblers_shop": {
        "name": "The Cobbler's Shop",
        "npc": "Marta Sole",
        "atmosphere": "A snug brick-walled shop. Shoes of all shapes and sizes in the front window. The smell of leather and beeswax. Marta's laugh arrives before you open the door. She works with nimble fingers and keeps up a constant stream of conversation — she prefers it to silence and has never experienced a lull she couldn't fill.",
        "who": "Marta Sole",
        "connections": "Village (outside)",
        "contents": """\
## Items Present

### For Sale
- Boot repair: 2-8 sp depending on damage
- Standard boots: 1-2 gp
- Custom footwear: 3-8 gp, 2-5 days
- Beeswax polish: 2 cp

## Notes for DM
- Marta can read where people have been from the state of their boots — worn heels, mud type, unusual wear patterns
- She knows who has been traveling toward the Obelisk Reach recently from their footwear
"""
    },
}

for key, b in simple_buildings.items():
    files[f"driftmoor/{key}/PLACE.md"] = f"""\
# PLACE.md — {b['name']}

## Description and Atmosphere
{b['atmosphere']}

## Who Is Normally Here
- **{b['npc']}**

## Connections
- {b['connections']}

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** {b['npc']}
- **Recent events:** None yet — session not started
- **Active conditions:** None established
"""
    files[f"driftmoor/{key}/CONTENTS.md"] = b['contents']

# ═════════════════════════════════════════════
# OBELISK REACH
# ═════════════════════════════════════════════

files["obelisk_reach/PLACE.md"] = """\
# PLACE.md — The Obelisk Reach

## Description and Atmosphere
A jagged expanse of cliffs and rocky plateaus north of Driftmoor. Named for the shattered obelisk that looms over the landscape. The terrain is treacherous — narrow paths, hidden caves, eerie rock formations. Strange symbols carved into the cliffs are thought to predate even the oldest known civilizations.

The air here feels different. Charged. Sounds carry strangely. Animals avoid it. At night, lights have been seen moving among the formations.

## Sub-Places
- `shattered_obelisk/` — the central ruin
- `echoing_caverns/` — cave network beneath the Reach

## Who Is Normally Here
- Nobody, by choice
- Shadowbeasts, with increasing frequency
- The occasional desperate or foolhardy investigator

## Connections
- Road north from Driftmoor
- `shattered_obelisk/` (visible from approach)
- `echoing_caverns/` (entrance hidden in the cliff face, DC 13 Perception to locate)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active — shadowbeast presence, strange lights at night
- **Recent events:** None yet — session not started
- **Active conditions:** Strange lights reported by Darwin Cragg from watchtower; Wilfred's shadow giant sighting near the cliffs
"""

files["obelisk_reach/CONTENTS.md"] = """\
# CONTENTS.md — The Obelisk Reach (General)

## Creatures and Threats

### Shadowbeasts
- Multiple individuals, increasing in number
- Territorial around the shattered obelisk
- Nocturnal preference but active in deep shadow during daylight in the caverns

### Environmental Hazards
- Crumbling cliff edges (DC 12 DEX save or take 1d6 falling damage when moving quickly near edges)
- Slippery surfaces (difficult terrain after rain)
- Narrow paths (single file, disadvantage on ranged attacks)

## Items (General Area)
- Obelisk fragments embedded in cliff rock (require tools to extract)
- Strange carved symbols in the cliff face (unknown civilization, not removable)
- Moonlace herb: grows in sheltered cliff crevices near the obelisk (Lytha's needed ingredient)

## Notes for DM
- The symbols in the cliff face match symbols appearing elsewhere in the region — this is a deliberate pattern
- Moonlace is identifiable with DC 12 Nature check; Aeliana identifies it automatically
- Obelisk fragment extraction from the cliff requires 10 minutes and tools; produces one shard (250 gp value to Kelem)
"""

files["obelisk_reach/shattered_obelisk/PLACE.md"] = """\
# PLACE.md — The Shattered Obelisk

## Description and Atmosphere
A towering fractured stone spire. What remains standing is still massive — the break is somewhere in the upper third, and the fallen sections have scattered across the cliffs, some embedded deep in the rock. The surface hums faintly with magical energy. The dark stone occasionally flickers with veins of glowing light. Standing near it produces a low vibration felt in the chest.

The ground around the base is scorched in a pattern that radiates outward. Old scorch. Whatever happened here was not recent.

## Who Is Normally Here
- Shadowbeasts (territorial)
- Nobody else, voluntarily

## Connections
- Obelisk Reach approach path
- Echoing Caverns entrance (below, to the west of the obelisk base)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active magical emanation
- **Creatures present:** 1d4 shadowbeasts in the immediate vicinity
- **Recent events:** None yet — session not started
- **Active conditions:** Faint hum audible within 30 ft; dark veins visible at night
"""

files["obelisk_reach/shattered_obelisk/CONTENTS.md"] = """\
# CONTENTS.md — The Shattered Obelisk

## Items Present

### Obelisk Fragments
- Multiple fragments scattered across the area
- Each extractable shard: 250 gp to Kelem Dustcloak
- Unstable: carrying an uncontained shard requires DC 12 CON save each hour or take 1d4 psychic damage
- Elyssa Moonglow can provide containment vessel for safe transport

### Flora
- Moonlace herb: 2d4 patches in sheltered crevices near the base
  - DC 12 Nature to identify (Aeliana automatic)
  - Required by Lytha Varrow for shadowbeast repellent research

### Inscriptions
- Base of the obelisk: inscriptions in an unknown language
  - DC 16 Arcana or History to partially translate
  - Elyssa can translate more fully given time and rubbings

## Creatures
- 1d4 shadowbeasts (territorial, aggressive if approached without precaution)

## Notes for DM
- The obelisk is the campaign's central mystery object — it should feel significant and slightly wrong
- Players who touch a bare fragment without containment feel a pulse of dark energy (no damage, but unsettling — DC 12 WIS save or feel drawn to touch it again)
- The inscriptions, partially translated: references to a binding, a seal, and something described as "the hunger beneath"
"""

files["obelisk_reach/echoing_caverns/PLACE.md"] = """\
# PLACE.md — The Echoing Caverns

## Description and Atmosphere
A network of caves beneath the Obelisk Reach. The entrance is a narrow crack in the cliff face west of the obelisk base, easy to miss. Inside: unnatural sounds echo from deeper chambers — not wind. The walls are damp and dark. The air is colder than it should be. Occasionally, a distant sound resolves briefly into something that sounds almost like a voice.

Father Elden Greybeard came here decades ago. His companions did not leave.

## Who Is Normally Here
- Nobody living, voluntarily
- Shadowbeasts in the deeper chambers
- Whatever took Elden's companions (DM's determination)
- Elden's companions' remains (somewhere in the deeper chambers)

## Connections
- Entrance: cliff face west of obelisk base (DC 13 Perception to locate)
- Deeper chambers: ancient, mapped only partially by Elyssa from old records

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active — sounds, shadowbeast presence in deep chambers
- **Recent events:** None yet — session not started
- **Active conditions:** Elden's companions' remains unrecovered; ancient chambers unexplored
"""

files["obelisk_reach/echoing_caverns/CONTENTS.md"] = """\
# CONTENTS.md — The Echoing Caverns

## Creatures
- Shadowbeasts: 2d4 in deeper chambers
- Unknown creature(s): responsible for Elden's companions' deaths — DM's determination
  - Suggested: a creature of shadow and old magic, bound to the cavern by the obelisk's collapse

## Items Present

### Near Entrance
- Old torch bracket on the wall (rusted, unusable)
- Scratches on the wall near the entrance — old, possibly a count of days

### Deeper Chambers
- Elden's companions' remains (skeletal, decades old)
  - With remains: worn holy symbol of Pelor (Elden's companion was a cleric)
  - With remains: a fragment of parchment with partial map of the cavern system
- Ancient chamber walls: carved with the same unknown symbols as the cliff face and obelisk base
- Obelisk fragment embedded in the cavern floor (large, not easily removable)

## Notes for DM
- The Echoing Caverns should feel like the campaign's first major dungeon
- The unrecovered remains are Elden's personal quest — restoring them to proper burial will matter to him deeply
- The ancient chamber symbols, combined with the obelisk inscriptions and the cliff symbols, spell out more of whatever the obelisk was originally doing
- The large embedded fragment is the source of the cavern's supernatural qualities — destroying or containing it would reduce (not eliminate) the shadowbeast threat
"""

# ═════════════════════════════════════════════
# GREYWATER RIVER
# ═════════════════════════════════════════════

files["greywater_river/PLACE.md"] = """\
# PLACE.md — The Greywater River

## Description and Atmosphere
A fast-moving river cutting through the region, originating in the Mistwood Hills to the northeast and flowing into the sea at Driftmoor. The river is vital — irrigation for the farms, transport for grain and goods, fishing for the town. The banks are lined with willows downstream, open fields upstream.

In recent months, strange shadowy creatures have been seen skulking near the banks. The otters have gone quiet. The kingfishers still fish, but they do not linger.

## Sub-Places
- `old_mill/` — the Haverstead family mill, a few miles upriver
- `willowford_bridge/` — the main crossing

## Who Is Normally Here
- Farmers moving goods by raft downstream
- Fisherfolk along the lower banks
- Wildlife: trout, otters (less visible recently), kingfishers

## Connections
- Driftmoor harbor (downstream)
- Old Mill (a few miles upriver)
- Willowford Bridge (midway)
- Mistwood Hills (source, northeast)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Uneasy — shadowy creature sightings along banks
- **Recent events:** A farmer's child gone missing near the Old Mill
- **Active conditions:** Shadowbeast presence near banks at night
"""

files["greywater_river/CONTENTS.md"] = """\
# CONTENTS.md — The Greywater River (General)

## Creatures
- Trout (fishing, edible)
- Otters (present but withdrawn from usual spots)
- Kingfishers (present)
- Shadowbeasts: 1d2 near banks at night — DC 14 Perception to detect before they detect the party

## Environmental Features
- Fast current: DC 13 Athletics to swim across without being pushed downstream
- Willows along lower banks: provide concealment (advantage on Stealth while using them)
- Raft travel: downstream to Driftmoor 2 hours, upstream to mill 4 hours

## Notes for DM
- The river is a travel corridor — encounters here should feel transient, not dungeon-like
- Shadowbeast tracks in the riverbank mud are findable (DC 11 Survival) and can be followed
"""

files["greywater_river/old_mill/PLACE.md"] = """\
# PLACE.md — The Old Mill

## Description and Atmosphere
A large two-story stone building on the Greywater River, a few miles upriver from Driftmoor. Moss-covered steep roof, cracked exterior walls with spiderwebbing, ivy climbing the stone. The waterwheel is massive but old — wooden paddles worn thin. Inside, the constant rumble of grinding grain and a fine layer of flour dust on every surface. The building groans in wind.

The Haverstead family has run this mill for generations. It is essential to the local economy and slowly falling apart.

## Sub-Places
- `ground_floor/` — the milling operation
- `upper_floor/` — family living quarters

## Exterior
- Small yard where farmers unload grain
- Riverbank lined with willows
- Fields stretching out in every direction, golden at harvest

## Who Is Normally Here
- **Gregan Haverstead** — at the grinding stones
- **Mara Haverstead** — managing household, helping with customers
- **Davin Haverstead** — assisting where he can
- **Tessa Haverstead** — quick with repairs, often elsewhere
- **Baby Isla** — strapped to Mara's back

## Connections
- River road from Driftmoor (2 hours downstream by raft, longer on foot)
- `ground_floor/` and `upper_floor/`

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Haverstead family
- **Recent events:** Shadowbeast attacked a grain-delivery farmer; Tessa exploring near obelisk unsupervised
- **Active conditions:** Strange symbols on mill beams; waterwheel deteriorating; riverbank erosion threatening structure
"""

files["greywater_river/old_mill/CONTENTS.md"] = """\
# CONTENTS.md — The Old Mill (General)

## Exterior Items
- Farmer's carts and wagons (visiting, during harvest)
- Grain sacks waiting for processing

## Notable
- Strange symbols carved into the mill's exterior beams — match symbols elsewhere in the region
- Riverbank erosion visible on the north-facing wall — structural risk

## Notes for DM
- The mill is under threat from multiple directions: supernatural (symbols, shadowbeast attacks), structural (erosion, aging waterwheel), and personal (Tessa's dangerous explorations)
- The symbols were noticed by Tessa before Gregan — she has been copying them secretly
"""

files["greywater_river/old_mill/ground_floor/PLACE.md"] = """\
# PLACE.md — Old Mill: Ground Floor

## Description and Atmosphere
The main milling area. Dominated by a pair of large millstones — the constant rumble is the heartbeat of the building. Flour dust coats every surface. Sacks of grain stacked in one corner waiting to be processed. The smell is sweet and dusty simultaneously. The noise makes conversation difficult when the stones are turning.

## Who Is Normally Here
- **Gregan Haverstead** — at the stones
- **Mara Haverstead** — with customers at the counter
- **Davin Haverstead** — loading and unloading

## Connections
- Exterior yard (main door)
- Upper floor (interior staircase)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Gregan, Mara, Davin during working hours
- **Active conditions:** Millstones occasionally seizing; symbols on beams visible
"""

files["greywater_river/old_mill/ground_floor/CONTENTS.md"] = """\
# CONTENTS.md — Ground Floor

## Items Present

### Mundane
- Millstones (operational, aging)
- Grain sacks (stacked, waiting)
- Flour sacks (processed, for collection)
- Counter and scale for weighing

### Notable
- Strange symbols carved into several of the main support beams
  - Tessa has been making rubbings of these in secret
  - Match symbols at the Obelisk Reach and Driftmoor buildings
- Waterwheel mechanism access panel (exterior-facing, shows wear and stress)

## Notes for DM
- The symbols on the beams are the clearest set in the campaign — they are accessible without danger and can be studied
- DC 14 Investigation on the symbols yields the same partial meaning as other symbol sets
- Gregan will not let strangers examine the beams closely without a trust check (DC 12 Persuasion)
"""

files["greywater_river/old_mill/upper_floor/PLACE.md"] = """\
# PLACE.md — Old Mill: Upper Floor

## Description and Atmosphere
The family's modest living quarters. A communal sleeping area and a small kitchen. The roof leaks in heavy rain — patches of mismatched wood and plaster mark the repairs. Personal and worn in the way of a family that has lived in the same space for generations. Baby Isla's corner is the tidiest part of the room.

## Who Is Normally Here
- **Mara Haverstead** — kitchen and child care
- **Baby Isla** — in her corner or strapped to Mara
- **Tessa Haverstead** — when she is actually here and not exploring
- The rest of the family sleeps here

## Connections
- Ground floor (interior staircase)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Mara, Isla during the day
- **Active conditions:** Isla unusually fussy near the outer walls since symbols appeared
"""

files["greywater_river/old_mill/upper_floor/CONTENTS.md"] = """\
# CONTENTS.md — Upper Floor

## Items Present

### Mundane
- Communal sleeping area (bedrolls and simple beds)
- Small kitchen (basic cookware, modest food stores)
- Patched walls and roof

### Notable
- Tessa's hidden rubbings of the beam symbols — tucked under her mattress
  - DC 13 Perception to notice without searching; DC 10 if searching Tessa's area
- Mara's household journal — practical notes but includes observations about the mill's changes and Tessa's behavior

## Notes for DM
- Tessa's rubbings are the key item here — they confirm the symbols are being actively studied by someone in the family
- Mara's journal is not secret; she will show it if asked directly
"""

files["greywater_river/willowford_bridge/PLACE.md"] = """\
# PLACE.md — Willowford Bridge

## Description and Atmosphere
A sturdy wooden bridge crossing the Greywater River. Wide enough for a cart. The planks are solid but weathered. A small toll booth on the Driftmoor side where the toll farmer watches the crossing. Willows on both banks. On a clear day you can see the mill upstream and the town rooftops downstream.

## Who Is Normally Here
- The toll farmer (Human, male, older — not detailed in source material, DM's discretion)
- Farmers with carts, travelers on foot

## Connections
- Road to Driftmoor (south)
- Road to Old Mill and Mistwood Hills (north)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Toll farmer
- **Recent events:** None
- **Active conditions:** None established
"""

files["greywater_river/willowford_bridge/CONTENTS.md"] = """\
# CONTENTS.md — Willowford Bridge

## Items Present
- Toll booth (simple wooden structure)
- Rope and hook for emergency crossing if bridge is damaged

## Toll
- Foot travelers: 1 cp
- Loaded cart: 5 cp
- Horse and rider: 2 cp

## Notes for DM
- The toll farmer sees everyone who travels the river road — a useful intelligence source if the party thinks to ask
- The bridge is a potential choke point — could be damaged by shadowbeast activity or used as an ambush site
"""

# ═════════════════════════════════════════════
# MISTWOOD HILLS
# ═════════════════════════════════════════════

files["mistwood_hills/PLACE.md"] = """\
# PLACE.md — The Mistwood Hills

## Description and Atmosphere
Rolling hills covered in dense, fog-laden forest stretching northeast of Driftmoor. Towering pines, persistent low fog, eerie atmosphere. Paths seem to shift. Hunters and loggers speak of vanishing routes, strange whispers, and shadowy figures deeper in the woods. The light is always dim under the canopy, even at midday.

The Mistwood is not inherently evil. It is old, and old things do not always welcome visitors.

## Sub-Places
- `old_watchtower/` — crumbling stone tower on a hilltop
- `fey_glade/` — hidden deep in the Mistwood, shimmering with otherworldly energy

## Who Is Normally Here
- Hunters and loggers (near edges only)
- Fennel (Lytha's missing apprentice — somewhere inside)
- Fey presence (subtle, not hostile by default)
- Shadowy figures reported deeper in

## Connections
- Northeast of Driftmoor (road becomes path becomes track)
- Greywater River (source area, northeast)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Unsettled — shadowy figures reported, music heard at night
- **Recent events:** Fennel missing; Kara's horse missing with tracks leading this direction
- **Active conditions:** Haunting music heard from within; faint lights visible at night from town
"""

files["mistwood_hills/CONTENTS.md"] = """\
# CONTENTS.md — The Mistwood Hills (General)

## Creatures
- Wolves (packs, territorial but not aggressive unless threatened)
- Deer, rabbits, foxes (normal wildlife)
- Shadowy figures (nature unclear — fey? shadowbeasts? something else?)
- Fey presence (subtle — flickering lights, whispered sounds, paths that redirect)

## Flora
- Towering pines (dominant)
- Dense undergrowth near fey glade
- Rare herbs deeper in (source for Lytha's more unusual ingredients)

## Environmental Hazards
- Paths seem to vanish: DC 13 Survival to maintain direction; failure results in 1d4 hours of wandering
- Fog: disadvantage on Perception checks beyond 30 ft
- Fey disorientation: anyone who follows the music without awareness risks walking deeper than intended

## Notes for DM
- The Mistwood is a flexible threat space — it can be fey-touched, shadowbeast-infected, or both
- Fennel's location should be decided before the session: captured by fey, hiding from shadows, or lost and injured are all viable
"""

files["mistwood_hills/old_watchtower/PLACE.md"] = """\
# PLACE.md — The Old Watchtower

## Description and Atmosphere
A crumbling stone tower on a hilltop in the Mistwood. Once used to spot incoming raiders from the sea — you can see why, the view from the top is remarkable. Now overgrown with vines and moss. The upper level is partially collapsed. The staircase inside is intact but requires care.

From the top: a clear view of the entire region — the town, the harbor, the Obelisk Reach, the river valley, the sea.

## Who Is Normally Here
- Nobody regularly
- Hunters sometimes shelter here

## Connections
- Mistwood Hills paths (approach from south)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Empty
- **Recent events:** None
- **Active conditions:** None
"""

files["mistwood_hills/old_watchtower/CONTENTS.md"] = """\
# CONTENTS.md — The Old Watchtower

## Items Present

### Mundane
- Crumbling stone walls (partial collapse at top)
- Intact staircase (DC 10 Athletics to climb safely; failure means 1d4 damage from loose stone)
- Old fire beacon at the top (rusted, non-functional)

### Notable
- View from the top: the best vantage point in the region
  - On a clear day: full view of Obelisk Reach, town, harbor, sea, river valley
  - At night: shadowbeast movement visible near the obelisk area
- Scratched into the interior wall: old military marks, dates, and one newer inscription that does not match the style

### Hidden
- Loose stone in the wall (DC 14 Perception): small cache — old coins (5d6 sp), a rusted dagger, a folded note in faded ink (DM's discretion on contents)

## Notes for DM
- The watchtower is a useful reorientation point — showing the party the region from above helps with spatial understanding
- The newer inscription on the wall was left by someone within the last year; its content is DM's discretion
"""

files["mistwood_hills/fey_glade/PLACE.md"] = """\
# PLACE.md — The Fey Glade

## Description and Atmosphere
Hidden deep in the Mistwood. The trees thin suddenly into a circular clearing. The light here is different — warmer, cleaner than the fog-filtered dimness of the surrounding forest. The grass is impossibly green. Flowers bloom that have no business blooming in this season. At night, the glade shimmers with faint colored light. The air smells of something sweet and entirely unidentifiable.

Time may pass differently here. The party may not notice immediately.

## Who Is Normally Here
- Fey presence (level and nature at DM's discretion)
- Possibly Fennel — drawn here or led here

## Connections
- Mistwood Hills deep paths (DC 15 Survival to find deliberately; otherwise stumbled upon)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active fey presence
- **Recent events:** None yet — session not started
- **Active conditions:** The glade is partially shielded from the obelisk's influence — shadowbeasts avoid it
"""

files["mistwood_hills/fey_glade/CONTENTS.md"] = """\
# CONTENTS.md — The Fey Glade

## Items Present

### Natural
- Out-of-season flowers (identifiable as having medicinal properties — DC 13 Nature)
- Clear spring at the glade's edge (water is pure and slightly restorative — drinking restores 1 HP)
- Fey-touched herbs (more potent versions of common herbs — worth double to Lytha Varrow)

### Possibly Present (DM's discretion)
- Fennel (Lytha's apprentice): sheltering here, confused about how long he has been gone
- Fey gift left in the clearing: small object of unexpected value, with an attached obligation

## Creatures
- No shadowbeasts (the glade repels them)
- Fey: level of engagement is DM's discretion — from passive shimmer to active NPC encounter

## Notes for DM
- The glade is a sanctuary and a resource — the party should feel it as a genuinely safe place, which makes it valuable
- Time distortion: anyone who sleeps in the glade wakes feeling fully rested regardless of actual time passed, but may have missed events
- The fey-touched herbs double Lytha's potion efficacy if used as ingredients
"""

# ═════════════════════════════════════════════
# AZURE SEA
# ═════════════════════════════════════════════

files["azure_sea/PLACE.md"] = """\
# PLACE.md — The Azure Sea

## Description and Atmosphere
Cold, rocky coastline with strong tides and unpredictable weather. Driftmoor's harbor is one of the few safe spots for boats in the area. The water is dark blue-gray, beautiful in daylight and threatening at dusk. The sea stacks rise from the water like giants frozen in motion. The Drowned Isle is visible only at low tide — a dark hump of rock and ruins.

The sea is where Driftmoor's livelihood comes from. It is also where some of its fear lives.

## Sub-Places
- `sea_stacks/` — isolated rock formations near shore
- `drowned_isle/` — partially submerged island, visible at low tide

## Who Is Normally Here
- Driftmoor fisherfolk (during the day, not after dark recently)
- Trade vessels (occasional)
- Shadowy shapes beneath the harbor surface (recent, unexplained)

## Connections
- Driftmoor harbor (the safe landing point)
- Coastal path south to Plains of Stonehearth
- Sea routes to other settlements (days of travel)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Unsettled — fisherfolk avoiding certain waters
- **Recent events:** Shadowy shapes reported under harbor water; barnacle-covered chest found on Drowned Isle
- **Active conditions:** Fisherfolk avoiding the area around the Drowned Isle
"""

files["azure_sea/CONTENTS.md"] = """\
# CONTENTS.md — The Azure Sea (General)

## Creatures
- Fish (abundant, primary food source)
- Giant crabs (coastal rocks, aggressive if disturbed)
- Shadowy aquatic shapes (near harbor and Drowned Isle — nature unknown, possibly shadowbeast variant)

## Environmental Hazards
- Strong tides: caught in open water during tide change requires DC 14 Athletics
- Coastal storms: fast-moving, can trap parties on the sea stacks or Drowned Isle without warning
- Unpredictable weather: DC 12 Survival to read the signs 1 hour ahead

## Notes for DM
- The shadowy harbor shapes are a low-key ongoing mystery — they have not attacked anything yet
- The Drowned Isle is the sea-based dungeon space; time the party's access to coincide with low tide for atmosphere
"""

files["azure_sea/sea_stacks/PLACE.md"] = """\
# PLACE.md — The Sea Stacks

## Description and Atmosphere
Tall isolated rock formations rising from the water near the shore. The legend says they were once giants turned to stone. Looking at them in evening light, when the rock takes on reddish hues and their shadows fall across the water, the legend is not difficult to believe.

Seabirds nest in the crevices. The bases are accessible at low tide on foot, barely. At high tide the bases are submerged and approach requires swimming or a boat.

## Who Is Normally Here
- Seabirds (nesting)
- Fisherfolk sometimes shelter behind them from weather

## Connections
- Coastal path from Driftmoor (accessible at low tide)
- Azure Sea (accessible by boat at any tide)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Seabirds only
- **Recent events:** None
- **Active conditions:** None established
"""

files["azure_sea/sea_stacks/CONTENTS.md"] = """\
# CONTENTS.md — The Sea Stacks

## Items Present

### Natural
- Seabird nests (eggs in season — disturbing them angers the birds)
- Tidal pools at the bases (crabs, small fish, sea flora)
- Hand and footholds suitable for climbing (DC 12 Athletics)

### Hidden
- A carved marking on the landward face of the largest stack (DC 14 Perception)
  - Similar style to cliff symbols at the Obelisk Reach
  - Suggests the obelisk's influence or the civilization that created it extended to the coast

## Notes for DM
- The carving connects the sea stacks to the broader symbol mystery
- The stacks make a good dramatic set piece for an encounter — high, exposed, tide-dependent
"""

files["azure_sea/drowned_isle/PLACE.md"] = """\
# PLACE.md — The Drowned Isle

## Description and Atmosphere
A partially submerged island visible only during low tide — a dark hump of ancient rock and half-collapsed stone structures rising from the sea. Fisherfolk call it cursed. They are not wrong, exactly. The ruins suggest something was built here deliberately, long ago. The sea has been reclaiming it for centuries.

At low tide: accessible on foot from the sea stacks with careful movement. Two hours of access before the tide returns. At high tide: submerged to the point where only the highest ruins break the surface.

## Who Is Normally Here
- Nobody, by choice
- Shadowy shapes in the water around it at night

## Connections
- Sea stacks (accessible at low tide, DC 11 Athletics across the exposed rock)
- Azure Sea (by boat)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Unexplored by party
- **Recent events:** A local fisherman found a barnacle-covered chest on the isle and was too afraid to open it
- **Active conditions:** Chest present; shadowy shapes around the isle at night
"""

files["azure_sea/drowned_isle/CONTENTS.md"] = """\
# CONTENTS.md — The Drowned Isle

## Items Present

### Ruins
- Half-collapsed stone structures (same unknown civilization as Obelisk Reach symbols)
- Carvings on surviving walls (same symbol set, more complete — DC 12 Arcana for partial translation)
- One intact chamber below the ruins (flooded at high tide, accessible at low tide)

### The Chest
- Barnacle-covered, old, heavy
- Lock: rusted but intact (DC 13 Thieves' Tools, or DC 16 STR to force)
- Contents (DM's discretion — suggestions):
  - Maps of the region from before the obelisk shattered, showing the isle as a waypoint
  - A sealed glass vial containing dark liquid (shadowbeast essence? potion ingredient?)
  - An intact document in the same language as the obelisk inscriptions

### Flooded Chamber (at low tide only)
- Intact altar to an unknown entity
- Obelisk fragment embedded in the altar stone (not removable without destroying the altar)
- Skeletal remains of someone who came here and did not leave

## Creatures
- Giant crabs (territorial, 1d4 near the accessible areas)
- Shadowy aquatic shapes (1d2 in the water around the isle at night; avoid the isle itself)

## Notes for DM
- The Drowned Isle is the campaign's sea-based mystery location — it ties the obelisk to a larger pre-existing structure
- Two-hour low tide window creates natural time pressure for exploration
- The altar fragment is the most significant find here — it explains that the obelisk was part of a network, not a standalone structure
"""

# ═════════════════════════════════════════════
# PLAINS OF STONEHEARTH
# ═════════════════════════════════════════════

files["plains_of_stonehearth/PLACE.md"] = """\
# PLACE.md — The Plains of Stonehearth

## Description and Atmosphere
Windswept grasslands dotted with rocky outcroppings and small caves, southeast of Driftmoor. Used for grazing sheep and goats. Sparsely populated — a few farmsteads visible from a distance, smoke from chimneys. The wind is constant here, and the grass moves in waves. The rocky outcroppings break the flatness at intervals.

Shadowbeasts have been sighted here, preying on livestock and unwary travelers. The farmers are frightened and their fences keep getting broken.

## Who Is Normally Here
- Sheep and goat farmers
- Livestock
- Shadowbeasts, at night

## Connections
- Southeast of Driftmoor (coastal path)
- Plains extend southeast beyond the immediate region

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active shadowbeast predation on livestock
- **Recent events:** Multiple livestock kills; one farmer reported seeing a shadowbeast in daylight
- **Active conditions:** Farmers requesting help; shadowbeast den possibly in the rocky outcroppings
"""

files["plains_of_stonehearth/CONTENTS.md"] = """\
# CONTENTS.md — The Plains of Stonehearth

## Creatures
- Sheep and goats (farmed, numerous)
- Wolves (occasional, less threatening than shadowbeasts currently)
- Shadowbeasts: 1d4 at night, hunting livestock; possible den in cave system within the outcroppings

## Items Present
- Rocky outcroppings: small caves suitable for shelter or shadowbeast lairs
- Farmsteads: basic structures with livestock pens (some broken, recent)
- Shadowbeast kills: identifiable carcasses (Lytha Varrow can use parts; DC 11 Nature to extract useful components)

## Environmental
- Constant wind: disadvantage on ranged attacks in windy conditions
- Open terrain: no cover except rocky outcroppings (30-60 ft between cover points)
- Caves in outcroppings: dark, potentially occupied

## Notes for DM
- The plains are the most accessible combat encounter zone in the campaign
- A shadowbeast den in the caves is a natural early dungeon — small, straightforward, yields shadowbeast parts for Lytha
- Farmer NPCs here are not detailed — use as needed for urgency and local color
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
