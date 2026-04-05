#!/usr/bin/env lobster run
# Driftmoor Fey Glade Orchestrator
# Sequential turn-by-turn character action generation with context injection
#
# Phase 1: Three automated characters (Aeliana, Fennel, Shadowbeast)
# One scene, 1-3 turns, validate condition vector directionality
#
# KEY DESIGN: Sequential, not parallel
# Each character acts in initiative order, reading full scene history up to their turn

name: driftmoor_fey_glade_phase1
description: "Fey Glade scene with three automated characters, sequential turns"

args:
  num_turns:
    type: integer
    default: 3
    description: "Number of full turns to simulate (1 turn = all 3 characters act)"
  starting_turn:
    type: integer
    default: 1
  seed:
    type: integer
    default: 42
    description: "Deterministic seed for initiative rolls"

env:
  DRIFTMOOR_ROOT: "."
  SCENARIO_PATH: "./scenario"
  RUNTIME_PATH: "./runtime"

steps:
  # =========================================================================
  # PHASE 1: Load initial state
  # =========================================================================
  
  - id: load_initial_state
    command: |
      python3 << 'PYTHON_EOF'
      import json
      import sys
      from pathlib import Path
      
      # Load character SOUL.md, IDENTITY.md, CONDITION.md for all three
      characters = {
          "aeliana": {"role": "ranger", "initiative_base": 17},
          "fennel": {"role": "herb_gatherer", "initiative_base": 5},
          "shadowbeast": {"role": "creature", "initiative_base": 15},
      }
      
      state = {
          "characters": characters,
          "scene": {
              "name": "Fey Glade",
              "zones": {
                  "trail": ["aeliana"],
                  "treeline": [],
                  "glade": ["fennel"],
                  "pool": [],
              },
              "history": [],  # Appended with each action
          },
          "turn": 1,
          "initiative_order": ["aeliana", "shadowbeast", "fennel"],  # Sorted by base initiative
      }
      
      print(json.dumps(state, indent=2))
      PYTHON_EOF
    description: "Initialize game state from scenario files"

  # =========================================================================
  # TURN LOOP
  # =========================================================================

  # Turn 1 ================================================================
  
  - id: turn_1_aeliana
    command: |
      python3 << 'PYTHON_EOF'
      import json
      import sys
      
      # This is where we spawn the Aeliana sub-agent
      # For now, mock the response to show the structure
      
      action_output = {
          "character": "aeliana",
          "turn": 1,
          "initiative": 17,
          "internal": "The trail ends here. Warmth in the air, shimmer beyond the trees. Something wrong — place holds its breath.",
          "body_language": "Crouched low, one hand on bowstring, other hovering near quiver. Weight on balls of feet, perfectly still.",
          "spoken": "",
          "action": "Advance carefully to the treeline, senses alert for any shift in the shimmer."
      }
      
      print(json.dumps(action_output, indent=2))
      PYTHON_EOF
    description: "Aeliana's Turn 1 action (initiative 17)"

  - id: append_aeliana_to_history
    command: |
      python3 << 'PYTHON_EOF'
      # Simulate appending Aeliana's action to scene history
      # In the real version, we load scene history, append, and save
      echo "Aeliana's action appended to scene history."
      PYTHON_EOF
    description: "Append Aeliana's output to scene history (available to next character)"

  - id: turn_1_shadowbeast
    command: |
      python3 << 'PYTHON_EOF'
      import json
      import sys
      
      # Shadowbeast's Turn 1
      # NOTE: This prompt will include Aeliana's action from the previous step
      # (simulated here, but in the real version we pass the updated scene history)
      
      action_output = {
          "character": "shadowbeast",
          "turn": 1,
          "initiative": 15,
          "internal": "warmth-pulse close... alert-shape moves toward boundary... shimmer-wrong resists... shadow-body coils... wait... stillness holds...",
          "body_language": "Shadows along the treeline thicken, a deeper darkness pooling and shifting. Tendrils of black mist curl slowly outward, then retract. Faint vibration hums through ground.",
          "spoken": "",
          "action": "Slides sideways along the boundary, keeping equal distance from the watching prey. Settles into stillness opposite the one near the pool."
      }
      
      print(json.dumps(action_output, indent=2))
      PYTHON_EOF
    description: "Shadowbeast's Turn 1 action (initiative 15) — SEES Aeliana's advance"

  - id: append_shadowbeast_to_history
    command: |
      python3 << 'PYTHON_EOF'
      echo "Shadowbeast's action appended to scene history."
      PYTHON_EOF
    description: "Append Shadowbeast output to scene history"

  - id: turn_1_fennel
    command: |
      python3 << 'PYTHON_EOF'
      import json
      import sys
      
      # Fennel's Turn 1
      # NOTE: This prompt includes BOTH Aeliana's and Shadowbeast's actions
      
      action_output = {
          "character": "fennel",
          "turn": 1,
          "initiative": 5,
          "internal": "Pull — toward her. Anchor. Not alone. Cold edge at back. Watching. Waiting. Stillness holds. Sound breaks. Teeth in silence. Do not break. Do not call. Stay. Stay.",
          "body_language": "Fennel freezes, breath shallow and controlled. His raised hand stops mid-motion. Eyes lock on Aeliana's back, then flick once toward the shifting shadow. Stance tightens, knees slightly bent.",
          "spoken": "",
          "action": "Slowly wave arms from glade edge toward her, hold up open-hand stop gesture, then point directly toward the shadowbeast position."
      }
      
      print(json.dumps(action_output, indent=2))
      PYTHON_EOF
    description: "Fennel's Turn 1 action (initiative 5) — SEES both Aeliana and Shadowbeast"

  - id: append_fennel_to_history
    command: |
      python3 << 'PYTHON_EOF'
      echo "Fennel's action appended to scene history."
      PYTHON_EOF
    description: "Append Fennel output to scene history"

  # End of Turn 1 =========================================================
  
  - id: end_of_turn_1_state_update
    command: |
      python3 << 'PYTHON_EOF'
      import json
      
      # After all three characters have acted, update condition vectors and persist state
      updates = {
          "turn": 2,
          "aeliana_condition_delta": {
              "cortisol": 0.25,
              "norepinephrine": 0.15,
              "dopamine": -0.10,
              "acetylcholine": 0.20,
          },
          "shadowbeast_condition_delta": {
              "norepinephrine": 0.10,
          },
          "fennel_condition_delta": {
              "cortisol": 0.15,
              "oxytocin": 0.20,
          },
      }
      
      print(json.dumps(updates, indent=2))
      PYTHON_EOF
    description: "Apply condition delta updates, persist CONDITION.md files for next turn"

  # Turn 2 and 3 would follow the same pattern
  # (Omitted here for brevity; full implementation will include all turns)

  - id: finalize_output
    command: |
      python3 << 'PYTHON_EOF'
      import json
      
      output = {
          "status": "complete",
          "turns_executed": 1,
          "scene": "Fey Glade",
          "characters": ["aeliana", "fennel", "shadowbeast"],
          "validation_status": "Ready for ground_truth.md comparison",
      }
      
      print(json.dumps(output, indent=2))
      PYTHON_EOF
    description: "Finalize and output session summary"
