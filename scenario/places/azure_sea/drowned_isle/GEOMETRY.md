# GEOMETRY.md — The Drowned Isle

## Scene

- **name:** The Drowned Isle
- **place_path:** places/azure_sea/drowned_isle
- **z_level:** -0.5
- **width:** 80.0
- **height:** 80.0
- **origin:** 860.0, 4360.0, -0.5

Notes: A partially submerged island visible only at low tide. Origin
at southwest corner. Most of the isle is exposed rock and ancient
ruins. The tidal pool at the center never fully drains. The ruins
are broken walls and half-collapsed chambers — nothing stands above
3 meters. The chest found by the fisherman sits in the eastern ruins.
Two hours of access at low tide before water returns.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| isle_center       | 40.0 | 40.0 |
| tidal_pool        | 35.0 | 45.0 |
| eastern_ruins     | 60.0 | 35.0 |
| western_ruins     | 20.0 | 40.0 |
| barnacle_chest    | 58.0 | 33.0 |
| landing_rocks     | 70.0 | 10.0 |
| highest_point     | 40.0 | 50.0 |
| collapsed_chamber | 25.0 | 50.0 |

---

## Zones

| name            | render_z | vertices                                    |
|-----------------|----------|---------------------------------------------|
| EASTERN_RUINS   | 2        | (50,25) (70,25) (70,45) (50,45)              |
| WESTERN_RUINS   | 2        | (10,30) (30,30) (30,55) (10,55)              |
| TIDAL_POOL      | 2        | (30,40) (40,40) (40,50) (30,50)              |
| EXPOSED_ROCK    | 1        | (5,5) (75,5) (75,75) (5,75)                  |
| SUBMERGED       | 0        | (0,0) (80,0) (80,80) (0,80)                  |

---

## Impassable

| description     | vertices                                    |
|-----------------|---------------------------------------------|
| Tidal pool      | (30,40) (40,40) (40,50) (30,50)              |
| Collapsed walls | (12,42) (18,42) (18,52) (12,52)              |

---

## Connections

| name            | x    | y    | destination                  |
|-----------------|------|------|------------------------------|
| landing_rocks   | 70.0 | 10.0 | places/azure_sea/sea_stacks  |
| swim_to_sea     | 40.0 | 0.0  | places/azure_sea             |

---

## Boundaries

### Tidal Submersion

- **type:** conditional
- **blocks:** all
- **effect:** at high tide, all zones except HIGHEST_POINT are submerged; 2-hour access window at low tide
- **vertices:** (0,0) (80,0) (80,80) (0,80)
