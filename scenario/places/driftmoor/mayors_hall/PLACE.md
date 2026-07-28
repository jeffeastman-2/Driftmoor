# PLACE.md — The Mayor's Hall

## Place Identity
- **type:** civic hall
- **aliases:** mayor's hall, mayors hall, town hall, civic hall, The Mayor's Hall

## Description and Atmosphere
The largest and most prominent building in Driftmoor — two stories of timber and stone built to withstand coastal weather and project quiet authority. Situated near the village square. Practical in design with small touches of civic pride: carved wooden trim along the eaves, a tended flower bed outside, the town crest on the double oak doors.

Inside it smells of old paper, woodsmoke, and the faint whiskey the mayor keeps in his office.

## Sub-Places
- `mayors_office/` — Aldren Thorne's working space
- `records_room/` — locked, town documents and historical ledgers
- `living_quarters/` — Aldren's modest upstairs suite
- Main Hall (covered in this file — no sub-directory needed)

## Main Hall
The heart of the building. Rows of simple wooden benches face a raised dais with a long table and high-backed chair. Walls adorned with maps of the surrounding region, fishing nets, and framed sketches of early Driftmoor. A weathered bronze bell near the back — used to call meetings or sound alarms.

## Exterior
- Wide double doors of dark oak, iron-banded, carved with Driftmoor's crest
- Flagpole with faded town banner
- Stone steps flanked by lanterns lit each evening

## Resident NPCs and Creatures

### aldren
- **type:** npc
- **soul_file:** scenario/people/npcs/aldren/SOUL.md
- **identity_file:** scenario/people/npcs/aldren/IDENTITY.md
- **position:** 58, 29

### elise
- **type:** npc
- **soul_file:** scenario/people/npcs/elise/SOUL.md
- **identity_file:** scenario/people/npcs/elise/IDENTITY.md
- **position:** 16, 45

## Scene Introductions

### aldren
You are at the long table in the main hall with town records spread before
you. The building is quiet enough to hear the fire and the occasional footstep
outside the oak doors. Driftmoor's ordinary problems are waiting in neat
stacks; the less ordinary ones refuse to stay on paper.

### elise
You are in the records room checking the shelf where the old incident ledger
should be. The surrounding volumes are ordered correctly, and the gap is too
clean to be an accident. Aldren is working in the main hall. You have the room
key at your belt and a list of recent archive requests beside the lamp.

## Who Is Normally Here
- **Aldren Thorne** — mayor, usually in his office during the day
- **Elise Harper** — sharp-eyed clerk, manages the records room

## Connections
- Village square (outside)
- `mayors_office/` (left of main hall)
- `records_room/` (behind the office, locked)
- `living_quarters/` (upstairs)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Aldren Thorne (office), Elise Harper (records area)
- **Recent events:** None yet — session not started
- **Active conditions:** Records room ledger missing
