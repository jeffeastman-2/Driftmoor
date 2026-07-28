# GEOMETRY.md — The Corral

## Scene

- **name:** The Corral
- **place_path:** places/driftmoor/corral
- **z_level:** 16.25
- **width:** 65
- **height:** 81
- **origin:** 1356, 139, 16.25

---

## Landmarks

| name          | x  | y  |
|---------------|----|----|
| main_gate     | 65 | 40 |
| stable_gate   | 0  | 40 |
| water_trough  | 12 | 16 |
| corral_center | 33 | 41 |

---

## Zones

| name     | render_z | vertices                        |
|----------|----------|---------------------------------|
| CORRAL   | 5.0      | (0,0) (65,0) (65,81) (0,81)   |
| EXTERIOR | 0.0      | (-8,-8) (73,-8) (73,89) (-8,89) |

---

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| North fence  | (0,75) (65,75) (65,81) (0,81)  |
| South fence  | (0,0) (65,0) (65,6) (0,6)      |

---

## Connections

| name             | x  | y  | destination      |
|------------------|----|----|------------------|
| corral_to_street | 65 | 40 | places/driftmoor |
