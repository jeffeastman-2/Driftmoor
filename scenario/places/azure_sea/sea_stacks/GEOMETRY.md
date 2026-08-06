# GEOMETRY.md — The Sea Stacks

## Scene

- **name:** The Sea Stacks
- **place_path:** places/azure_sea/sea_stacks
- **z_level:** 0.0
- **width:** 390.0
- **height:** 325.0
- **origin:** 3705.0, 18687.5, 0.0

Notes: Tall isolated rock formations rising from the water near
shore. Origin at southwest corner of the cluster area. The stacks
themselves are vertical stone pillars 48.75-97.5m tall. The bases are
accessible at low tide on foot; at high tide the bases are submerged.
Seabirds nest in the crevices above. The gaps between stacks are
navigable by small boat.

---

## Landmarks

| name            | x     | y     |
|-----------------|-------|-------|
| stack_north     | 162  | 260  |
| stack_central   | 195  | 162  |
| stack_south     | 130  | 65  |
| stack_east      | 292  | 178  |
| nesting_ledge   | 178  | 266  |
| shelter_cove    | 227  | 130  |
| tidal_passage   | 97  | 162  |

---

## Zones

| name | render_z | auto_wall | vertices |
|----------------|----------|---------|---------------------------------------------|
| STACK_NORTH | 9.75 |  | (130,227) (195,227) (195,292) (130,292) |
| STACK_CENTRAL | 9.75 |  | (162,130) (227,130) (227,195) (162,195) |
| STACK_SOUTH | 9.75 |  | (97,32) (162,32) (162,97) (97,97) |
| STACK_EAST | 9.75 |  | (260,146) (325,146) (325,211) (260,211) |
| SHALLOWS | 3.25 |  | (32,16) (357,16) (357,308) (32,308) |
| EXTERIOR | 0.0 |  | (0,0) (390,0) (390,325) (0,325) |
---

## Walls

- **auto_wall:** false

This is a sea-stacks exploration site — rock formations to climb between, not rooms with doors. None of these zones share a coincident edge with any other, so the per-zone perimeter pass would seal every one into an isolated box with no door to open it.

## Impassable

| description      | vertices                                    |
|------------------|---------------------------------------------|
| Stack North base | (139,237) (185,237) (185,282) (139,282)              |
| Stack Central    | (172,139) (217,139) (217,185) (172,185)              |
| Stack South base | (107,42) (152,42) (152,87) (107,87)              |
| Stack East base  | (269,156) (315,156) (315,201) (269,201)              |

---

## Connections

| name               | x     | y    | destination                    |
|--------------------|-------|------|--------------------------------|
| to_drowned_isle    | 32  | 32 | places/azure_sea/drowned_isle  |
| to_coastal_path    | 357 | 162 | places/azure_sea               |

---

## Boundaries

### Tidal Access

- **type:** conditional
- **blocks:** all
- **effect:** stack bases accessible only at low tide on foot; at high tide requires swimming (DC 42.25 Athletics, cold water)
- **vertices:** (32,16) (357,16) (357,308) (32,308)
