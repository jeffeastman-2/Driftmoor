# Gate of Two Peoples

## Description
The shaft opens into a low gatehouse built in two incompatible styles made to
cooperate. Dwarven stonework carries the load; silver elven ribs curve through
it like the frame of an instrument. Neither half opens the gate alone. The
wheel establishes tension while the bells must sound the answering cadence.

An inscription gives the prison's clearest early clue: "Stone holds the
chamber. Promise holds the chain. The living hold the lock. Song determines
the turning." Beyond it, the avenue reveals the scale of the buried city, but
the words still do not say which way the prison must turn.

## Ambient
- light: dim violet seam-light around the closed gate
- sound: every noise returns as two notes, one metallic and one stone-deep
- smell: dust, old bronze, dry webbing
- temperature: cold and motionless
- footing: level fitted stone

## Items
### dwarven_gate_wheel
- label: Dwarven gate wheel
- size: large
- weight: 240 lb
- pickable: false
- wearable: false
- flavor_only: false
- description: A shoulder-high iron wheel that tensions the gate's stone bolts.
- appearance by distance:
  - intermediate: a broad iron wheel set into the west wall
  - far: a dark circular mechanism
  - distant: a round shadow against fitted stone
- interactions:
  - examine: Dwarven numerals mark three tension settings; only the middle setting aligns the elven resonators. A socket in its hub fits a heavy mace haft as an improvised lever.
  - press: The wheel turns under sustained force and holds at each numbered detent.

### elven_resonance_bells
- label: Elven resonance bells
- size: medium
- weight: 30 lb
- pickable: false
- wearable: false
- flavor_only: false
- description: Seven silver cups on a curved frame, each sounding without being struck when touched.
- appearance by distance:
  - intermediate: a fan of tarnished silver bells on the east wall
  - far: several pale cups in a curved line
  - distant: a faint silver arc
- interactions:
  - examine: The seal requires three notes sounded simultaneously, not a sequential melody.
  - press: A touched bell sounds a clear tone. The correct three-note chord opens the gate only while the wheel holds the middle setting.

## Features / landmarks
- gate_threshold: sealed double gate operated by both mechanisms
- avenue_threshold: first view down the processional city axis

## Creatures present
- none

## Exits
- north: Broken Lift
- south: Avenue of Sleeping Blades
