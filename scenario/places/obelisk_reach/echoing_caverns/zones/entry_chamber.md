# Entry Chamber

## Description

The crack in the cliff face opens into a low, wide chamber—no taller than a tall man at its highest point. Daylight bleeds in through the entrance as a pale wedge that dies quickly against the dark stone. The floor is uneven, scattered with old rockfall, water-smoothed in places. The air is colder than it should be for the season, and unnaturally still; the wind that scours the Reach above does not follow you down here.

Evidence of recent death marks this space. A snapped torch lies near the south passage mouth, its pitch head unburned. A dark stain smears the floor a few paces north of that passage, drawn out into a tapering streak that points south. A leather pack, half-buried under fallen rock, slumps against the west wall. And running across the chamber floor toward the passage threshold are parallel scrapes—the kind something heavy makes when dragged. *Someone died here. Someone else moved them.*

Listening, you become aware of a faint, distant sound from deeper in: not wind, not water—something in between, almost rhythmic. The space carries an older weight than mere abandonment; this chamber has secrets it has not shared in years.

## Ambient

- **Light:** None. Daylight from the entrance fades to deep shadow within twenty feet. Beyond that, torch-light and darkvision only.
- **Sound:** The chamber echoes with a false quality—footsteps carry strangely here, occasionally seeming to precede themselves. The deeper hum from the lower caverns is barely audible, like the stone remembering something.
- **Temperature:** Cold. Not knife-edge, but the kind of cold that soaks into clothes and stays.
- **Footing:** Uneven stone, treacherous in shadow. Water-smoothed in patches, rough and jagged in others.
- **Smell:** Mineral. Damp stone. The faint iron-copper trace of very old blood, so faint it might be imagination.

## Items

### torch_bracket
- **label:** Torch bracket
- **size:** small
- **weight:** 2 lb
- **pickable:** false
- **wearable:** false
- **flavor_only:** true
- **description:** An iron bracket fixed to the stone just inside the entrance, rust-pitted beyond use. Whatever torch it once held burned decades ago. The bracket is too corroded to reuse—striking it leaves rust flakes in your palm.
- **appearance by distance:**
  - intermediate: a rusted iron bracket fixed to the entrance wall, fist-sized
  - far: a small dark fixture on the wall near the cave mouth
  - distant: a dark nub on the entrance wall

- **interactions:**
  - examine: An old iron bracket, once held a torch. The corrosion is deep; flakes when touched. Whatever torch stood here has been gone for decades.

### wall_scratches
- **label:** Tally scratches
- **size:** tiny
- **weight:** —
- **pickable:** false
- **wearable:** false
- **flavor_only:** true
- **description:** Scratch marks worked into the rock near the entrance with the point of something hard—a knife, perhaps, or a shard of the dark stone that marks the deeper chambers. The strokes are weathered and uneven, but the count is legible: nineteen vertical marks, crossed by a slanting twentieth that trails off as though the hand making it faltered. Whoever was counting no longer is.
- **appearance by distance:**
  - intermediate: faint scratch-marks worked into the rock near the entrance, arranged in tallies
  - far: a faint pattern of marks on the wall near the entrance
  - distant: marks on the entrance wall, too faint to read

- **interactions:**
  - examine: Tally marks. Nineteen, with a twentieth that trails off. A person counting something—likely days. The hand that made the twentieth tally faltered or stopped.
  - search: Scratched with something harder than the surrounding rock. Possibly an obelisk shard, though that is speculation.

### snapped_torch
- **label:** Snapped torch
- **size:** small
- **weight:** 1 lb
- **pickable:** true
- **wearable:** false
- **flavor_only:** false
- **description:** A wooden torch, snapped clean across the middle, lying on the floor near the mouth of the First Passage. The pitch-soaked head is intact but never lit; the fracture is fresh-looking against the weathered wood, though the wax has gone hard with age. The break is sideways across the grain—not a clean snap but a violent one. Whoever broke it did so in a hurry: perhaps in a fall, perhaps as the torch was wrenched from their hand.
- **appearance by distance:**
  - intermediate: a short, pale length of wood lying on the stone, visibly broken
  - far: a slim pale streak low on the cavern floor
  - distant: a faint pale fleck against the dark floor

- **interactions:**
  - examine: The break is across the grain—a sideways snap from impact or sudden force, not deliberate. The head is unburned, meaning it was dropped before it could be lit. Either the carrier never made it past this chamber, or they were retreating in the dark.
  - pick up: The pieces lift freely. The pitch head still has fuel; with a fresh shaft and a few minutes' work it could be made to burn. Otherwise it is firewood.

### old_bloodstain
- **label:** Dark stain
- **size:** medium
- **weight:** —
- **pickable:** false
- **wearable:** false
- **flavor_only:** false
- **description:** A dark patch on the stone floor near the south wall, three paces shy of the passage mouth. Not red—black, the way old blood goes when it has soaked into porous rock and dried for decades. The shape is unmistakably directional: not a pool but a smear, drawn out into a tapering streak that points south, into the First Passage. Something bled here, and then was moved.
- **appearance by distance:**
  - intermediate: a dark stain spread across the floor near the south wall, distinctly directional
  - far: a dark patch low on the cavern floor
  - distant: a shadow on the stone near the south wall

- **interactions:**
  - examine: The streak is several feet long, deliberately directional. The wider end is near where the bleeder fell or was struck; the tapered end points into the First Passage. A character who has seen battle recognizes a body being dragged, not crawling or walking.
  - search: The crust lifts in dark flakes. Without alchemical resources, no further detail can be learned here. Old blood, decades at minimum. Possibly older.

### discarded_pack
- **label:** Discarded pack
- **size:** small
- **weight:** 3 lb (without contents)
- **pickable:** true
- **wearable:** false
- **flavor_only:** false
- **description:** A leather pack, half-buried under a pile of fallen rock against the west wall. The buckles are tarnished green, the leather gone hard and brittle with age. The flap has come open and the contents are partly visible: a coil of mildewed rope, a tin cup, a small wax-sealed packet that has not yet rotted through. The rockfall on top is older than the pack; the pack was placed here deliberately, and the rocks fell later.
- **appearance by distance:**
  - intermediate: a low, hunched bundle slumped against the west wall, half under fallen rock
  - far: a dark heap at the base of the west wall
  - distant: a low shadow at the foot of the west wall

- **interactions:**
  - examine: A journeyman's pack, the kind meant for expedition work. The leather is hard with age, the buckles green with copper corrosion. Someone made it this far into the caverns and left this behind—or someone carried it from further in and abandoned it at the entrance.
  - search: With effort the pack can be dug free and extracted from the rockfall (1 turn). It contains: 50 ft of rope (mildewed, will take half its normal stress before snapping); a tin cup (usable); a folded paper map of the upper Reach (water-stained but readable, showing the obelisk and the entrance crack—confirming this pack belonged to an earlier expedition into these caverns, or one contemporary with Father Elden's lost party).

### drag_marks
- **label:** Drag marks
- **size:** large
- **weight:** —
- **pickable:** false
- **wearable:** false
- **flavor_only:** false
- **description:** A pair of parallel scrapes on the stone floor, each about a hand's breadth apart, running roughly six paces from the chamber's center toward the mouth of the First Passage. The scrapes are shallow but unmistakable against the weathered stone—the kind of marks left by something heavy being hauled across rock. They end abruptly at the passage threshold, as though whatever was being dragged moved into the passage and was lost to sight.
- **appearance by distance:**
  - intermediate: twin scrapes scored across the stone floor, purposeful and parallel
  - far: faint parallel lines on the floor extending toward the passage
  - distant: pale streaks on the cavern floor, arranged in pairs

- **interactions:**
  - examine: The marks pair with the bloodstain: a body dragged south, into the passage. The length of the trail (six paces) suggests the drag began roughly in the center of the chamber. The marks do not continue past the threshold; the floor of the First Passage is too damp and too uneven to record them further.
  - search: The scrapes are the right width to be heels. Whatever did the dragging was walking on two legs—or carrying the weight high enough that only the feet trailed. Something with intent, not accident.

## Features / Landmarks

- **entrance_crack** — Along the north wall. A narrow crack in the cliff face above, the way you entered. Daylight filters in here, fading to shadow within twenty feet. The crack is narrow; entering requires squeezing through.
- **first_passage_mouth** — At the south end of the chamber, near the center of the south wall. The floor sinks here into a narrow downward passage. A natural fold of stone narrows the opening; no more than a stooped man in height. This passage is called the First Passage.

## Creatures Present

None currently. The chamber is empty, but the evidence speaks of recent death.

## Exits

- **north** to surface (via entrance crack)
- **south** to First Passage (via first_passage_mouth)

## Proposed (review → keep needs GEOMETRY placement, or cut)

Ideas to enrich the zone. NOT loaded by the engine. No coordinates. Keep what we like (then a human adds it to GEOMETRY and promotes it into the sections above); cut the rest.

### Creatures (≤ 2 per zone)

- **Spiderlings (brood cluster)** — The giant spider's offspring, recently hatched and still small enough to fit through cracks near the entrance. They hunt in loose coordination, drawn to light and movement. Power: minor. Role: minor pack hunter / web-builder. Fits because: The entrance is part of the spider's territory and hunting ground. Webs near the cave mouth (referenced in the Description) catch prey entering the caverns. The Spiderlings set the tone: *this* is where the wrongness begins, and it bites. Encounters a spiderling swarm early establishes the spider infestation as an active, spreading threat, not just a lurking apex predator in the deep chambers.

### Treasure & Notable Items (≤ 3 per zone)

- **Shard of the carved cliff** — A fragment of the dark stone that marks the obelisk and the entrance carvings above, worked loose from the cliff face and fallen into the chamber. Tier: mundane. ~Value: curiosity only. Affordances: pickable, small, weightless. Fits because: The chamber abuts the cliff carved with strange script; a fragment here connects the entrance mysteries to what lies deeper. Could be examined by Elyssa as a sample of the inscribed stone.

### Features (optional)

- **Webbing near the entrance mouth** — Thin strands of silk drape the crack entrance on the interior side, partially obscured by shadow. Fresh enough to be sticky; old enough to be nearly invisible unless you're looking for it. Evidence of active web-building by creatures that hunt at the threshold.
- Uneven footing that makes stealth difficult—stepping carelessly produces echoes that carry downward into the First Passage, alerting anything listening below.
- A faint draft from the First Passage mouth—barely noticeable until you stand directly over it, then unmistakable. Something deeper in draws air through these chambers, and occasionally sends it back.
- **"Something moves up there if a torch is held high"** — Ceiling ambusher hint: shadows in the upper vault shift and resettle when light reaches them. Not immediately threatening, but unnerving. Sets up the ceiling-hunter predator archetype (leading to the matriarch above the burial vault deeper in).
