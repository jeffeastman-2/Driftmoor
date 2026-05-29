# EXPLORATION.md — Exploration Motivation and Anti-Loop Policy
# Driftmoor Engine Draft Specification

---

## Overview

This document defines the intended exploration policy for party-driven
scenes in Driftmoor. The goal is to keep characters moving outward
through meaningful space instead of getting trapped in local inspection
loops.

This is a **draft** spec. It describes the target behavior for the
exploration policy and the engine hooks that should enforce it. The
policy is expected to evolve as we test more scenes.

The core idea is simple:

- local clues are useful only if they change the next decision
- repeated searching in the same zone should lose priority
- once a zone is sufficiently searched, the party should advance
- when one character commits to moving forward, the others should tend
  to follow
- unresolved local puzzles should keep the party in place until they
  either yield progress or are clearly exhausted

This policy complements the existing per-character loop guards. The
loop guards stop repetition; this spec defines why the party should keep
pressing deeper into unexplored territory.

---

## 1. Exploration Goal

Every active party in a scene should have an implicit objective to make
forward progress through the scene until one of the following is true:

- the current zone has been saturated for useful information
- the current zone contains an unresolved puzzle that still has a live
  path to resolution
- the party has a strong reason to remain in place
- movement into the next zone is blocked by a real engine constraint
- the scene's objective has been completed

"Forward progress" means:

- entering a new zone
- investigating a newly visible item or landmark that was not already
  examined
- following a discovered exit, passage, trail, or clue to the next area

Forward progress does **not** mean endlessly re-checking the same local
objects.

---

## 2. Terms

### 2.1 Zone Saturation

A zone is saturated when repeated searches in that zone stop yielding
new facts, new items, new exits, or new risks.

Saturation is a policy concept, not a hard world-state truth. The engine
may approximate it using search counts, discovered items, and repeated
intents.

### 2.2 Forward-Puller

A forward-puller is the character currently most likely to move the party
into a new zone.

A forward-puller may be chosen implicitly by behavior:

- the first character to commit to movement into a new zone
- the character whose last action produced useful new information and
  then moved on
- a character designated by a future party-leader mechanic

### 2.3 Search Churn

Search churn is repeated search behavior in the same zone without new
state changes. Examples:

- searching the snapped torch again after it has already been examined
- repeatedly inspecting a bloodstain after the trail is understood
- rotating among nearby evidence without approaching the next space

Search churn is the behavior this spec is meant to suppress.

---

## 3. State to Track

The engine should track the following exploration state.

### 3.1 Per Character

- visited zones
- last few search targets
- last movement direction or destination
- recent local search history

### 3.2 Per Zone

- number of searches performed
- discovered items
- discovered exits or passages
- unresolved puzzle state and whether it still appears solvable locally
- whether the zone has yielded new information recently
- whether the zone is considered saturated

### 3.3 Party-Wide

- current exploration goal
- last zone where useful progress happened
- nominated forward-puller, if any
- whether the party should be nudged outward

The state does not need to be perfect. It only needs to be good enough to
bias the party toward progress.

---

## 4. Policy Rules

### 4.1 Local Search Rule

Search is allowed when a character is in a zone with unsaturated
information.

If the zone contains an unresolved puzzle, search and interaction should
keep priority until the puzzle either advances, resolves, or is clearly
shown to be a dead end.

Search should lose priority when:

- the same target is searched repeatedly
- the zone has already produced its obvious clues
- the search result has not changed the party's next decision

### 4.2 Redirection Rule

When local search has gone stale, the engine or prompt should prefer:

- movement into an adjacent unexplored zone
- following a passage, trail, or exit
- interacting with a new object that changes the party's position or
  understanding

### 4.3 Party-Follow Rule

If one character commits to moving forward, the others should tend to
follow instead of independently re-litigating the same local evidence.

This can be expressed in prompts, in engine scoring, or in both.

### 4.4 Exhaustion Rule

When a zone has been adequately searched, repeated search intents should
be down-ranked in favor of movement.

When a zone has an unresolved puzzle, repeated search should instead be
interpreted as continued puzzle engagement rather than pure churn, as
long as the actions are still producing new puzzle-relevant state.

The engine may respond with one of the following patterns:

- soft nudge: change the suggested target to a new zone or passage
- hard redirect: replace repeated local search with movement outward
- soft failure: allow the search, but make it less attractive next turn

---

## 5. Recommended Engine Hooks

This policy can be enforced in several places.

### 5.1 Player-Left Prompting

The prompt should explicitly tell the model:

- local clues matter only if they change the next move
- after a zone has been adequately searched, move on
- if a passage or new zone is available, prefer that over another search
- if another party member is already moving forward, follow them

### 5.2 Session-Level Loop Detection

The session loop can detect repeated search signatures and redirect the
character toward a different item or zone.

This is the best place for hard enforcement because it is engine-side and
not dependent on prompt compliance.

### 5.3 Perception / Context Assembly

The context builder can emphasize:

- unexplored exits
- visible items in the current zone
- whether those items have already been examined
- adjacent zones that have not yet been visited

### 5.4 Narration / DM Reinforcement

The narrator can reinforce progress by highlighting:

- what was learned from local search
- what remains unanswered
- which exit or passage now matters

Narration should not keep re-centering the same evidence once the party
has already understood it.

---

## 6. Suggested Implementation Shape

This is the minimal policy shape implied by the current experiments:

- a saturation check for each zone
- a repeated-search detector per character
- a party-level preference for the first successful forward movement
- a forward-puller cue that helps the rest of the party follow
- a redirection path from repeated local search toward unexplored space

The current anti-loop guards are a first pass. This spec is the broader
motivation layer above them.

---

## 7. Non-Goals

This spec does **not** try to solve:

- combat strategy
- puzzle solving
- human player UI
- exact pathfinding heuristics
- narrative style or prose quality

Those are separate problems.

This policy only concerns exploration momentum and the reduction of
stuck-in-place search loops.

---

## 8. Tuning Notes

The following values are expected to change during testing:

- how many repeated searches count as saturation
- how aggressive the engine should be when redirecting movement
- whether one character or the whole party gets nudged first
- how strongly unexplored zones are preferred over already-visited ones

The policy should remain stable even as those thresholds move.

---

## 9. Relationship to Existing Code

The current implementation work is centered around:

- `engine/player_router.py` for prompt-level exploration pressure
- `engine/session.py` for engine-side search and movement redirection
- `engine/verb_resolver.py` for grounded item interaction resolution
- `engine/session.py` and `engine/narrator.py` for reinforcing usable progress

This spec defines the target behavior; the code should be brought into
alignment with it over time.
