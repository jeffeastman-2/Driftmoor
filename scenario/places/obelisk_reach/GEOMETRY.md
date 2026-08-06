# GEOMETRY.md — The Obelisk Reach

## Scene

- **name:** The Obelisk Reach
- **place_path:** places/obelisk_reach
- **z_level:** 260.0
- **width:** 9100.0
- **height:** 11375.0
- **origin:** 7800.0, 37375.0, 260.0

Notes: Jagged cliffs and rocky plateaus north of Driftmoor. Origin
at southwest corner. The Shattered Obelisk dominates the northern
portion. The Echoing Caverns entrance is a crack in the cliff face
west of the obelisk. Strange symbols are carved into the cliffs.
Animals avoid this area. The terrain is treacherous with narrow paths.

---

## Landmarks

| name                  | x      | y      |
|-----------------------|--------|--------|
| obelisk_reach_edge    | 3575 | 4225 |
| shattered_obelisk     | 3250 | 7475 |
| echoing_caverns_mouth | 4225 | 6500 |
| cliff_approach        | 2600  | 2600  |
| symbol_cliff          | 1625  | 4875 |
| narrow_path           | 3900 | 5200 |
| scorched_ground       | 3250 | 8125 |
| outlook_ledge         | 5850 | 5850 |

---

## Zones

| name | render_z | auto_wall | vertices |
|--------------------|----------|---------|-------------------------------------------------------|
| SHATTERED_OBELISK | 9.75 |  | (2275,6500) (4225,6500) (4225,8775) (2275,8775) |
| ECHOING_CAVERNS | 9.75 |  | (3575,5525) (5200,5525) (5200,7475) (3575,7475) |
| CLIFF_PLATEAU | 6.5 |  | (650,3250) (7150,3250) (7800,10400) (0,10400) |
| APPROACH_PATH | 3.25 |  | (1300,650) (4550,650) (4550,3250) (1300,3250) |
| CLIFFS | 3.25 |  | (0,0) (9100,0) (9100,11375) (0,11375) |
| EXTERIOR | 0.0 |  | (0,0) (9100,0) (9100,11375) (0,11375) |
---

## Walls

- **auto_wall:** false

This is a cliffs-and-plateaus region map — an exploration area, not
rooms with doors. CLIFFS and EXTERIOR share the exact same footprint;
none of these zones share a coincident edge with any other, so the
per-zone perimeter pass would seal every one into an isolated box with
no door to open it.

## Impassable

| description          | vertices                                              |
|----------------------|-------------------------------------------------------|
| Western cliff face   | (0,4875) (650,4875) (650,11375) (0,11375)                |
| Eastern cliff drop   | (7800,4875) (9100,4875) (9100,11375) (7800,11375)        |

---

## Connections

| name                | x      | y      | destination                              |
|---------------------|--------|--------|------------------------------------------|
| approach_south      | 2925  | 325  | places/driftmoor                         |
| to_obelisk          | 3250 | 7475 | places/obelisk_reach/shattered_obelisk   |
| to_caverns          | 4225 | 6500 | places/obelisk_reach/echoing_caverns     |
| to_mistwood_east    | 8450 | 4875 | places/mistwood_hills                    |

---

## Boundaries

### Obelisk Distortion Field

- **type:** magical
- **blocks:** none
- **effect:** perception checks degraded, compasses spin, light sources flicker; stronger near the obelisk
- **vertices:** (650,3250) (7800,3250) (7800,10400) (650,10400)
