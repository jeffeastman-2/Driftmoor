# GEOMETRY.md — The Forge

## Scene

- **name:** The Forge
- **place_path:** places/driftmoor/forge
- **z_level:** 16.25
- **width:** 29
- **height:** 27.5
- **origin:** 602.5, 122, 0

---

## Landmarks

| name             | x  | y  |
|------------------|----|----|
| forge_entrance   | 0  | 3.5  |
| anvil            | 13 | 6.5 |
| forge_hearth     | 6.5 | 13 |
| forge_wall_marks | 16 | 27.5 |
| stable_door      | 22 | 0 |

---

## Zones

| name     | render_z | vertices                    |
|----------|----------|-----------------------------|
| FORGE    | 6.5      | (0,0) (29,0) (29,27.5) (0,27.5) |
| EXTERIOR | 0.0      | (-4,-4) (33,-4) (33,31.5) (-4,31.5) |

---

## Impassable

| description     | vertices                         |
|-----------------|----------------------------------|
| Forge back wall | (0,24.5) (29,24.5) (29,27.5) (0,27.5)  |

---

## Connections

| name            | x  | y  | destination              |
|-----------------|----|----|--------------------------|
| forge_to_street | 0  | 3.5  | places/driftmoor         |
| forge_to_stables | 22 | 0 | places/driftmoor/stables |

---

## Items

| id               | x  | y    | label                    |
|------------------|----|------|--------------------------|
| forge_wall_marks | 16 | 24.25 | Shadow-burned wall marks |

---

## Boundaries

### Forge Heat Zone

- **type:** conditional
- **blocks:** none
- **render:** hidden
- **effect:** within 10 ft of the hearth — extreme heat; prolonged unprotected exposure risks exhaustion
- **vertices:** (1.5,8) (11.5,8) (11.5,18) (1.5,18)
