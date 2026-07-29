# GEOMETRY.md — Fisherfolk Quarter

## Scene

- **name:** Fisherfolk Quarter
- **place_path:** places/driftmoor/fisherfolk
- **z_level:** 16.25
- **width:** 30
- **height:** 21
- **origin:** 150, 375, 0

Notes: A shared yard and narrow lane among several harbor cottages. The scene
represents the accessible common space rather than every private room.

## Landmarks

| name | x | y |
|------|---|---|
| lane_gate | 15 | 0 |
| net_mending_yard | 15 | 10 |
| cottage_row | 15 | 17.5 |
| gear_racks | 5 | 10 |
| pot_stack | 25 | 10 |

## Zones

| name | render_z | vertices |
|------|----------|----------|
| SHARED_YARD | 3.25 | (0,0) (30,0) (30,16) (0,16) |
| COTTAGE_PORCHES | 3.5 | (0,16) (30,16) (30,21) (0,21) |
| EXTERIOR | 0.0 | (-4.5,-4.5) (34.5,-4.5) (34.5,25.5) (-4.5,25.5) |

## Impassable

| description | vertices |
|-------------|----------|
| Cottage walls | (0,19.5) (30,19.5) (30,21) (0,21) |

## Connections

| name | x | y | destination |
|------|---|---|-------------|
| lane_gate | 15 | 0 | places/driftmoor |
