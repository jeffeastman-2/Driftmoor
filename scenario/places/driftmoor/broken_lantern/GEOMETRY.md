# GEOMETRY.md — The Broken Lantern (Tavern)

## Scene

- **name:** The Broken Lantern
- **place_path:** places/driftmoor/broken_lantern
- **z_level:** 16.25
- **width:** 81.25
- **height:** 65.0
- **origin:** 9321.0, 8021.0, 16.25

Notes: Ground floor contains the main room, bar, stage corner, private
booths, kitchen, storage room, and meeting room. Upper floor (z=26.0)
has three guest rooms accessed by a creaky interior staircase. The
broken lantern hangs above the front door on the south face. The
building is timber with a sloping roof and ivy on the east wall.

---

## Landmarks

| name             | x    | y    |
|------------------|------|------|
| front_door       | 39 | 0  |
| hearth           | 71 | 39 |
| bar_counter      | 65 | 22  |
| stage_corner     | 9  | 45 |
| booth_row        | 9  | 22  |
| staircase        | 58 | 55 |
| kitchen_center   | 65 | 55 |
| storage_center   | 26  | 55 |
| meeting_room_ctr | 9  | 55 |
| broken_lantern   | 39 | -3 |

---

## Zones

| name          | render_z | vertices                              |
|---------------|----------|---------------------------------------|
| STAGE         | 6.5        | (0,39) (26,39) (26,55) (0,55)           |
| BOOTHS        | 6.5        | (0,13) (26,13) (26,39) (0,39)             |
| BAR           | 6.5        | (48,13) (74,13) (74,45) (48,45)         |
| KITCHEN       | 6.5        | (48,45) (81,45) (81,65) (48,65)       |
| STORAGE_ROOM  | 6.5        | (26,45) (48,45) (48,65) (26,65)         |
| MEETING_ROOM  | 6.5        | (0,45) (26,45) (26,65) (0,65)           |
| MAIN_ROOM     | 3.25        | (0,0) (81,0) (81,45) (0,45)           |
| EXTERIOR      | 0.0        | (-16,-16) (97,-16) (97,81) (-16,81)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| Bar counter      | (48,16) (74,16) (74,22) (48,22)           |
| Kitchen wall     | (48,45) (81,45) (81,48) (48,48)       |
| Back wall        | (0,61) (81,61) (81,65) (0,65)         |

---

## Connections

| name              | x    | y    | destination                    |
|-------------------|------|------|--------------------------------|
| front_door        | 39 | 0  | places/driftmoor               |
| to_upper_floor    | 58 | 55 | places/driftmoor/broken_lantern/upper_floor |
| kitchen_back_door | 81 | 55 | places/driftmoor               |

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
- **vertices:** (0,45) (81,45) (81,65) (0,65)

---

## Starting Positions

| character | x    | y    | zone      |
|-----------|------|------|-----------|
| kaelin    | 16  | 26  | BOOTHS    |
| cinnabar  | 20  | 22  | BOOTHS    |
| tess      | 65  | 26  | BAR       |
| wilfred   | 56  | 20  | BAR       |
| bran      | 14  | 52  | MEETING_ROOM |
| marda     | 11  | 52  | MEETING_ROOM |