# PLACE.md — The Sleeping City of Nhal'Zirath

## Place Identity
- **id:** sleeping_city

## Description and Atmosphere
Nhal'Zirath is a drow city caught in the instant of its defeat. Translucent
temporal webbing fills its alcoves and side streets, preserving citizens,
soldiers, and court officials as though they drew breath only a moment ago.
Nothing has rotted. Nothing has truly slept. Pale violet light crawls through
the web in pulses too slow to be a heartbeat.

The only surviving approach is a dwarven freight lift buried behind the
deliberately collapsed tunnel in the Echoing Caverns. Elven harmonics and
dwarven mechanisms cooperate at every important threshold: evidence that the
two peoples built the prison together, then destroyed the road behind them.
Beyond the city, their work ends at the Crypt of Seven Chains, where Queen Vaelithra—the
Chain-Bride—lies on a black bier beneath six connected fey chains—four sound
and two dangerously frayed—while the broken seventh lies on the floor.

The city is not an ordinary ruin. Disturbing its seals can wake inhabitants in
different places and in different states of confusion. Most initially believe
the final hours of Nhal'Zirath are still unfolding. They defend helpless
sleepers, distrust strangers, and do not all agree that their queen should be
freed.

## Resident NPCs and Creatures

### sleeping_mage
- **type:** creature
- **creature_file:** scenario/creatures/humanoids/drow_mage/CREATURE.md
- **soul_file:** scenario/creatures/humanoids/drow_mage/SOUL.md
- **identity_file:** scenario/creatures/humanoids/drow_mage/IDENTITY.md
- **scene_handle:** the web-sleeping mage
- **position:** 65, 98, -95
- **activation:** state:web_sleep_disturbed

### sleeping_sentry
- **type:** creature
- **creature_file:** scenario/creatures/humanoids/drow/CREATURE.md
- **soul_file:** scenario/creatures/humanoids/drow/SOUL.md
- **identity_file:** scenario/creatures/humanoids/drow/IDENTITY.md
- **scene_handle:** the cocooned sentry
- **position:** 55, 102, -95
- **activation:** state:avenue_cocoon_opened

## Who Is Normally Here
- Hundreds of drow citizens held in temporal web-sleep
- Royal guards preserved at their final posts
- Arcane custodians of the web-sleep and planar seals
- No living surface folk; the approach has been sealed for centuries

## Scene Introductions

### sleeping_mage
The interruption is infinitesimal. A wrong note enters the suspension lattice
and becomes impossible to ignore. The city should be falling. The Queen's
ritual should still be unresolved. Yet dust lies outside the web, and the
strangers' magic belongs to an age you do not recognize. First preserve the
lattice. Then learn how much time has been stolen.

### sleeping_sentry
Light moves beyond the cocoon. The last alarm is still sounding in memory, but
the stone outside has aged and the voices are strange. Protect the sleepers.
Call the challenge in Elvish. Strike only if the strangers harm those who
cannot yet defend themselves.

## Connections
- North through the Gate of Two Peoples to the freight level (level-2)
- South down the Stairway to Royal Precinct (level-4)
- Deeper sealed districts of Nhal'Zirath are visible through temporal webbing but are not presently traversable

## Dynamic State
- **Current status:** Sealed; Vaelithra conscious; the city suspended in temporal web-sleep
- **Recent events:** None since the joint elven-dwarven sealing
- **Active conditions:** Upper lift destroyed; Gate of Two Peoples locked; four chains sound; two chains frayed; seventh chain broken
- **web_sleep_disturbed:** false
- **hall_seal_breached:** false
- **avenue_cocoon_opened:** false
