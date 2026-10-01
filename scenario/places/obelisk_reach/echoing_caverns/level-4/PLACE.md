# PLACE.md — The Royal Precinct of the Echoing Caverns

## Description and Atmosphere
The Royal Precinct is a series of royal chambers carved with intricate detail,
reflecting the former glory of the buried kingdom. The air is colder here,
carrying the scent of ancient stone and the faint metallic tang of the deep
earth. The walls are lined with faded tapestries and cracked statuary. A
narrow stairway connects to level 3 above.

## Resident NPCs and Creatures

### royal_guard_commander
- **type:** creature
- **creature_file:** scenario/creatures/humanoid/guard/royal_commander/CREATURE.md
- **soul_file:** scenario/creatures/humanoid/guard/royal_commander/SOUL.md
- **identity_file:** scenario/creatures/humanoid/guard/royal_commander/IDENTITY.md
- **scene_handle:** the royal guard commander
- **position:** 60, 110, -120
- **activation:** zone_entry:Royal Guard Checkpoint

### seven_chains_mechanism
- **type:** magical_construct
- **location:** Throne of Seven Chains
- **activation:** zone_entry:Throne of Seven Chains
- **description:** Seven thick iron chains hanging from the ceiling, each with a heavy, rusted link.

## Who Is Normally Here
- Royal guard commander and two guards (Royal Guard Checkpoint/Barracks)
- Court cooks preparing meals (Court Kitchens)
- The seven chains mechanism in the throne room
- Occasional shadowbeast scouts exploring from the deeper chambers

## Scene Introductions

### royal_guard_commander
A tall, stern-faced guard in ornate but battered armor greets you at the
checkpoint. His eyes scan each of you, missing nothing. The air smells of
old leather and cold iron. Behind him, a heavy iron door with a complex
mechanism stands closed.

"State your business in the Royal Precinct," he says, his voice firm but not
unfriendly. "The throne room is off-limits to all but those with royal blood.
The rest of the Precinct is accessible, but tread carefully — ancient magics
lurk in these halls."

## Connections
- Level 3: stairs from city (narrow stairway requiring DC 10 Dexterity to navigate safely)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active — royal guards on duty, throne mechanism dormant
- **Recent events:** None yet — session not started
- **Active conditions:** Throne mechanism requires royal blood to activate; ancient magics unstable
