# GEOMETRY.md — The Corral

## Scene

- **name:** The Corral
- **place_path:** places/driftmoor/corral
- **z_level:** 16.25
- **width:** 32.5
- **height:** 40.5
- **origin:** 678, 69.5, 0

---

## Landmarks

| name          | x  | y  |
|---------------|----|----|
| main_gate     | 32.5 | 20 |
| stable_gate   | 0  | 20 |
| water_trough  | 6 | 8 |
| corral_center | 16.5 | 20.5 |

---

## Zones

| name     | render_z | vertices                        |
|----------|----------|---------------------------------|
| CORRAL   | 5.0      | (0,0) (32.5,0) (32.5,40.5) (0,40.5)   |
| EXTERIOR | 0.0      | (-4,-4) (36.5,-4) (36.5,44.5) (-4,44.5) |

---

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| North fence  | (0,37.5) (32.5,37.5) (32.5,40.5) (0,40.5)  |
| South fence  | (0,0) (32.5,0) (32.5,3) (0,3)      |

---

## Connections

| name             | x  | y  | destination      |
|------------------|----|----|------------------|
| corral_to_street | 32.5 | 20 | places/driftmoor |
