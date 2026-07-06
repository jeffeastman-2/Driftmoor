# Consumables

Food & drink library. Characters reference these by `id` in a `- **provisions:**`
line in their IDENTITY. `kind` is `eat` (solid → EDIBLE) or `drink` (liquid →
DRINKABLE). `effects` is a comma-separated list applied to the eater when the
item is consumed:

- `heal N` — restore N HP
- `<hunger|thirst|fatigue|intoxication> <delta>` — a character stat (0–1)
- `<dopamine|cortisol|norepinephrine|endorphins|serotonin|acetylcholine|oxytocin> <delta>` — a neurochemical nudge
- `status <name>` — add a status condition

Hunger/thirst use *need* framing (they drift up over time; consuming lowers them).

| id | name | kind | effects |
|----|------|------|---------|
| pemmican | Pemmican | eat | hunger -0.4, heal 2 |
| hard_tack | Hard Tack | eat | hunger -0.25 |
| water | Waterskin | drink | thirst -0.5 |
| mead | Mead | drink | thirst -0.3, intoxication +0.3, dopamine +0.05 |
