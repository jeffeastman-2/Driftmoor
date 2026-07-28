# GEOMETRY.md — Fisherfolk Quarter

## Scene

- **name:** Fisherfolk Quarter
- **place_path:** places/driftmoor/fisherfolk
- **z_level:** 16.25
- **width:** 60
- **height:** 42
- **origin:** 8750, 8550, 16.25

Notes: A shared yard and narrow lane among several harbor cottages. The scene
represents the accessible common space rather than every private room.

## Landmarks

| name | x | y |
|------|---|---|
| lane_gate | 30 | 0 |
| net_mending_yard | 30 | 20 |
| cottage_row | 30 | 35 |
| gear_racks | 10 | 20 |
| pot_stack | 50 | 20 |

## Zones

| name | render_z | vertices |
|------|----------|----------|
| SHARED_YARD | 3.25 | (0,0) (60,0) (60,32) (0,32) |
| COTTAGE_PORCHES | 3.5 | (0,32) (60,32) (60,42) (0,42) |
| EXTERIOR | 0.0 | (-9,-9) (69,-9) (69,51) (-9,51) |

## Impassable

| description | vertices |
|-------------|----------|
| Cottage walls | (0,39) (60,39) (60,42) (0,42) |

## Connections

| name | x | y | destination |
|------|---|---|-------------|
| lane_gate | 30 | 0 | places/driftmoor |
