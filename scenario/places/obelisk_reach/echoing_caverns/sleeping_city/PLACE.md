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
Their work ends at the Crypt of Seven Chains, where Queen Vaelithra—the
Chain-Bride—lies on a black bier beneath six connected fey chains—four sound
and two dangerously frayed—while the broken seventh lies on the floor.

The city is not an ordinary ruin. Disturbing its seals can wake inhabitants in
different places and in different states of confusion. Most initially believe
the final hours of Nhal'Zirath are still unfolding. They defend helpless
sleepers, distrust strangers, and do not all agree that their queen should be
freed.

## Resident NPCs and Creatures

### vaelithra
- **type:** creature
- **creature_file:** scenario/creatures/humanoids/drow_priestess_of_lolth/CREATURE.md
- **soul_file:** scenario/creatures/humanoids/drow_priestess_of_lolth/SOUL.md
- **identity_file:** scenario/creatures/humanoids/drow_priestess_of_lolth/IDENTITY.md
- **scene_handle:** Queen Vaelithra
- **position:** 60, 14, -55
- **activation:** zone_entry:Crypt of Seven Chains

### sleeping_mage
- **type:** creature
- **creature_file:** scenario/creatures/humanoids/drow_mage/CREATURE.md
- **soul_file:** scenario/creatures/humanoids/drow_mage/SOUL.md
- **identity_file:** scenario/creatures/humanoids/drow_mage/IDENTITY.md
- **scene_handle:** the web-sleeping mage
- **position:** 74, 94, -45
- **activation:** state:web_sleep_disturbed

### royal_guard
- **type:** creature
- **creature_file:** scenario/creatures/humanoids/drow_elite_warrior/CREATURE.md
- **soul_file:** scenario/creatures/humanoids/drow_elite_warrior/SOUL.md
- **identity_file:** scenario/creatures/humanoids/drow_elite_warrior/IDENTITY.md
- **scene_handle:** the royal guard officer
- **position:** 48, 42, -45
- **activation:** state:hall_seal_breached

### sleeping_sentry
- **type:** creature
- **creature_file:** scenario/creatures/humanoids/drow/CREATURE.md
- **soul_file:** scenario/creatures/humanoids/drow/SOUL.md
- **identity_file:** scenario/creatures/humanoids/drow/IDENTITY.md
- **scene_handle:** the cocooned sentry
- **position:** 48, 88, -45
- **activation:** state:avenue_cocoon_opened

## Who Is Normally Here
- Queen Vaelithra, conscious but crypt-bound
- Hundreds of drow citizens held in temporal web-sleep
- Royal guards preserved at their final posts
- Arcane custodians of the web-sleep and planar seals
- No living surface folk; the approach has been sealed for centuries

## Scene Introductions

### vaelithra
The seventh chain stirs before the footfalls reach the crypt. New minds cross
the old harmonics: brief lives, sharp wants, futures branching around them.
You cannot rise. You do not need to. Let them see the living city their peoples
buried. Let them reach the key believing the choice was always theirs.

### sleeping_mage
The interruption is infinitesimal. A wrong note enters the suspension lattice
and becomes impossible to ignore. The city should be falling. The Queen's
ritual should still be unresolved. Yet dust lies outside the web, and the
strangers' magic belongs to an age you do not recognize. First preserve the
lattice. Then learn how much time has been stolen.

### royal_guard
Foreign movement on the Avenue. The gate has failed; the crypt approach may be
compromised. Your last order was to hold the Hall, but the Queen's final rite
endangered the city you swore to protect. Rally whoever wakes. Establish the
truth. Do not let panic choose your allegiance for you.

### sleeping_sentry
Light moves beyond the cocoon. The last alarm is still sounding in memory, but
the stone outside has aged and the voices are strange. Protect the sleepers.
Call the challenge in Elvish. Strike only if the strangers harm those who
cannot yet defend themselves.

## Connections
- Up through the Broken Lift to the Collapsed Tunnel in the Echoing Caverns
- Deeper sealed districts of Nhal'Zirath are visible through temporal webbing but are not presently traversable

## Dynamic State
- **Current status:** Sealed; Vaelithra conscious; the city suspended in temporal web-sleep
- **Recent events:** None since the joint elven-dwarven sealing
- **Active conditions:** Upper lift destroyed; Gate of Two Peoples locked; four chains sound; two chains frayed; seventh chain broken
- **web_sleep_disturbed:** false
- **hall_seal_breached:** false
- **avenue_cocoon_opened:** false
