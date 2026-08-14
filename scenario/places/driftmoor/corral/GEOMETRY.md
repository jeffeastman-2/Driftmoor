# GEOMETRY.md — The Corral

## Scene

- **name:** The Corral
- **place_path:** places/driftmoor/corral
- **z_level:** 16.25
- **width:** 32.5
- **height:** 40.5
- **origin:** 678, 10, 0

---

## Landmarks

| name          | x  | y  |
|---------------|----|----|
| main_gate     | 32.5 | 20 |
| stable_gate   | 0  | 20 |
| water_trough  | 3.65 | 6.956 |
| hay_bale      | 4.112 | 15.637 |
| corral_center | 16.5 | 20.5 |

---

## Zones

| name | render_z | auto_wall | vertices |
|----------|----------|---------|---------------------------------|
| CORRAL | 5.0 |  | (0,0) (32.5,0) (32.5,40.5) (0,40.5) |
| EXTERIOR | 0.0 |  | (-4,-4) (36.5,-4) (36.5,44.5) (-4,44.5) |
---

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| North fence  | (0,37.5) (32.5,37.5) (32.5,40.5) (0,40.5)  |
| South fence  | (0,0) (32.5,0) (32.5,3) (0,3)      |
| West fence south | (0,0) (1,0) (1,18) (0,18)       |
| West fence north | (0,22) (1,22) (1,40.5) (0,40.5) |
| East fence south | (31.5,0) (32.5,0) (32.5,18) (31.5,18) |
| East fence north | (31.5,22) (32.5,22) (32.5,40.5) (31.5,40.5) |

---

## Connections

| name             | x  | y  | destination      |
|------------------|----|----|------------------|
| corral_to_street | 32.5 | 20 | places/driftmoor |
