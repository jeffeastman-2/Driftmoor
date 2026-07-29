# GEOMETRY.md — The Broken Lantern (Tavern)

## Scene

- **name:** The Broken Lantern
- **place_path:** places/driftmoor/broken_lantern
- **z_level:** 16.25
- **width:** 40.625
- **height:** 32.5
- **origin:** 427.5, 252, 0

Notes: Ground floor contains the main room, bar, stage corner, private
booths, kitchen, storage room, and meeting room. Upper floor (z=26.0)
has three guest rooms accessed by a creaky interior staircase. The
broken lantern hangs above the front door on the south face. The
building is timber with a sloping roof and ivy on the east wall.

---

## Landmarks

| name             | x    | y    |
|------------------|------|------|
| front_door       | 19.5 | 0  |
| hearth           | 35.5 | 19.5 |
| bar_counter      | 32.5 | 11  |
| stage_corner     | 4.5  | 22.5 |
| booth_row        | 4.5  | 11  |
| staircase        | 29 | 27.5 |
| kitchen_center   | 32.5 | 27.5 |
| storage_center   | 13  | 27.5 |
| meeting_room_ctr | 4.5  | 27.5 |
| broken_lantern   | 19.5 | -1.5 |

---

## Zones

| name          | render_z | vertices                              |
|---------------|----------|---------------------------------------|
| STAGE         | 6.5        | (0,19.5) (13,19.5) (13,27.5) (0,27.5)           |
| BOOTHS        | 6.5        | (0,6.5) (13,6.5) (13,19.5) (0,19.5)             |
| BAR           | 6.5        | (24,6.5) (37,6.5) (37,22.5) (24,22.5)         |
| KITCHEN       | 6.5        | (24,22.5) (40.5,22.5) (40.5,32.5) (24,32.5)       |
| STORAGE_ROOM  | 6.5        | (13,22.5) (24,22.5) (24,32.5) (13,32.5)         |
| MEETING_ROOM  | 6.5        | (0,22.5) (13,22.5) (13,32.5) (0,32.5)           |
| MAIN_ROOM     | 3.25        | (0,0) (40.5,0) (40.5,22.5) (0,22.5)           |
| EXTERIOR      | 0.0        | (-8,-8) (48.5,-8) (48.5,40.5) (-8,40.5)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| Bar counter      | (24,8) (37,8) (37,11) (24,11)           |
| Kitchen wall     | (24,22.5) (40.5,22.5) (40.5,24) (24,24)       |
| Back wall        | (0,30.5) (40.5,30.5) (40.5,32.5) (0,32.5)         |

---

## Connections

| name              | x    | y    | destination                    |
|-------------------|------|------|--------------------------------|
| front_door        | 19.5 | 0  | places/driftmoor               |
| to_upper_floor    | 29 | 27.5 | places/driftmoor/broken_lantern/upper_floor |
| kitchen_back_door | 40.5 | 27.5 | places/driftmoor               |

## Items

| id                 | x   | y   | label                      |
|--------------------|-----|-----|----------------------------|
| broken_lantern_sign| 39  | -3  | Broken lantern sign        |
| bar_stools         | 60  | 18  | Bar stools                 |
| service_bell       | 63  | 22  | Service bell               |
| room_key_ring      | 64  | 23  | Room key ring              |
| ale_tankards       | 66  | 24  | Ale tankards               |
| tip_bowl           | 17  | 27  | Tip bowl                   |
| lute_case          | 14  | 25  | Lute case                  |
| dice_cup           | 10  | 33  | Dice cup                   |
| ledger_book        | 13  | 51  | Ledger book                |
| sealed_letter      | 12  | 52  | Sealed letter              |
| spare_blanket      | 30  | 56  | Spare blanket              |
| crate_saltfish     | 34  | 58  | Crate of saltfish          |
| kitchen_knife      | 67  | 53  | Kitchen knife              |
| stew_pot           | 71  | 57  | Stew pot                   |
| coal_scuttle       | 72  | 41  | Coal scuttle               |
| candle_stub_bundle | 22  | 48  | Bundle of candle stubs     |

---

## Boundaries

### Tess's Back Rooms

- **type:** conditional
- **blocks:** all
- **effect:** storage room and meeting room require Tess's permission or a successful Persuasion/Deception check to access
- **vertices:** (0,22.5) (40.5,22.5) (40.5,32.5) (0,32.5)

---
