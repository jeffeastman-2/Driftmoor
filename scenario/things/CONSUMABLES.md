# Consumables

Food & drink library. Characters reference these by `id` in the flat
`## Equipment` list in their IDENTITY (also expanded from a pack's `contents`).
`kind` is `eat` (solid → EDIBLE) or `drink` (liquid → DRINKABLE). `effects` is a
comma-separated list applied to the eater when the item is consumed:

- `heal N` — restore N HP
- `<hunger|thirst|fatigue|intoxication> <delta>` — a character stat (0–1)
- `<dopamine|cortisol|norepinephrine|endorphins|serotonin|acetylcholine|oxytocin> <delta>` — a neurochemical nudge
- `status <name>` — add a status condition

Hunger/thirst use *need* framing (they drift up over time; consuming lowers them).

| id | price | name | kind | effects |
|----|-------|------|------|---------|
| pemmican | 5 sp | Pemmican | eat | hunger -0.4, heal 2 |
| hard_tack | 2 sp | Hard Tack | eat | hunger -0.25 |
| rations | 5 sp | Rations | eat | hunger -0.3 |
| water | 2 sp | Waterskin | drink | thirst -0.5 |
| mead | 2 sp | Mead | drink | thirst -0.3, intoxication +0.3, dopamine +0.05 |
| moonlace |  | Moonlace | eat | dopamine +0.05 |
| mistwood_herbs |  | Mistwood Herbs | eat |  |

