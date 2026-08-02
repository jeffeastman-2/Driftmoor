# CONTENTS.md — The Broken Lantern

## Creatures
- Tavern regulars and evening customers rotate through the main room.
- Named social anchors in this scene include Tess, Wilfred, Bran, and Marda.

---

## Items

### broken_lantern_sign
*Emoji:* 🏮

A cracked iron lantern hangs above the front door on a bent bracket. The glass is smoke-blackened and one pane is missing entirely. The faded inn emblem is still barely visible under grime and weather.

*(Not pickup-able; flavor.)*

### bar_stool
*Emoji:* 🪑

One loose, mismatched oak stool stands at the end of the bar, repaired with rope lashings and light enough to lift in a hurry. The remaining stools are ordinary fixed furnishings.

*(Pickup-able.)*

*Weapon:* improvised_stool

*Interactions (DM ground truth):*
- **pick up / take** → Awkward but sturdy enough to wield or throw as an improvised weapon.

### service_bell
*Emoji:* 🔔

A brass hand-bell sits near the center of the bar where Tess can reach it without turning. The handle is polished from constant use, while the base is sticky with old ale.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **ring** → The bell cuts through tavern noise. Tess notices immediately; nearby patrons look over.
- **pick up / take** → The bell lifts easily. Taking it openly annoys Tess unless returned quickly.

### room_key_ring
*Emoji:* 🗝️

A thick iron ring holds three stamped room keys and one smaller key for the upstairs linen chest. It usually sits beside Tess while she tracks paid rooms.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **examine** → Key stamps show room numbers and one unmarked utility key.
- **pick up / take** → Easy to pocket; theft is obvious if Tess is watching.

### ale_tankards
*Emoji:* 🍺

Three pewter tankards sit on the wet bar in various states of empty. One is clean, one smells strongly of sour stout, and one still has foam clinging to the rim.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **pick up / take** → Characters can carry one or more tankards without difficulty.
- **drink** → If a tankard has ale remaining, it counts as one cheap tavern drink.

### tip_bowl
*Emoji:* 🪙

A shallow wooden bowl sits near the hearth-side performance space with scattered copper and a bent silver bit. Someone scratched "NO FREE SONGS" into the rim.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **examine** → Contains a small handful of mixed coin from prior performances.
- **pick up / take** → Taking it openly is seen as theft by most patrons.

### lute_case
*Emoji:* 🎵

A worn leather lute case rests near the booths, patched at the seams and smelling faintly of rosin and rain. One buckle is missing and replaced by twine.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **open** → Contains spare strings, a tuning key, and folded sheet scraps.
- **pick up / take** → Portable; ownership disputes likely if taken without asking.

### dice_cup
*Emoji:* 🎲

A chipped clay dice cup lies on a side table with four bone dice and a scoring slate. The cup's lip is cracked but still usable.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **roll** → Produces a simple gambling beat for roleplay; nearby patrons may join.
- **pick up / take** → Easy to pocket; considered petty theft if witnessed.

### kitchen_knife
*Emoji:* 🔪

A broad kitchen knife lies on the prep table beside chopped onions and carrots. The edge is kept practical-sharp, not ceremonial.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **pick up / take** → Functions as an improvised light weapon.

### stew_pot
*Emoji:* 🍲

A black iron stew pot hangs over the kitchen fire, simmering onion broth with root vegetables and a few scraps of fish. Steam keeps the room warm and humid.

*(Not pickup-able while full and hot.)*

*Interactions (DM ground truth):*
- **serve** → Produces basic hot meal portions.
- **taste** → Confirms it is edible, simple, and undersalted.

### coal_scuttle
*Emoji:* 🪣

A dented iron coal scuttle sits near the hearth with enough fuel for one long evening. Coal dust marks the handle and surrounding floorboards.

*(Pickup-able.)*

*Interactions (DM ground truth):*
- **pick up / take** → Portable but heavy when full; leaves visible soot traces.

---

## Notes for DM
- The tavern should feel lived-in: sound, smell, and routine labor in motion.
- Portable objects create opportunities for stealth, service gestures, and social friction.
- Ledger + sealed letter support the payout dispute and suspicious-meeting threads.

---

## Runtime Containers

These containers are authoritative for stock placement and access.

| id | name | owner | access | affordances |
|---|---|---|---|---|
| merchant_stock | Merchant stock displays | tess | public | container |

## Runtime Things

This table is the authoritative runtime inventory for this place.

| id | name | emoji | container | owner | price | category | affordances | availability | effect |
|---|---|---|---|---|---|---|---|---|---|
| lamb_stew_with_bread | Lamb Stew with bread |  | merchant_stock | tess | 2 sp | mundane | consumable, edible, holdable | public |  |
| roasted_fish_with_potatoes | Roasted Fish with potatoes |  | merchant_stock | tess | 3 sp | mundane | consumable, edible, holdable | public |  |
| salted_pork_with_greens | Salted Pork with greens |  | merchant_stock | tess | 4 sp | mundane | consumable, edible, holdable | public |  |
| driftmoor_pie_seafood_and_vegetables | Driftmoor Pie (seafood and vegetables) |  | merchant_stock | tess | 5 sp | mundane | consumable, edible, holdable | public |  |
| driftmoor_ale | Driftmoor Ale |  | merchant_stock | tess | 4 cp | mundane | consumable, drinkable, holdable | public |  |
| apple_cider | Apple Cider |  | merchant_stock | tess | 6 cp | mundane | consumable, drinkable, holdable | public |  |
| fisherman_s_delight_potent_local_spirit | Fisherman's Delight (potent local spirit) |  | merchant_stock | tess | 1 sp | mundane | consumable, drinkable, holdable | public |  |
| private_room_per_night | Private room (per night) |  |  | tess | 5 sp | service |  | public |  |
| shared_room_2_beds_per_person | Shared room, 2 beds (per person) |  |  | tess | 3 sp | service |  | public |  |
| meeting_room_rental | Meeting room rental |  |  | tess | A few silver; negotiable | service |  | public |  |
| bath | Bath |  |  | tess | 2 sp | service |  | public |  |
| laundry | Laundry |  |  | tess | 1 sp | service |  | public |  |
