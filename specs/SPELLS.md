# SPELLS

Practical reference for human DMs running Driftmoor today.

This file documents the spells currently implemented in Python spell resolution.
Source of truth is the spell book in engine/spell_resolver.py.

## Contributor Checklist (When Adding Or Changing A Spell)

1. Update resolver data in engine/spell_resolver.py.
2. Update cast behavior in engine/spell_resolver.py if mechanics changed.
3. Add or update unit tests in tests/test_spell_resolver.py.
4. Add or update session integration tests in tests/test_session.py for turn-loop behavior.
5. Add or update resume/checkpoint tests when ongoing effects are involved.
6. Add or update this file's spell entry (name, engine type, dice, concentration, duration, DM note).
7. If behavior is partial, update the TODO section below.
8. Run tests/test_spells_spec_sync.py and relevant spell/session test subsets.

## Scope And Limits

- This is current engine behavior, not full 5e rules text.
- Spell use is validated against known or prepared lists.
- Level 1+ spells consume slots; cantrips do not.
- If a caster starts a new concentration spell, prior concentration effect ends.
- Durations are tracked in rounds in runtime state and tick down once per completed turn.
- Unknown or unavailable spell names are rejected in session adjudication.
- Most offensive spells currently apply listed damage directly to targets in request order.
- Saving throws, attack-roll-to-hit, area templates, and many rider effects are not yet modeled.

## Cantrips (Level 0)

### Fire Bolt
- Engine type: damage
- Dice: 1d10
- Concentration: no
- Duration: instantaneous
- DM note: Applies direct damage to each target in the cast request.

### Sacred Flame
- Engine type: damage
- Dice: 1d8
- Concentration: no
- Duration: instantaneous
- DM note: Target makes a Dex save vs caster save DC; on success, no damage.

### Vicious Mockery
- Engine type: damage
- Dice: 1d4
- Concentration: no
- Duration: instantaneous
- DM note: Target makes a Wis save vs caster save DC; on failure takes damage and receives a one-time disadvantage rider on its next combat-resolver attack.

### Spare the Dying
- Engine type: stabilize
- Dice: none
- Concentration: no
- Duration: instantaneous
- DM note: Emits stabilize_attempt event; full death-save state machine is not yet implemented.

### Guidance
- Engine type: utility
- Dice: none
- Concentration: yes
- Duration: 10 rounds
- DM note: Tracked as active concentration effect only; bonus-to-check application is not yet wired.

### Light
- Engine type: utility
- Dice: none
- Concentration: no
- Duration: 600 rounds
- DM note: Tracked as active effect only; illumination and visibility changes are not yet modeled.

## Level 1 Spells

### Healing Word
- Engine type: heal
- Dice: 1d4 + spellcasting ability modifier
- Concentration: no
- Duration: instantaneous
- DM note: Heals each listed target, clamped to target max HP.

### Cure Wounds
- Engine type: heal
- Dice: 1d8 + spellcasting ability modifier
- Concentration: no
- Duration: instantaneous
- DM note: Heals each listed target, clamped to target max HP.

### Guiding Bolt
- Engine type: damage
- Dice: 4d6
- Concentration: no
- Duration: instantaneous
- DM note: Uses spell attack roll (d20 + spell attack bonus vs target AC); hit deals damage. Advantage-on-next-attack rider is not modeled yet.

### Magic Missile
- Engine type: damage
- Dice: 3d4+3
- Concentration: no
- Duration: instantaneous
- DM note: Auto-hit is implemented as three missiles (1d4+1 each), allocated round-robin across listed targets.

### Burning Hands
- Engine type: damage
- Dice: 3d6
- Concentration: no
- Duration: instantaneous
- DM note: Targets make Dex save vs caster save DC; success takes half damage (rounded down), failure takes full damage. Cone geometry selection is not yet modeled.

### Bless
- Engine type: utility
- Dice: none
- Concentration: yes
- Duration: 10 rounds
- DM note: Tracked as concentration effect; d4 bonus to attack and saves is not yet applied mechanically.

### Shield of Faith
- Engine type: utility
- Dice: none
- Concentration: yes
- Duration: 100 rounds
- DM note: Tracked as concentration effect; AC bonus is not yet applied mechanically.

### Faerie Fire
- Engine type: utility
- Dice: none
- Concentration: yes
- Duration: 10 rounds
- DM note: Tracked as concentration effect; outline and advantage effects are not yet applied.

### Sanctuary
- Engine type: utility
- Dice: none
- Concentration: no
- Duration: 10 rounds
- DM note: Tracked as active effect; targeting/ward behavior is not yet enforced.

### Shield
- Engine type: utility
- Dice: none
- Concentration: no
- Duration: 1 round
- DM note: Tracked as active effect; reactive timing and AC bonus behavior are not yet enforced.

### Teleport
- Engine type: teleport
- Dice: none
- Concentration: no
- Duration: instantaneous
- DM note: 7th-level slot is consumed by the resolver; the actual relocation is applied by the session, which owns scene geometry and position state. The caster lands at a named zone (centroid) or landmark in the current scene; mishap/associated-object range tables are not modeled.

## Session And Resume Semantics

- Active spell effects and concentration owner map are checkpointed.
- Resume restores in-progress spell durations and concentration state.
- After resume, concentration replacement still works (for example, Guidance then Bless).
- Duration countdown continues across resumed runs (one round tick per completed turn).

## TODO (Implementation Roadmap)

This is a mechanics backlog for bringing spell behavior closer to table 5e.

### High Priority

- [ ] Add attack-roll and save pipelines for spells that require them.
- [ ] Implement area-of-effect targeting and geometry selection.
- [ ] Apply utility riders currently tracked but not enforced (Bless, Guidance, Shield of Faith, Faerie Fire, Sanctuary, Shield).
- [ ] Emit explicit expiry events in turn narration/logs when timed effects end.

### Damage Cantrip/Spell Gaps

- [ ] Guiding Bolt: apply advantage rider for the next attack against target.
- [ ] Burning Hands: cone geometry/template target selection.

### Utility And Defensive Gaps

- [ ] Guidance: apply bonus to the next ability check, then consume effect.
- [ ] Light: integrate with scene visibility/line-of-sight model.
- [ ] Bless: apply d4 to attack rolls and saving throws for affected allies.
- [ ] Shield Of Faith: apply temporary AC bonus while effect persists.
- [ ] Faerie Fire: apply visibility/advantage behavior per target.
- [ ] Sanctuary: enforce ward targeting logic and save gate for attackers.
- [ ] Shield: enforce reaction timing window and temporary AC adjustment.

### Systemic Follow-Ups

- [ ] Add per-spell integration tests that verify both cast-time and ongoing-turn behavior.
- [ ] Add explicit resolver hooks for concentration break on damage/incapacitation.
- [ ] Add spell upcasting behavior (slot scaling) where applicable.
- [ ] Keep this file synchronized with engine/spell_resolver.py whenever spell entries change.
