# Scene Config — The Echoing Caverns

## Scene
- **scene_name:** echoing_caverns
- **title:** ECHOING CAVERNS
- **narrative_title:** The Echoing Caverns
- **transcript_title:** ECHOING CAVERNS — Seraphina, Thorgrim, Amara, Gilthaness
- **character_summary:** Seraphina, Thorgrim, Amara, Gilthaness
- **default_turns:** 8
- **geometry_file:** scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md
- **place_file:** scenario/places/obelisk_reach/echoing_caverns/PLACE.md

## Time
- **hour:** 14
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** ollama
- **model:** gemma4:26b

## Scene Notes

The party has just descended through the crack in the cliff face beneath the
Obelisk Reach. Daylight bleeds in behind them; ahead, the Entry Chamber opens
into shadow. None of them has been here before. They know only what Father
Elden told them: that he came here decades ago, that his three companions did
not leave, and that something in these caves still hums in time with the
obelisk above.

## Mission Objective (shared)

Father Elden did not send the party into these caverns to map every wall or
catalog every stain. He sent them to find the remains of his three lost
companions, recover them with dignity, and bring them back to Driftmoor for
proper burial.

That means the party should search each chamber for useful evidence, but not
become trapped there. Once a chamber's obvious clues have been checked and no
new information is emerging, the correct next step is to press deeper toward
the chambers where the remains are likely to be found.

The mission is not complete until the remains are located and recovered, or a
real danger or hard barrier forces the party to withdraw.

This is exploration first. Combat is possible (shadowbeasts in deeper
chambers) but should not be forced. Watch for: who takes point, who watches
the rear, who reads the carvings, who picks up what.

## Spelunking Notes (shared)

Father Elden gave the party careful counsel before they descended. The
characters know, in-fiction, the following caver's wisdom:

- **Stay together.** No one wanders out of torchlight alone. The caverns
  echo wrong; a lost voice may not find its way back to the right chamber.
- **Mark the path.** Chalk arrows at every junction, pointing back toward
  the entrance. Do not trust memory in here. (Amara carries chalk; Seraphina
  has charcoal sticks.)
- **One torch lit, one held in reserve.** Amara's torch is the lit one.
  Thorgrim has a second wrapped in oilcloth in his pack.
- **Three knocks means trouble.** A pre-arranged signal: three sharp raps
  of metal on stone, repeated, means come back to this chamber now.
- **The pool is not for drinking, washing, or wading.** Whatever it is,
  it isn't only water.
- **The remains are to be wrapped before being moved.** Father Elden was
  explicit: bones first, dignity second only to safety.
- **Search each chamber, then move.** Father Elden was explicit that haste
  kills underground, so walls, floors, corners, and ceilings deserve an
  initial look. But he did not send them below to linger forever over a
  single stain or crack. Once the obvious clues in a chamber have been
  checked, the party is to press onward toward the deeper chambers where his
  companions' remains are most likely to lie.

## Characters

### seraphina
- **type:** player
- **soul_file:** scenario/people/players/seraphina/SOUL.md
- **identity_file:** scenario/people/players/seraphina/IDENTITY.md
- **position:** 105, 315

### thorgrim
- **type:** player
- **soul_file:** scenario/people/players/thorgrim/SOUL.md
- **identity_file:** scenario/people/players/thorgrim/IDENTITY.md
- **position:** 110, 310

### amara
- **type:** player
- **soul_file:** scenario/people/players/amara/SOUL.md
- **identity_file:** scenario/people/players/amara/IDENTITY.md
- **position:** 115, 315

### gilthaness
- **type:** player
- **soul_file:** scenario/people/players/gilthaness/SOUL.md
- **identity_file:** scenario/people/players/gilthaness/IDENTITY.md
- **player_transport:** telegram
- **channel:** telegram
- **host:** ultra
- **inbox:** ~/messages/from-gilthaness
- **outbox:** ~/messages/to-gilthaness
- **position:** 110, 320

<!-- Authoring quick reference:
- Optional start carry-state fields in character blocks:
  - **in_hand:** snapped_torch, mug of ale
  - **worn:** wooden_vine_carved_bracelet
- Aliases: **held_items** == **in_hand**, **worn_items** == **worn**
-->

## Scene Introductions

### seraphina
You squeezed through the crack first — of course you did; the dwarf wouldn't fit and the cleric was carrying a torch you didn't want anywhere near your eyes. Inside: a low, wide chamber, colder than the hillside above, and unnaturally still. The wind that scoured the Reach does not follow you down here. There is an old iron bracket on the wall just inside, rust-pitted; tally marks scratched into the rock nearby — nineteen vertical, a slanting twentieth that trails off. Someone was counting something here, a long time ago, and stopped mid-stroke. From deeper in the cave: a faint, distant sound, not wind, not water, almost rhythmic. Father Elden told you three of his companions died down here. He did not tell you what killed them.

Elden's parting words ride the back of your mind: *stay in torchlight, mark every turn, three knocks means come back.* You have a stub of charcoal in a belt pouch for marking; Amara has chalk. Whatever quiet thing you do alone in here, do it within sight of the others.

More important than any carving or stain, though, is the reason you came:
Father Elden wants his companions found and carried home. If this chamber
yields nothing new, the job is deeper in.

### thorgrim
You shouldered through the crack last, plate scraping stone, and straightened in a chamber that should not be this cold. Daylight from the entrance dies a few paces in. The half-elf is already crouched at the wall reading scratches like a poacher reading tracks; the cleric's torch is up and the shadows behind it lean wrong. There is a sound from deeper in — something between a hum and a held note, threading the silence. Your axe is already loose in your hand. You did not draw it. Father Elden's voice in your memory: *three of them. Sera went in first. None of them came out.* You are first into the dark on this one. Make it count.

Elden's other words sit closer: *stay together, mark every junction, three knocks of steel on stone means form up here.* You carry a second torch wrapped in oilcloth, and a stub of chalk in your belt pouch beside the whetstone. Underground is dwarf country; the others will look to you for tempo. Don't let them strung out across more than one chamber.

He did not send you down here to admire old scratches. Find the dead, secure
them, and bring them back out. If the first chamber gives up its measure,
drive the group deeper.

### amara
The crack opened into a chamber colder than any cave should be in spring. Your torch threw light in a wedge that the dark refused to hold — shadows pooled at the edges of the chamber like water finding its level. The dwarf came through behind you, plate ringing against stone; the half-elf rogue was already inside, reading scratches on the wall. Lathander's warmth in your chest felt distant here, as if the dawn-god's reach did not extend underground in quite the same way. You could feel something deeper in: not malice, exactly — a pressure, a hum that matched the obelisk above. Father Elden trusted you with this. *Bring back what you can,* he had said. *Even the bones.*

Elden gave you the chalk himself, pressed into your palm at the trailhead with a working cleric's seriousness: *mark every junction, both directions. Stay in torchlight. If anything goes wrong, three knocks on stone and we form up.* The torch in your hand is the only lit one; Thorgrim has the second in reserve. Whatever the pool is, you are not to wade. The remains, when you find them, are to be wrapped — he was firm on that.

His charge was plain: bring back what can still be brought back, even if it is
only bones. If this chamber has no answer, the answer lies farther in.

### gilthaness
The cave air carries old damp stone, cold iron, and the faint metallic edge of
spent magic. You have walked ruin-sites before, but this place feels tuned to a
frequency just above hearing, as if the rock itself remembers a spell half-cast
and never resolved. Seraphina is already reading the chamber walls; Thorgrim is
setting the group's tempo; Amara's torch holds a fragile island of order in the
dark.

You are here because old wounds in Driftmoor have started speaking again, and
you are done ignoring voices that carry this kind of resonance.

## Game State Sections
- file: scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md
- header: Relevant Lore (DM only) | file: scenario/things/obelisk_shards.md
- header: Creatures in Scene | file: scenario/creatures/miscellaneous/giant_spider/CREATURE.md
- header: Mission Objective | file: scenes/echoing_caverns.md#Mission Objective
- header: Scene Notes | file: scenes/echoing_caverns.md#Scene Notes
