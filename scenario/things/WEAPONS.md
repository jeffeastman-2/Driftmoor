# Weapons

Weapon library for the Fey Glade scene. Characters reference weapons by `id` in CONFIG.md.
`attack_bonus` is NOT stored here — it is set per-character in CONFIG.md as `weapon_id+N`.
Python reads the base stat (damage, range, reach, properties) from this table.

| id | name | damage | damage_type | reach | range_normal | range_max | properties |
|----|------|--------|-------------|-------|--------------|-----------|------------|
| longbow | Longbow | 1d8 | piercing | 5 | 150 | 600 | two_handed,ammunition:arrow |
| shortbow | Shortbow | 1d6 | piercing | 5 | 80 | 320 | two_handed,ammunition:arrow |
| light_crossbow | Light Crossbow | 1d8 | piercing | 5 | 80 | 320 | two_handed,ammunition:bolt,loading |
| shortsword | Short Sword | 1d6 | piercing | 5 | 0 | 0 | finesse,light |
| rapier | Rapier | 1d8 | piercing | 5 | 0 | 0 | finesse |
| battle_axe | Battle Axe | 1d8 | slashing | 5 | 0 | 0 | versatile:1d10 |
| mace | Mace | 1d6 | bludgeoning | 5 | 0 | 0 | |
| quarterstaff | Quarterstaff | 1d6 | bludgeoning | 5 | 0 | 0 | versatile:1d8 |
| dagger | Dagger | 1d4 | piercing | 5 | 20 | 60 | finesse,light,thrown |
| belt_knife | Belt Knife | 1d4 | piercing | 5 | 0 | 0 | light |
| improvised_spear | Improvised Spear | 1d8 | piercing | 5 | 0 | 0 | two_handed |
| shadowbeast_claw | Claw | 1d6 | slashing | 5 | 0 | 0 | natural |
| spider_bite | Bite | 1d8+3 | piercing | 5 | 0 | 0 | natural |
