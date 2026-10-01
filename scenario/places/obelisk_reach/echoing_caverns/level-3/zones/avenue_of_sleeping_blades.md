# Avenue of Sleeping Blades

## Description
The avenue is a broad ceremonial spine rather than a corridor. Armored drow
stand cocooned in wall alcoves with blades drawn, preserved in the instant an
alarm reached them. Side streets vanish behind curtains of temporal web. In
the avenue's middle, a collapsed civic rotunda forces travelers around its
east or west side and breaks the direct charge toward the Hall.

Four doors create choices rather than four isolated rooms: two enter opposite
ends of the Chainworks, one exposes the web-sealed Sleeping District, and one
leads through the mirrors to an alternate Hall entrance.

Cause and effect slip here. Bright light makes heads turn inside unopened
cocoons. Speaking a creature's name makes the nearest sleeper repeat it.
Damaging one cocoon wakes its occupant and begins stirring the next. A suspended
mage silently mouths a counterspell whenever magic is cast nearby.

## Ambient
- light: dim violet pulses from cocoons and webbed streets
- sound: muffled near the web; sharp and exposed around the rotunda
- smell: mineral dust and the faint ozone of suspended magic
- temperature: cold, with warmer air trapped close to occupied cocoons
- footing: broad paving split by fallen rotunda stone

## Items
### sleeping_blade_cocoons
- label: Sleeping blade cocoons
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: Rows of translucent temporal cocoons holding armed drow sentries at their final posts.
- appearance by distance:
  - intermediate: motionless armored figures behind glassy violet web
  - far: ranks of pale upright forms in wall alcoves
  - distant: repeating violet silhouettes down the avenue
- interactions:
  - examine: The occupants breathe only when the web pulses; to them no measurable time is passing.
  - search: One cocoon near the rotunda is already hairline-cracked and will open if the avenue's web is disturbed again.

### rotunda_mosaic
- label: Shattered civic mosaic
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A broken floor mosaic showing Nhal'Zirath suspended between the Material Plane and Feywild.
- appearance by distance:
  - intermediate: colored stone fragments forming two overlapping cities
  - far: a fractured circle of violet and green tesserae
  - distant: a colored ring amid grey rubble
- interactions:
  - examine: Eight crowned figures surround a ninth whose face has been deliberately removed.
  - search: The missing face was pried out before the collapse; its setting matches the empty center frame in the Hall.

### suspended_drow_mage
- label: Suspended drow mage
- size: medium
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A robed drow mage suspended upright in translucent web, lips moving a heartbeat before nearby spells are cast.
- appearance by distance:
  - intermediate: a cocooned robed figure silently forming arcane words
  - far: a slender dark figure behind violet web
  - distant: a pale upright shape among the sentries
- interactions:
  - examine: The mage is not awake, but mouths the gestures of counterspell before a nearby caster completes a spell.
  - search: A cracked spell focus remains clenched in one hand inside the cocoon.

## Features / landmarks
- chainworks_upper_door: upper west side door into the machinery loop
- sleeping_district_seal: upper east side door revealing the city's true scale
- civic_rotunda: impassable central collapse with routes on both sides
- chainworks_lower_door: lower west return from the machinery loop
- mirror_approach_door: lower east alternate route to the Hall
- hall_main_threshold: processional entrance to the Hall

## Creatures present
- sleeping_sentry

## Exits
- north: Gate of Two Peoples
- west upper and lower: Chainworks loop
- east upper: Sleeping District
- east lower: Mirror Approach
- south: Hall of Unchosen Queens
