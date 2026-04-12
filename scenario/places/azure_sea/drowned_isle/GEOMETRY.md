# GEOMETRY.md — The Drowned Isle

## Scene

- **name:** The Drowned Isle
- **place_path:** places/azure_sea/drowned_isle
- **z_level:** -1.62
- **width:** 260.0
- **height:** 260.0
- **origin:** 2795.0, 14170.0, -1.62

Notes: A partially submerged island visible only at low tide. Origin
at southwest corner. Most of the isle is exposed rock and ancient
ruins. The tidal pool at the center never fully drains. The ruins
are broken walls and half-collapsed chambers — nothing stands above
9.75 meters. The chest found by the fisherman sits in the eastern ruins.
Two hours of access at low tide before water returns.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| isle_center       | 130.0 | 130.0 |
| tidal_pool        | 113.75 | 146.25 |
| eastern_ruins     | 195.0 | 113.75 |
| western_ruins     | 65.0 | 130.0 |
| barnacle_chest    | 188.5 | 107.25 |
| landing_rocks     | 227.5 | 32.5 |
| highest_point     | 130.0 | 162.5 |
| collapsed_chamber | 81.25 | 162.5 |

---

## Zones

| name            | render_z | vertices                                    |
|-----------------|----------|---------------------------------------------|
| EASTERN_RUINS   | 6.5        | (162.5,81.25) (227.5,81.25) (227.5,146.25) (162.5,146.25)              |
| WESTERN_RUINS   | 6.5        | (32.5,97.5) (97.5,97.5) (97.5,178.75) (32.5,178.75)              |
| TIDAL_POOL      | 6.5        | (97.5,130.0) (130.0,130.0) (130.0,162.5) (97.5,162.5)              |
| EXPOSED_ROCK    | 3.25        | (16.25,16.25) (243.75,16.25) (243.75,243.75) (16.25,243.75)                  |
| SUBMERGED       | 0.0        | (0.0,0.0) (260.0,0.0) (260.0,260.0) (0.0,260.0)                  |

---

## Impassable

| description     | vertices                                    |
|-----------------|---------------------------------------------|
| Tidal pool      | (97.5,130.0) (130.0,130.0) (130.0,162.5) (97.5,162.5)              |
| Collapsed walls | (39.0,136.5) (58.5,136.5) (58.5,169.0) (39.0,169.0)              |

---

## Connections

| name            | x    | y    | destination                  |
|-----------------|------|------|------------------------------|
| landing_rocks   | 227.5 | 32.5 | places/azure_sea/sea_stacks  |
| swim_to_sea     | 130.0 | 0.0  | places/azure_sea             |

---

## Boundaries

### Tidal Submersion

- **type:** conditional
- **blocks:** all
- **effect:** at high tide, all zones except HIGHEST_POINT are submerged; 6.5-hour access window at low tide
- **vertices:** (0.0,0.0) (260.0,0.0) (260.0,260.0) (0.0,260.0)
