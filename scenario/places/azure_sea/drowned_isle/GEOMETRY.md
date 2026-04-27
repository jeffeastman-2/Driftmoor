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
| isle_center       | 130 | 130 |
| tidal_pool        | 113 | 146 |
| eastern_ruins     | 195 | 113 |
| western_ruins     | 65 | 130 |
| barnacle_chest    | 188 | 107 |
| landing_rocks     | 227 | 32 |
| highest_point     | 130 | 162 |
| collapsed_chamber | 81 | 162 |

---

## Zones

| name            | render_z | vertices                                    |
|-----------------|----------|---------------------------------------------|
| EASTERN_RUINS   | 6.5        | (162,81) (227,81) (227,146) (162,146)              |
| WESTERN_RUINS   | 6.5        | (32,97) (97,97) (97,178) (32,178)              |
| TIDAL_POOL      | 6.5        | (97,130) (130,130) (130,162) (97,162)              |
| EXPOSED_ROCK    | 3.25        | (16,16) (243,16) (243,243) (16,243)                  |
| SUBMERGED       | 0.0        | (0,0) (260,0) (260,260) (0,260)                  |

---

## Impassable

| description     | vertices                                    |
|-----------------|---------------------------------------------|
| Tidal pool      | (97,130) (130,130) (130,162) (97,162)              |
| Collapsed walls | (39,136) (58,136) (58,169) (39,169)              |

---

## Connections

| name            | x    | y    | destination                  |
|-----------------|------|------|------------------------------|
| landing_rocks   | 227 | 32 | places/azure_sea/sea_stacks  |
| swim_to_sea     | 130 | 0  | places/azure_sea             |

---

## Boundaries

### Tidal Submersion

- **type:** conditional
- **blocks:** all
- **effect:** at high tide, all zones except HIGHEST_POINT are submerged; 6.5-hour access window at low tide
- **vertices:** (0,0) (260,0) (260,260) (0,260)
