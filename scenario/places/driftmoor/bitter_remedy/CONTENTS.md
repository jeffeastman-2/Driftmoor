# CONTENTS.md — The Bitter Remedy

## Items for Sale
| Item | Price | Effect |
|------|-------|--------|
| Healing Salve | 5 gp | Restores 1d4 HP when applied |
| Potion of Healing | 50 gp | 2d4+2 HP |
| Antitoxin | 25 gp | Advantage on poison saves for 1 hour |
| Sleep Draught | 15 gp | Sleep 1d4 hours (DC 12 CON to resist) |
| Glowcap Spores | 10 gp | Illuminates 5-ft radius for 1 hour when released |
| Herbal Poultices | 3 gp | Advantage on CON checks for illness recovery |
| Fire Oil | 25 gp | Coat weapons or use as improvised explosive |
| Shadowbeast Pelt Dye | 10 gp | Stains clothing black, absorbs some light |

## Back Room (restricted)
- Living mass of writhing vines — Lytha's experiment gone wrong
- Volatile alchemical ingredients
- Personal research notes (not accessible without confronting the vine creature)
- Moonlace herb sample (small, reference only — she needs more from near the obelisk)

## Notes for DM
- The vine creature in the back room is a contained hazard — if the party helps clear it, Lytha's gratitude is significant
- Lytha will buy monster parts at fair prices — establish rates based on creature rarity
- Shadowbeast blood is her current priority purchase

---

## Runtime Containers

These containers are authoritative for stock placement and access.

| id | name | owner | access | affordances |
|---|---|---|---|---|
| merchant_stock | Merchant stock displays | lytha | public | container |

## Runtime Things

This table is the authoritative runtime inventory for this place.

| id | name | emoji | container | owner | price | category | affordances | availability | effect |
|---|---|---|---|---|---|---|---|---|---|
| healing_salve | Healing Salve |  |  | lytha | 5 gp | service |  | public | Restores 1d4 HP when applied to wounds |
| potion_of_healing | Potion of Healing |  |  | lytha | 50 gp | service | consumable, drinkable, holdable | public | Restores 2d4+2 HP |
| antitoxin | Antitoxin |  | merchant_stock | lytha | 25 gp | mundane | consumable, drinkable, holdable | public | Advantage on poison saving throws for 1 hour |
| sleep_draught | Sleep Draught |  | merchant_stock | lytha | 15 gp | mundane | consumable, drinkable, holdable | public | Sleep 1d4 hours; DC 12 CON save to resist |
| glowcap_spores_pouch | Glowcap Spores (pouch) |  | merchant_stock | lytha | 10 gp | mundane | holdable | public | Illuminates 5-ft radius for 1 hour when released; clings to surfaces |
| herbal_poultices | Herbal Poultices |  | merchant_stock | lytha | 3 gp | mundane | holdable | public | Advantage on CON checks for illness recovery |
| fire_oil | Fire Oil |  | merchant_stock | lytha | 25 gp | mundane | holdable | public | Coats weapons or functions as improvised explosive; 1d6 fire damage |
| shadowbeast_pelt_dye | Shadowbeast Pelt Dye |  | merchant_stock | lytha | 10 gp | mundane | holdable | public | Stains clothing black; absorbs some light (minor stealth benefit at DM's discretion) |
| shadowbeast_pelt | Shadowbeast pelt |  | merchant_stock | lytha | 8 gp (fresh) / 5 gp (cured) | mundane | holdable | public | See `shadowbeast_parts.md` |
| shadowbeast_blood_vial | Shadowbeast blood (vial) |  | merchant_stock | lytha | 25 gp | mundane | holdable | public | Fresh only (within 2 hours); alchemical vial required |
| shadowbeast_claws | Shadowbeast claws |  | merchant_stock | lytha | 2 gp each | mundane | holdable | public | Any condition |
| shadowbeast_eyes | Shadowbeast eyes |  | merchant_stock | lytha | 20 gp each | mundane | holdable | public | Preserved in alchemical vial only |
| moonlace_herb_bunch | Moonlace herb (bunch) |  | merchant_stock | lytha | 15 gp | mundane | holdable | public | Fresh from near obelisk |
| unusual_plants_or_monster_parts | Unusual plants or monster parts |  | merchant_stock | lytha | Varies | mundane | holdable | public | She will assess on sight |
| custom_remedy_or_potion | Custom remedy or potion |  |  | lytha | Ingredients + 10 gp labor | service | consumable, drinkable, holdable | public | 1-2 days |
| herbal_knowledge_consultation | Herbal knowledge consultation |  |  | lytha | 2 gp or a favor | service |  | public | Immediate |
| monster_part_identification | Monster part identification |  |  | lytha | 1 gp per part | service |  | public | Immediate |
| alchemical_collection_vials_sealed | Alchemical collection vials (sealed) |  | merchant_stock | lytha | 2 gp each | mundane | holdable | public | In stock |
