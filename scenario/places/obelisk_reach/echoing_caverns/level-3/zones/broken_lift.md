# Broken Lift

## Description
A dwarven freight shaft descends from the deliberately collapsed tunnel. Its
iron-bound cage survives below the smashed upper mechanism, suspended crookedly
between green-black chains. Chisel scars above show that the destroyers broke
the hoist from the cavern side after sending their last party down.

The cage can be reached by repairing the brake, climbing the chains, or making
a dangerous descent. Counterweight chains occasionally become briefly
insubstantial, and loud work advances the city's awakening. A fall ends at the
gatehouse roof rather than the crypt, but it is still far enough to maim.

## Ambient
- light: none except carried light
- sound: slow chain-creak and falling grit
- smell: cold iron, old grease, wet limestone
- temperature: cold with a faint updraft
- footing: tilted cage floor, loose rubble, open drops

## Items
### snapped_hoist_chain
- label: Snapped hoist chain
- size: large
- weight: 180 lb
- pickable: false
- wearable: false
- flavor_only: false
- description: A deliberately cut dwarven chain whose upper links are peeled apart by wedges.
- appearance by distance:
  - intermediate: a massive severed chain hanging beside the cage
  - far: a dark segmented line in the shaft
  - distant: a narrow black interruption overhead
- interactions:
  - examine: Tool marks prove the chain was destroyed from above, after the cage descended.
  - search: One link bears both a dwarven maker's stamp and a later elven sealing rune. Another contains a trapped echo that repeats something a party member has not said yet.

### counterweight_brake
- label: Counterweight brake
- size: medium
- weight: 70 lb
- pickable: false
- wearable: false
- flavor_only: false
- description: A toothed bronze brake controlling the surviving lower counterweight.
- appearance by distance:
  - intermediate: a greened bronze lever and ratchet beside the cage
  - far: a blocky metal mechanism on the shaft wall
  - distant: a dull green shape beside the chains
- interactions:
  - examine: The brake is jammed, not broken; proper leverage and cleaning can make the cage descend safely.
  - press: Releasing it without controlling the lever drops the cage violently to the gatehouse level.

## Features / landmarks
- upper_lift_mouth: rubble-choked opening to the Collapsed Tunnel
- lift_cage: dwarven freight dumbwaiter, large enough for ore carts or a party

## Creatures present
- none

## Exits
- up: Collapsed Tunnel in the Echoing Caverns
- down: Gate of Two Peoples
