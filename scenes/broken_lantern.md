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
- **position:** 16, 26

### cinnabar
- **type:** player
- **soul_file:** scenario/people/players/cinnabar/SOUL.md
- **identity_file:** scenario/people/players/cinnabar/IDENTITY.md
- **position:** 20, 22

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

## Game State Sections
- header: Scene: The Broken Lantern (Tavern) | file: scenario/places/driftmoor/broken_lantern/PLACE.md
- file: scenario/places/driftmoor/broken_lantern/CONTENTS.md
- header: Scene Notes | file: scenes/broken_lantern.md#Scene Notes
