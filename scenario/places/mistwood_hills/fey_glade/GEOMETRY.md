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
| glade_center     | 162.5  | 162.5  |
| pool_surface     | 138.12  | 170.62  |
| carved_stone     | 136.5  | 169.0  |
| trail_entrance   | 191.75  | 146.25  |
| oak_west         | 139.75  | 162.5  |
| oak_east         | 185.25  | 162.5  |

## Zones

Zone order matters — first match wins in zone_at(). FOREST must be last.

| name     | vertices                                                   |
|----------|------------------------------------------------------------|
| POOL     | (136.5,169.0,0.97) (139.75,169.0,0.97) (139.75,172.25,0.97) (136.5,172.25,0.97)          |
| GLADE    | (130.0,146.25,0.65) (195.0,146.25,0.65) (195.0,178.75,0.65) (130.0,178.75,0.65)          |
| TRAIL    | (191.75,146.25,0.33) (195.0,146.25,0.33) (325.0,13.0,0.0) (321.75,9.75,0.0)           |
| FOREST   | (0.0,0.0,0.0) (325.0,0.0,0.0) (325.0,325.0,0.0) (0.0,325.0,0.0)          |

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| Pool surface | (136.5,169.0) (139.75,169.0) (139.75,172.25) (136.5,172.25)  |

## Connections

| name          | x     | y    | destination          |
|---------------|-------|------|----------------------|
| trail_exit    | 321.75  | 13.0  | mistwood_hills path  |

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
- **vertices:** (126.75,143.0) (198.25,143.0) (198.25,182.0) (126.75,182.0)
- **behavior:** see LORE.md — barrier strength varies by time of day and conditions; do not adjudicate from this file

## Starting Positions

| character    | x     | y     | zone     |
|--------------|-------|-------|----------|
| aeliana      | 256.75  | 81.25  | TRAIL    |
| fennel       | 190.0  | 162.5  | GLADE    |
| shadowbeast  | 65.0  | 162.5  | FOREST   |
