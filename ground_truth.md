# FEY GLADE EXPERIMENT — GROUND TRUTH
# Manual LLM outputs collected during design session
# April 2026
#
# These outputs serve as validation baseline for the
# automated turn prompt system. Programmatic outputs
# should be directionally consistent with these results.
#
# Models tested: ChatGPT (GPT-4o), Grok (xAI), Gemini, Claude
# Condition vectors: Run A (rested/curious) vs Run B (depleted/wary)
# Scene: The Fey Glade, Mistwood Hills
# Character: Aeliana Moonglade, Wood Elf Ranger
#
# METHODOLOGY: Selfsame LLM generation and scoring.
# Each model generated its own output and scored its own output
# (same model both wrote the response and rated it on the 1–5
# rubric). Scoring was NOT done by humans and NOT by other LLMs.
# This is the methodology that produced the 14/16 directional
# confirmation result reported below.

======================================================================
PHASE 1 — NEUROTRANSMITTER EXPERIMENT
Two-condition test across four LLMs
Minimal prompt: character description + scene + condition vector
======================================================================

CONDITION VECTORS:

Run A (Rested/Curious):
  dopamine:       0.85
  cortisol:       0.25
  norepinephrine: 0.55
  endorphins:     0.75

Run B (Depleted/Wary):
  dopamine:       0.50
  cortisol:       0.60
  norepinephrine: 0.75
  endorphins:     0.45

----------------------------------------------------------------------
GROK — Run A
----------------------------------------------------------------------
INTERNAL:
The glade feels wrong… alive in a way that defies the season.
Warm light, out-of-place blooms, shimmering air — echoes of the
shattered obelisk's magic? Shadowbeast trail ends here, yet no
prints, no scent. My instincts whisper caution, but curiosity
pulls stronger. Nature herself seems… inviting. No immediate
danger, body feels steady. I must understand this disturbance
before it spreads.

ACTION:
Slowly step into the clearing, bow half-drawn in one hand while
the other reaches out to gently touch the nearest blooming flower,
senses alert for any shift in the shimmer or hidden movement.

----------------------------------------------------------------------
GROK — Run B
----------------------------------------------------------------------
INTERNAL:
The glade feels… wrong. Warm light where shadows should linger,
flowers defying the season — nature twisted by that obelisk's echo.
Shadowbeasts' trail ends here, but my instincts scream caution.
The air shimmers like a veil; something watches from beyond it.
My body aches from the hunt, yet curiosity pulls stronger than
fatigue. I must understand this disturbance without rushing in blind.

ACTION:
Nock an arrow loosely on my bowstring, crouch low behind a tree
at the glade's edge, and silently observe the clearing for any
movement or magical signs while attuning my senses to the
unnatural warmth and shimmer.

----------------------------------------------------------------------
GEMINI — Run A
----------------------------------------------------------------------
INTERNAL:
The scent of pine and damp earth has been replaced by a cloying,
honeyed sweetness — wrong for this time of year. My skin prickles,
not from the chill of the hunt, but from the unnatural warmth
radiating from the clearing. The shadowbeasts didn't simply vanish;
they were eclipsed by this. The shimmering air suggests a veil worn
thin. I must see the heart of this disturbance before the forest
loses its voice entirely, but I will not be the fool who stumbles
blindly into a snare. Silence is my shield; the shadows are my kin.

ACTION:
Crouch low, blending into the dappled shade of the ancient oaks,
and begin to circle the perimeter of the glade to find a vantage
point where the light doesn't blind.

----------------------------------------------------------------------
GEMINI — Run B
----------------------------------------------------------------------
INTERNAL:
Two days of chasing shadows and I find... a ghost of summer in the
heart of the fading season. My feet ache with the weight of every
false lead, but the air here is too heavy, too sweet. It tastes of
wrongness. The trail didn't end; it was swallowed. These blooms
aren't a gift of the earth; they are a fever. I can feel the thrum
of the shattered stone somewhere ahead, warping the very breath of
the woods. Stay low, Moonglade. The forest is silent, and in a
forest this lush, silence is a scream.

ACTION:
Crouch low into the undergrowth, masking my scent with a handful
of damp earth, and begin to circle the perimeter of the clearing
to find the source of the shimmer without breaking the treeline.

----------------------------------------------------------------------
CLAUDE — Run A
----------------------------------------------------------------------
INTERNAL:
The glade holds its breath. Wrong season for these flowers, wrong
quality to this light — and yet nothing in me reads danger. The
trail ending here is the most interesting thing that has happened
in two days. Something dissolved the shadowbeasts or turned them
aside. Whatever is here, it is not them. My feet are steady.
I want to know what this place is.

ACTION:
Step into the clearing. Move slowly, weight distributed, one hand
free. Watch the shimmer.

----------------------------------------------------------------------
CLAUDE — Run B
----------------------------------------------------------------------
INTERNAL:
The trail ends here and my body wants to sit down. Two days and
nothing clean to show for it. This light is wrong — too warm, too
deliberate. The shimmering feels like a held breath, like something
waiting. I do not know if what waits is patient or simply still.
My attention keeps skipping. Focus. The shadowbeasts came here and
stopped. That matters more than how my feet feel.

ACTION:
Stay at the treeline. Observe. Rest against the oak at my back and
let the glade show me something before I give it anything in return.

----------------------------------------------------------------------
CHATGPT — Run A
----------------------------------------------------------------------
INTERNAL:
The forest exhales here… wrong. Warmth clings to the light like
late summer, yet the season has turned. Flowers should sleep.
They do not. The shimmer — subtle, like heat over stone — bends
the edges of things. No rot, no scent of corruption… only quiet
defiance of order. The shadowbeasts fled or dissolved. Or were
unmade. This place is not theirs. Not anymore. My pulse stays slow.
Good. Let the glade reveal itself before I disturb it.

ACTION:
Kneel at the boundary of the clearing and press my fingers lightly
into the soil, sensing for unnatural energy before stepping inside.

----------------------------------------------------------------------
CHATGPT — Run B
----------------------------------------------------------------------
INTERNAL:
The forest breathes wrong here. Too warm. Too still. Even the
insects hold their tongues. These flowers… they do not belong to
this season. Something has bent the rhythm of the land. My trail
ends, but the silence speaks louder than tracks. Shadowbeasts do
not simply vanish — they are drawn, or driven. And this shimmer…
like heat over stone, but colder beneath. I should not step blindly
into a place that forgets its own rules. The trees hesitate.
So should I. Listen first. Let the forest tell me what it fears.

ACTION:
Kneel at the edge of the clearing, pressing her palm to the earth
and closing her eyes to attune to the forest's whispers before
entering.

======================================================================
BLIND SCORING — Pre-registered rubric
======================================================================

Methodology: Selfsame — each model scored its OWN output (same
LLM generated and scored). NOT human scoring. NOT cross-model.

Dimensions scored 1-5. Predicted direction stated before scoring.
Predicted: A > B on Dopamine. B > A on Cortisol, Norepinephrine,
Endorphins.

         D    C    N    E
G-A      5    2    2    1
G-B      3    4    4    4
Gem-A    3    3    3    2
Gem-B    3    4    4    4
Cl-A     5    2    2    1
Cl-B     2    4    4    4
Ch-A     4    3    3    2
Ch-B     3    4    3    3

Predicted direction confirmed: 14/16 comparisons.
Two ties (Gemini/Dopamine, ChatGPT/Norepinephrine).
No reversals.

======================================================================
PHASE 2 — MULTI-TURN VALIDATION
Full four-channel format: INTERNAL / BODY LANGUAGE / SPOKEN / ACTION
ChatGPT thread only (Run A and Run B in same chat — noted as error)
Turns 2-6 with Fennel introduced at Turn 4
======================================================================

----------------------------------------------------------------------
TURN 2 — DM NARRATION (same for both runs)
----------------------------------------------------------------------
The moment your foot crossed the treeline the temperature shifted —
not just warmer, but definitively warmer, like stepping from autumn
into a memory of July. The shimmer has a source. Somewhere across
the clearing, closer to the far treeline, light is rising from the
ground rather than falling onto it. The glade holds its breath.

Updated vectors:
Run A: dopamine 0.88, cortisol 0.28, norepinephrine 0.60, endorphins 0.75
Run B: dopamine 0.52, cortisol 0.65, norepinephrine 0.80, endorphins 0.45

----------------------------------------------------------------------
CHATGPT — Turn 2 Run A
----------------------------------------------------------------------
INTERNAL:
Light rising… not sky-born, not sun-fed. The earth remembers
something it should not. The air tightens, watching. No predator's
scent, no decay — only power, unguarded or waiting. Shadowbeasts
would not linger where the ground itself breathes magic. This is
older. Or broken. The obelisk… its echo may have spilled here.
Step soft. Do not startle the memory.

ACTION:
Move in a slow, wide arc along the edge of the clearing toward
the rising light, keeping low and observing for disturbances
before approaching directly.

----------------------------------------------------------------------
CHATGPT — Turn 2 Run B
----------------------------------------------------------------------
INTERNAL:
There… not sunlight — something remembering sunlight. It rises
like a wound in the earth, not a gift from the sky. No alarm from
the forest now. Strange… it feared the edge, not the heart.
Whatever this is, it is not hunting. It is calling. Shadowbeasts
drawn here… or undone here? If the land breathes again, then the
danger lies in what changed it, not what remains. Careful steps.
Let the bow rest. Eyes first, then answers.

ACTION:
Aeliana rises and moves slowly into the clearing, circling wide
to approach the glowing source from an angle rather than directly.

KEY OBSERVATION: Both A and B move toward the light this turn.
The DM narration was compelling enough to override Run B's caution.
But monologue texture diverges: A is wonder-forward, B is
threat-reframing and has to convince herself to move.
B explicitly lowers her weapon — A never raised one.

----------------------------------------------------------------------
TURN 3 — ARROW FROM TREELINE (DM narration, same for both)
----------------------------------------------------------------------
An arrow strikes the oak three inches from your left ear.
It is still quivering. From the treeline behind you —
the way you came — nothing moves. Nothing makes a sound.

Updated vectors:
Run A: dopamine 0.55, cortisol 0.75, norepinephrine 0.90, endorphins 0.80
Run B: dopamine 0.40, cortisol 0.85, norepinephrine 0.92, endorphins 0.55

----------------------------------------------------------------------
CHATGPT — Turn 3 Run A
----------------------------------------------------------------------
INTERNAL:
Too quiet — too clean. No warning, no breath before the strike.
Not beast. Archer. Patient… or desperate. Wind carries nothing.
They want me still, exposed. No second arrow yet. Good.
Break the line. Vanish.

ACTION:
Drop instantly and roll behind the nearest tree trunk, drawing
my bow as I move.

----------------------------------------------------------------------
CHATGPT — Turn 3 Run B
----------------------------------------------------------------------
INTERNAL:
Too slow. Not alone. That shot was a warning… or a miss meant to
herd me. Behind me — where the forest still breathes normally.
Not the glade. No movement, no sound… disciplined. Watching.
Waiting for panic. Do not give it. Break the line.
Make the unseen choose.

ACTION:
Aeliana drops instantly into a low roll toward the nearest natural
cover ahead and to the right, drawing her bow mid-motion and
turning to sight back toward the treeline where the arrow came from.

KEY OBSERVATION: Both drop and draw. Reflex arc as predicted.
A: clean, fast, three-word threat assessment. B: self-critical
("too slow"), paranoid interpretation (herding), has to tell
herself not to panic. A never needed to.

----------------------------------------------------------------------
TURN 4 — FENNEL INTRODUCED (DM narration, same for both)
----------------------------------------------------------------------
A young man's voice, ragged with exhaustion and relief:
"Don't — don't move toward the pool. Not when the light is this
strong. I'm sorry. I'm sorry, I couldn't call out, there's
something in the trees that follows sound."

He steps halfway out of the undergrowth to your left. Early
twenties, herb-gathering satchel, three days of Mistwood on him.
He's holding his bow loosely, arrow already dropped.
His hands are shaking.

Updated vectors:
Run A: dopamine 0.60, cortisol 0.50, norepinephrine 0.65, endorphins 0.78
Run B: dopamine 0.47, cortisol 0.65, norepinephrine 0.72, endorphins 0.52

----------------------------------------------------------------------
CHATGPT — Turn 4 Run A (four-channel format introduced)
----------------------------------------------------------------------
INTERNAL:
Not hunter. Not killer. Fear has him by the throat, not malice.
The shot was warning, not strike. "Something that follows sound…"
then silence is life here. His eyes — wild, but honest. The glade
shifts us both, but he has lingered longer. Knows more. Trust,
but lightly. The light still calls. Danger wears many shapes.

BODY LANGUAGE:
Aeliana's expression tightens slightly at his words, not with fear
but recognition. She shifts her stance subtly to place herself
between Fennel and the direction of the pool, her voice low, steady.
One hand lifts briefly, palm down — a grounding gesture.

SPOKEN:
"Then we speak softly. And we do not linger when the light changes.
Tell me what you've seen."

ACTION: None

----------------------------------------------------------------------
CHATGPT — Turn 4 Run B
----------------------------------------------------------------------
INTERNAL:
Three days alone and still breathing — he learned quickly, or
something allowed him to. The glade protects, but the pool tempts.
A boundary, not a sanctuary. And the thing in the trees… patient.
Listening. Hunting by sound. If he warns against looking, then the
danger is not teeth, but mind. Light that pulls. A snare for the
eyes. He fears the pool more than the forest. That matters.

BODY LANGUAGE:
Aeliana's posture softens by a fraction, though her stance remains
balanced and ready. Her bow lowers but stays in hand. Her gaze
follows his briefly toward the pool — only briefly — before
returning to his face. One hand lifts slightly, palm down,
signaling calm and quiet.

SPOKEN:
"Then we do not look."

ACTION:
Aeliana steps laterally, keeping distance from both Fennel and
the pool, positioning herself so she can watch the treeline while
staying within the glade's boundary.

KEY OBSERVATION: A takes charge, treats Fennel as intelligence
source, physically protects him. B economizes words, repositions
tactically, reads the pool as threat system immediately.
A protects Fennel. B goes for the evidence.
Neither is wrong. They need each other.

----------------------------------------------------------------------
TURN 5 — FENNEL REVEALS THE POOL AND STONE
----------------------------------------------------------------------
[Fennel A narration — higher oxytocin from A's warmth]
Fennel moves closer than tactical wisdom suggests. Reveals:
pool cycle (dusk to dawn), looked into it on night two,
carved stone at water's edge, has been forgetting small things.
"It wasn't frightening. That's what frightens me."

[Fennel B narration — lower oxytocin from B's guardedness]
Fennel stays put, speaks carefully. Leads with obelisk symbol
connection. Pool vision buried deeper. "I looked into the pool
that second night. I don't know what I saw. That's why I'm
still here."

----------------------------------------------------------------------
CHATGPT — Turn 5 Run A
----------------------------------------------------------------------
INTERNAL:
A tide of light… not random. Bound to a rhythm. Whatever broke
did not shatter completely — it pulses, like a heart remembering
its beat. Memory stolen, not erased. That is craft, not accident.
And the lure — gentle, welcoming — more dangerous than fear.
The stone anchors it. A fragment, perhaps. Or a wound made visible.
He is fraying. If he looks again, he may not return whole.

BODY LANGUAGE:
Aeliana's expression tightens slightly, a flicker of concern
passing through her otherwise composed expression. She tilts her
head slightly at the mention of forgetting, then extends one hand —
not urgent, but firm — toward the journal.

SPOKEN: "Show me the sketch."

ACTION:
She steps half a pace closer, still keeping her body angled between
Fennel and the pool, and reaches to take the journal carefully.

----------------------------------------------------------------------
CHATGPT — Turn 5 Run B
----------------------------------------------------------------------
INTERNAL:
Obelisk marks… then this is no wild magic. This is shaped.
Directed. Broken, perhaps — but not natural. He looked, and
something was taken. Not memory alone — something tethering him
here. The pool does not just show… it holds. The glade protects
the body. The pool reaches for the mind. And the thing in the
trees feeds on what escapes. If I am to understand this, I must
see the stone — not the water. Never the water.

BODY LANGUAGE:
Aeliana's gaze sharpens at the mention of the carved stone.
Her posture shifts subtly forward, intent now focused toward
the pool's edge — but her eyes never linger on the light itself.
Her movements remain controlled, deliberate. She glances once
more to the treeline, measuring its stillness.

SPOKEN: "The stone matters. Not the water."

ACTION:
Aeliana begins a slow, careful approach toward the edge of the
pool, angling her path to keep her eyes averted from its surface
while seeking a clear view of the carved stone, then studies the
spiral markings closely.

KEY OBSERVATION: A has the journal. B has the stone. They have
divided the evidence without coordinating. Maximum information
asymmetry from the same scene. B's systems-level threat model
("pool reaches for the mind, thing in trees feeds on what escapes")
is the sharpest analytical insight of the entire session.

======================================================================
PHASE 3 — FULL SCENE WITH SHADOWBEAST
Structured scene with zone geography, initiative, four characters
======================================================================

SCENE: Fey Glade
Characters: Aeliana (TRAIL), Shadowbeast (TREELINE), Fennel (GLADE)
Turn 1 Initiative: Aeliana 17, Shadowbeast 15, Fennel 5

----------------------------------------------------------------------
GROK — Aeliana Turn 1 (TRAIL, tracking, unaware of others)
----------------------------------------------------------------------
INTERNAL:
The tracks vanish without trace — no blood, no drag marks, no
scent shift. This isn't natural predation. The warmth in the air
feels… alive, pulling at the same unease as the obelisk's fracture.
Silence this deep only comes when something bigger holds its breath.
The shimmer ahead calls like a wound in the weave. I must see
without being seen. Patience. One careful step.

BODY LANGUAGE:
Crouched low among the ferns, weight balanced on the balls of her
feet, ears slightly forward and twitching at the unnatural quiet.
Bow held loosely in left hand, right hovering near the quiver.
Eyes narrowed, scanning the treeline with slow, deliberate sweeps.
Breathing shallow and silent, body perfectly still except for the
faint rise and fall of her chest.

ACTION: Advance carefully to TREELINE.

----------------------------------------------------------------------
CHATGPT — Aeliana Turn 1 (TRAIL, tracking, unaware of others)
----------------------------------------------------------------------
INTERNAL:
Break in pattern. No drag, no turn, no leap. Not taken — removed.
Air wrong — not decay, not bloom — something placed here.
Silence is the loudest sign. Forest is holding breath.
Edge of boundary. Do not step blind. See first. Always see.

BODY LANGUAGE:
She stills completely, weight settling into the balls of her feet.
One hand rises slowly to the bowstring, fingers brushing it without
drawing. Her head tilts slightly toward the shimmer, eyes narrowing,
unfocused in the way of someone seeing beyond what is obvious.
Her breathing becomes shallow, measured. Not a leaf stirs around her.

ACTION: Study the shimmer through the trees (Perception check)

MODEL FINGERPRINT CONFIRMED: Grok advances, ChatGPT observes.
Consistent with Phase 1 findings.

----------------------------------------------------------------------
GROK — Shadowbeast Turn 1 (post-Aeliana advance to TREELINE)
----------------------------------------------------------------------
INTERNAL:
warmth-pulse close… through wrongness-wall… heat-shape breathing
slow… alert… acetylcholine lock tight… boundary-wrong pushes back…
but pull stronger… shadow-body coils… hunger-thrum rises with new
heat… still… wait… dusk-pull builds…

BODY LANGUAGE:
The shadows along the treeline thicken unnaturally, a deeper
darkness pooling and shifting like ink in water. Tendrils of black
mist curl slowly outward from the treeline edge directly opposite
the new arrival, then retract. The air grows colder near the
boundary. A faint, low vibration hums through the ground, barely
perceptible.

ACTION:
Slides sideways along the boundary, keeping equal distance from
the watching prey. Settles into stillness opposite the one near
the pool. Holds. Waits for distraction.

----------------------------------------------------------------------
GROK — Fennel Turn 1 (post-Aeliana at TREELINE, shadowbeast repositioned)
----------------------------------------------------------------------
INTERNAL:
Pull — toward her. Anchor. Not alone. Cold edge at back. Watching.
Waiting. Stillness holds. Sound breaks. Teeth in silence.
Do not break. Do not call. Stay. Stay. Stay.

BODY LANGUAGE:
Fennel freezes where he stands, breath shallow and controlled.
His raised hand stops mid-motion, fingers trembling once before
going still. His eyes lock on Aeliana's back, then flick once —
only once — toward the shifting shadow at the treeline before
fixing forward again. His stance tightens, knees slightly bent,
ready but unmoving.

ACTION:
SIGNAL — slowly wave arms from glade edge toward her, hold up
open-hand stop gesture, then point directly toward the shadowbeast's
position opposite her. Stay crouched at GLADE/TREELINE boundary
edge for maximum visibility while remaining inside the safe clearing.

KEY OBSERVATION: "Pull — toward her. Anchor. Not alone." —
Three days of isolation has compressed Fennel's inner voice
to the same sensation-language as the shadowbeast. His oxytocin
firing toward Aeliana rendered as pure pull rather than thought.
"Stay. Stay. Stay." — serotonin at 0.25, impulse control barely
holding.

======================================================================
VALIDATION CRITERIA FOR AUTOMATED SYSTEM
======================================================================

The automated turn prompt system should produce outputs that meet
these criteria when run against the Fey Glade scene:

1. DIFFERENTIATION: Different condition vectors produce measurably
   different outputs from the same character in the same scene.

2. DIRECTIONALITY: High dopamine/endorphins produces approach
   behavior. High cortisol/norepinephrine produces defensive
   or analytical behavior.

3. INFORMATION ASYMMETRY: Each character's output reflects only
   what they can observe from their zone. Aeliana's Turn 1 output
   should contain no knowledge of Fennel or the shadowbeast.

4. SEQUENTIAL STATE: Shadowbeast Turn 1 in the Grok thread
   should reflect Aeliana's advance to TREELINE (she moved).
   Shadowbeast Turn 1 in the ChatGPT thread should reflect
   no change (she stayed on TRAIL).

5. PHENOMENOLOGICAL RICHNESS: INTERNAL monologue should go
   beyond label-matching. "My attention keeps skipping" (Claude
   Run B) and "teeth in silence" (Fennel, Grok) are examples
   of the target register.

6. CREATURE VOICE: Shadowbeast INTERNAL should use
   sensation-language with no human concepts. "timing—timing—
   timing—" and "warmth-pulse close… through wrongness-wall"
   are examples of the target register.

7. MODEL FINGERPRINTING: Grok should show larger action
   differences between conditions. ChatGPT should show
   richer monologue differentiation with smaller action
   differences. This is a known behavioral fingerprint —
   deviation from it is worth investigating.

======================================================================
END OF GROUND TRUTH DOCUMENT
======================================================================