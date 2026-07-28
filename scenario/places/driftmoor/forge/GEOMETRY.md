# GEOMETRY.md — The Forge

## Scene

- **name:** The Forge
- **place_path:** places/driftmoor/forge
- **z_level:** 16.25
- **width:** 58
- **height:** 55
- **origin:** 1205, 244, 16.25

---

## Landmarks

| name             | x  | y  |
|------------------|----|----|
| forge_entrance   | 0  | 7  |
| anvil            | 26 | 13 |
| forge_hearth     | 13 | 26 |
| forge_wall_marks | 32 | 33 |
| stable_door      | 58 | 10 |

---

## Zones

| name     | render_z | vertices                    |
|----------|----------|-----------------------------|
| FORGE    | 6.5      | (0,0) (58,0) (58,55) (0,55) |
| EXTERIOR | 0.0      | (-8,-8) (66,-8) (66,63) (-8,63) |

---

## Impassable

| description     | vertices                         |
|-----------------|----------------------------------|
| Forge back wall | (0,49) (58,49) (58,55) (0,55)  |

---

## Connections

| name            | x  | y  | destination              |
|-----------------|----|----|--------------------------|
| forge_to_street | 0  | 7  | places/driftmoor         |
| forge_to_stables | 58 | 10 | places/driftmoor/stables |

---

## Boundaries

### Forge Heat Zone

- **type:** conditional
- **blocks:** none
- **effect:** within 10 ft of the hearth — extreme heat; prolonged unprotected exposure risks exhaustion
- **vertices:** (3,16) (23,16) (23,36) (3,36)
