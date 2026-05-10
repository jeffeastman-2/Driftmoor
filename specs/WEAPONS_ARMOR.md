# WEAPONS.md and ARMOR.md FORMAT SPECIFICATION

`WEAPONS.md` and `ARMOR.md` are library tables: shared catalogs of
mechanical equipment stats that characters reference by `id`. They are
parsed as Markdown pipe tables.

Parser: `engine/weapon_loader.py::load_weapons`, `::load_armors`. The
table reader is `_parse_md_table`.

Currently both files live at `scenario/things/WEAPONS.md` and
`scenario/things/ARMOR.md`. They are scenario-wide singletons, not
per-scene.

## Table format

```markdown
# <Title>

<optional prose explanation>

| col1 | col2 | ... |
|------|------|-----|
| v11  | v12  | ... |
| v21  | v22  | ... |
```

Rules:

1. Header row defines column names (lowercased, used as dict keys).
2. The separator row (`|---|---|`) must follow the header.
3. Every subsequent row of the form `| ... | ... |` is parsed as a record.
4. Cell values are trimmed; no type inference is done in the parser —
   the consumer is responsible for casting (most numeric fields are cast
   by the dataclass constructor downstream).
5. Empty cells become empty strings.
6. Prose before, after, and between tables is ignored.

## WEAPONS.md schema

Required columns:

| column | type | meaning |
|---|---|---|
| id | str | Unique key; characters reference this in IDENTITY/CONFIG |
| name | str | Display name |
| damage | str | Dice expression, e.g. `1d8`, `2d6`, `1d4+1` |
| damage_type | str | `slashing`, `piercing`, `bludgeoning`, `radiant`, `fire`, etc. |
| reach | int | Melee reach in feet (0 for ranged-only) |
| range_normal | int | Normal range in feet (0 if melee-only) |
| range_max | int | Maximum range in feet (0 if melee-only) |
| properties | csv | Comma-separated property flags |

### `properties` flag vocabulary

- `finesse` — use STR or DEX, attacker's choice.
- `light` — usable in dual-wield off-hand.
- `heavy` — disadvantage for Small creatures.
- `two_handed` — requires two hands.
- `versatile:<dice>` — one-handed damage as listed; two-handed damage
  per the suffix (e.g. `versatile:1d10`).
- `thrown` — usable as a ranged thrown weapon.
- `ammunition:<type>` — requires a specific ammunition.
- `loading` — only one shot per attack action.
- `reach` — melee reach extended (10 ft); for weapons whose `reach`
  column is already > 5 this is redundant.
- `natural` — creature's natural weapon; not a manufactured item.

### Notes

- `attack_bonus` is **not** stored in WEAPONS.md. It is per-character
  and recorded in the character's CONFIG.md as `<weapon_id>+N`.
- For natural creature weapons, `id` should be `<creature>_<part>`
  (e.g. `shadowbeast_claw`, `spider_bite`).

## ARMOR.md schema

Required columns:

| column | type | meaning |
|---|---|---|
| id | str | Unique key |
| name | str | Display name |
| ac_base | int | Base AC value |
| ac_dex_cap | int or `none` | Max DEX modifier added to AC; `none` = uncapped (light armor) |
| stealth_disadvantage | bool | `true` / `false` |

### Authoring conventions

- `ac_base` for heavy armor: plate 18, chain mail 16, splint 17.
- `ac_base` for medium armor: scale mail 14, half-plate 15.
- `ac_base` for light armor: leather 11, studded leather 12.
- `ac_base: 10` represents unarmored; pair with `ac_dex_cap: none`.
- Class features that grant a special AC formula (Draconic Resilience,
  Unarmored Defense, Mage Armor) are represented as their own armor
  rows with `ac_base` reflecting the resulting numeric AC at the
  authoring character's stats. Re-derive per-character if scaling is
  needed.
- Natural-armor entries for creatures use `id = natural_armor_<creature>`.

## Authoring rules

1. `id` must be unique within each file. Duplicate ids silently
   overwrite the earlier row in the loader's dict.
2. Use snake_case for ids: `chain_mail`, not `Chain Mail`.
3. Keep the columns in the documented order. Re-ordering won't break
   parsing (column names are used as keys) but consistency aids review.
4. Do not introduce new columns without updating both this spec and
   the corresponding dataclass in `models/weapon.py`.
5. Prose above the table should explain conventions specific to the
   file (e.g. "`ac_dex_cap: none` means uncapped"), not duplicate this
   spec.

## Open issues

- `properties` parsing is by string-contains, not by structured flag.
  A weapon with the `light` property and one with `flight` would both
  match a `light` lookup if any such lookup existed.
- `damage` is currently a single dice expression. Multi-die weapons
  (e.g. brutal critical) and weapons with damage type variations
  (silvered, magical bonus) need extension.
- No validator confirms creature natural-weapon ids match the actual
  creature record's expected weapon set.
