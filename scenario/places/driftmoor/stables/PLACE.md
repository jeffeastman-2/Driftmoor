# PLACE.md — The Stables

## Place Identity
- **type:** stable
- **aliases:** stable, stables, livery, horse stable, The Stables

## Description and Atmosphere
Clean and well-maintained — Kara's domain. Space for a dozen horses. Saddle racks and feed bins neatly organized. Smells of hay and horse. The animals here are calm around Kara and noticeably less so around strangers.

The horses near the Mistwood road stall have been spooked for weeks.

## Resident NPCs and Creatures

### kara
- **type:** npc
- **soul_file:** scenario/people/npcs/kara/SOUL.md
- **identity_file:** scenario/people/npcs/kara/IDENTITY.md

### bramble
- **type:** creature
- **name:** Bramble
- **creature_file:** scenario/creatures/horse/CREATURE.md
- **soul_file:** scenario/creatures/horse/SOUL.md
- **identity_file:** scenario/creatures/horse/IDENTITY.md
- **scene_handle:** the bay mare Bramble
- **faction:** neutral
- **position:** 30, 55

### thistle
- **type:** creature
- **name:** Thistle
- **creature_file:** scenario/creatures/horse/CREATURE.md
- **soul_file:** scenario/creatures/horse/SOUL.md
- **identity_file:** scenario/creatures/horse/IDENTITY.md
- **scene_handle:** the dapple-gray mare Thistle
- **faction:** neutral
- **position:** 66, 55

## Who Is Normally Here
- **Kara Stonebrook**
- **Bramble** — a steady bay mare Kara often uses to calm the other horses
- **Thistle** — a watchful dapple-gray mare, currently uneasy near the Mistwood-side stalls
- Other horses may be present as boarders or Darrin's stock

## Scene Introductions

### kara
You are in the stables brushing down the bay mare. She is still jittery — all the horses have been since the night the gelding vanished. You found the tracks yourself. Claws, not hooves, heading into the Mistwood tree line. Your father told you to forget about it. You have not forgotten about it. Through the stable wall you can hear the forge hammer and the dwarf moving around. He has been studying those marks on the wall. You want to ask him what he thinks.

### bramble
Morning light reaches your stall. Kara is close, brushing your bay coat with
the familiar steady rhythm. Her voice is safe. The other mare is tense, and
the empty stall still carries the fading scent of the herd mate who did not
return. You stand quietly, one hind hoof resting, listening to the hammer
beyond the wall.

### thistle
The empty stall smells wrong. Beyond the stable door, the road wind carries a
trace you do not know and do not trust. Your dapple-gray skin twitches; your
ears keep turning toward Mistwood. Bramble is nearby and Kara's voice is
familiar, so you remain in your stall, alert but not panicked.

## Connections
- Road (outside)
- Forge (interior door)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Kara Stonebrook, Bramble, Thistle
- **Active conditions:** Horses near Mistwood stall unsettled; one prize horse missing
