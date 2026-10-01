# PLACE.md — The Freight Quarter of the Echoing Caverns

## Description and Atmosphere
The Freight Quarter is a series of storage and labor chambers carved into the
cavern wall near the level transition points. The air smells of damp earth,
old grain, and the faint sulfurous tang of beast pens. Torches burn in wall
brackets along the main corridors, but side chambers dim quickly. The broken
lift shaft connects to level 1 above; the gate of two peoples leads down to
level 3.

## Resident NPCs and Creatures

### freight_master_goblin
- **type:** creature
- **creature_file:** scenario/creatures/intelligent/goblin/freight_master/CREATURE.md
- **soul_file:** scenario/creatures/intelligent/goblin/freight_master/SOUL.md
- **identity_file:** scenario/creatures/intelligent/goblin/freight_master/IDENTITY.md
- **scene_handle:** the freight master
- **position:** 45, 145, -75
- **activation:** zone_entry:Factor's Office

### caged_beasts
- **type:** creature_group
- **location:** Beast Pens
- **activation:** zone_entry:Beast Pens
- **description:** Three emaciated giant lizards chained to iron bollards, growing more agitated as the party approaches.

## Who Is Normally Here
- Freight master and two goblin underlings (Factor's Office)
- One or two beast handlers (Cistern/Cold Larder)
- The caged beasts in the pens
- Occasional shadowbeast scouts exploring from level 3

## Scene Introductions

### freight_master_goblin
A wiry goblin in patched leather greets you with a toothy smile that doesn't
reach his eyes. He stands near a heavy oak desk, a ledger open before him.
The air smells of damp parchment and old ink. Behind him, a metal door with a
rusted keyhole leads deeper into the facilities.

"Welcome, welcome, travelers! Just passing through, I expect? The freight
master is always happy to assist honest folk. Though..." His eyes flick to
the beast pens beyond. "There are rules. Must follow the rules. Now, what
brings you to the Freight Quarter?"

## Connections
- Level 1: broken lift shaft (DC 12 Strength to climb the collapsed lift cage)
- Level 3: gate of two peoples (requires turning the rusted gate lever)

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active — freight operations in progress, beasts agitated
- **Recent events:** None yet — session not started
- **Active conditions:** Lift shaft partially collapsed; beasts growing restless
