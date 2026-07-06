# Gear

Mundane non-weapon, non-armor possessions — tools, trinkets, and other
wearables — as Thing templates. A character's IDENTITY references these by `id`
in an Equipment sub-list (e.g. `- **tools:** thieves_tools`), optionally
overriding the display name for that character's instance
(`- **wearables:** bracelet: Wooden vine-carved bracelet`).

`kind` drives the affordance:
- `tool` — holdable, usable (`use the ...`); may `produce` another Thing
- `wearable` — occupies a body slot (`wear`/`remove`)

`effects` is the same comma-separated grammar as CONSUMABLES.md (usually empty
for plain gear; e.g. a ring might carry `ac +1` or a stat).

| id | name | kind | effects |
|----|------|------|---------|
| bracelet | Bracelet | wearable | |
| ring | Ring | wearable | |
| cloak | Cloak | wearable | |
| thieves_tools | Thieves' Tools | tool | |
| disguise_kit | Disguise Kit | tool | |
| healers_kit | Healer's Kit | tool | |
| torch | Torch | tool | |
