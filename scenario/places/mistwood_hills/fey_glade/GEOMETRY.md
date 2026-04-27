# GEOMETRY.md — The Fey Glade

## Scene

- **name:** The Fey Glade
- **place_path:** places/mistwood_hills/fey_glade
- **z_level:** 0.65
- **width:** 325.0
- **height:** 325.0
- **origin:** 3971.5, 8476.0, 0.65

## Landmarks

| name             | x     | y     |
|------------------|-------|-------|
| glade_center     | 162  | 162  |
| pool_surface     | 138  | 170  |
| carved_stone     | 136  | 169  |
| trail_entrance   | 191  | 146  |
| oak_west         | 139  | 162  |
| oak_east         | 185  | 162  |

## Zones

Zone order matters — first match wins in zone_at(). FOREST must be last.

| name     | vertices                                                   |
|----------|------------------------------------------------------------|
| POOL     | (132,164,0.97) (144,164,0.97) (144,176,0.97) (132,176,0.97)          |
| GLADE    | (130,146,0.65) (195,146,0.65) (195,178,0.65) (130,178,0.65)          |
| TRAIL    | (191,146,0.33) (195,146,0.33) (325,13,0.0) (321,9,0.0)           |
| FOREST   | (0,0,0.0) (325,0,0.0) (325,325,0.0) (0,325,0.0)          |

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| Pool surface | (136,169) (139,169) (139,172) (136,172)  |

## Connections

| name          | x     | y    | destination          |
|---------------|-------|------|----------------------|
| trail_exit    | 321  | 13  | mistwood_hills path  |

## Visibility

Dense Mistwood forest heavily occludes sight-lines. Rules:

| from_zone | to_zone | max_range_ft |
|-----------|---------|-------------|
| GLADE     | GLADE   | 9999        |
| GLADE     | POOL    | 9999        |
| POOL      | GLADE   | 9999        |
| POOL      | POOL    | 9999        |
| GLADE     | TRAIL   | 80          |
| TRAIL     | GLADE   | 80          |
| GLADE     | FOREST  | 30          |
| FOREST    | GLADE   | 30          |
| TRAIL     | TRAIL   | 9999        |
| TRAIL     | FOREST  | 0           |
| FOREST    | TRAIL   | 0           |
| FOREST    | FOREST  | 30          |

## Boundaries

### Fey Glade Repulsion Boundary

- **type:** magical
- **blocks:** shadowbeast, shadow_creature, undead
- **effect:** fey resonance antithetical to shadow essence — blocked creatures feel deep sourceless wrongness
- **vertices:** (126,143) (198,143) (198,182) (126,182)
- **save:** wisdom
- **crossing_dc:** dusk:8, evening:14, night:18, dawn:8
- **crossing_damage_success:** dusk:1d4, evening:1d6, night:1d6+2, dawn:1d4
- **behavior:** see LORE.md — barrier strength varies by time of day; quiescent in daylight (shadowbeast avoids daylight by its own nature, not barrier force); dusk through dawn uses crossing_dc table

## Starting Positions

| character    | x     | y     | zone     |
|--------------|-------|-------|----------|
| aeliana      | 256  | 81  | TRAIL    |
| fennel       | 190  | 162  | GLADE    |
| shadowbeast  | 65  | 162  | FOREST   |
