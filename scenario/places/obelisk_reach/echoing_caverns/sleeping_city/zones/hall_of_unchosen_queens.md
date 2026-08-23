# Hall of Unchosen Queens

## Description
Eight dark mirrors stand before the crypt, one answering each adventurer who
enters. Each shows a personally desirable future that is real and possible,
while withholding its cost. Vaelithra offers the same bargain through every
reflection: "Leave the song unfinished, and this future remains possible."

Touching or accepting a vision grants inspiration or a brief appropriate
benefit, but lets the Queen speak privately through that character during the
final ritual. Renouncing the offered futures operates the Choice station.

## Ambient
- light: each mirror illuminates only its viewer
- sound: Vaelithra's voice arrives privately from the glass
- smell: cold stone and faint perfume from an absent court
- temperature: neutral near a vision, bitterly cold between mirrors
- footing: polished black floor with no dust

## Items
### eight_future_mirrors
- label: Eight dark mirrors
- size: large
- weight: 500 lb each
- pickable: false
- wearable: false
- flavor_only: false
- description: Eight dark mirrors that present desirable possible futures while hiding their costs.
- appearance by distance:
  - intermediate: eight black panels holding scenes instead of reflections
  - far: a row of tall dark frames lit from within
  - distant: alternating bands of darkness and colored light
- interactions:
  - examine: Each mirror responds to one viewer and shows a temptation shaped by that person's deepest unfinished want.
  - search: Elven script below the frames says that a freely renounced future can become strength for the binding.

### seventh_chain_key
- label: Seventh-chain key
- size: small
- weight: 2 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A tuning fork of black stone and silver made to carry the unresolved melody into the crypt.
- appearance by distance:
  - intermediate: a two-pronged black-and-silver ritual key
  - far: a slim forked object on a low plinth
  - distant: a small pale glint before the crypt doors
- interactions:
  - examine: It resonates with two possible endings: an easy descending cadence and an incomplete rising phrase awaiting another voice.
  - pick up: The key hums in sympathy with Kaelin's unresolved melody.

## Features / landmarks
- hall_main_threshold: direct entrance from the Avenue
- hall_mirror_threshold: alternate entrance from the Mirror Approach
- crypt_threshold: doors that continuously hesitate a finger-width inward and outward

## Creatures present
- royal_guard

## Exits
- north: Avenue of Sleeping Blades
- northeast: Mirror Approach
- south: Crypt of Seven Chains

