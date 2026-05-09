# Scene Config — The Echoing Caverns

## Scene
- **scene_name:** echoing_caverns
- **title:** ECHOING CAVERNS
- **narrative_title:** The Echoing Caverns
- **transcript_title:** ECHOING CAVERNS — Seraphina, Thorgrim, Amara
- **character_summary:** Seraphina (Grok), Thorgrim (DeepSeek), Amara (GPT-4o)
- **default_turns:** 8
- **geometry_file:** scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md
- **place_file:** scenario/places/obelisk_reach/echoing_caverns/PLACE.md

## Time
- **hour:** 14
- **minute:** 0
- **day:** 1
- **season:** spring
- **turn_duration:** 10

## DM
- **provider:** anthropic
- **model:** claude-sonnet-4-20250514

## Scene Notes

The party has just descended through the crack in the cliff face beneath the
Obelisk Reach. Daylight bleeds in behind them; ahead, the Entry Chamber opens
into shadow. None of them has been here before. They know only what Father
Elden told them: that he came here decades ago, that his three companions did
not leave, and that something in these caves still hums in time with the
obelisk above.

This is exploration first. Combat is possible (shadowbeasts in deeper
chambers) but should not be forced. Watch for: who takes point, who watches
the rear, who reads the carvings, who picks up what.

## Spelunking Notes (shared)

Father Elden gave the party careful counsel before they descended. The
characters know, in-fiction, the following caver's wisdom:

- **Stay together.** No one wanders out of torchlight alone. The caverns
  echo wrong; a lost voice may not find its way back to the right chamber.
- **Mark the path.** Chalk arrows at every junction, pointing back toward
  the entrance. Do not trust memory in here. (Amara carries chalk; Seraphina
  has charcoal sticks.)
- **One torch lit, one held in reserve.** Amara's torch is the lit one.
  Thorgrim has a second wrapped in oilcloth in his pack.
- **Three knocks means trouble.** A pre-arranged signal: three sharp raps
  of metal on stone, repeated, means come back to this chamber now.
- **The pool is not for drinking, washing, or wading.** Whatever it is,
  it isn't only water.
- **The remains are to be wrapped before being moved.** Father Elden was
  explicit: bones first, dignity second only to safety.
- **Search each chamber before pressing on.** Father Elden was explicit:
  his companions died because they pushed deeper before securing what they
  had already entered. Walls, floors, corners, and ceilings all bear
  examining. The caverns reward thoroughness — old hands, hidden seams,
  things tucked where torchlight does not naturally fall. Do not move to
  the next chamber until the current one has been searched.

## Characters

### seraphina
- **type:** player
- **soul_file:** scenario/people/players/seraphina/SOUL.md
- **identity_file:** scenario/people/players/seraphina/IDENTITY.md
- **scene_handle:** the half-elf rogue
- **hp:** 9
- **ac:** 11
- **provider:** xai
- **model:** grok-3
- **dopamine:** 0.55
- **cortisol:** 0.4
- **norepinephrine:** 0.6
- **endorphins:** 0.5
- **serotonin:** 0.5
- **acetylcholine:** 0.7
- **oxytocin:** 0.35
- **dopamine_baseline:** 0.5
- **dopamine_volatility:** 0.5
- **cortisol_baseline:** 0.4
- **cortisol_volatility:** 0.5
- **acetylcholine_baseline:** 0.65
- **acetylcholine_volatility:** 0.4

### thorgrim
- **type:** player
- **soul_file:** scenario/people/players/thorgrim/SOUL.md
- **identity_file:** scenario/people/players/thorgrim/IDENTITY.md
- **scene_handle:** the dwarf fighter
- **hp:** 13
- **ac:** 18
- **provider:** deepseek
- **model:** deepseek-chat
- **dopamine:** 0.45
- **cortisol:** 0.35
- **norepinephrine:** 0.5
- **endorphins:** 0.45
- **serotonin:** 0.6
- **acetylcholine:** 0.6
- **oxytocin:** 0.5
- **dopamine_baseline:** 0.45
- **dopamine_volatility:** 0.3
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.4
- **serotonin_baseline:** 0.6
- **serotonin_volatility:** 0.25

### amara
- **type:** player
- **soul_file:** scenario/people/players/amara/SOUL.md
- **identity_file:** scenario/people/players/amara/IDENTITY.md
- **scene_handle:** the Lathander cleric
- **hp:** 10
- **ac:** 16
- **provider:** openai
- **model:** gpt-4o
- **dopamine:** 0.5
- **cortisol:** 0.4
- **norepinephrine:** 0.45
- **endorphins:** 0.5
- **serotonin:** 0.6
- **acetylcholine:** 0.55
- **oxytocin:** 0.55
- **dopamine_baseline:** 0.5
- **dopamine_volatility:** 0.4
- **cortisol_baseline:** 0.35
- **cortisol_volatility:** 0.5
- **serotonin_baseline:** 0.6
- **serotonin_volatility:** 0.3
- **oxytocin_baseline:** 0.5
- **oxytocin_volatility:** 0.4

### giant_spider
- **type:** creature
- **creature_file:** scenario/creatures/giant_spider.md
- **soul_file:** scenario/creatures/giant_spider_soul.md
- **identity_file:** scenario/creatures/giant_spider_identity.md
- **scene_handle:** the giant spider
- **hp:** 26
- **ac:** 14
- **faction:** hostile
- **activation:** zone_entry:Secret Chamber
- **provider:** deepseek
- **model:** deepseek-chat
- **pronouns:** it/its
- **weapons:** spider_bite+5
- **armor:** natural_armor_spider
- **dopamine:** 0.6
- **cortisol:** 0.2
- **norepinephrine:** 0.7
- **endorphins:** 0.5
- **serotonin:** 0.4
- **acetylcholine:** 0.85
- **oxytocin:** 0.0
- **dopamine_baseline:** 0.55
- **dopamine_volatility:** 0.4
- **cortisol_baseline:** 0.2
- **cortisol_volatility:** 0.4
- **oxytocin_baseline:** 0.0
- **oxytocin_volatility:** 0.0

## Scene Introductions

### seraphina
You squeezed through the crack first — of course you did; the dwarf wouldn't fit and the cleric was carrying a torch you didn't want anywhere near your eyes. Inside: a low, wide chamber, colder than the hillside above, and unnaturally still. The wind that scoured the Reach does not follow you down here. There is an old iron bracket on the wall just inside, rust-pitted; tally marks scratched into the rock nearby — nineteen vertical, a slanting twentieth that trails off. Someone was counting something here, a long time ago, and stopped mid-stroke. From deeper in the cave: a faint, distant sound, not wind, not water, almost rhythmic. Father Elden told you three of his companions died down here. He did not tell you what killed them.

Elden's parting words ride the back of your mind: *stay in torchlight, mark every turn, three knocks means come back.* You have a stub of charcoal in a belt pouch for marking; Amara has chalk. Whatever quiet thing you do alone in here, do it within sight of the others.

### thorgrim
You shouldered through the crack last, plate scraping stone, and straightened in a chamber that should not be this cold. Daylight from the entrance dies a few paces in. The half-elf is already crouched at the wall reading scratches like a poacher reading tracks; the cleric's torch is up and the shadows behind it lean wrong. There is a sound from deeper in — something between a hum and a held note, threading the silence. Your axe is already loose in your hand. You did not draw it. Father Elden's voice in your memory: *three of them. Sera went in first. None of them came out.* You are first into the dark on this one. Make it count.

Elden's other words sit closer: *stay together, mark every junction, three knocks of steel on stone means form up here.* You carry a second torch wrapped in oilcloth, and a stub of chalk in your belt pouch beside the whetstone. Underground is dwarf country; the others will look to you for tempo. Don't let them strung out across more than one chamber.

### amara
The crack opened into a chamber colder than any cave should be in spring. Your torch threw light in a wedge that the dark refused to hold — shadows pooled at the edges of the chamber like water finding its level. The dwarf came through behind you, plate ringing against stone; the half-elf rogue was already inside, reading scratches on the wall. Lathander's warmth in your chest felt distant here, as if the dawn-god's reach did not extend underground in quite the same way. You could feel something deeper in: not malice, exactly — a pressure, a hum that matched the obelisk above. Father Elden trusted you with this. *Bring back what you can,* he had said. *Even the bones.*

Elden gave you the chalk himself, pressed into your palm at the trailhead with a working cleric's seriousness: *mark every junction, both directions. Stay in torchlight. If anything goes wrong, three knocks on stone and we form up.* The torch in your hand is the only lit one; Thorgrim has the second in reserve. Whatever the pool is, you are not to wade. The remains, when you find them, are to be wrapped — he was firm on that.

### giant_spider
Stillness. Eight feet braced against cold stone above. The web-strands hum faint with the small things that live in the dark — but no warmth, no heavy tread, not for a long time. The chamber-mouth has been silent. The hairline in the far stone has not parted. You wait. You have waited longer than this. The webs hold. The vault below is cold and unmoving. Should warmth come — should the wall part and feet enter — drop. Bite the soft thing first. Wrap what does not die fast.

## Game State Sections
- file: scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md
- header: Relevant Lore (DM only) | file: scenario/things/obelisk_shards.md
- header: Creatures in Scene | file: scenario/creatures/giant_spider.md
- header: Scene Notes | file: scenes/echoing_caverns.md#Scene Notes
