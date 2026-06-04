# Scene Config — The Broken Lantern

## Scene
- **scene_name:** broken_lantern
- **title:** BROKEN LANTERN
- **narrative_title:** The Broken Lantern
- **transcript_title:** BROKEN LANTERN — Kaelin, Cinnabar, Tess, Wilfred, Bran, Marda
- **character_summary:** Kaelin, Cinnabar, Tess, and regulars at the Broken Lantern
- **default_turns:** 4
- **geometry_file:** scenario/places/driftmoor/broken_lantern/GEOMETRY.md
- **place_file:** scenario/places/driftmoor/broken_lantern/PLACE.md

## Time
- **hour:** 20
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** ollama
- **model:** gemma4:26b

## Scene Notes

This is an exploration/social scene in the village tavern. No combat expected.
Kaelin has no coin and is hungry. They need to earn a meal.
Tess is sharp, fair, and always looking for useful people.
Wilfred is at the bar muttering about shadow giants near the obelisk — this is a real plot thread, not just drunk talk.
Bran and Marda are in a low-grade argument over a delayed fishing payout and have both had enough ale to be loud about it.
The meeting room behind the kitchen has suspicious guests.
Strange noises have been reported from an unoccupied upstairs room.
Politeness and tavern norms matter: greetings, service talk, and social feelers should happen early unless someone has a clear reason to stay silent.

# Exit Motivations (DM only)

Characters may leave this scene. Recognise and permit these:
- Kaelin is a wanderer — they may want to explore the village, especially if they hear about the forge symbols or the pawnshop.
- Tess may send someone to investigate the noises upstairs (this leads to a sub-location, not a scene exit).
- If Wilfred's obelisk talk catches Kaelin's ear, they may head north toward the obelisk reach at dawn.
- The suspicious meeting room guests may leave — Tess may ask someone to follow them.

## Characters

### kaelin
- **type:** player
- **soul_file:** scenario/people/players/kaelin/SOUL.md
- **identity_file:** scenario/people/players/kaelin/IDENTITY.md

### cinnabar
- **type:** player
- **soul_file:** scenario/people/players/cinnabar/SOUL.md
- **identity_file:** scenario/people/players/cinnabar/IDENTITY.md

### tess
- **type:** npc
- **soul_file:** scenario/people/npcs/tess/SOUL.md
- **identity_file:** scenario/people/npcs/tess/IDENTITY.md

### wilfred
- **type:** npc
- **soul_file:** scenario/people/npcs/wilfred/SOUL.md
- **identity_file:** scenario/people/npcs/wilfred/IDENTITY.md

### bran
- **type:** npc
- **soul_file:** scenario/people/npcs/bran/SOUL.md
- **identity_file:** scenario/people/npcs/bran/IDENTITY.md

### marda
- **type:** npc
- **soul_file:** scenario/people/npcs/marda/SOUL.md
- **identity_file:** scenario/people/npcs/marda/IDENTITY.md

## Scene Introductions

### kaelin
Evening at the Broken Lantern. You pushed through the door ten minutes ago — new town, no coin, empty stomach. The room is half full. Fisherfolk, a couple of farmers, a drunk at the end of the bar muttering about shadow giants. The woman behind the bar has already looked you over twice. You unslung your lute and found a stool near the fire. If you play well enough, dinner is free. It usually is.

### cinnabar
You arrive at the Broken Lantern with road dust still in your cuffs and the
town's salt wind still in your hair. The common room is warm, crowded, and full
of listening opportunities. A halfling bard is already set up by the fire,
working the room for food and coin. Behind the bar, Tess Malwin is watching
everyone at once and pretending not to. You came here to listen before you act.
If Driftmoor is fraying, taverns hear it first.

### tess
Evening crowd. The usual faces. Wilfred is three ales deep and talking about shadow giants again. Then the door opens and a halfling walks in — wild hair, patched clothes, lute across their back, and the particular confidence of someone who has talked their way into a meal before. They have already found the stool by the fire. No coin visible. You have seen this act. The question is whether this one is worth feeding.

### wilfred
You are already halfway through a story no one asked for and one-third through another ale someone else paid for. You keep saying the same thing: you saw shapes near the obelisk cliffs that were too tall and too wrong to be men. Most people in the room roll their eyes when you start, but Tess listens just enough to make you think you are not entirely mad.

### bran
You are at a side table with Marda, arguing about a fishing payout that came up short after gear repairs. You think someone in town is skimming. Marda thinks you are counting wrong and picking fights because you hate being embarrassed in public. The ale has not improved either of your tempers.

### marda
You are at a side table with Bran, trying to keep a straightforward accounting argument from becoming a tavern scene. Bran is loud and stubborn. You are tired, annoyed, and very aware that everyone can hear at least half of this. You do not mind an audience if it helps settle the point.

## Game State Sections
- header: Scene: The Broken Lantern (Tavern) | file: scenario/places/driftmoor/broken_lantern/PLACE.md
- file: scenario/places/driftmoor/broken_lantern/CONTENTS.md
- header: Scene Notes | file: scenes/broken_lantern.md#Scene Notes
