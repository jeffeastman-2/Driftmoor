# Armor

Worn armor library. A character references armor by `id` in their IDENTITY
`## Equipment` list. Worn armor REPLACES the base of the AC calculation
(``ac_base`` + DEX, capped per ``ac_dex_cap``; `none` = uncapped light armor);
shields/rings/potions are additive `ac +N` effects instead (see GEAR.md).

Natural AC (a creature's intrinsic defense — a spider's 14, a shadowbeast's 11)
is NOT armor: it's the creature's `natural_ac` in its own stat block, so it does
not live here.

| id | name | ac_base | ac_dex_cap | stealth_disadvantage |
|----|------|---------|------------|----------------------|
| plate_armor | Plate Armor | 18 | 0 | true |
| chain_mail | Chain Mail | 16 | 0 | true |
| studded_leather | Studded Leather | 12 | none | false |
| leather_armor | Leather Armor | 11 | none | false |
| clothing | Normal Clothing | 10 | none | false |
