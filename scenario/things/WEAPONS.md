# Weapons

Weapon library for the Fey Glade scene. Characters reference weapons by `id` in
their IDENTITY `## Equipment` list. Base stats (damage, range, reach, properties,
tags) live here and are shared by every wielder; the per-character attack bonus
is computed at load (ability mod + proficiency, if the wielder is proficient).

`tags` are categorical: a proficiency tier (`simple`/`martial`) plus weapon
group(s) (`sword`/`blade`/`axe`/`bow`/…). They drive proficiency checks AND noun
grounding ("draw my sword" → a weapon tagged `sword`). `natural` weapons need no
proficiency.

| id | name | damage | damage_type | reach | range_normal | range_max | properties | tags |
|----|------|--------|-------------|-------|--------------|-----------|------------|------|
| longbow | Longbow | 1d8 | piercing | 5 | 150 | 600 | two_handed,ammunition:arrow | martial,bow |
| shortbow | Shortbow | 1d6 | piercing | 5 | 80 | 320 | two_handed,ammunition:arrow | simple,bow |
| light_crossbow | Light Crossbow | 1d8 | piercing | 5 | 80 | 320 | two_handed,ammunition:bolt,loading | simple,crossbow |
| shortsword | Short Sword | 1d6 | piercing | 5 | 0 | 0 | finesse,light | martial,sword,blade |
| longsword | Long Sword | 1d8 | slashing | 5 | 0 | 0 | versatile:1d10 | martial,sword,blade |
| rapier | Rapier | 1d8 | piercing | 5 | 0 | 0 | finesse | martial,sword,blade |
| battle_axe | Battle Axe | 1d8 | slashing | 5 | 0 | 0 | versatile:1d10 | martial,axe |
| greatsword | Greatsword | 2d6 | slashing | 5 | 0 | 0 | heavy,two_handed | martial,sword,blade |
| mace | Mace | 1d6 | bludgeoning | 5 | 0 | 0 | | simple,mace |
| quarterstaff | Quarterstaff | 1d6 | bludgeoning | 5 | 0 | 0 | versatile:1d8 | simple,staff |
| dagger | Dagger | 1d4 | piercing | 5 | 20 | 60 | finesse,light,thrown | simple,dagger,blade |
| belt_knife | Belt Knife | 1d4 | piercing | 5 | 0 | 0 | light | simple,dagger,blade |
| improvised_spear | Improvised Spear | 1d8 | piercing | 5 | 0 | 0 | two_handed | simple,spear |
